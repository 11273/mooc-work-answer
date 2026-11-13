"""在当前原生平台构建单文件程序，并在隔离的中文路径中运行成品自检。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
SOURCES = ("StartWork.py", "update.py", "pyproject.toml", "StartWorkLite.spec",
           "AIMoocMain", "ZYKMoocMain", "MoocMain", "NewMoocMain", "base")


def native_target():
    system = {"win32": "windows", "darwin": "macos", "linux": "linux"}.get(sys.platform)
    machine = {"amd64": "x64", "x86_64": "x64", "arm64": "arm64", "aarch64": "arm64"}.get(platform.machine().lower())
    if not system or not machine:
        raise RuntimeError("Unsupported build host")
    return system, machine


def validate_version(value):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._+-]{0,79}", value):
        raise ValueError("Build version must be a safe tag or verification identifier")
    return value


def stage_sources(source, target, version):
    for name in SOURCES:
        original, copied = source / name, target / name
        if original.is_dir():
            shutil.copytree(original, copied, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        else:
            shutil.copy2(original, copied)
    icon = target / "images" / "icon.ico"
    icon.parent.mkdir()
    shutil.copy2(source / "images" / "icon.ico", icon)
    entrypoint = target / "StartWork.py"
    text = entrypoint.read_text(encoding="utf-8")
    marker = '_RELEASE_TAG_PLACEHOLDER = "${TAG_NAME}"'
    if text.count(marker) != 1:
        raise RuntimeError("Release version marker was not found exactly once")
    entrypoint.write_text(text.replace(marker, "_RELEASE_TAG_PLACEHOLDER = " + repr(version), 1), encoding="utf-8")


def smoke_check(executable, version, architecture):
    with tempfile.TemporaryDirectory(prefix="mooc-package-smoke-") as folder:
        working = Path(folder) / "中文 运行目录"
        temporary = Path(folder) / "中文 临时目录"
        working.mkdir()
        temporary.mkdir()
        relocated = working / executable.name
        shutil.copy2(executable, relocated)
        environment = os.environ.copy()
        for key in ("PYTHONPATH", "PYTHONHOME"):
            environment.pop(key, None)
        for key in ("TMPDIR", "TEMP", "TMP"):
            environment[key] = str(temporary)
        result = subprocess.run([str(relocated), "--self-test"], cwd=working, env=environment,
                                capture_output=True, text=True, encoding="utf-8", timeout=180)
        if result.returncode:
            raise RuntimeError("Packaged executable failed:\n" + result.stdout + result.stderr)
        report = json.loads(result.stdout)
        expected_machine = {"x64": {"amd64", "x86_64"}, "arm64": {"arm64", "aarch64"}}[architecture]
        if not report.get("ok") or not report.get("frozen") or report.get("version") != version:
            raise RuntimeError("Executable self-test or injected version failed: " + result.stdout)
        if report.get("machine", "").lower() not in expected_machine:
            raise RuntimeError("Executable architecture differs from the artifact label")
        return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True)
    parser.add_argument("--platform", choices=("windows", "linux", "macos"))
    parser.add_argument("--arch", choices=("x64", "arm64"))
    parser.add_argument("--dist", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    system, architecture = native_target()
    if (args.platform and args.platform != system) or (args.arch and args.arch != architecture):
        parser.error("PyInstaller must run on the matching native OS and architecture")
    version = validate_version(args.version)
    name = f"MoocWorkAnswer-{version}-lite-{system}-{architecture}"
    destination = args.dist.resolve()
    destination.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="mooc-package-build-") as folder:
        staging = Path(folder) / "source"
        staging.mkdir()
        stage_sources(ROOT, staging, version)
        environment = os.environ.copy()
        environment["MOOC_BUILD_NAME"] = name
        environment["PYINSTALLER_CONFIG_DIR"] = str(Path(folder) / "cache")
        subprocess.run([sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean",
                        "--distpath", str(destination), "--workpath", str(Path(folder) / "work"),
                        str(staging / "StartWorkLite.spec")], cwd=staging, env=environment, check=True)
    executable = destination / (name + (".exe" if system == "windows" else ""))
    report = smoke_check(executable, version, architecture)
    report["sha256"] = hashlib.sha256(executable.read_bytes()).hexdigest()
    executable.with_name(executable.name + ".smoke.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    executable.with_name(executable.name + ".sha256").write_text(f"{report['sha256']}  {executable.name}\n", encoding="utf-8")
    print(json.dumps(report))


if __name__ == "__main__":
    main()

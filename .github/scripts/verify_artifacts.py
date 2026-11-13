"""验证下载后的四个平台成品、校验文件和自检报告。"""
import argparse
import hashlib
import json
from pathlib import Path


TARGETS = {
    "windows-x64": ("win32", {"amd64", "x86_64"}, ".exe"),
    "linux-x64": ("linux", {"x86_64"}, ""),
    "macos-x64": ("darwin", {"x86_64"}, ""),
    "macos-arm64": ("darwin", {"arm64", "aarch64"}, ""),
}
CHECKS = {"aes", "lxml", "https_certificates", "unicode_paths", "markdown", "word", "answers", "image_links"}
ROOT = Path(__file__).resolve().parents[2]


def verify_artifacts(directory, version, python_version):
    if len(list(directory.glob("*.smoke.json"))) != len(TARGETS):
        raise ValueError("Expected exactly four executable self-test reports")
    reports = {}
    for target, (system, machines, suffix) in TARGETS.items():
        binary = directory / f"MoocWorkAnswer-{version}-lite-{target}{suffix}"
        report = json.loads(binary.with_name(binary.name + ".smoke.json").read_text(encoding="utf-8"))
        if report.get("ok") is not True or report.get("frozen") is not True or not CHECKS.issubset(report.get("checks", [])):
            raise ValueError(f"Incomplete executable self-test: {target}")
        if report.get("version") != version or report.get("python") != python_version:
            raise ValueError(f"Unexpected application or Python version: {target}")
        if report.get("platform") != system or report.get("machine", "").lower() not in machines:
            raise ValueError(f"Unexpected platform or architecture: {target}")
        with binary.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        checksum = binary.with_name(binary.name + ".sha256").read_text(encoding="utf-8").strip().split(maxsplit=1)
        if report.get("sha256") != digest or checksum != [digest, binary.name]:
            raise ValueError(f"SHA-256 mismatch: {target}")
        reports[target] = report
    return reports


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--version", required=True)
    args = parser.parse_args()
    python_version = (ROOT / ".python-version").read_text(encoding="utf-8").strip()
    reports = verify_artifacts(args.directory, args.version, python_version)
    print(json.dumps({"ok": True, "python": python_version, "verified": sorted(reports)}))


if __name__ == "__main__":
    main()

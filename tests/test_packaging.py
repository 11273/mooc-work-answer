import importlib.util
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from base.package_check import run_package_check

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("build_package", ROOT / ".github" / "scripts" / "build_package.py")
build_package = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build_package)
spec = importlib.util.spec_from_file_location("verify_artifacts", ROOT / ".github" / "scripts" / "verify_artifacts.py")
artifact_check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(artifact_check)


class PackagingTests(unittest.TestCase):
    def test_unsupported_python_exits_before_loading_dependencies(self):
        result = subprocess.run([sys.executable, "-c", "import sys; sys.version_info = (3, 11, 0); import StartWork"],
                                cwd=ROOT, capture_output=True, encoding="utf-8")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("3.12.16", result.stderr)
        self.assertNotIn("ModuleNotFoundError", result.stderr)

    def test_package_check_is_offline_and_exports_real_word(self):
        with patch("requests.sessions.Session.request", side_effect=AssertionError("Unexpected network request")):
            result = run_package_check("v-test")
        self.assertTrue(result["ok"])
        self.assertEqual(result["version"], "v-test")
        self.assertIn("https_certificates", result["checks"])
        self.assertIn("word", result["checks"])

    def test_build_version_rejects_unsafe_paths_and_shell_syntax(self):
        for version in ["../main", "bad name", "$(command)", "a\nb"]:
            with self.subTest(version=version), self.assertRaises(ValueError):
                build_package.validate_version(version)
        self.assertEqual(build_package.validate_version("v3.3.4-rc.1"), "v3.3.4-rc.1")

    def test_native_target_reports_actual_architecture(self):
        with patch.object(build_package.sys, "platform", "darwin"), patch.object(build_package.platform, "machine", return_value="arm64"):
            self.assertEqual(build_package.native_target(), ("macos", "arm64"))

    def test_staging_keeps_original_source_and_excludes_account_data(self):
        with tempfile.TemporaryDirectory() as folder:
            source, target = Path(folder) / "source", Path(folder) / "target"
            source.mkdir()
            target.mkdir()
            for name in build_package.SOURCES:
                path = source / name
                if path.suffix:
                    path.write_text("", encoding="utf-8")
                else:
                    path.mkdir()
                    (path / "__init__.py").write_text("", encoding="utf-8")
            original = '_RELEASE_TAG_PLACEHOLDER = "${TAG_NAME}"\n'
            (source / "StartWork.py").write_text(original, encoding="utf-8")
            (source / "images").mkdir()
            (source / "images" / "icon.ico").write_bytes(b"icon")
            (source / "tiku").mkdir()
            (source / "tiku" / "private.json").write_text("private account data", encoding="utf-8")
            build_package.stage_sources(source, target, "verify-123")
            self.assertEqual((source / "StartWork.py").read_text(encoding="utf-8"), original)
            self.assertIn("verify-123", (target / "StartWork.py").read_text(encoding="utf-8"))
            self.assertFalse((target / "tiku").exists())


class ArtifactTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        for target, (system, machines, suffix) in artifact_check.TARGETS.items():
            binary = self.directory / f"MoocWorkAnswer-verify-test-lite-{target}{suffix}"
            binary.write_bytes(b"sample executable")
            digest = hashlib.sha256(binary.read_bytes()).hexdigest()
            report = {"ok": True, "frozen": True, "platform": system, "machine": sorted(machines)[0],
                      "version": "verify-test", "python": "3.12.16", "sha256": digest,
                      "checks": ["aes", "lxml", "https_certificates", "unicode_paths", "markdown", "word", "answers", "image_links"]}
            binary.with_name(binary.name + ".smoke.json").write_text(json.dumps(report), encoding="utf-8")
            binary.with_name(binary.name + ".sha256").write_text(f"{digest}  {binary.name}\n", encoding="utf-8")

    def verify(self):
        return artifact_check.verify_artifacts(self.directory, "verify-test", "3.12.16")

    def test_all_four_downloaded_artifacts_are_verified(self):
        self.assertEqual(len(self.verify()), 4)

    def test_corrupted_download_is_rejected(self):
        binary = self.directory / "MoocWorkAnswer-verify-test-lite-linux-x64"
        binary.write_bytes(b"corrupted download")
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            self.verify()

    def test_missing_platform_is_rejected(self):
        next(self.directory.glob("*.smoke.json")).unlink()
        with self.assertRaisesRegex(ValueError, "four"):
            self.verify()

    def test_old_python_and_mislabeled_architecture_are_rejected(self):
        path = self.directory / "MoocWorkAnswer-verify-test-lite-windows-x64.exe.smoke.json"
        original = json.loads(path.read_text(encoding="utf-8"))
        for field, value in [("python", "3.12.10"), ("machine", "arm64")]:
            with self.subTest(field=field):
                path.write_text(json.dumps(dict(original, **{field: value})), encoding="utf-8")
                with self.assertRaises(ValueError):
                    self.verify()

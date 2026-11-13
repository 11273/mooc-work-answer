import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from base.package_check import run_package_check

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("build_package", ROOT / ".github" / "scripts" / "build_package.py")
build_package = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build_package)


class PackagingTests(unittest.TestCase):
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

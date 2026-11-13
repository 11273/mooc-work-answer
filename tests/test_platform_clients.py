import json
import logging
from unittest.mock import ANY, Mock, patch
import unittest

import requests

from AIMoocMain.api import AIMoocApi
from AIMoocMain.main import AIMoocHandler
from ZYKMoocMain.api import ZYKMoocApi
from ZYKMoocMain.main import ZYKMoocHandler
from base.api_client import BaseAPIClient
from base.pagination import collect_rows
from base.resources import ResourceUnavailable, completed_resource_ids, resource_metadata, resource_total
from base.util import get_mp3_duration, parse_duration
from NewMoocMain.oauth_login import OAuthLoginHandler
from StartWork import get_export_courses
from update import _is_release_version, check_for_updates


class PaginationTests(unittest.TestCase):
    def test_reads_server_capped_pages_until_total(self):
        pages = []
        def fetch(page, size):
            pages.append(page)
            return {"rows": [{"id": str(page)}], "total": 3}
        self.assertEqual(len(collect_rows(fetch)), 3)
        self.assertEqual(pages, [1, 2, 3])

    def test_repeated_pages_raise_instead_of_truncating(self):
        with self.assertRaisesRegex(RuntimeError, "分页未前进"):
            collect_rows(lambda *args: {"rows": [{"id": "same"}], "total": 2})

    def test_error_does_not_become_empty_course_list(self):
        with self.assertRaisesRegex(RuntimeError, "登录失效"):
            collect_rows(lambda *args: {"code": 401, "msg": "登录失效"})

    def test_all_course_statuses_are_explicit_for_export(self):
        client = Mock()
        client.my_course_list_all.side_effect = lambda flag: {"rows": [{"id": str(flag)}]}
        self.assertEqual(len(get_export_courses(client, 0)), 3)
        self.assertEqual([c.kwargs["flag"] for c in client.my_course_list_all.call_args_list], [1, 2, 3])

    def test_learning_course_filter_defaults_to_ongoing(self):
        api = AIMoocApi.__new__(AIMoocApi)
        api.get = Mock(return_value={"rows": []})
        api.my_course_list()
        self.assertEqual(api.get.call_args.kwargs["params"]["queryStatus"], 1)
        self.assertEqual(api.get.call_args.kwargs["params"]["queryType"], 1)


class ClientTests(unittest.TestCase):
    def test_timeout_is_set_on_network_requests(self):
        client = BaseAPIClient("https://example.test")
        response = Mock(status_code=200)
        response.json.return_value = {"code": 200, "data": {"ok": True}}
        client.session.request = Mock(return_value=response)
        self.assertEqual(client.get("/info"), {"ok": True})
        self.assertEqual(client.session.request.call_args.kwargs["timeout"], (10, 30))

    def test_http_errors_return_failure(self):
        client = BaseAPIClient("https://example.test")
        response = Mock(status_code=401)
        response.raise_for_status.side_effect = requests.HTTPError(response=response)
        client.session.request = Mock(return_value=response)
        self.assertIsNone(client.get("/info", origin_response=True))

    def test_put_can_preserve_status_envelope(self):
        client = BaseAPIClient("https://example.test")
        response = Mock(status_code=200)
        response.json.return_value = {"code": 200, "msg": "保存成功", "data": None}
        client.session.request = Mock(return_value=response)
        self.assertEqual(client.put("/record", origin_response=True)["msg"], "保存成功")

    def test_credentials_are_absent_from_request_and_error_logs(self):
        client = BaseAPIClient("https://example.test")
        client.session.request = Mock(side_effect=requests.ConnectionError("url?token=PRIVATE_TOKEN"))
        with self.assertLogs("base.api_client", level="DEBUG") as captured:
            client.post("/login?token=PRIVATE_TOKEN", json={"password": "PRIVATE_PASSWORD"})
        output = " ".join(captured.output)
        self.assertNotIn("PRIVATE_TOKEN", output)
        self.assertNotIn("PRIVATE_PASSWORD", output)

    def test_zyk_record_preserves_business_status(self):
        api = ZYKMoocApi.__new__(ZYKMoocApi)
        api.student_id = "student"
        api.put = Mock(return_value={"code": 200, "msg": "保存成功"})
        result = api.study_record("course", "parent", 1, "resource", 1, 1, 1)
        self.assertEqual(result["code"], 200)
        self.assertTrue(api.put.call_args.kwargs["origin_response"])

    def test_zyk_missing_user_info_does_not_crash(self):
        api = ZYKMoocApi.__new__(ZYKMoocApi)
        api.get = Mock(return_value=None)
        api.get_info()

    def test_oauth_callback_only_listens_on_loopback(self):
        oauth = OAuthLoginHandler()
        with patch.object(oauth, "find_available_port", return_value=39019), \
             patch("NewMoocMain.oauth_login.HTTPServer") as server, \
             patch("NewMoocMain.oauth_login.threading.Thread"):
            self.assertTrue(oauth.start_server())
            server.assert_called_once_with(("127.0.0.1", 39019), ANY)
            oauth.stop_server()


class ResourceTests(unittest.TestCase):
    def test_duration_formats(self):
        for value, expected in [("01:02:03.5", 3723), ("02:03.5", 123), ("12.5", 12), (12.5, 12)]:
            self.assertEqual(parse_duration(value), expected)

    def test_invalid_duration_rejected(self):
        for value in [None, "NaN", "inf", "-1", "1:2:3:4"]:
            with self.subTest(value=value), self.assertRaises((TypeError, ValueError)):
                parse_duration(value)

    def test_metadata_accepts_json_dict_and_absent_data(self):
        for raw in ['{"page_count":5}', {"page_count": 5}]:
            self.assertEqual(resource_total("ppt", resource_metadata(raw)), 5)
        self.assertEqual(resource_total("图文", resource_metadata(None)), 1)

    def test_completed_records_support_ids_and_objects(self):
        self.assertEqual(completed_resource_ids(["a", {"sourceId": "b"}, {"coursewareId": "c"}]), {"a", "b", "c"})

    def test_legacy_video_extensions_use_real_duration(self):
        for kind in ["avi", "wmv", "mov", "mpg", "flv"]:
            self.assertEqual(resource_total(kind, {"duration": "00:03:36.542"}), 216)

    def test_document_pages_do_not_depend_on_text_conversion_flag(self):
        self.assertEqual(resource_total("doc", {"has_txt_file": False, "page_count": 5}), 5)

    def test_legacy_resource_without_duration_is_explicitly_skipped(self):
        handler = self.ai_handler(False)
        handler.handle_resource({"id": "doc", "courseInfoId": "info", "courseId": "course", "fileType": "video",
                                 "fileUrl": json.dumps({"duration": 0, "ossOriUrl": "https://example.test/old.swf"})}, "parent")
        self.assertEqual(handler.stats["unavailable"], 1)
        self.assertEqual(handler.stats["errors"], 0)
        handler.client.study_record.assert_not_called()

    def test_mpeg_25_audio_does_not_raise_key_error(self):
        response = Mock(status_code=200, headers={"Content-Length": "100000"})
        response.raw.read.return_value = bytes([255, 227, 128, 0]) + bytes(30)
        with patch("base.util.requests.get", return_value=response):
            self.assertGreater(get_mp3_duration("https://example.test/audio.mp3"), 0)
        response.close.assert_called_once()

    def ai_handler(self, dry_run):
        handler = AIMoocHandler.__new__(AIMoocHandler)
        handler.client = Mock()
        handler.dry_run = dry_run
        handler.study_record_list = set()
        handler.stats = {"courses": 0, "checked": 0, "updated": 0, "skipped": 0, "errors": 0}
        handler.logging = logging.getLogger("resource-test")
        return handler

    def test_mooc_read_only_check_never_writes_progress(self):
        handler = self.ai_handler(True)
        handler.handle_resource({"id": "doc", "courseInfoId": "info", "courseId": "course", "fileType": "pdf", "fileUrl": None}, "parent")
        self.assertEqual(handler.stats["checked"], 1)
        self.assertEqual(handler.stats["errors"], 0)
        handler.client.study_record.assert_not_called()

    def test_progress_uses_actual_resource_parent(self):
        handler = self.ai_handler(False)
        handler.client.study_record.return_value = {"code": 200, "msg": "保存成功"}
        with patch("AIMoocMain.main.time.sleep"):
            handler.handle_resource({"id": "doc", "courseInfoId": "info", "courseId": "course", "parentId": "section",
                                     "fileType": "pdf", "fileUrl": json.dumps({"page_count": 16})}, "chapter")
        self.assertEqual(handler.client.study_record.call_args.args[2], "section")
        self.assertEqual(handler.client.study_record.call_args.args[-1], 16)
        self.assertEqual(handler.stats["updated"], 1)

    def test_failed_study_save_is_not_reported_as_success(self):
        handler = self.ai_handler(False)
        handler.client.study_record.return_value = {"code": 500, "msg": "失败"}
        with patch("AIMoocMain.main.time.sleep"):
            handler.handle_resource({"id": "doc", "courseInfoId": "info", "courseId": "course", "fileType": "图文"}, "parent")
        self.assertEqual(handler.stats["errors"], 1)
        self.assertEqual(handler.stats["updated"], 0)

    def test_assessment_nodes_are_skipped_in_both_platforms(self):
        handler = self.ai_handler(False)
        zyk = ZYKMoocHandler.__new__(ZYKMoocHandler)
        zyk.client, zyk.dry_run, zyk.stats, zyk.logging = handler.client, False, handler.stats, handler.logging
        for kind in ["作业", "测验", "考试", "讨论"]:
            handler.handle_resource({"fileType": kind}, "parent")
            zyk.handle_resource({"fileType": kind})
        self.assertEqual(handler.stats["skipped"], 8)
        handler.client.study_record.assert_not_called()
        handler.client.course_content.assert_not_called()

    def test_invalid_release_version_is_not_compared(self):
        for value in ["1..2", "dev", "${TAG_NAME}", "v1."]:
            self.assertFalse(_is_release_version(value))

    def test_update_without_gui_does_not_abort_startup(self):
        with patch("update.get_latest_release", return_value={"tag_name": "v9.0.0", "html_url": "https://example.test/release"}), \
             patch("update.show_update_prompt", side_effect=RuntimeError("No display")):
            check_for_updates("v3.3.4")

    def test_prerelease_tag_does_not_break_version_comparison(self):
        with patch("update.get_latest_release", return_value={"tag_name": "v9.0.0-beta", "html_url": "https://example.test/release"}), \
             patch("update.show_update_prompt") as prompt:
            check_for_updates("v3.3.4")
            prompt.assert_not_called()

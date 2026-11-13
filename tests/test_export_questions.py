import copy
import json
from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile

from AIMoocMain.export_questions import (
    QuizExportHandler, _merge_record_answers, collect_quiz_catalog,
    parse_index_input, parse_options, parse_question, question_to_markdown,
    write_questions_docx,
)

COURSE = {"id": "course-info", "courseId": "course", "courseName": "测试课程"}
OPTIONS = [{"SortOrder": 0, "Content": "甲"}, {"SortOrder": 1, "Content": "乙"}]


class ExportClient:
    user_id = "student"

    def __init__(self):
        self.paper_calls = []
        self.info_calls = []
        self.full_record = True
        self.records = [
            {"id": "old", "status": 2, "studentSubmitTime": "2026-09-29 10:00:00"},
            {"id": "latest", "status": 2, "studentSubmitTime": "2026-09-30 10:00:00"},
        ]
        self.list_response = {"code": 200, "rows": [
            {"id": "exam1", "name": "第一章"}, {"id": "exam2", "name": "第二章"},
        ]}

    def get_exam_list_by_student(self, *args):
        return copy.deepcopy(self.list_response)

    def get_exam_student_records(self, *args):
        return {"code": 200, "data": copy.deepcopy(self.records)}

    def get_exam_record_info(self, **kwargs):
        self.info_calls.append(kwargs["task_id"])
        q = {"questionId": "question", "typeId": 1, "answer": "1", "stuAnswer": "1"}
        if self.full_record:
            q.update(title="真实记录题干", dataJson=OPTIONS)
        return {"code": 200, "data": {"questions": [q]}}

    def get_exam_paper(self, exam_id, group_id="0"):
        self.paper_calls.append(exam_id)
        return {"code": 200, "data": {"questions": [{
            "id": "paper-question", "questionId": "question", "typeId": 1,
            "title": "试卷题干", "answer": "0", "dataJson": OPTIONS,
        }]}}


class AnswerTests(unittest.TestCase):
    def test_preserves_subjective_answers(self):
        for kind, raw, expected in [(4, "10", "10"), (4, 0, "0"),
                                    (6, "Hello world, x=10", "Hello world, x=10"),
                                    (6, "x < 2 and y > 3", "x < 2 and y > 3"),
                                    (5, ["NaCl", "10"], "NaCl；10")]:
            with self.subTest(kind=kind, raw=raw):
                q = parse_question({"typeId": kind, "stdAnswer": raw}, 1)
                self.assertEqual(q["std_answer"], expected)

    def test_record_subjective_answer_preserves_text(self):
        q = parse_question({"id": "q", "typeId": 6}, 1)
        _merge_record_answers([q], [{"questionId": "q", "answer": "Hello world"}])
        self.assertEqual(q["std_answer"], "Hello world")

    def test_judgement_standard_and_student_answers(self):
        for value, expected in [(0, "错误"), ("0", "错误"), (False, "错误"),
                                (1, "正确"), ("1", "正确"), (True, "正确")]:
            with self.subTest(value=value):
                q = parse_question({"id": "q", "typeId": 3, "stuAnswer": value}, 1)
                _merge_record_answers([q], [{"questionId": "q", "answer": value, "stuAnswer": value}])
                self.assertEqual(q["std_answer"], expected)
                self.assertEqual(q["my_answer"], expected)

    def test_latest_submission_overwrites_draft(self):
        q = parse_question({"id": "q", "typeId": 1, "answer": "0", "dataJson": OPTIONS}, 1)
        _merge_record_answers([q], [{"questionId": "q", "answer": "1", "stuAnswer": "1"}])
        self.assertEqual(q["my_answer"], "B")

    def test_empty_latest_answer_clears_draft(self):
        q = parse_question({"id": "q", "typeId": 1, "stuAnswer": "0", "dataJson": OPTIONS}, 1)
        _merge_record_answers([q], [{"questionId": "q", "answer": "1", "stuAnswer": ""}])
        self.assertEqual(q["my_answer"], "")

    def test_standard_answer_resets_option_highlights(self):
        q = parse_question({"id": "q", "typeId": 1, "dataJson": [
            {"SortOrder": 0, "Content": "甲", "IsAnswer": True}, OPTIONS[1],
        ]}, 1)
        _merge_record_answers([q], [{"questionId": "q", "answer": "1"}])
        self.assertEqual([o["is_answer"] for o in q["options"]], [False, True])

    def test_false_option_flags_remain_false(self):
        for value in [False, 0, "0", "false", "False"]:
            self.assertFalse(parse_options([{"Content": "甲", "IsAnswer": value}])[0]["is_answer"])

    def test_judgement_option_only_answer_is_not_a_letter(self):
        q = parse_question({"typeId": 3, "options": [
            {"SortOrder": 0, "Content": "错误", "IsAnswer": True},
        ]}, 1)
        self.assertEqual(q["std_answer"], "错误")

    def test_matches_answers_by_question_id_not_position(self):
        questions = [parse_question({"questionId": key, "typeId": 1, "options": OPTIONS}, i)
                     for i, key in enumerate(["a", "b"], 1)]
        _merge_record_answers(questions, [{"questionId": "b", "answer": "0"}, {"questionId": "a", "answer": "1"}])
        self.assertEqual([q["std_answer"] for q in questions], ["B", "A"])

    def test_image_and_math_content_is_preserved(self):
        q = parse_question({"typeId": 1, "title": 'x < 2，图示：<img src="/image.png" alt="结构图">'}, 1)
        output = question_to_markdown(q)
        self.assertIn("x < 2", output)
        self.assertIn("![结构图](https://ai.icve.com.cn/image.png)", output)

    def test_word_preserves_image_as_clickable_link(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "questions.docx"
            q = parse_question({"typeId": 1, "title": '<img src="https://example.test/figure.png">'}, 1)
            write_questions_docx(target, "测试题", [], [(None, [q])])
            with ZipFile(target) as archive:
                self.assertIn("查看原图", archive.read("word/document.xml").decode())
                self.assertIn("https://example.test/figure.png", archive.read("word/_rels/document.xml.rels").decode())

    def test_large_selection_range_is_bounded(self):
        self.assertEqual(parse_index_input("1-999999999999", 3), [1, 2, 3])


class ExportFlowTests(unittest.TestCase):
    def export(self, folder, client=None, **kwargs):
        return QuizExportHandler(client=client or ExportClient(), course_rows=[COURSE],
                                 category_ids=[3], output_dir=folder, **kwargs)

    def test_archived_record_export_does_not_open_paper(self):
        client = ExportClient()
        client.get_exam_paper = lambda *args: self.fail("历史已交卷内容不应进入作答接口")
        with tempfile.TemporaryDirectory() as folder:
            result = self.export(folder, client, submitted_only=True, export_format="both", include_my_answer=True)
            self.assertTrue(result.success)
            self.assertEqual(result.stats["papers"], 2)
            self.assertEqual(client.info_calls, ["latest", "latest"])
            self.assertEqual(len(list(Path(folder).rglob("*.docx"))), 2)

    def test_pending_records_are_skipped_without_opening_paper(self):
        client = ExportClient()
        client.records = [{"id": "draft", "status": 0}]
        with tempfile.TemporaryDirectory() as folder:
            result = self.export(folder, client, submitted_only=True)
            self.assertTrue(result.success)
            self.assertEqual(result.stats["skipped"], 2)
            self.assertFalse(client.paper_calls)

    def test_answer_only_records_merge_into_paper(self):
        client = ExportClient()
        client.full_record = False
        with tempfile.TemporaryDirectory() as folder:
            result = self.export(folder, client, include_my_answer=True)
            self.assertTrue(result.success)
            text = next(Path(folder).rglob("*.md")).read_text(encoding="utf-8")
            self.assertIn("**我的答案：** B", text)
            self.assertNotIn("**我的答案：** A", text)

    def test_no_student_answer_in_default_documents(self):
        with tempfile.TemporaryDirectory() as folder:
            self.export(folder)
            self.assertNotIn("我的答案", next(Path(folder).rglob("*.md")).read_text(encoding="utf-8"))

    def test_incomplete_submitted_record_does_not_start_an_attempt(self):
        client = ExportClient()
        client.full_record = False
        with tempfile.TemporaryDirectory() as folder:
            result = self.export(folder, client, submitted_only=True)
            self.assertFalse(result.success)
            self.assertFalse(client.paper_calls)

    def test_business_error_is_reported_as_failure(self):
        client = ExportClient()
        client.list_response = {"code": 401, "msg": "登录失效"}
        with tempfile.TemporaryDirectory() as folder:
            result = self.export(folder, client)
            self.assertFalse(result.success)
            self.assertEqual(result.stats["errors"], 1)

    def test_catalog_errors_are_not_silent_empty_lists(self):
        client = ExportClient()
        client.list_response = {"code": 500, "msg": "服务异常"}
        with self.assertRaisesRegex(RuntimeError, "服务异常"):
            collect_quiz_catalog(client, [COURSE])

    def test_all_quiz_modes_and_formats(self):
        for mode, fmt, count in [("per_chapter", "md", 2), ("single", "both", 1), ("merged", "docx", 1)]:
            with self.subTest(mode=mode, fmt=fmt), tempfile.TemporaryDirectory() as folder:
                result = self.export(folder, quiz_mode=mode, export_format=fmt, selected_exam_ids=["exam2"])
                self.assertTrue(result.success)
                suffix = ".md" if fmt == "md" else ".docx"
                self.assertEqual(len(list(Path(folder).rglob("*" + suffix))), count)

    def test_same_named_course_offerings_do_not_overwrite_merged_files(self):
        courses = [dict(COURSE, id="offering-one"), dict(COURSE, id="offering-two")]
        with tempfile.TemporaryDirectory() as folder:
            result = QuizExportHandler(client=ExportClient(), course_rows=courses, category_ids=[3],
                                       quiz_mode="merged", output_dir=folder)
            self.assertTrue(result.success)
            self.assertEqual(len(list(Path(folder).rglob("*.md"))), 2)

    def test_long_chinese_paper_titles_remain_exportable(self):
        client = ExportClient()
        client.list_response = {"rows": [{"id": "a" * 36, "name": "中文题目" * 30}]}
        with tempfile.TemporaryDirectory() as folder:
            result = self.export(folder, client, export_format="both")
            self.assertTrue(result.success)
            for path in Path(folder).rglob("*.*"):
                self.assertLessEqual(len(path.name.encode("utf-8")), 255)

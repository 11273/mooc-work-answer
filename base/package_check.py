"""离线检查打包后实际使用的依赖和导出能力，不访问账号或网络。"""
import json
import platform
from pathlib import Path
import ssl
import sys
import tempfile
from zipfile import ZipFile

import certifi
from docx import Document
from lxml import etree

from AIMoocMain.export_questions import parse_question, question_to_markdown, write_questions_docx
from base.util import aes_decrypt_ecb, aes_encrypt_ecb


def run_package_check(version):
    key = b"0123456789abcdef"
    payload = '{"probe":"packaging"}'
    if aes_decrypt_ecb(key, aes_encrypt_ecb(key, payload)) != payload:
        raise RuntimeError("AES dependency check failed")
    if etree.fromstring("<probe>中文</probe>".encode("utf-8")).text != "中文":
        raise RuntimeError("lxml dependency check failed")
    ca_file = Path(certifi.where())
    if not ca_file.is_file() or not ssl.create_default_context(cafile=str(ca_file)).cert_store_stats()["x509_ca"]:
        raise RuntimeError("Bundled HTTPS certificates are unavailable")

    raw_questions = [
        {"typeId": 1, "title": "选择题检查", "answer": "1", "stuAnswer": "0", "options": [
            {"SortOrder": 0, "Content": "甲"}, {"SortOrder": 1, "Content": "乙"},
        ]},
        {"typeId": 3, "title": "判断题检查", "answer": "0", "stuAnswer": "1"},
        {"typeId": 4, "title": "数字答案检查", "answer": "10"},
        {"typeId": 6, "title": "文本答案检查", "answer": "Hello world"},
        {"typeId": 1, "title": '<img src="https://example.invalid/figure.png" alt="题图">'},
    ]
    questions = [parse_question(raw, index, from_record=True) for index, raw in enumerate(raw_questions, 1)]
    with tempfile.TemporaryDirectory(prefix="mooc-self-test-") as folder:
        target = Path(folder) / "中文 路径"
        target.mkdir()
        markdown = "\n\n".join(question_to_markdown(q, include_my_answer=True) for q in questions)
        md_path = target / "题目导出.md"
        md_path.write_text(markdown, encoding="utf-8")
        if md_path.read_text(encoding="utf-8") != markdown or "**正确答案：** 10" not in markdown:
            raise RuntimeError("Markdown or Unicode path check failed")
        word_path = target / "题目导出.docx"
        write_questions_docx(word_path, "打包自检", ["离线样例"], [("导出检查", questions)], include_my_answer=True)
        with ZipFile(word_path) as archive:
            if archive.testzip() is not None:
                raise RuntimeError("Invalid Word archive")
            if "https://example.invalid/figure.png" not in archive.read("word/_rels/document.xml.rels").decode("utf-8"):
                raise RuntimeError("Word image link check failed")
        text = "\n".join(p.text for p in Document(str(word_path)).paragraphs)
        for answer in ("正确答案：B", "正确答案：错误", "正确答案：10", "正确答案：Hello world", "我的答案：正确"):
            if answer not in text:
                raise RuntimeError("Word answer check failed: " + answer)
    return {
        "ok": True, "version": version, "frozen": bool(getattr(sys, "frozen", False)),
        "platform": sys.platform, "machine": platform.machine(), "python": platform.python_version(),
        "checks": ["aes", "lxml", "https_certificates", "unicode_paths", "markdown", "word", "answers", "image_links"],
    }

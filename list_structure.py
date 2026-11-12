# -*- coding: utf-8 -*-
"""列出指定课程的章节/资源目录

用法:
  uv run python list_structure.py 物理因子治疗
  uv run python list_structure.py          # 默认物理因子治疗
"""

import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

from MoocMain.log import Logger
from AIMoocMain.api import AIMoocApi

logger = Logger(__name__).get_log()


def walk_cells(client: AIMoocApi, course_info_id: str, course_id: str,
               parent_id: str, indent: int = 0) -> List[Dict[str, Any]]:
    """递归获取并打印课程资源节点"""
    nodes = client.get_cell_list(course_info_id, course_id, parent_id) or []
    rows: List[Dict[str, Any]] = []

    if not isinstance(nodes, list):
        return rows

    prefix = "  " * indent
    for node in nodes:
        if not isinstance(node, dict):
            continue
        name = node.get("name") or node.get("title") or "未知"
        file_type = node.get("fileType") or node.get("type") or ""
        node_id = node.get("id")
        item = {
            "id": node_id,
            "name": name,
            "fileType": file_type,
            "children": [],
        }
        logger.info(f"{prefix}- {name} ({file_type})")
        children = node.get("children") or []
        if children:
            # 结构里已带 children 时直接递归展示
            for child in children:
                if not isinstance(child, dict):
                    continue
                child_rows = _walk_inline(client, course_info_id, course_id, child, indent + 1)
                item["children"].extend(child_rows)
        elif node_id:
            # 叶子节点：再拉一层 cellList（有的接口 children 为空但仍有下级）
            child_rows = walk_cells(client, course_info_id, course_id, node_id, indent + 1)
            item["children"].extend(child_rows)
        rows.append(item)
    return rows


def _walk_inline(client: AIMoocApi, course_info_id: str, course_id: str,
                 node: Dict[str, Any], indent: int) -> List[Dict[str, Any]]:
    """处理 courseDesign 返回里内嵌的 children"""
    name = node.get("name") or node.get("title") or "未知"
    file_type = node.get("fileType") or node.get("type") or ""
    node_id = node.get("id")
    prefix = "  " * indent
    logger.info(f"{prefix}- {name} ({file_type})")

    item = {"id": node_id, "name": name, "fileType": file_type, "children": []}
    children = node.get("children") or []
    if children:
        for child in children:
            if isinstance(child, dict):
                item["children"].extend(
                    _walk_inline(client, course_info_id, course_id, child, indent + 1)
                )
    elif node_id:
        item["children"].extend(
            walk_cells(client, course_info_id, course_id, node_id, indent + 1)
        )
    return [item]


def main() -> None:
    keyword = sys.argv[1] if len(sys.argv) > 1 else "物理因子治疗"

    logger.info("=" * 50)
    logger.info("课程目录查看（需浏览器 OAuth 登录）")
    logger.info(f"关键词: {keyword}")
    logger.info("=" * 50)
    input("* 按回车键打开浏览器登录...")

    from NewMoocMain.oauth_login import oauth_login
    token = oauth_login(timeout=300)
    if not token:
        logger.error("❌ 登录失败")
        return

    client = AIMoocApi(token=token)
    courses = client.my_course_list(page_size=9999) or {}
    rows = courses.get("rows") or []
    logger.info(f"共 {len(rows)} 门课程")

    matched = [c for c in rows if keyword in (c.get("courseName") or "")]
    if not matched:
        logger.warning(f"未找到包含「{keyword}」的课程，全部课程如下：")
        for c in rows:
            logger.info(f"  - {c.get('courseName')} ({c.get('courseInfoName')})")
        return

    out_dir = Path("exports") / "structure" / time.strftime("%Y%m%d_%H%M%S")
    out_dir.mkdir(parents=True, exist_ok=True)

    for course in matched:
        course_name = course.get("courseName", "未知课程")
        course_info_id = course.get("id") or course.get("courseInfoId")
        course_id = course.get("courseId")
        logger.info("")
        logger.info(f"🎯 课程: {course_name}")
        logger.info(f"   courseInfoId={course_info_id}")
        logger.info(f"   courseId={course_id}")
        if not course_info_id or not course_id:
            logger.warning("   缺少 ID，跳过")
            continue

        design = client.study_design_list(course_info_id, course_id) or []
        logger.info(f"   章节数(顶层): {len(design) if isinstance(design, list) else '?'}")
        logger.info("-" * 40)

        structure = walk_cells(client, course_info_id, course_id, "", indent=0) if not design else []
        # 优先用 study_design_list 的顶层结构
        if isinstance(design, list) and design:
            structure = []
            for chapter in design:
                if not isinstance(chapter, dict):
                    continue
                name = chapter.get("name") or chapter.get("title") or "未知"
                ch_id = chapter.get("id")
                logger.info(f"📖 {name}")
                children = chapter.get("children") or []
                chapter_item = {"id": ch_id, "name": name, "children": []}
                if children:
                    for child in children:
                        if isinstance(child, dict):
                            chapter_item["children"].extend(
                                _walk_inline(client, course_info_id, course_id, child, 1)
                            )
                elif ch_id:
                    chapter_item["children"].extend(
                        walk_cells(client, course_info_id, course_id, ch_id, 1)
                    )
                structure.append(chapter_item)

        out_file = out_dir / f"{course_name}_目录.json"
        out_file.write_text(
            json.dumps(
                {
                    "course": course_name,
                    "courseInfoId": course_info_id,
                    "courseId": course_id,
                    "structure": structure,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        logger.info(f"✅ 已保存: {out_file}")

    logger.info(f"📁 输出目录: {out_dir.resolve()}")


if __name__ == "__main__":
    main()

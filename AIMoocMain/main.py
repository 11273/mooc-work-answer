import random
import time
from typing import List, Dict, Any

from MoocMain.log import Logger
from AIMoocMain.api import AIMoocApi
from base.resources import ASSESSMENT_TYPES, ResourceUnavailable, completed_resource_ids, resource_metadata, resource_total


class AIMoocHandler:
    def __init__(self, jump_content: str = "", token: str = None, username: str = None, password: str = None, dry_run: bool = False, client=None):
        """初始化 API 客户端和日志"""
        # 跳过课程列表
        self.jump_list = []
        # 已完成的课程id列表
        self.study_record_list = set()
        self.dry_run = dry_run
        self.stats = {"courses": 0, "checked": 0, "updated": 0, "skipped": 0, "unavailable": 0, "errors": 0}
        if jump_content and "#" in jump_content:
            self.jump_list = jump_content.split("#")[1:]

        # 根据是否提供token选择不同的初始化方式
        self.client = client or AIMoocApi(token=token, username=username, password=password)

        self.logging = Logger(__name__).get_log()
        self.success = self.start_courses()

    def start_courses(self) -> bool:
        """获取并处理课程列表"""
        try:
            courses = self.client.my_course_list_all()
            total_courses = courses.get("total", 0)
            course_rows = courses.get("rows", [])

            self.logging.info(
                f"📚 获取课程成功，共 {total_courses} 门课程，当前获取到 {len(course_rows)} 门课程"
            )

            if not course_rows:
                self.logging.warning("⚠️ 当前没有课程数据")
                return True
            self.logging.info("")
            self.logging.info("➕➕➕ 课程读取 ➕➕➕")

            # 记录跳过的课程
            skipped_courses = []
            for index, course in enumerate(course_rows, start=1):  # 添加索引，从 1 开始
                course_name = course.get("courseName", "未知课程")
                teacher = course.get("displayName", "未知教师")  # 适配新字段
                course_info_name = course.get("courseInfoName", "未知课程信息")
                study_speed = course.get("studySpeed", "未知")  # 适配新字段：学习进度
                final_score = course.get("finalScore", "未知")

                # 判断是否跳过该课程
                if any(s in course_name for s in self.jump_list):
                    skipped_courses.append(course_name)
                    self.logging.info(
                        f"⏭️ [跳过] 课程: {course_name} ({course_info_name}) | 教师: {teacher} | 📊 学习进度: {study_speed}% | 成绩: {final_score}"
                    )
                    continue
                self.logging.info(
                    f"🪧 [{index}] 课程: {course_name} ({course_info_name}) | 教师: {teacher} | 📊 学习进度: {study_speed}% | 成绩: {final_score}"
                )

            self.logging.info("➕➕➕ 课程读取完成 ➕➕➕")
            self.logging.info("")
            # 打印跳过的课程
            if skipped_courses:
                self.logging.info(
                    f"🚫 共跳过 {len(skipped_courses)} 门课程: {', '.join(skipped_courses)}"
                )
            else:
                self.logging.info("✅ 没有需要跳过的课程")
            for course in course_rows:
                if any(s in (course.get("courseName") or "") for s in self.jump_list):
                    continue
                self.process_course(course)
            self.logging.info(f"📊 {'只读检查' if self.dry_run else '学习管理'}: {self.stats}")
            return self.stats["errors"] == 0

        except Exception as e:
            self.stats["errors"] += 1
            self.logging.error(f"❌ 获取课程失败: {e}")
            return False

    def process_course(self, course: Dict[str, Any]) -> None:
        """处理单个课程"""
        course_name = course.get("courseName", "未知课程")
        teacher = course.get("displayName", "未知教师")  # 适配新字段
        course_info_name = course.get("courseInfoName", "未知课程信息")
        study_speed = course.get("studySpeed", "未知")  # 适配新字段：学习进度
        final_score = course.get("finalScore", "未知")
        course_info_id = course.get("id")
        course_id = course.get("courseId")

        self.logging.info(
            f"🎯 课程: {course_name} ({course_info_name}) | 教师: {teacher} | 📊 学习进度: {study_speed}% | 成绩: {final_score}"
        )

        if course_info_id:
            study_design_list = self.client.study_design_list(course_info_id, course_id)
            completed = self.client.study_record_list(
                course_info_id, course_id
            )
            if not isinstance(study_design_list, list) or not isinstance(completed, list):
                self.logging.error(f"❌ 读取课程目录或学习记录失败: {course_name}")
                self.stats["errors"] += 1
                return
            self.study_record_list = completed_resource_ids(completed)
            self.stats["courses"] += 1
            for node in study_design_list:
                parent_id = node.get("id")
                cell_list = self.client.get_cell_list(
                    course_info_id, course_id, parent_id
                )
                if not isinstance(cell_list, list):
                    self.logging.error(f"❌ 读取章节失败: {course_name}")
                    self.stats["errors"] += 1
                    continue
                self.print_course_structure(cell_list, parent_id)
        else:
            self.stats["errors"] += 1
            self.logging.warning(f"⚠️ 课程 {course_name} 缺少 CourseInfoId，跳过")

    def print_course_structure(
        self, nodes: List[Dict[str, Any]], parent_id: str, indent: int = 0
    ) -> None:
        """递归打印课程结构"""
        prefix = " " * (indent * 4)  # 每层缩进 4 个空格

        for node in nodes:
            name = node.get("name", "未知")
            file_type = node.get("fileType", "未知")
            self.logging.info(f"{prefix}- {name} ({file_type})")

            children = node.get("children", [])
            if children:
                self.print_course_structure(children, parent_id, indent + 1)
            else:
                self.handle_resource(node, parent_id, indent)

    def handle_resource(self, node: Dict[str, Any], parent_id: str, indent: int = 0) -> None:
        """读取资源元数据；--check 仅检查，不写入学习记录。"""
        resource_name = node.get("name") or "未知资源"
        file_type = node.get("fileType") or "未知类型"
        source_id = node.get("id")
        prefix = " " * ((indent + 1) * 4)
        if file_type in ASSESSMENT_TYPES:
            self.stats["skipped"] += 1
            self.logging.info(f"{prefix}⏭️ 跳过{file_type}: {resource_name}")
            return
        record = node.get("studentStudyRecord") or {}
        if str(source_id) in self.study_record_list or str(record.get("speed")) in ("100", "100.0"):
            self.stats["skipped"] += 1
            return
        try:
            if not source_id or not node.get("courseInfoId") or not node.get("courseId"):
                raise ValueError("资源缺少课程或课件 ID")
            metadata = resource_metadata(node.get("fileUrl"))
            if not metadata.get("duration") and node.get("videoTime"):
                metadata["videoTime"] = node["videoTime"]
            total_num = resource_total(file_type, metadata)
            self.stats["checked"] += 1
            if self.dry_run:
                self.logging.info(f"{prefix}🔎 {resource_name} ({file_type})，学习数 {total_num}")
                return
            time.sleep(round(random.uniform(0.5, 1.5), 2))
            response = self.client.study_record(
                node["courseId"], node["courseInfoId"], node.get("parentId") or parent_id,
                total_num, source_id, total_num, total_num, total_num,
            )
            if not isinstance(response, dict) or response.get("code") not in (200, "200"):
                raise RuntimeError(response.get("msg", "保存学习记录失败") if isinstance(response, dict) else "保存学习记录失败")
            self.stats["updated"] += 1
            self.logging.info(f"{prefix}✅ {resource_name}: {response.get('msg', '保存成功')}")
        except ResourceUnavailable as error:
            self.stats["skipped"] += 1
            self.stats["unavailable"] = self.stats.get("unavailable", 0) + 1
            self.logging.warning(f"{prefix}⚠️ {resource_name}: {error}")
        except Exception as error:
            self.stats["errors"] += 1
            self.logging.error(f"{prefix}❌ {resource_name}: {error}")

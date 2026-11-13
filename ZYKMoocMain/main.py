import random
import time
from typing import List, Dict, Any

from MoocMain.log import Logger
from ZYKMoocMain.api import ZYKMoocApi
from base.resources import ASSESSMENT_TYPES, VIDEO_TYPES, AUDIO_TYPES, DOCUMENT_TYPES, ResourceUnavailable, resource_metadata, resource_total


class ZYKMoocHandler:
    def __init__(self, username: str = "", password: str = "", jump_content: str = "", token: str = None, dry_run: bool = False, client=None):
        """初始化 API 客户端和日志"""
        self.jump_list = []
        self.dry_run = dry_run
        self.stats = {"courses": 0, "checked": 0, "updated": 0, "skipped": 0, "unavailable": 0, "errors": 0}
        if jump_content and '#' in jump_content:
            self.jump_list = jump_content.split('#')[1:]

        # 根据是否提供token选择不同的初始化方式
        if client is not None:
            self.client = client
        elif token:
            self.client = ZYKMoocApi(token=token)
        else:
            self.client = ZYKMoocApi(username, password)

        self.logging = Logger(__name__).get_log()
        self.success = self.start_courses()

    def start_courses(self) -> bool:
        """获取并处理课程列表"""
        try:
            courses = self.client.my_course_list_all()
            total_courses = courses.get("total", 0)
            course_rows = courses.get("rows", [])

            self.logging.info(f"📚 获取课程成功，共 {total_courses} 门课程，当前获取到 {len(course_rows)} 门课程")

            if not course_rows:
                self.logging.warning("⚠️ 当前没有课程数据")
                return True
            self.logging.info("")
            self.logging.info("➕➕➕ 课程读取 ➕➕➕")

            # 记录跳过的课程
            skipped_courses = []
            for index, course in enumerate(course_rows, start=1):  # 添加索引，从 1 开始
                course_name = course.get("courseName", "未知课程")
                teacher = course.get("presidingTeacher", "未知教师")
                course_info_name = course.get("courseInfoName", "未知课程信息")
                study_time = course.get("studyTime", "未知")
                final_score = course.get("finalScore", "未知")


                # 判断是否跳过该课程
                if any(s in course_name for s in self.jump_list):
                    skipped_courses.append(course_name)
                    self.logging.info(
                        f"⏭️ [跳过] 课程: {course_name} ({course_info_name}) | 教师: {teacher} | ⏳ 学习时长: {study_time} | 成绩: {final_score}"
                    )
                    continue
                self.logging.info(
                    f"🪧 [{index}] 课程: {course_name} ({course_info_name}) | 教师: {teacher} | ⏳ 学习时长: {study_time} | 成绩: {final_score}"
                )

            self.logging.info("➕➕➕ 课程读取完成 ➕➕➕")
            self.logging.info("")
            # 打印跳过的课程
            if skipped_courses:
                self.logging.info(f"🚫 共跳过 {len(skipped_courses)} 门课程: {', '.join(skipped_courses)}")
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
        teacher = course.get("presidingTeacher", "未知教师")
        course_info_name = course.get("courseInfoName", "未知课程信息")
        study_time = course.get("studyTime", "未知")
        final_score = course.get("finalScore", "未知")
        course_info_id = course.get("courseInfoId")

        self.logging.info(
            f"🎯 课程: {course_name} ({course_info_name}) | 教师: {teacher} | ⏳ 学习时长: {study_time} | 成绩: {final_score}"
        )

        if course_info_id:
            study_design_list = self.client.study_design_list(course_info_id)
            if not isinstance(study_design_list, list):
                self.stats["errors"] += 1
                self.logging.error(f"❌ 读取课程目录失败: {course_name}")
                return
            self.stats["courses"] += 1
            self.print_course_structure(study_design_list)
        else:
            self.stats["errors"] += 1
            self.logging.warning(f"⚠️ 课程 {course_name} 缺少 CourseInfoId，跳过")

    def print_course_structure(self, nodes: List[Dict[str, Any]], indent: int = 0) -> None:
        """递归打印课程结构"""
        prefix = " " * (indent * 4)  # 每层缩进 4 个空格

        for node in nodes:
            name = node.get("name", "未知")
            file_type = node.get("fileType", "未知")
            self.logging.info(f"{prefix}- {name} ({file_type})")

            children = node.get("children", [])
            if children:
                self.print_course_structure(children, indent + 1)
            else:
                self.handle_resource(node, indent)

    def handle_resource(self, node: Dict[str, Any], indent: int = 0) -> None:
        """检查资源并在普通模式保存进度；作业、测验和考试始终跳过。"""
        resource_name = node.get("name") or "未知资源"
        file_type = node.get("fileType") or "未知类型"
        record = node.get("studentStudyRecord") or {}
        prefix = " " * ((indent + 1) * 4)
        if file_type in ASSESSMENT_TYPES or str(record.get("speed")) in ("100", "100.0"):
            self.stats["skipped"] += 1
            return
        try:
            source_id = node.get("id")
            if not source_id or not node.get("courseInfoId"):
                raise ValueError("资源缺少课程或课件 ID")
            content = self.client.course_content(source_id)
            if not isinstance(content, dict):
                raise RuntimeError("获取课件信息失败")
            metadata = dict(content)
            if content.get("fileUrl"):
                metadata.update(resource_metadata(content["fileUrl"]))
            if content.get("urlShort") and file_type.lower() in VIDEO_TYPES | AUDIO_TYPES | DOCUMENT_TYPES:
                status = self.client.upload_file_status(content["urlShort"])
                if not isinstance(status, dict):
                    raise RuntimeError("获取课件时长或页数失败")
                metadata.update(resource_metadata(status.get("args") or {}))
            total_num = resource_total(file_type, metadata)
            self.stats["checked"] += 1
            if self.dry_run:
                self.logging.info(f"{prefix}🔎 {resource_name} ({file_type})，学习数 {total_num}")
                return
            time.sleep(random.randint(1, 3))
            response = self.client.study_record(node["courseInfoId"], node.get("parentId"), total_num,
                                                source_id, total_num, total_num, total_num)
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

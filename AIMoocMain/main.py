import json
import random
import time
from typing import List, Dict, Any

from MoocMain.log import Logger
from AIMoocMain.api import AIMoocApi
from base.util import parse_duration, get_mp3_duration


class AIMoocHandler:
    def __init__(self, jump_content: str = "", token: str = None):
        """初始化 API 客户端和日志"""
        # 跳过课程列表
        self.jump_list = []
        # 已完成的课程id列表
        self.study_record_list = []
        if jump_content and "#" in jump_content:
            self.jump_list = jump_content.split("#")[1:]

        # 根据是否提供token选择不同的初始化方式
        self.client = AIMoocApi(token=token)

        self.logging = Logger(__name__).get_log()
        self.start_courses()

    def start_courses(self) -> None:
        """获取并处理课程列表"""
        try:
            courses = self.client.my_course_list(page_size=9999)
            total_courses = courses.get("total", 0)
            course_rows = courses.get("rows", [])

            self.logging.info(
                f"📚 获取课程成功，共 {total_courses} 门课程，当前获取到 {len(course_rows)} 门课程"
            )

            if not course_rows:
                self.logging.warning("⚠️ 当前没有课程数据")
                return
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
                if any(s in course.get("courseName") for s in self.jump_list):
                    continue
                self.process_course(course)

        except Exception as e:
            self.logging.error(f"❌ 获取课程失败: {e}")

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
            self.study_record_list = self.client.study_record_list(course_info_id, course_id)
            for node in study_design_list:
                parent_id = node.get("id")
                cell_list = self.client.get_cell_list(
                    course_info_id, course_id, parent_id
                )
                self.print_course_structure(cell_list, parent_id)
        else:
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

    def handle_resource(
        self, node: Dict[str, Any], parent_id: str, indent: int = 0
    ) -> None:
        """处理最终的资源，并保存学习记录"""
        resource_name = node.get("name", "未知资源")
        file_type = node.get("fileType", "未知类型")
        course_id = node.get("courseId")
        source_id = node.get("id")
        prefix = " " * ((indent + 1) * 4)  # 每层缩进 4 个空格

        self.logging.info(
            f"{prefix} 💭 资源: {resource_name} | 类型: {file_type}"
        )

        # 跳过作业
        if file_type == "作业":
            self.logging.info(f"{prefix} ✅ 跳过作业")
            return
        
        # 跳过考试
        if file_type == "考试":
            self.logging.info(f"{prefix} ✅ 跳过考试")
            return
        
        # 跳过测验
        if file_type == "测验":
            self.logging.info(f"{prefix} ✅ 跳过测验")
            return

        # 已完成的课程不再处理
        if source_id in self.study_record_list:
            self.logging.info(f"{prefix} ✅ 跳过已完成的课程: {resource_name}")
            return

        try:
            # 默认学习总数1：图片
            total_num = 1
            # 获取课件信息
            # course_content = self.client.course_content(source_id)
            # 不知道应该学习多久，需要调用接口并转换

            course_content = json.loads(node.get("fileUrl"))
            url_short = course_content.get("url")
            # mp3 时长接口无法查询，本地获取
            if file_type == "mp3":
                mp3_duration = get_mp3_duration(course_content.get("ossOriUrl"))
                total_num = int(mp3_duration)
            if file_type == "zip":
                total_num = 1
            elif url_short:
                file_status = self.client.upload_file_status(url_short)
                file_status_args = file_status.get("args")
                # 视频类型
                file_status_args_duration = file_status_args.get("duration")
                # 文件类型
                file_status_args_has_txt_file = file_status_args.get("has_txt_file")
                if file_status_args_duration:
                    total_num = parse_duration(file_status_args_duration)
                elif file_status_args_has_txt_file:
                    total_num = file_status_args.get("page_count")

            course_info_id = node.get("courseInfoId")
            study_time = total_num

            wait_time = random.randint(1, 3)

            self.logging.info(
                f"{prefix} ⏳ 学习数: {total_num}，等待 {wait_time} 秒..."
            )

            time.sleep(wait_time)
            response = self.client.study_record(
                course_id,
                course_info_id,
                parent_id,
                study_time,
                source_id,
                total_num,
                total_num,
                total_num,
            )
            self.logging.info(f"{prefix} ✅ API 响应: {response['msg']}")
        except Exception as e:
            self.logging.error(f"{prefix} ❌ 处理资源失败: {e}")

import base64
import json
import textwrap
from typing import Dict, Any, Optional, List

from MoocMain.log import Logger
from base.api_client import BaseAPIClient

logging = Logger(__name__).get_log()

# API 基础 URL
BASE_URL = "https://ai.icve.com.cn/prod-api"
SSO_URL = "https://sso.icve.com.cn/prod-api"
UPLOAD_BASE_URL = "https://urc.icve.com.cn/stage-api"


def _parse_jwt_user_id(token: Optional[str]) -> Optional[str]:
    """从 JWT payload 里取 user_id（与 ICVE_Toolkit 一致）"""
    if not token or token.count(".") < 2:
        return None
    try:
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        data = json.loads(base64.urlsafe_b64decode(payload).decode("utf-8"))
        uid = data.get("user_id") or data.get("userId") or data.get("id")
        return str(uid) if uid not in (None, "") else None
    except Exception:
        return None


class AIMoocApi(BaseAPIClient):
    def __init__(self, token: str = None, username: str = None, password: str = None):
        super().__init__(BASE_URL)

        self.token = token  # 如果提供了token，就使用OAuth登录
        self.access_token = None
        self.username = username
        self.password = password
        self.user_info: Dict[str, Any] = {}
        self.user_id: Optional[str] = None
        self.login()

    def login(self) -> None:
        """登录逻辑"""
        # 如果没有提供token，使用用户名密码登录
        if not self.token:
            logging.info("🔐 使用用户名密码登录...")
            self.token = self._get_sso_token()
            if not self.token:
                logging.error("❌ 登录失败，未获取到 token")
                return
        else:
            logging.info("🔐 使用OAuth登录获取的token...")

        self.access_token = self._get_access_token(self.token)
        if self.access_token:
            self.set_auth_token(self.access_token)
            self.get_info()
        else:
            logging.error("❌ 登录失败")

    def _get_sso_token(self) -> Optional[str]:
        """第一步：调用 SSO 登录，获取 token"""
        login_url = "/data/userLogin"
        payload = {
            "type": 1,
            "userName": self.username,
            "password": self.password,
            "webPageSource": 1,
        }

        result = self.post(login_url, json=payload, base_url=SSO_URL)
        if not result:
            return None

        token = result
        if token:
            logging.debug(f"🔑 获取到 token: {token}")
        return token

    def _get_access_token(self, token: str) -> Optional[str]:
        """第二步：使用 token 获取 access_token"""
        pass_login_url = f"/auth/passLogin?token={token}"
        result = self.get(pass_login_url)

        if result and "access_token" in result:
            return result["access_token"]
        return None

    def get_info(self) -> None:
        """获取用户信息"""
        endpoint = "/system/baseUser/info"
        user = self.get(endpoint) or {}
        self.user_info = user if isinstance(user, dict) else {}
        self.user_id = _parse_jwt_user_id(self.access_token) or str(
            self.user_info.get("id") or self.user_info.get("userId") or ""
        ) or None

        # 性别显示转换
        sex_display = {1: "男", 2: "女", 0: "未知"}.get(user.get("sex", 0), "未知")

        # 用户类型显示转换
        user_type_display = "学生" if user.get("userType") == "1" else "其他"

        # 管理员状态
        is_admin = user.get("isAdmin", 0) == 1

        # 记录日志
        logging.info(
            textwrap.dedent(
                f"""
            ┏━━━━━━━━━━━━━━━━ ✅ 用户登录成功 ━━━━━━━━━━━━━━━┓
            ┃ 📌 用户 ID    : {user.get('id', '未知')}
            ┃ 👤 用户名    : {user.get('userName', '未知')}（{user.get('displayName', '未知')}）
            ┃ 📧 邮箱      : {user.get('email', '未知') if user.get('email') else '未填写'}
            ┃ 📱 手机号    : {user.get('phoneNumber', '未知')}
            ┃ 🧑 性别      : {sex_display}
            ┃ 🏫 学校      : {user.get('schoolName', '未知')}
            ┃ 🎓 学号/工号 : {user.get('userNum', '未知')}
            ┃ 🔹 用户类型  : {user_type_display}
            ┃ 🔸 管理员    : {"是" if is_admin else "否"}
            ┃ 📅 创建时间  : {user.get('createTime', '未知')}
            ┃ 🔄 更新时间  : {user.get('updateTime', '未知')}
            ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
            """
            )
        )

    def my_course_list(
        self, page_num: int = 1, page_size: int = 6, query_type: int = 1, flag: int = 1
    ) -> Dict[str, Any]:
        """获取我的课程列表"""
        endpoint = "/course/courseInfo/myCourse"
        params = {
            # 分页
            "pageNum": page_num,
            # 分页大小
            "pageSize": page_size,
            # 1 AI优课 2 常规MOOC 不传则全部
            # "courseType": query_type,
            # 1 进行中 2 即将开始 3 已结束
            "queryStatus": flag,
            # 查询类型
            "queryType": query_type
        }
        return self.get(endpoint, params=params)

    def study_design_list(
        self, course_info_id: str, course_id: str
    ) -> List[Dict[str, Any]]:
        """获取课程详细列表"""
        endpoint = "/course/courseDesign/getStudentDesignList"
        params = {"courseInfoId": course_info_id, "courseId": course_id}
        return self.get(endpoint, params=params)

    def study_record_list(
        self, course_info_id: str, course_id: str
    ) -> List[Dict[str, Any]]:
        """获取课程已完成的学习记录"""
        endpoint = "/course/studyRecord/completed/courseware"
        params = {"courseInfoId": course_info_id, "courseId": course_id}
        return self.get(endpoint, params=params)

    def get_cell_list(
        self, course_info_id: str, course_id: str, parent_id: str
    ) -> List[Dict[str, Any]]:
        """获取课程结构"""
        endpoint = "/course/courseDesign/getCellList"
        params = {
            "courseInfoId": course_info_id,
            "courseId": course_id,
            "parentId": parent_id,
        }
        return self.get(endpoint, params=params)

    def course_content(self, source_id: str) -> Dict[str, Any]:
        """获取单个课程详细信息"""
        endpoint = f"/teacher/courseContent/{source_id}"
        return self.get(endpoint)

    def study_record(
        self,
        course_id: str,
        course_info_id: str,
        parent_id: str,
        study_time: int,
        source_id: str,
        actual_num: int,
        last_num: int,
        total_num: int,
    ) -> Dict[str, Any]:
        """保存学习记录"""
        endpoint = "/course/studyRecord"
        params = {
            "courseId": course_id,
            "courseInfoId": course_info_id,
            "parentId": parent_id,
            "sourceId": source_id,
            "actualNum": actual_num,
            "lastNum": last_num,
            "totalNum": total_num,
            "studyDuration": study_time,
        }

        return self.post(endpoint, json=params, origin_response=True)

    def get_exam_list_by_student(
        self, course_info_id: str, course_id: str, category_id: int, page_num: int = 1, page_size: int = 999
    ) -> Any:
        """获取学生的作业/测验/考试列表

        categoryId: 1/2/3（具体含义以接口返回的名称字段为准）
        """
        endpoint = "/course/exam/record/getExamListByStudent"
        params = {
            "pageNum": page_num,
            "pageSize": page_size,
            "courseInfoId": course_info_id,
            "courseId": course_id,
            "categoryId": category_id,
        }
        return self.get(endpoint, params=params, origin_response=True)

    def get_exam_paper(self, exam_id: str, group_id: str = "0") -> Any:
        """获取试卷题目（作业/测验/考试共用）"""
        endpoint = "/course/exam/paper"
        params = {"id": exam_id, "groupId": group_id}
        return self.get(endpoint, params=params, origin_response=True)

    def get_exam_record_info(
        self,
        course_info_id: str,
        task_id: str,
        exam_id: str,
        student_id: Optional[str] = None,
        type_id: str = "1",
    ) -> Any:
        """获取考试/测验作答记录详情（含标准答案、已交卷时含我的答案）

        GET /course/exam/record/getInfo
        taskId 取 paper 响应里 taskExamRecord.id
        studentId 默认取登录用户 id（JWT user_id / baseUser.id）
        """
        endpoint = "/course/exam/record/getInfo"
        params = {
            "courseInfoId": course_info_id,
            "taskId": task_id,
            "examId": exam_id,
            "studentId": student_id or self.user_id or "",
            "type": type_id,
        }
        return self.get(endpoint, params=params, origin_response=True)

    def upload_file_status(self, url_short: str) -> Dict[str, Any]:
        """获取单个课程详细信息"""
        endpoint = f"/{url_short}/status"
        return self.post(endpoint, base_url=UPLOAD_BASE_URL)

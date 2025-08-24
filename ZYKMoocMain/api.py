import json
import textwrap
from typing import Dict, Any, Optional, List

from MoocMain.log import Logger
from base.api_client import BaseAPIClient
from base.util import aes_encrypt_ecb

logging = Logger(__name__).get_log()

# API 基础 URL
SSO_URL = "https://sso.icve.com.cn/prod-api"
ZYK_BASE_URL = "https://zyk.icve.com.cn/prod-api"
ZYK_UPLOAD_BASE_URL = "https://upload.icve.com.cn"


class ZYKMoocApi(BaseAPIClient):
    def __init__(self, username: str = "", password: str = "", token: str = None):
        super().__init__(ZYK_BASE_URL)
        self.username = username
        self.password = password
        self.student_id = ''

        self.token = token  # 如果提供了token，就使用OAuth登录
        self.access_token = None

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
        payload = {"type": 1, "userName": self.username, "password": self.password, "webPageSource": 1}

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
        endpoint = "/system/user/getInfo"
        response = self.get(endpoint)
        user = response.get("user", {})

        # 获取 student_id
        self.student_id = user['userId']

        # 记录日志
        logging.info(
            textwrap.dedent(f"""
            ┏━━━━━━━━━━━━━━━━ ✅ 用户登录成功 ━━━━━━━━━━━━━━━┓
            ┃ 📌 用户 ID    : {user.get('userId', '未知')}
            ┃ 👤 用户名    : {user.get('userName', '未知')}（{user.get('nickName', '未知')}）
            ┃ 📧 邮箱      : {user.get('email', '未知')}
            ┃ 📱 手机号    : {user.get('phonenumber', '未知')}
            ┃ 🧑 性别      : {user.get('sex', '未知')}
            ┃ 🏫 学校      : {user.get('schoolName', '未知')}
            ┃ 🎓 学号/工号 : {user.get('jobNo', '未知')}
            ┃ 🔹 用户类型  : {"管理员" if user.get("admin", False) else "普通用户"}
            ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
            """)
        )

    def my_course_list(self, page_num: int = 1, page_size: int = 6, flag: int = 1) -> Dict[str, Any]:
        """获取我的课程列表"""
        endpoint = "/teacher/courseList/myCourseList"
        params = {"pageNum": page_num, "pageSize": page_size, "flag": flag}
        return self.get(endpoint, params=params)

    def study_design_list(self, course_info_id: str) -> List[Dict[str, Any]]:
        """获取课程详细列表"""
        endpoint = "/teacher/courseContent/studyDesignList"
        params = {"courseInfoId": course_info_id}
        return self.get(endpoint, params=params)

    def course_content(self, source_id: str) -> Dict[str, Any]:
        """获取单个课程详细信息"""
        endpoint = f"/teacher/courseContent/{source_id}"
        return self.get(endpoint)

    def study_record(
            self, course_info_id: str, parent_id: str, study_time: int, source_id: str,
            actual_num: int, last_num: int, total_num: int
    ) -> Dict[str, Any]:
        """保存学习记录"""
        endpoint = "/teacher/studyRecord"
        params = {
            "courseInfoId": course_info_id,
            "id": None,
            "parentId": parent_id,
            "studyTime": study_time,
            "sourceId": source_id,
            "studentId": self.student_id,
            "actualNum": actual_num,
            "lastNum": last_num,
            "totalNum": total_num
        }
        json_str = json.dumps(params, separators=(',', ':'))
        return self.put(endpoint, data=aes_encrypt_ecb(b"djekiytolkijduey", json_str))

    def upload_file_status(self, url_short: str) -> Dict[str, Any]:
        """获取单个课程详细信息"""
        endpoint = f"/{url_short}/status"
        return self.post(endpoint, base_url=ZYK_UPLOAD_BASE_URL)

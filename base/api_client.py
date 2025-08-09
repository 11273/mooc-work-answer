from MoocMain.log import Logger
from base.util import create_session, parse_response

logger = Logger(__name__).get_log()


class BaseAPIClient:
    """
    通用 API 客户端基类，支持多个 base_url，封装 GET、POST、PUT 请求
    """

    def __init__(self, base_url):
        self.session = create_session()
        self.default_base_url = base_url  # 默认的 base_url
        self.access_token = None  # 存储 Token

    def set_auth_token(self, token):
        """设置 Authorization 头"""
        self.access_token = token
        self.session.headers.update({"Authorization": f"Bearer {token}"})

    def get(self, endpoint, params=None, base_url=None):
        """封装 GET 请求，支持自定义 base_url"""
        url = f"{base_url or self.default_base_url}{endpoint}"
        try:
            logger.debug(f"GET 请求: {url} | 参数: {params}")
            response = self.session.get(url, params=params)
            # logger.debug(f"GET 响应: {response.status_code} | {response.text}")
            return parse_response(response)
        except Exception as e:
            logger.error(f"GET 请求失败: {e}")
            return None

    def post(self, endpoint, json=None, data=None, base_url=None, origin_response=False):
        """封装 POST 请求，支持自定义 base_url"""
        url = f"{base_url or self.default_base_url}{endpoint}"
        try:
            logger.debug(f"POST 请求: {url} | JSON: {json} | 表单数据: {data}")
            response = self.session.post(url, json=json, data=data)
            logger.debug(f"POST 响应: {response.status_code} | {response.text}")
            if origin_response:
                return response.json()
            else:
                return parse_response(response)
        except Exception as e:
            logger.error(f"POST 请求失败: {e}")
            return None

    def put(self, endpoint, json=None, data=None, base_url=None):
        """封装 PUT 请求，支持自定义 base_url"""
        url = f"{base_url or self.default_base_url}{endpoint}"
        try:
            logger.debug(f"PUT 请求: {url} | JSON: {json} | 表单数据: {data}")
            response = self.session.put(url, json=json, data=data)
            logger.debug(f"PUT 响应: {response.status_code} | {response.text}")
            return parse_response(response)
        except Exception as e:
            logger.error(f"PUT 请求失败: {e}")
            return None

    def login(self):
        """子类必须实现登录逻辑"""
        raise NotImplementedError("子类必须实现 login() 方法")

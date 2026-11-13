from urllib.parse import urlsplit

from MoocMain.log import Logger
from base.util import create_session, parse_response

logger = Logger(__name__).get_log()


class BaseAPIClient:
    """通用 API 客户端；限制网络等待时间，日志不记录凭据和完整响应。"""

    def __init__(self, base_url):
        self.session = create_session()
        self.default_base_url = base_url
        self.access_token = None
        self.timeout = (10, 30)

    def set_auth_token(self, token):
        self.access_token = token
        self.session.headers.update({"Authorization": f"Bearer {token}"})

    def _request(self, method, endpoint, base_url=None, origin_response=False, **kwargs):
        url = f"{base_url or self.default_base_url}{endpoint}"
        parts = urlsplit(url)
        log_url = f"{parts.scheme}://{parts.netloc}{parts.path}"
        try:
            logger.debug("%s 请求: %s", method, log_url)
            response = self.session.request(method, url, timeout=self.timeout, **kwargs)
            response.raise_for_status()
            logger.debug("%s 响应: HTTP %s", method, response.status_code)
            return response.json() if origin_response else parse_response(response)
        except Exception as error:
            # requests 异常字符串可能包含 token 查询参数，不能直接写入日志。
            status = getattr(getattr(error, "response", None), "status_code", None)
            logger.error("%s 请求失败: %s (%s%s)", method, log_url, type(error).__name__,
                         f", HTTP {status}" if status else "")
            return None

    def get(self, endpoint, params=None, base_url=None, origin_response=False):
        return self._request("GET", endpoint, params=params, base_url=base_url, origin_response=origin_response)

    def post(self, endpoint, json=None, data=None, base_url=None, origin_response=False):
        return self._request("POST", endpoint, json=json, data=data, base_url=base_url,
                             origin_response=origin_response)

    def put(self, endpoint, json=None, data=None, base_url=None, origin_response=False):
        return self._request("PUT", endpoint, json=json, data=data, base_url=base_url,
                             origin_response=origin_response)

    def login(self):
        raise NotImplementedError("子类必须实现 login() 方法")

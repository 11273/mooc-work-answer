# -*- coding: utf-8 -*-
# @Time : 2022/7/28 10:08
# @Author : Melon
# @Site : 
# @Note : 
# @File : moocGateWay.py.py
# @Software: PyCharm
import re
import time
import uuid
from io import BytesIO

import requests
from lxml import etree

from MoocMain.log import Logger

logger = Logger(__name__).get_log()

MOOC_HEP_APPID = '62c68c16986dff657908e4bc'
MOOC_HEP_USER_POOLID = '62c68bfa7f89491f3b70f280'
MOOC_WX_APPID = 'wxf7f671abd8620e81'

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36',
}


def get_qrconnect_image(session, uuid_val):
    url = "https://open.weixin.qq.com/connect/qrconnect"
    payload = {
        'appid': MOOC_WX_APPID,
        'redirect_uri': f'https://core.u2.hep.com.cn/connection/social/hep-wx/{MOOC_HEP_APPID}/callback',
        'response_type': 'code',
        'scope': 'snsapi_login',
        'state': uuid_val,
    }
    get = session.get(url=url, params=payload, headers=headers)
    etree_html = etree.HTML(get.content)
    return 'https://open.weixin.qq.com' + \
           etree_html.xpath("//div[@id='wx_default_tip']/img[@class='web_qrcode_img']/@src")[0]


def open_image(session, image_url):
    try:
        from PIL import Image
        requests_get = session.get(url=image_url, headers=headers)
        Image.open(BytesIO(requests_get.content)).show()
    except Exception as e:
        logger.info(e)
        logger.info('打开微信二维码失败，请重新运行!!!')


def get_qrconnect_result(session, qrcode_image_code):
    url = "https://lp.open.weixin.qq.com/connect/l/qrconnect"
    payload = {
        'uuid': qrcode_image_code,
        '_': time.time(),
    }
    get = session.get(url=url, params=payload, headers=headers)
    return get.text


def get_hep_callback(session, qrconnect_result_code, uuid_val):
    url = "https://icve-gateway-web.u2.hep.com.cn/connections/social/hep-wx"
    payload = {
        'app_id': MOOC_HEP_APPID,
        'redirect_url': 'https://wangguan.icve.com.cn/sso/login2/?state=http://mooc.icve.com.cn/',
    }
    session.get(url=url, params=payload, headers=headers)  # 必须调用 同一个会话中会自动处理
    url = f"https://core.u2.hep.com.cn/connection/social/hep-wx/{MOOC_HEP_USER_POOLID}/callback"
    payload = {
        'code': qrconnect_result_code,
        'state': uuid_val,
    }
    get = session.get(url=url, params=payload, headers=headers)
    etree_html = etree.HTML(get.content)

    return {
        'interactionKey': etree_html.xpath("//input[@name='interactionKey']/@value")[0],
        'debug_conn_id': etree_html.xpath("//input[@name='debug_conn_id']/@value")[0],
    }


def get_hep_relay_login_state(session, payload):
    url = "https://icve-gateway-web.u2.hep.com.cn/interaction/federation/relayLoginState"
    login = session.post(url=url, data=payload, headers=headers)
    # 内部 header Location 里面就有登录的链接，进入之后返回ck
    return login.cookies


def mooc_gateway_auth(session):
    logger.info("\n\n===== 【正在进行 mooc 网关认证，请在弹出二维码 15s 内进行微信扫码，逾期请重新运行！】===== ")
    uuid_uuid = uuid.uuid1()
    # 获取二维码链接
    qrconnect_image_url = get_qrconnect_image(session=session, uuid_val=uuid_uuid)
    logger.debug('二维码链接获取成功: %s', qrconnect_image_url)
    # 打开二维码进行扫码
    open_image(session=session, image_url=qrconnect_image_url)
    # 获取二维码唯一code
    image_url_code = qrconnect_image_url.replace('https://open.weixin.qq.com/connect/qrcode/', '')
    logger.debug('二维码 code 截取成功: %s', image_url_code)
    # 获取扫码结果
    qrconnect_result_code = None
    while not qrconnect_result_code:
        logger.info('监听扫码结果中......')
        get_qrconnect_result_val = get_qrconnect_result(session=session, qrcode_image_code=image_url_code)
        re_findall = re.findall(r"(?<=window.wx_code=').*(?=';)", get_qrconnect_result_val)
        if re_findall:
            qrconnect_result_code = re_findall[0]
    logger.debug('扫码结果为: %s', qrconnect_result_code)
    # 获取生成 GATEWAY_TOKEN 的主要参数
    payload = get_hep_callback(session=session, qrconnect_result_code=qrconnect_result_code, uuid_val=uuid_uuid)
    logger.debug('回调返回值 payload: %s', payload)
    # 获取到之后 用参数进行模拟登录 获取 GATEWAY_TOKEN
    get_hep_relay_login_state(session=session, payload=payload)
    logger.debug('COOKIES: %s', session.cookies)
    return len([key for key in session.cookies.keys() if 'GATEWAY_TOKEN' in key]) > 0


if __name__ == '__main__':
    mooc_gateway_auth(requests.session())

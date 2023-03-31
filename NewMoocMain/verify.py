# -*- coding: utf-8 -*-
# @Time : 2023/3/31 10:15
# @Author : Melon
# @Site : 
# @File : verify.py
# @Software: PyCharm
import base64
import time
import uuid
from io import BytesIO

import cv2
import numpy as np
import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from PIL import Image
from MoocMain.log import Logger

logger = Logger(__name__).get_log()


def get_aes(word, key):
    aes = AES.new(key.encode(), AES.MODE_ECB)
    res = aes.encrypt(pad(word.encode(), AES.block_size, style='pkcs7'))
    return str(base64.b64encode(res), encoding="utf-8")


# 获取验证码信息
def get_verify_info(client_uid):
    # post请求api
    url = "https://sso.icve.com.cn/captcha/get"
    data = {
        "captchaType": "blockPuzzle",
        "clientUid": f"slider-{client_uid}",
        "ts": int(time.time() * 1000)
    }
    result = requests.post(url, json=data)
    return result.json()


# 验证验证码
def verify_code(client_uid, word, key, token):
    url = "https://sso.icve.com.cn/captcha/check"
    data = {
        "captchaType": "blockPuzzle",
        "pointJson": get_aes(word, key),
        "token": token,
        "clientUid": f"slider-{client_uid}",
        "ts": int(time.time() * 1000)
    }
    result = requests.post(url, json=data)
    return result.json()


# 计算缺口位置
def get_position(original_image_base64, jigsaw_image_base64):
    original_image = Image.open(BytesIO(base64.b64decode(original_image_base64)))
    jigsaw_image = Image.open(BytesIO(base64.b64decode(jigsaw_image_base64)))
    target_width, target_height = 384, 200
    original_image = original_image.resize((target_width, target_height), resample=Image.Resampling.LANCZOS)
    original_cv_image = cv2.cvtColor(np.array(original_image), cv2.COLOR_RGB2BGR)
    jigsaw_cv_image = cv2.cvtColor(np.array(jigsaw_image), cv2.COLOR_RGB2BGR)
    bg_edge = cv2.Canny(original_cv_image, 150, 180)
    tp_edge = cv2.Canny(jigsaw_cv_image, 150, 180)
    bg_pic = cv2.cvtColor(bg_edge, cv2.COLOR_GRAY2RGB)
    cut_pic = cv2.cvtColor(tp_edge, cv2.COLOR_GRAY2RGB)
    res = cv2.matchTemplate(bg_pic, cut_pic, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)  # 寻找最优匹配
    return max_loc[0] * 310 / 384


def start_verify():
    logger.info("模拟滑块验证码中，请耐心等待...")
    while True:
        client_uid = uuid.uuid4()
        verify_info = get_verify_info(client_uid)
        original_image_base64 = verify_info['repData']['originalImageBase64']
        jigsaw_image_base64 = verify_info['repData']['jigsawImageBase64']
        position = get_position(original_image_base64, jigsaw_image_base64)
        secret_key = verify_info['repData']['secretKey']
        token = verify_info['repData']['token']
        coordinate = '{"x":' + str(position) + ',"y": 5}'
        code_result = verify_code(client_uid, coordinate, secret_key, token)

        if code_result['repCode'] == '0000':
            word = f"{code_result['repData']['token']}---{coordinate}"
            imgCode = get_aes(word, secret_key)
            logger.info("成功。")
            return imgCode
        else:
            logger.info(code_result['repMsg'])

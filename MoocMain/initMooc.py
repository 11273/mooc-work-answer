# -*- coding: utf-8 -*-
# @Time : 2022/3/31 9:34
# @Author : Melon
# @Site : 
# @Note : 
# @File : initMooc.py
# @Software: PyCharm
import time
from io import BytesIO

# import ddddocr
import requests
from PIL import Image

BASE_URL = 'https://mooc.icve.com.cn'

# 登录
LOGIN_SYSTEM_URL = BASE_URL + '/portal/LoginMooc/loginSystem'


# def auto_identify_verify_code(verify_code_content):
#     """
#     自动识别验证码
#     :param verify_code_content: 验证码 content
#     :return: 验证码
#     """
#     print("\t-->进行自动识别验证码 ~ ", end="")
#     try:
#         ocr = ddddocr.DdddOcr(show_ad=False)
#         res = ocr.classification(verify_code_content)
#         print("识别成功:" + str(res))
#         return res
#     except Exception as e:
#         print("识别失败:" + str(e))
#         return "xxxx"


def manual_identify_verify_code(verify_code_content):
    """
    手动输入验证码
    :param verify_code_content: 验证码 content
    :return: 验证码
    """
    Image.open(BytesIO(verify_code_content)).show()
    return input("请输入验证码：")


def to_url(name, password, login_fail_num):
    code_url = "https://mooc.icve.com.cn/portal/LoginMooc/getVerifyCode?ts={}".format(time.time())
    code_result = requests.post(url=code_url)
    # ----------去除自动输入验证码start
    # if login_fail_num < 3:
    #     code_value = auto_identify_verify_code(code_result.content)
    # else:
    #     code_value = manual_identify_verify_code(code_result.content)
    # ----------去除自动输入验证码end
    code_value = manual_identify_verify_code(code_result.content)
    # ----------改为手动输入验证码
    data = {
        'userName': name,
        'password': password,
        'verifycode': code_value
    }
    result = requests.post(url=LOGIN_SYSTEM_URL, data=data, cookies=code_result.cookies)
    return result


def login(name, password):  # 0.登录
    """
    登录
    :param name: 用户名
    :param password: 密码
    :return: cookies
    """
    login_fail_num = 0
    print('正在登录账号:', name)
    while login_fail_num < 4:
        result = to_url(name, password, login_fail_num)
        json_result = result.json()
        if json_result['code'] == 1 and json_result['msg'] == "登录成功":
            print("==================== 登陆成功:【" + str(name), json_result['schoolName'],  "】 ====================")
            return result.cookies
        else:
            print("\t\t--->", json_result['msg'])
            login_fail_num += 1
    raise Exception("账号:" + str(name) + " 登录失败")

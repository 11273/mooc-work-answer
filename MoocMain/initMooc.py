# -*- coding: utf-8 -*-
# @Time : 2022/3/31 9:34
# @Author : Melon
# @Site : 
# @Note : 
# @File : initMooc.py
# @Software: PyCharm
import asyncio
import os
import random
import time
from io import BytesIO


import requests

import MoocMain.lookVideo as mook_video
from MoocMain.log import Logger

logger = Logger(__name__).get_log()

BASE_URL = 'https://mooc-old.icve.com.cn'
# 登录
LOGIN_SYSTEM_URL = BASE_URL + '/portal/LoginMooc/loginSystem'
# 获取验证码
GET_VERIFY_CODE = BASE_URL + '/portal/LoginMooc/getVerifyCode?ts={ts}'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36'
}


def get_verify_code(session):
    code_result = session.post(url=GET_VERIFY_CODE.format(ts=time.time()), headers=HEADERS)
    verify_code_file = './verify_code.jpg'
    try:
        from PIL import Image
        Image.open(BytesIO(code_result.content)).show()
        time.sleep(0.2)
        code_value = input("请输入验证码：")
    except Exception as e:
        logger.info(e)
        logger.info('打开验证码失败!!! 请前往该项目根目录找到并打开 verify_code.jpg 后输入验证码!!!')
        with open(verify_code_file, "wb", ) as f:
            f.write(code_result.content)
        code_value = input("请输入验证码：")
    finally:
        # 删除验证码照片
        if os.path.exists(verify_code_file):
            os.remove(verify_code_file)
    if not code_result.cookies or not code_value:
        logger.error('识别验证码出错，程序退出!')
        input()
        exit(0)
    return {'verify_code_ck': code_result.cookies, 'verify_code_value': code_value}


def to_login(session, name, password):  # 0.登录
    logger.info('\n正在登录账号: %s', name)
    verify_code = get_verify_code(session)
    vc_ck = verify_code['verify_code_ck']
    vc_val = verify_code['verify_code_value']
    data = {
        'userName': name,
        'password': password,
        'verifycode': vc_val
    }
    result = session.post(url=LOGIN_SYSTEM_URL, data=data, cookies=vc_ck, headers=HEADERS)
    json_result = result.json()
    if json_result['code'] == 1 and json_result['msg'] == "登录成功":
        logger.info("====> 登陆成功:【%s】", json_result['schoolName'])
        return result.cookies
    else:
        logger.error("====> 登陆失败: %s", json_result['msg'])
        logger.error('程序关闭，请重新执行......')
        input()
        exit(0)


def save_cookies(session, username1, password1):  # 登录
    ck = {}
    if username1 and password1:
        ck['ck1'] = to_login(session, username1, password1)
    else:
        logger.error("请填写账号1 账号以及密码!!! 程序关闭，请重新执行......")
        input()
        exit(0)
    return ck


def getCourseOpenList(session):
    time.sleep(0.25)
    url = "https://mooc-old.icve.com.cn/portal/Course/getMyCourse?isFinished=0&pageSize=5000"
    result = session.post(url=url, headers=HEADERS).json()
    return result['list']


def run(username1, password1):
    session = requests.session()

    # TODO 出现微信扫码认证，请打开下面注释
    # from moocGateWay import mooc_gateway_auth
    # mooc_gateway_auth(session)

    user_cookies = save_cookies(session, username1, password1)
    pass_work = None
    for err_n in range(10, 0, -1):
        is_continue_work = []
        try:
            logger.info('\n')
            session.cookies.update(user_cookies['ck1'])
            username1course = getCourseOpenList(session)
            logger.info('%s 大号所有课程 %s', "*" * 40, "*" * 40)
            filter_map = {}
            filter_idx = 0
            for course_item in username1course:
                filter_idx += 1
                logger.info('*\t【%s】总进度:%s %%\t\t课程名: %s', filter_idx, course_item['process'],
                            course_item['courseName'])
                filter_map[filter_idx] = course_item['courseName']
            logger.info("*" * 90)
            time.sleep(0.2)
            logger.info('\n(可选)请输入需要跳过的课程序号，英文逗号隔开，回车跳过(例: 1,3,4) ↓')
            if not pass_work:
                filter_list = input("请输入: ") or []
            else:
                filter_list = pass_work
            if filter_list:
                filter_list.replace(" ", "").split(',')
                is_continue_work = [filter_map[int(i)] for i in filter_list.replace(" ", "").split(',') if i]

            # 获取大号的所有课程
            username1course = getCourseOpenList(session)
            logger.info('%s 大号所有课程 %s', "*" * 40, "*" * 40)
            for course_item in username1course:
                if course_item['courseName'] in is_continue_work:
                    logger.info(
                        '* 【pass】  总进度: %s %%\t\t课程名: %s', course_item['process'], course_item['courseName'])
                else:
                    logger.info(
                        '*\t\t\t总进度: %s %%\t\t课程名: %s', course_item['process'], course_item['courseName'])
            logger.info("*" * 90 + '\n')
            logger.info('-' * 60)
            logger.info('-' * 25 + '刷课开始！' + '-' * 25)
            logger.info('-' * 60 + '\n')
            asyncio.run(mook_video.start(session, is_continue_work))
            break
        except Exception as e:
            sleep_int = random.randint(10, 30)
            logger.exception('程序出现异常，延时 %ss 后重试，剩余重试次数: %s，等待重试 %s', sleep_int, err_n, e)
            time.sleep(sleep_int)
            continue

    logger.info('\n')
    logger.info('=' * 100)
    logger.info('%s 运行结束 支持一下！By https://github.com/11273/mooc-work-answer %s', '=' * 20, '=' * 20)
    logger.info('=' * 100)
    logger.info('程序运行结束，关闭程序......')
    input()

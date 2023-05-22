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
import workMain
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


def save_cookies(session, username1, password1, username2, password2):  # 登录
    ck = {}
    if username1 and password1:
        ck['ck1'] = to_login(session, username1, password1)
        if username2 and password2:
            if username1 == username2 and password1 == password2:
                logger.error('小号请勿使用与大号相同账号！！！ 程序关闭，请重新执行......')
                input()
                exit(0)
            ck['ck2'] = to_login(session, username2, password2)
        else:
            logger.info("\n>>> 未填写账号2信息，仅刷课不答题!")
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


def run(username1, password1,
        username2,
        password2,
        is_withdraw_course,
        is_work_exam_type0,
        is_work_exam_type1,
        is_work_exam_type2,
        is_work_score):
    session = requests.session()

    # TODO 出现微信扫码认证，请打开下面注释
    # from moocGateWay import mooc_gateway_auth
    # mooc_gateway_auth(session)

    user_cookies = save_cookies(session, username1, password1, username2, password2)
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
            if not user_cookies.get('ck2', None):
                raise Exception("获取Cookie失败！")

            logger.info('-' * 60)
            logger.info('-' * 25 + '答题中！' + '-' * 25)
            logger.info('-' * 60)

            # 0.获取小号的所有课程
            session.cookies.update(user_cookies['ck2'])
            username2course = workMain.getMyCourse(session)['list']
            if is_withdraw_course:
                # 1.退出小号的所有课程
                for u2course_item in username2course:
                    work_withdraw_course = workMain.withdrawCourse(session, u2course_item['courseOpenId'],
                                                                   u2course_item['stuId'])
                    logger.info('[小号退出课程] 结果: %s\t退出课程: %s', work_withdraw_course['msg'],
                                u2course_item['courseName'])

            # 3.添加大号课程给小号
            username2course = workMain.getMyCourse(session)['list']
            for u1course_item in username1course:
                if u1course_item['courseOpenId'] in [x['courseOpenId'] for x in username2course]:
                    logger.info('[小号添加课程] 结果: 课程已存在! \t\t添加课程: %s ', u1course_item['courseName'])
                else:
                    work_add_my_mooc_course = workMain.addMyMoocCourse(session,
                                                                       u1course_item['courseOpenId'])
                    logger.info('[小号添加课程] 结果: %s \t\t添加课程: %s ', work_add_my_mooc_course.get('msg', 'Fail'),
                                u1course_item['courseName'])
                    if work_add_my_mooc_course['code'] == -2:
                        verify_code = get_verify_code(session)
                        vc_ck = verify_code['verify_code_ck']
                        vc_val = verify_code['verify_code_value']
                        work_add_my_mooc_course = workMain.addMyMoocCourse(session, u1course_item['courseOpenId'],
                                                                           vc_val, vc_ck['verifycode'])
                        logger.info('[小号添加课程] 结果: %s \t\t添加课程: %s ',
                                    work_add_my_mooc_course.get('msg', 'Fail'),
                                    u1course_item['courseName'])

            # 4.再次查看小号课程
            username2course = workMain.getMyCourse(session)['list']
            logger.info('%s 小号所有课程(请检查大号的课程已全部显示在此处) %s', "*" * 24, "*" * 24)
            for course_item in username2course:
                if course_item['courseName'] in is_continue_work:
                    logger.info(
                        '* 【pass】  总进度: %s %%\t\t课程名: %s', course_item['process'], course_item['courseName'])
                else:
                    logger.info(
                        '*\t\t\t总进度: %s %%\t\t课程名: %s', course_item['process'], course_item['courseName'])
            logger.info("*" * 90 + '\n')
            logger.info('-' * 65)
            logger.info('-' * 20 + '初始化课程成功，开始答题！' + '-' * 20)
            logger.info('-' * 65)

            # 5.小号做作业，考试，测验
            work_exam_type = []
            if is_work_exam_type0:
                work_exam_type.append(0)
            if is_work_exam_type1:
                work_exam_type.append(1)
            if is_work_exam_type2:
                work_exam_type.append(2)
            for t in work_exam_type:
                for u1course in username1course:
                    if u1course['courseName'] in is_continue_work:
                        logger.info('【大号】 跳过课程 \t当前课程 \t【%s】', u1course['courseName'])
                        continue
                    # 6.大号开始答题
                    logger.info('【大号】 开始答题 \t当前课程 \t【%s】', u1course['courseName'])
                    workMain.run_start_work(session, user_cookies['ck1'], user_cookies['ck2'], t,
                                            u1course['courseOpenId'],
                                            is_work_score)
                    logger.info('%s 答题结束, 必须登录官网检查, 部分未提交的请手动提交!!! %s', '*' * 20, '*' * 20)
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

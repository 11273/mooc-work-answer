# -*- coding: utf-8 -*-
# @Time : 2022/3/31 9:34
# @Author : Melon
# @Site : 
# @Note : 
# @File : initMooc.py
# @Software: PyCharm
import os
import random
import sys
import time
from io import BytesIO

import ddddocr
import requests
from PIL import Image

import MoocMain.lookVideo as mook_video
import MoocMain.workMain as mooc_work

BASE_URL = 'https://mooc.icve.com.cn'
# 登录
LOGIN_SYSTEM_URL = BASE_URL + '/portal/LoginMooc/loginSystem'
# 获取验证码
GET_VERIFY_CODE = BASE_URL + '/portal/LoginMooc/getVerifyCode?ts={ts}'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36'
}


def get_verify_code():
    get_num = 10
    while get_num:
        get_num -= 1
        code_result = requests.post(url=GET_VERIFY_CODE.format(ts=time.time()), headers=HEADERS)
        if get_num > 4:
            print('自动识别验证码-->', end=' ')
            try:
                ocr = ddddocr.DdddOcr(show_ad=False, old=True)
                code_value = ocr.classification(code_result.content)
                if not len(code_value) == 4 or not code_value.isdigit():
                    print('识别失败:', code_value, end=' ')
                    continue
                else:
                    print('识别成功:', code_value, end=' ')
            except NameError as e:
                print(e)
                get_num = 4
                continue
        else:
            verify_code_file = './verify_code.jpg'
            try:
                Image.open(BytesIO(code_result.content)).show()
                code_value = input("请输入验证码：")
            except Exception as e:
                print(e)
                print('打开验证码失败!!! 请前往该项目根目录找到并打开 verify_code.jpg 后输入验证码!!!')
                with open(verify_code_file, "wb", ) as f:
                    f.write(code_result.content)
                code_value = input("请输入验证码：")
            finally:
                # 删除验证码照片
                if os.path.exists(verify_code_file):
                    os.remove(verify_code_file)
        if not code_result.cookies or not code_value:
            print('识别验证码出错，程序退出!')
            sys.exit(0)
        return {'verify_code_ck': code_result.cookies, 'verify_code_value': code_value}
    print('多次未成功识别验证码，程序退出，请重新运行!')
    sys.exit(0)


def to_login(name, password):  # 0.登录
    """
    登录
    :param name: 用户名
    :param password: 密码
    :return: cookies
    """
    print('\n正在登录账号:', name, end='\t')
    verify_code = get_verify_code()
    vc_ck = verify_code['verify_code_ck']
    vc_val = verify_code['verify_code_value']
    data = {
        'userName': name,
        'password': password,
        'verifycode': vc_val
    }
    result = requests.post(url=LOGIN_SYSTEM_URL, data=data, cookies=vc_ck, headers=HEADERS)
    json_result = result.json()
    if json_result['code'] == 1 and json_result['msg'] == "登录成功":
        print("====> 登陆成功:【", json_result['schoolName'], "】")
        return result.cookies
    else:
        print("====> 登陆失败", json_result['msg'])
        sys.exit(0)


def save_cookies(username1, password1, username2=None, password2=None):  # 登录
    ck = {}
    if username1 and password1:
        ck['ck1'] = to_login(username1, password1)
        if username2 and password2:
            if username1 == username2 and password1 == password2:
                print('小号请勿使用与大号相同账号！！！')
                sys.exit(0)
            ck['ck2'] = to_login(username2, password2)
        else:
            print("\n>>> 未填写账号2信息，仅刷课不答题!")
    else:
        print("请填写账号1 账号以及密码!!!")
        exit(0)
    return ck


def run(username1,
        password1,
        username2,
        password2,
        is_look_video,
        is_withdraw_course,
        is_work_exam_type0,
        is_work_exam_type1,
        is_work_exam_type2,
        is_work_score,
        is_continue_work):
    for err_n in range(10, 0, -1):
        try:
            user_cookies = save_cookies(username1, password1, username2, password2)
            print('\n')
            if is_look_video:
                print('-' * 60, '\n' + '-' * 25, '刷课中！', '-' * 25, '\n' + '-' * 60, '\n')
                mook_video.start(user_cookies['ck1'], is_continue_work)

            if not user_cookies.get('ck2', None):
                exit(0)

            print('-' * 60, '\n' + '-' * 25, '答题中！', '-' * 25, '\n' + '-' * 60, '\n')

            # 0.获取小号的所有课程
            username2course = mooc_work.getMyCourse(user_cookies['ck2'])['list']
            if is_withdraw_course:
                # 1.退出小号的所有课程
                for u2course_item in username2course:
                    work_withdraw_course = mooc_work.withdrawCourse(user_cookies['ck2'], u2course_item['courseOpenId'],
                                                                    u2course_item['stuId'])
                    print('[小号退出课程] 结果: %s\t退出课程: %s' % (work_withdraw_course['msg'], u2course_item['courseName']))

            # 2.获取大号的所有课程
            username1course = mooc_work.getMyCourse(user_cookies['ck1'])['list']
            print("*" * 40, '大号所有课程', "*" * 40)
            for course_item in username1course:
                if course_item['courseName'] in is_continue_work:
                    print('* 【pass】  ', '总进度:', str(course_item['process']) + '%\t\t课程名:', course_item['courseName'])
                else:
                    print('*\t\t\t', '总进度:', str(course_item['process']) + '%\t\t课程名:', course_item['courseName'])
            print("*" * 90, '\n')
            # 3.添加大号课程给小号
            username2course = mooc_work.getMyCourse(user_cookies['ck2'])['list']
            for u1course_item in username1course:
                if u1course_item['courseOpenId'] in [x['courseOpenId'] for x in username2course]:
                    print('[小号添加课程] 结果: 课程已存在! \t\t添加课程: %s ' % (u1course_item['courseName']))
                else:
                    work_add_my_mooc_course = mooc_work.addMyMoocCourse(user_cookies['ck2'],
                                                                        u1course_item['courseOpenId'])
                    print('[小号添加课程] 结果: %s \t\t添加课程: %s ' % (
                    work_add_my_mooc_course.get('msg', 'Fail'), u1course_item['courseName']))
                    if work_add_my_mooc_course['code'] == -2:
                        verify_code = get_verify_code()
                        vc_ck = verify_code['verify_code_ck']
                        vc_val = verify_code['verify_code_value']
                        work_add_my_mooc_course = mooc_work.addMyMoocCourse(user_cookies['ck2'],
                                                                            u1course_item['courseOpenId'], vc_val,
                                                                            vc_ck['verifycode'])
                        print('[小号添加课程] 结果: %s \t\t添加课程: %s ' % (
                        work_add_my_mooc_course.get('msg', 'Fail'), u1course_item['courseName']))

            # 4.再次查看小号课程
            print()
            username2course = mooc_work.getMyCourse(user_cookies['ck2'])['list']
            print("*" * 24, '小号所有课程(请检查大号的课程已全部显示在此处)', "*" * 24)
            for course_item in username2course:
                if course_item['courseName'] in is_continue_work:
                    print('* 【pass】  ', '总进度:', str(course_item['process']) + '%\t\t课程名:', course_item['courseName'])
                else:
                    print('*\t\t\t', '总进度:', str(course_item['process']) + '%\t\t课程名:', course_item['courseName'])
            print("*" * 90, '\n')

            print('\n' + '-' * 65, '\n' + '-' * 20, '初始化课程成功，开始答题！', '-' * 20, '\n' + '-' * 65, '\n')

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
                        print('【大号】 跳过课程 \t当前课程 \t【%s】' % u1course['courseName'])
                        continue
                    # 6.大号开始答题
                    print('【大号】 开始答题 \t当前课程 \t【%s】' % u1course['courseName'])
                    mooc_work.run_start_work(user_cookies['ck1'], user_cookies['ck2'], t, u1course['courseOpenId'],
                                             is_work_score)
            break
        except Exception as e:
            sleep_int = random.randint(20, 60)
            print('程序出现异常，延时 %ss 后重试，剩余重试次数: %s，等待重试 %s' % (sleep_int, err_n, e))
            time.sleep(sleep_int)
            continue

    print('\n' + '=' * 111, '\n' + '=' * 20, '运行结束 感谢使用 支持一下！By https://github.com/11273/mooc-work-answer', '=' * 20,
          '\n' + '=' * 111, '\n')

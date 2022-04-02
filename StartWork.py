# -*- coding: utf-8 -*-
# @Time : 2021/11/2 16:41
# @Author : Melon
# @Site : 
# @Note : 
# @File : StartWork.py
# @Software: PyCharm
import json

import MoocMain.initMooc as mooc_init
import MoocMain.lookVideo as mook_video
import MoocMain.workMain as mooc_work

# ****************************************** 配置 ******************************************
# 账号1(大号)
username1 = ""  # 账号
password1 = ""  # 密码
# 账号2(小号)
username2 = ""  # 账号
password2 = ""  # 密码

# 账号1(大号)刷课
is_look_video = True

# 自动提交 作业 考试 测验
is_auto_submit = False

# 强制自动提交 作业 考试 测验(部分无法自动提交, 开启可强制提交)
is_auto_submit_enforce = False

# 小号退出所有课程
u2_withdraw_course = False

# 做作业
is_work_exam_type0 = False

# 做测验
is_work_exam_type1 = False

# 考试
is_work_exam_type2 = False

# ****************************************** 结束 ******************************************


def save_cookies():  # 登录
    ck = {}
    if username1 and password1:
        ck['username1cookie'] = mooc_init.login(username1, password1)
        if username2 and password2:
            ck['username2cookie'] = mooc_init.login(username2, password2)
        else:
            print(">>> 未填写账号2信息，仅刷课不答题!")
    else:
        print("请填写账号1 账号以及密码!!!")
        exit(0)
    return ck


def start_look_video(cookies):  # 刷课
    mook_video.start(cookies)


def start_work_exam_type0(cookies):  # 做作业
    pass


def start_work_exam_type1(cookies):  # 做测验
    pass


def start_work_exam_type2(cookies):  # 考试
    pass


if __name__ == '__main__':
    user_cookies = save_cookies()

    work_exam_type_map = {0: '作业', 1: '测验', 2: '考试'}

    if is_look_video:
        start_look_video(user_cookies['username1cookie'])
        print(">>> 刷课程序运行结束")
    # if is_work_exam_type0:
    #     start_work_exam_type0(save_cookies['username1cookie'])
    # if is_work_exam_type1:
    #     start_work_exam_type1(save_cookies['username1cookie'])
    # if is_work_exam_type2:
    #     start_work_exam_type2(save_cookies['username1cookie'])

    if not user_cookies.get('username2cookie', None):
        exit(0)

    # 0.获取小号的所有课程
    mooc_work.cookies = user_cookies['username2cookie']
    username2course = mooc_work.getMyCourse()['list']
    print('[小号] 获取所有课程: %s' % username2course)
    if u2_withdraw_course:
        # 1.退出小号的所有课程
        for u2course_item in username2course:
            work_withdraw_course = mooc_work.withdrawCourse(u2course_item['courseOpenId'], u2course_item['stuId'])
            print('[小号] 退出课程 \t结果: %s \t\t退出课程: %s' % (work_withdraw_course['msg'], u2course_item['courseName']))

    # 2.获取大号的所有课程
    mooc_work.cookies = user_cookies['username1cookie']
    username1course = mooc_work.getMyCourse()['list']
    print('【大号】 获取所有课程: %s' % username1course)

    # 3.添加大号课程给小号
    mooc_work.cookies = user_cookies['username2cookie']
    for u1course_item in username1course:
        work_add_my_mooc_course = mooc_work.addMyMoocCourse(u1course_item['courseOpenId'])
        print(
            '[小号] 添加课程 \t结果: %s \t添加课程: %s' % (work_add_my_mooc_course.get('msg', 'Fail'), u1course_item['courseName']))

    # 4.小号做作业，考试，测验
    mooc_work.cookies = user_cookies['username2cookie']
    username2course = mooc_work.getMyCourse()['list']
    print('[小号] 生成题库 1.获取所有课程: %s' % username2course)

    work_exam_history_list = []
    for u2course in username2course:
        print('\n[小号] 生成题库 2.当前课程 \t【%s(%s)】' % (u2course['courseName'], u2course['courseOpenName']))
        for work_exam_type in range(0, 3):
            # print('[小号] 做作业、考试、测验 2.作业类型 \t\t%s' % work_exam_type_map[work_exam_type])
            work_exam_list = mooc_work.getWorkExamList(u2course['courseOpenId'], work_exam_type)
            for work_exam in work_exam_list['list']:
                # 如果没有答案 ID 就进行做作业
                if work_exam['stuWorkExamId'] == '':
                    # 通过作业ID去交作业(必须先点做作业)
                    work_exam_preview = mooc_work.workExamPreview(work_exam['Id'])
                    work_exam_save = mooc_work.workExamSave(work_exam_preview['uniqueId'], work_exam['Id'],
                                                            work_exam_type)

                # 作业提交成功后，获取我做的所有作业记录，取第一条里面有答案ID
                work_exam_detail = mooc_work.workExamDetail(work_exam['Id'], u2course['courseOpenId'])
                work_exam_history = mooc_work.workExamHistory(work_exam['Id'], work_exam_detail['list'][0]['Id'],
                                                              u2course['courseOpenId'])
                for i in json.loads(work_exam_history['workExamData'])['questions']:
                    work_exam_history_list.append([i['questionId'], i['questionType'],
                                                   i['Answer'].encode("gbk", 'ignore').decode("gbk", "ignore")])
                print('[小号] 生成题库 3.获取成功：\t{%s} \t%s' % (work_exam_type_map[work_exam_type], work_exam['Title']))
    mooc_work.csvUtil('题库', work_exam_history_list)
    # 5.大号开始答题
    mooc_work.cookies = user_cookies['username1cookie']
    to_dict = mooc_work.csv_to_dict('题库.csv')
    to_dict = json.loads(to_dict)
    work_exam_type = 0
    course = mooc_work.getMyCourse()
    for work_exam_type in range(0, 3):
        for c in course['list']:
            print('【大号】 开始答题 \t当前课程 \t【%s】' % c['courseName'])
            exam_list = mooc_work.getWorkExamList(c['courseOpenId'], work_exam_type)
            for ss in exam_list['list']:
                if ss['getScore'] > 90:
                    print('当前作业大于90分 不答题', ss['Title'])
                    continue
                print('【大号】 当前 {%s} \t%s' % (work_exam_type_map[work_exam_type], ss['Title']))
                work_exam_preview = mooc_work.workExamPreview(ss['Id'])
                my_count = 0
                daan_count = 0
                for i in json.loads(work_exam_preview['workExamData'])['questions']:
                    my_count += 1
                    for j in to_dict:
                        if i['questionId'] == j['questionId']:
                            daan_count += 1
                            answer = mooc_work.onlineHomeworkAnswer(j['questionId'], j['Answer'], j['questionType'],
                                                                    work_exam_preview['uniqueId'])
                            print('【大号】 结果 %s \t当前作业 %s \t题目 %s' % (
                                'success' if answer['code'] == 1 else 'fail', ss['Title'],
                                i['TitleText'].encode("gbk", 'ignore').decode("gbk", "ignore")))
                if is_auto_submit_enforce or my_count == daan_count:
                    save = mooc_work.workExamSave(work_exam_preview['uniqueId'], ss['Id'], work_exam_type)
                    print(save)

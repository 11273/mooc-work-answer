# -*- coding: utf-8 -*-
# @Time : 2021/11/2 16:34
# @Author : Melon
# @Site : 
# @Note : 
# @File : workMain.py
# @Software: PyCharm
import csv
import json
import logging
import random
import time
from csv import DictReader

import requests
from PIL import Image

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_URL = 'https://mooc.icve.com.cn'


# 获取我加入的所有课程
GET_MY_COURSE_URL = BASE_URL + '/portal/Course/getMyCourse'

# 获取本课程 作业/测验/考试 ID api
GET_WORK_EXAM_LIST_URL = BASE_URL + '/study/workExam/getWorkExamList'

# 做作业 api
WORK_EXAM_PREVIEW_URL = BASE_URL + '/study/workExam/workExamPreview'

# 提交作业/测验 api
WORK_EXAM_SAVE_URL = BASE_URL + '/study/workExam/workExamSave'

# 提交考试 api
ONLINE_EXAM_SAVE_URL = BASE_URL + '/study/workExam/onlineExamSave'

# 查看答案
WORK_EXAM_HISTORY_URL = BASE_URL + '/study/workExam/history'

# 查看作答列表
WORK_EXAM_DETAIL_URL = BASE_URL + '/study/workExam/detail'

# 查看答案
ONLINE_HOMEWORK_ANSWER = BASE_URL + '/study/workExam/onlineHomeworkAnswer'

# 退出课程
COURSE_WITHDRAW_COURSE = BASE_URL + '/portal/Course/withdrawCourse'

# 获取该课程所有开课信息(一般最新的开课可以加入)
GET_ALL_COURSE_CLASS_URL = BASE_URL + '/portal/Course/getAllCourseClass'

# 用 courseOpenId 去添加课程
ADD_MY_MOOC_COURSE = BASE_URL + '/study/Learn/addMyMoocCourse'

cookies = None


def getMyCourse():  # 1 我的课程列表
    # isFinished 只获取没有结束的课程
    get = requests.get(url=GET_MY_COURSE_URL, params={'isFinished': 0, 'pageSize': 1000000}, cookies=cookies)
    return get.json()


def getWorkExamList(course_open_id, work_exam_type):  # 2 获取作业 考试 测验
    params = {
        'pageSize': 50000,
        'courseOpenId': course_open_id,
        'workExamType': work_exam_type  # 0是作业，1是测验，2是考试
    }
    get = requests.get(url=GET_WORK_EXAM_LIST_URL, params=params, cookies=cookies)
    return get.json()  # 添加课程成功返回


def workExamPreview(work_exam_id):  # 3 做作业
    params = {
        'workExamId': work_exam_id,
    }
    post = requests.post(url=WORK_EXAM_PREVIEW_URL, params=params, cookies=cookies)
    return post.json()


def workExamSave(unique_id, work_exam_id, work_exam_type):  # 4 交作业

    if work_exam_type == 2:
        params = {
            'uniqueId': unique_id,
            'examId': work_exam_id,
            'workExamType': work_exam_type,
            'useTime': random.randint(300, 1000)  # 答题时间随机
        }
        post = requests.post(url=ONLINE_EXAM_SAVE_URL, params=params, cookies=cookies)
    else:
        params = {
            'uniqueId': unique_id,
            'workExamId': work_exam_id,
            'workExamType': work_exam_type,
            'useTime': random.randint(300, 1000)  # 答题时间随机
        }
        post = requests.post(url=WORK_EXAM_SAVE_URL, params=params, cookies=cookies)
    return post.json()


def workExamDetail(work_exam_id, course_open_id):  # 5 查看作答列表
    params = {
        'workExamId': work_exam_id,
        'courseOpenId': course_open_id
    }
    post = requests.post(url=WORK_EXAM_DETAIL_URL, params=params, cookies=cookies)
    return post.json()


def onlineHomeworkAnswer(question_id, answer, question_type, unique_id):  # 6 填答题卡
    '''
    填答题卡
    :param question_id: 题目ID
    :param answer: 答案
    :param question_type: 1单选 2多选 3判断
    :param unique_id: 每次点做作业都会出现一个id，目前发现不提交作业就不会变
    :return:
    '''
    params = {
        'questionId': question_id,
        'answer': answer,
        'questionType': question_type,
        'uniqueId': unique_id
    }
    post = requests.post(url=ONLINE_HOMEWORK_ANSWER, params=params, cookies=cookies)
    print(post.content)
    return post.json()


def workExamHistory(work_exam_id, student_work_id, course_open_id):  # 7 获取答案
    params = {
        'workExamId': work_exam_id,
        'studentWorkId': student_work_id,
        'courseOpenId': course_open_id
    }
    post = requests.post(url=WORK_EXAM_HISTORY_URL, params=params, cookies=cookies)
    return post.json()


def withdrawCourse(course_open_id, user_id):  # 8 退出课程
    params = {
        'courseOpenId': course_open_id,
        'userId': user_id
    }
    post = requests.post(url=COURSE_WITHDRAW_COURSE, params=params, cookies=cookies)
    return post.json()


def addMyMoocCourse(course_open_id):  # 3 添加到我的课程
    params = {
        'courseOpenId': course_open_id,
        'courseId': ''
    }
    get = requests.post(url=ADD_MY_MOOC_COURSE, params=params, cookies=cookies)
    return get.json()  # 添加课程成功返回


def csvUtil(file_name, rows, *headers):  # 写 csv 文件
    # 题目id，作业类型，答案id
    headers = ['questionId', 'questionType', 'Answer']

    with open(file_name + '.csv', 'w', newline='') as f:
        f_csv = csv.writer(f)
        f_csv.writerow(headers)
        f_csv.writerows(rows)


def csv_to_dict(filename):
    try:
        with open(filename, 'r') as read_obj:
            dict_reader = DictReader(read_obj)
            list_of_dict = list(dict_reader)
            result = json.dumps(list_of_dict, indent=2)
        return result
    except IOError as err:
        print("I/O error({0})".format(err))


# def csvUtil(file_name, rows, *headers):  # 写 csv 文件
#     # 课程名， 第几次开课，课程id，作业名，作业id，答案id
#     headers = ['courseName', 'courseOpenName', 'courseOpenId', 'Title', 'workExamId', 'stuWorkExamId']
#
#     with open(file_name + '.csv', 'w', newline='')as f:
#         f_csv = csv.writer(f)
#         f_csv.writerow(headers)
#         f_csv.writerows(rows)

# -*- coding: utf-8 -*-
# @Time : 2021/11/2 16:34
# @Author : Melon
# @Site : 
# @Note : 
# @File : workMain.py
# @Software: PyCharm
import json
import random
import re
import time

from MoocMain.log import Logger

logger = Logger(__name__).get_log()

BASE_URL = 'https://mooc-old.icve.com.cn'

GET_MY_COURSE_URL = BASE_URL + '/portal/Course/getMyCourse'

GET_WORK_EXAM_LIST_URL = BASE_URL + '/study/workExam/getWorkExamList'

WORK_EXAM_PREVIEW_URL = BASE_URL + '/study/workExam/workExamPreview'

WORK_EXAM_SAVE_URL = BASE_URL + '/study/workExam/workExamSave'

ONLINE_EXAM_SAVE_URL = BASE_URL + '/study/workExam/onlineExamSave'

WORK_EXAM_HISTORY_URL = BASE_URL + '/study/workExam/history'

WORK_EXAM_DETAIL_URL = BASE_URL + '/study/workExam/detail'

ONLINE_HOMEWORK_ANSWER = BASE_URL + '/study/workExam/onlineHomeworkAnswer'

ONLINE_HOMEWORK_CHECK_SPACE = BASE_URL + '/study/workExam/onlineHomeworkCheckSpace'

COURSE_WITHDRAW_COURSE = BASE_URL + '/portal/Course/withdrawCourse'

GET_ALL_COURSE_CLASS_URL = BASE_URL + '/portal/Course/getAllCourseClass'

ADD_MY_MOOC_COURSE = BASE_URL + '/study/Learn/addMyMoocCourse'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36'
}


def getMyCourse(session):
    time.sleep(0.25)
    get = session.get(url=GET_MY_COURSE_URL, params={'isFinished': 0, 'pageSize': 1000000}, headers=HEADERS)
    return get.json()


def getWorkExamList(session, course_open_id, work_exam_type):
    time.sleep(0.25)
    params = {
        'pageSize': 50000,
        'courseOpenId': course_open_id,
        'workExamType': work_exam_type
    }
    get = session.get(url=GET_WORK_EXAM_LIST_URL, params=params, headers=HEADERS)
    return get.json()


def workExamPreview(session, work_exam_id):
    # time.sleep(0.25)
    params = {
        'workExamId': work_exam_id,
    }
    post = session.post(url=WORK_EXAM_PREVIEW_URL, params=params, headers=HEADERS)
    return post.json()


def workExamSave(session, unique_id, work_exam_id, work_exam_type):
    # time.sleep(0.5)
    params = {
        'uniqueId': unique_id,
        'workExamType': work_exam_type,
        'useTime': random.randint(300, 1000)
    }
    if work_exam_type == 2:
        params['examId'] = work_exam_id
        post = session.post(url=ONLINE_EXAM_SAVE_URL, params=params, headers=HEADERS)
    else:
        params['workExamId'] = work_exam_id
        post = session.post(url=WORK_EXAM_SAVE_URL, params=params, headers=HEADERS)
    return post.json()


def workExamDetail(session, work_exam_id, course_open_id):
    # time.sleep(0.25)
    params = {
        'workExamId': work_exam_id,
        'courseOpenId': course_open_id
    }
    post = session.post(url=WORK_EXAM_DETAIL_URL, params=params, headers=HEADERS)
    return post.json()


def onlineHomeworkAnswer(session, question_id, answer, question_type, unique_id):
    # time.sleep(0.5)
    params = {
        'questionId': question_id,
        'answer': answer,
        'questionType': question_type,
        'uniqueId': unique_id
    }
    post = session.post(url=ONLINE_HOMEWORK_ANSWER, data=params, headers=HEADERS)
    return post.json()


def onlineHomeworkCheckSpace(session, question_id, answer, question_type, unique_id):
    time.sleep(0.5)
    pattern = re.compile(r'<[^>]+>', re.S)
    answer = pattern.sub('', answer)
    answerJson_old = [{'ortOrder': 0, 'Content': answer}]
    answerJson = str(answerJson_old).replace("'", "\"").replace(r"\n", "")
    params = {
        'questionId': question_id,
        'answer': answer,
        'answerJson': answerJson,
        'questionType': question_type,
        'uniqueId': unique_id
    }
    post = session.post(url=ONLINE_HOMEWORK_CHECK_SPACE, params=params, headers=HEADERS)
    return post.json()


def workExamHistory(session, work_exam_id, student_work_id, course_open_id):
    time.sleep(0.25)
    params = {
        'workExamId': work_exam_id,
        'studentWorkId': student_work_id,
        'courseOpenId': course_open_id
    }
    post = session.post(url=WORK_EXAM_HISTORY_URL, params=params, headers=HEADERS)
    return post.json()


def withdrawCourse(session, course_open_id, user_id):
    time.sleep(0.25)
    params = {
        'courseOpenId': course_open_id,
        'userId': user_id
    }
    post = session.post(url=COURSE_WITHDRAW_COURSE, params=params, headers=HEADERS)
    return post.json()


def addMyMoocCourse(session, course_open_id, verify_code=None, vc_ck=None):
    time.sleep(0.25)
    params = {
        'courseOpenId': course_open_id,
        'courseId': ''
    }
    if verify_code:
        params['verifycode'] = verify_code
        session.cookies.set('verifycode', vc_ck)
    get = session.post(url=ADD_MY_MOOC_COURSE, params=params, headers=HEADERS)
    return get.json()


work_exam_type_map = {0: '作业', 1: '测验', 2: '考试'}
question_type_type_map = {
    1: '单选题',
    2: '多选题',
    3: '判断题',
    4: '填空题',
    5: '填空题',
    6: '问答题',
    7: '匹配题',
    8: '阅读理解',
    9: '完形填空',
    10: '文件作答',
    11: '视听题',
}


def run_start_work(session, ck1, ck2, work_exam_type, course_open_id, is_work_score):
    session.cookies.update(ck1)
    exam_list = getWorkExamList(session, course_open_id, work_exam_type)
    for exam_item in exam_list['list']:
        if not exam_item['IsOpenMutual']:
            logger.info('\t1. 当前{%s}: === 已截止 === \t【%s】', work_exam_type_map[work_exam_type], exam_item['Title'])
            continue
        if exam_item['getScore'] > is_work_score:
            logger.info('\t1. 当前{%s}: \t分数:%s \t大于预设分数: %s \t不答题 \t【%s】', work_exam_type_map[work_exam_type],
                        exam_item['getScore'], is_work_score, exam_item['Title'])
            continue
        logger.info('\t1. 当前{%s}:【%s】', work_exam_type_map[work_exam_type], exam_item['Title'])
        session.cookies.update(ck2)
        work_exam_answer_map = run_get_answer(session, work_exam_type, course_open_id, exam_item['Id'])
        session.cookies.update(ck1)
        work_exam_preview = workExamPreview(session, exam_item['Id'])
        work_exam_questions = json.loads(work_exam_preview['workExamData'])['questions']
        answer_count = 0
        for i in work_exam_questions:
            answer_map = work_exam_answer_map.get(i['questionId'], None)
            if answer_map:
                if not answer_map['Answer']:
                    logger.info('\t\t\t3. 作答中... 结果: 找到答案，但答案为空！ \t类型 %s \t题目: %s',
                                question_type_type_map.get(answer_map['questionType'], '未知'), i['TitleText'])
                    continue
                if answer_map['questionType'] == 5:
                    if len(i['answerList']) > 1:
                        logger.info('\t\t\t3. 作答中... 结果: 多个填空，暂不支持，输出答案请注意提取！ \t类型 %s \t题目: %s \t答案: %s',
                                    question_type_type_map.get(answer_map['questionType'], '未知'), i['TitleText'],
                                    answer_map['Answer'])
                        continue
                    answer_res = onlineHomeworkCheckSpace(session, i['questionId'], answer_map['Answer'],
                                                          answer_map['questionType'], work_exam_preview['uniqueId'])
                elif answer_map['questionType'] == 7:
                    logger.info('\t\t\t3. 作答中... 结果: 匹配题暂不支持，输出答案请注意提取！ \t类型 %s \t题目: %s \t答案: %s',
                                question_type_type_map.get(answer_map['questionType'], '未知'), i['TitleText'],
                                answer_map['Answer'])
                    continue
                elif answer_map['questionType'] == 8:
                    logger.info('\t\t\t3. 作答中... 结果: 阅读理解题暂不支持，输出答案请注意提取！ \t类型 %s \t题目: %s \t答案: %s',
                                question_type_type_map.get(answer_map['questionType'], '未知'), i['TitleText'],
                                answer_map['Answer'])
                    continue
                else:
                    answer_res = onlineHomeworkAnswer(session, i['questionId'], answer_map['Answer'],
                                                      answer_map['questionType'], work_exam_preview['uniqueId'])
                if answer_res['code'] == 1:
                    answer_count += 1

                if answer_map['questionType'] == 1:
                    answer_map['Answer'] = chr(97 + int(answer_map['Answer'].replace(",", ""))).upper()
                if answer_map['questionType'] == 2:
                    answer_map['Answer'] = ', '.join(
                        [chr(97 + int(x)).upper() for x in answer_map['Answer'].split(",") if x != ''])
                if answer_map['questionType'] == 3:
                    answer_map['Answer'] = '正确' if answer_map['Answer'] == '1' else '错误'
                logger.info('\t\t\t3. 作答中... 结果: %s \t类型: %s \t答案: %s \t\t【题目: %s】',
                            answer_res.get('allDo', answer_res.get('msg', answer_res['code'])),
                            question_type_type_map[answer_map['questionType']],
                            answer_map['Answer'], i['TitleText'])
            else:
                logger.info('\t\t\t3. 作答中... 结果: 未找到答案！ \t类型 %s \t题目: %s',
                            question_type_type_map[i['questionType']], i['TitleText'])
        if len(work_exam_questions) == answer_count:
            work_exam_save_res = workExamSave(session, work_exam_preview['uniqueId'], exam_item['Id'], work_exam_type)
            logger.info('\t\t\t\t4. ✅✅✅ 提交作业成功... 【%s】\t 状态: %s', exam_item['Title'], work_exam_save_res['msg'])
        else:
            logger.error('\t\t\t\t4. ⛔⛔⛔ 提交作业失败... 【%s】\t 状态: 未提交！请前往网页手动提交！注意作答时长！', exam_item['Title'])


def run_get_answer(session, work_exam_type, course_open_id, work_exam_id):
    work_exam_answer_map = {}
    work_exam_list = getWorkExamList(session, course_open_id, work_exam_type)
    for work_exam in [i for i in work_exam_list['list'] if i['Id'] == work_exam_id]:
        if work_exam['stuWorkExamId'] == '':
            work_exam_preview = workExamPreview(session, work_exam['Id'])
            work_exam_save_res = workExamSave(session, work_exam_preview['uniqueId'], work_exam['Id'], work_exam_type)
            msg = work_exam_save_res['msg']
        else:
            msg = '当前作业已存在作答记录!'
        work_exam_detail = workExamDetail(session, work_exam['Id'], course_open_id)
        if not work_exam_detail['list']:
            continue
        work_exam_history = workExamHistory(session, work_exam['Id'], work_exam_detail['list'][0]['Id'], course_open_id)
        for i in json.loads(work_exam_history['workExamData'])['questions']:
            work_exam_answer_map[i['questionId']] = {
                'questionType': i['questionType'],
                'Answer': i['Answer'],
            }
        logger.info('\t\t2. 生成题库中...\t当前{%s}: 【%s】 \t%s', work_exam_type_map[work_exam_type], work_exam['Title'], msg)
    return work_exam_answer_map

# -*- coding: utf-8 -*-
# @Time : 2022/11/26 10:42
# @Author : Melon
# @Site : 
# @File : init_mooc.py
# @Software: PyCharm
import base64
import datetime
import json
import random
import re
import time

import requests
from lxml import etree, html

from MoocMain.log import Logger
from NewMoocMain.acwv2 import get_acw_sc__v2
from NewMoocMain.icve_exam_parser import parse_exam_questions

logger = Logger(__name__).get_log()

session = requests.session()

topic_content_all = None
user = None
use_ai_answer = False
use_auto_submit = False
ai_exam_handler = None  # AI答题处理器实例

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36'
}


def time_to_seconds(f):
    b = f.split(":")
    d = int(b[0])
    a = int(b[1])
    c = int(b[2])
    e = d * 3600 + a * 60 + c
    return e


def auth(session, username, password):
    data = {
        # "imgCode": start_verify(),
        "userName": username,
        "password": password,
        "type": 1
    }
    url = "https://sso.icve.com.cn/prod-api/data/userLoginV2"
    post = session.post(url=url, json=data, headers=HEADERS)
    logger.debug(post.text)
    post_json = post.json()
    if post.ok and post_json['code'] == 200:
        logger.info(f"登录成功: {username}")
        return post_json['data']['token']
    else:
        logger.info(f"登录失败: {username} msg: {post_json['msg']}")
        input('程序退出')
        exit(0)


def is_login(session):
    url = "https://mooc.icve.com.cn/learning/o/student/training/islogin.action"
    post = session.post(url=url, headers=HEADERS)
    logger.debug(post.text)
    if 'token' not in post.text:
        logger.info(f"登录信息获取失败，重试中...: {post.text}")
        return is_login(session)
    return post.text


def student_mooc_select_mooc_course(session, token, type_value):
    if type_value == 3:
        url = "https://user.icve.com.cn/learning/u/userDefinedSql/getBySqlCode.json"
        data = {
            'data': 'info',
            'page.searchItem.queryId': 'getNewStuCourseInfoById',
            'page.searchItem.keyname': '',
            'page.curPage': 1,
            'page.pageSize': 500
        }
        session_post = session.post(url=url, data=data, headers=HEADERS)
        post_json = session_post.json()
        res_list = []
        for i in post_json['page']['items']:
            for j in i['info']:
                res_list.append([j['ext1'], j['ext2'], j['ext3'], '', '', '', j['ext9'], '', '', '', '', '',
                                 '', '', '', j['ext4']])
        return {"data": res_list}

    all_data = []
    page_number = 1
    total_pages = 1

    while page_number <= total_pages:

        params = f"token={token}&siteCode=zhzj&curPage={page_number}&pageSize=6&selectType=1"
        url = "https://mooc.icve.com.cn/patch/zhzj/studentMooc_selectMoocCourse.action"
        response = session.post(url=url, params=params, headers=HEADERS)

        try:
            post_json = response.json()
        except Exception as e:
            return student_mooc_select_mooc_course(session, token, type_value)

        if not post_json or 'data' not in post_json or post_json['data'] is None:
            break

        logger.info(f"\t>>> 课程获取第 {page_number} 页完成")
        all_data.extend(post_json['data'])
        total_pages = int(post_json.get('totalPage', 1))
        page_number += 1
        time.sleep(1.5)

    return {"data": all_data}


def sign_learn(session, course_id, type_value):
    if type_value == 3:
        url = "https://user.icve.com.cn/patch/zhzj/dataCheck.action"
    else:
        url = "https://mooc.icve.com.cn/patch/zhzj/dataCheck.action"
    data = {
        'courseId': course_id,
        'checkType': 1,
        'sign': 0,
        'template': 'blue'
    }
    session.post(url, params=data, headers=HEADERS)
    result = session.post(url, params=data, headers=HEADERS)
    result_json = result.json()
    post = session.get(url=result_json['data'], headers=HEADERS)
    logger.debug(post.text)
    if 'id="parm_0"' in post.text or 'window.top.location = "/";' in post.text:
        alicfw = input('填入alicfw(查看: https://github.com/11273/mooc-work-answer/blob/main/README_ALICFW.md): ')
        session.cookies.set('alicfw', alicfw)
        return sign_learn(session, course_id, type_value)


def courseware_index(session, course_id):
    params = {
        "params.courseId": course_id,
    }
    url = "https://course.icve.com.cn/learnspace/learn/learn/templateeight/courseware_index.action"
    post = session.get(url=url, params=params, headers=HEADERS)
    # logger.debug(post.text)
    return post.text


def query_video_resources(session, item_id):
    params = {
        "params.itemId": item_id,
    }
    url = "https://course.icve.com.cn/learnspace/learn/weixinCourseware/queryVideoResources.json"
    post = session.post(url=url, params=params, headers=HEADERS)
    logger.debug(post.text)
    return post.json()


def learning_time_query_course_item_info(session, item_id):
    params = {
        "itemId": item_id,
    }
    url = "https://course.icve.com.cn/learnspace/course/study/learningTime_queryCourseItemInfo.action"
    post = session.post(url=url, params=params, headers=HEADERS)
    logger.debug(post.text)
    return post.json()


def learning_time_save_course_item_learn_record(session, course_id, item_id):
    params = {
        "courseId": course_id,
        "studyTime": 300,
        "itemId": item_id,
        "recordType": 0
    }
    url = "https://course.icve.com.cn/learnspace/course/study/learningTime_saveCourseItemLearnRecord.action"
    post = session.post(url=url, params=params, headers=HEADERS)
    logger.debug(post.text)
    return post.json()


def learning_time_save_video_learn_time_long_record(session, study_record, limit_id):
    params = {
        "studyRecord": study_record,
        "limitId": limit_id,
    }
    url = "https://course.icve.com.cn/learnspace/course/study/learningTime_saveVideoLearnDetailRecord.action"
    post = session.post(url=url, params=params, headers=HEADERS)
    # 同一个视频同时请求两次需要间隔60S
    logger.debug(post.text)
    if "请每5分钟提交一次学习数据" in post.text:
        logger.info("\t\t\t\t !!!提交过快，每5分钟提交一次学习数据，进行延迟160s，请勿操作...")
        time.sleep(160)
        return learning_time_save_video_learn_time_long_record(session, study_record, limit_id)
    return post.json()


def learning_time_save_audio_learn_detail_record(session, study_record, limit_id):
    params = {
        "studyRecord": study_record,
        "limitId": limit_id,
    }
    url = "https://course.icve.com.cn/learnspace/course/study/learningTime_saveAudioLearnDetailRecord.action"
    post = session.post(url=url, params=params, headers=HEADERS)
    logger.debug(post.text)
    return post.json()


def content_audio(session, course_id, item_id):
    params = {
        'params.courseId': course_id,
        'params.itemId': item_id,
    }
    url = "https://course.icve.com.cn/learnspace/learn/learn/templateeight/content_audio.action"
    get_html = session.get(url=url, params=params, headers=HEADERS)
    # logger.debug(post.text)
    html = etree.HTML(get_html.text)
    audio_time = html.xpath('//input[@id="audioTime"]/@value')
    return audio_time[0]


def learning_time_query_learning_time(session, course_id):
    params = {
        "courseId": course_id,
    }
    url = "https://course.icve.com.cn/learnspace/course/study/learningTime_queryLearningTime.action"
    post = session.post(url=url, params=params, headers=HEADERS)
    logger.debug(post.text)
    # print(post.text)
    return post.json()


def learning_time_save_learning_time(session, course_id, limit_id):
    params = {
        "courseId": course_id,
        "studyTime": 300,
        "limitId": limit_id,
    }
    url = "https://course.icve.com.cn/learnspace/course/study/learningTime_saveLearningTime.action"
    post = session.get(url=url, params=params, headers=HEADERS)
    logger.debug(post.text)
    if '<script>' in post.text:
        acw_sc__v2 = get_acw_sc__v2(post.text)
        session.cookies.set('acw_sc__v2', acw_sc__v2)
        logger.info("\t\t\t\t\t 自动输入成功: %s，进行延迟，请勿操作...", acw_sc__v2)
        time.sleep(60)
        return learning_time_save_learning_time(session, course_id, limit_id)
    return post.json()


def video_learn_record_detail(session, course_id, item_id, video_total_time):
    params = {
        "params.courseId": course_id,
        "params.itemId": item_id,
        "params.videoTotalTime": video_total_time,
    }
    url = "https://course.icve.com.cn/learnspace/learn/learn/templateeight/include/video_learn_record_detail.action"
    post = session.post(url=url, params=params, headers=HEADERS)
    logger.debug(post.text)
    if '<script>' in post.text:
        acw_sc__v2 = get_acw_sc__v2(post.text)
        session.cookies.set('acw_sc__v2', acw_sc__v2)
        logger.info("\t\t\t\t\t 自动输入成功: %s，进行延迟，请勿操作...", acw_sc__v2)
        time.sleep(60)
        return video_learn_record_detail(session, course_id, item_id, video_total_time)
    return post.text


def course_topic_action(session, course_id, item_id, content):
    def get__main_id__create_user_id(session):
        params = {
            'action': 'item',
            'itemId': item_id,
            'courseId': course_id,
            'ssoUserId': user
        }
        url = "https://course.icve.com.cn/taolun/learn/courseTopicAction.action"
        get_html = session.get(url=url, params=params, headers=HEADERS)
        if '<script>' in get_html.text:
            acw_sc__v2 = get_acw_sc__v2(get_html.text)
            session.cookies.set('acw_sc__v2', acw_sc__v2)
            logger.info("\t\t\t\t\t 自动输入成功: %s，进行延迟，请勿操作...", acw_sc__v2)
            time.sleep(10)
            return get__main_id__create_user_id(session)
        html = etree.HTML(get_html.text)
        current_main_id = html.xpath('//input[@id="current_main_id"]/@value')[0]
        current_user_id = html.xpath('//input[@id="current_user_id"]/@value')[0]
        check_and_save_reply = html.xpath('//a[@id="editor_area"]/@onclick')[0]
        pattern = r"'([^']*)'"
        current_reply_user_id = re.findall(pattern, check_and_save_reply)[2]
        current_reply_user_name = re.findall(pattern, check_and_save_reply)[3]
        return current_main_id, current_user_id, current_reply_user_id, current_reply_user_name

    main_id, create_user_id, reply_user_id, reply_user_name = get__main_id__create_user_id(session)
    session.get('https://course.icve.com.cn/taolun/authimg', headers=HEADERS)
    params = {
        'currentId': main_id,
        'action': 'reply',
        'parentId': main_id,
        'mainId': main_id,
        'content': f'<p>{content}</p>',
        'itemId': item_id,
        'courseId': course_id,
        'createUserId': create_user_id,
        'createUserName': user,
        'replyUserId': reply_user_id,
        'replyUserName': reply_user_name
    }
    url = "https://course.icve.com.cn/taolun/learn/courseTopicAction.action"
    post = session.post(url=url, data=params, headers=HEADERS)
    logger.debug(post.text)
    if '<script>' in post.text:
        acw_sc__v2 = get_acw_sc__v2(post.text)
        session.cookies.set('acw_sc__v2', acw_sc__v2)
        logger.info("\t\t\t\t\t 自动输入成功: %s，进行延迟，请勿操作...", acw_sc__v2)
        time.sleep(10)
        return course_topic_action(session, course_id, item_id, content)
    return post.json()

def get_exam_info_by_item_id(session, item_id):
    ''' 先获取考试id '''
    params = {
        "params.itemId": item_id,
    }
    url = "https://course.icve.com.cn/learnspace/course/exam/courseExamAction_stuIntoExamConfirm.json"
    response = session.post(url=url, params=params, headers=HEADERS)
    tree = html.fromstring(response.text)
    exam_id = tree.xpath('//input[@id="examId"]/@value')
    if exam_id:
        return exam_id[0]
    else:
        return None


def get_exam_paper_info(session, exam_record_id):
    ''' 获取考试试卷信息 '''
    params = {
        "examRecordId": exam_record_id,
    }
    url = "https://spoc-exam.icve.com.cn/exam/examflow_getExamPaperInfo.action"
    post = session.post(url=url, params=params, headers=HEADERS)
    return post.json()


def get_exam_record_info_before_exam(session, exam_id):
    ''' 获取考试信息 '''
    params = {
        "params.examId": exam_id,
    }
    url = "https://spoc-exam.icve.com.cn/student/exam/studentExam_getRecordInfoBeforeExam.action"
    post = session.post(url=url, params=params, headers=HEADERS)
    return post.json()

def get_exam_record_info(session, batchId):
    ''' 获取考试记录 '''
    params = {
        "batchId": batchId,
    }
    url = "https://spoc-exam.icve.com.cn/exam/examflow_loadExamRecordInfo.action"
    post = session.post(url=url, params=params, headers=HEADERS)
    return post.json()

def create_exam_record(session, batchId):
    ''' 创建考试记录 '''
    params = {
        "batchId": batchId,
        "params.classId": "undefined",
        "token": int(time.time() * 1000),
    }
    url = "https://spoc-exam.icve.com.cn/exam/examflow_beforeIndex.action"
    post = session.post(url=url, data=params, headers=HEADERS)
    return post.json()

def get_exam_page_html(session, exam_record_id, page=1):
    ''' 获取考试页面html '''
    params = {
        "examRecordId": exam_record_id,
        "paperPageSeq": page,
    }
    url = "https://spoc-exam.icve.com.cn/exam/examflow_getPageHtml.action"
    post = session.post(url=url, params=params, headers=HEADERS)
    if post.status_code != 200:
        logger.debug('\t\t\t\t 获取考试页面html失败: %s', post.text)
        return None
    return post.text

def get_aes(session, course_id, item_id, video_total_time, audio=False, start_time=0.0, end_time=0.0):
    def get_params(p):
        def format_str(c, a):
            l = ""
            k = len(str(c))
            if k > 0:
                if k + 2 > a:
                    return str(c)
                else:
                    g = a - k - 2
                    h = 1
                    for e in range(g):
                        h = h * 10
                    b = int(random.random() * h)
                    f = len(str(b))
                    if f < g:
                        for d in range(f, g):
                            b = b * 10
                    if k >= 10:
                        l += str(k)
                    else:
                        l += "0" + str(k)
                    l += str(c) + str(b)
            else:
                return str(c)
            return l

        res = {
            'courseId': p['courseId'],
            'itemId': p['itemId'],
            'time1': format_str(int(time.time() * 1000), 20),
            'time2': format_str(int(p['startTime']), 20),
            'time3': format_str(time_to_seconds(p['videoTotalTime']), 20),
            'time4': format_str(int(p['endTime']), 20),
            'videoIndex': p['videoIndex'] if p.get('videoIndex') else 0,
            'time5': format_str(p['studyTimeLong'], 20),
            'terminalType': p['terminalType'] if p.get('terminalType') else 0
        }
        if audio:
            res['assessment'] = "1"
            res['residenceTime'] = p['studyTimeLong'] + random.randint(10, 30)
        # logger.debug(res)
        return res

    t = time_to_seconds(video_total_time) + 0.0

    data = {
        "courseId": course_id + '___',
        "itemId": item_id,
        "videoTotalTime": video_total_time,
        "startTime": start_time,
        "endTime": end_time,
        "studyTimeLong": end_time - start_time,
    }
    learning_time_save_learning_time(session, course_id, t)
    logger.debug(data)
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad
    key = b"learnspaceaes123"
    aes = AES.new(key, AES.MODE_ECB)
    res = aes.encrypt(pad(json.dumps(get_params(data)).replace(' ', '').encode('utf-8'), AES.block_size, style='pkcs7'))
    msg = str(base64.b64encode(res), encoding="utf-8")
    # logger.debug("密文:", msg)
    return msg


def save_exam_answers(session, exam_record_id, ai_answers):
    ''' 保存考试答案 '''
    params = {
        "examRecordId": exam_record_id,
        "studentAnswers": json.dumps(ai_answers, ensure_ascii=False),
    }
    url = "https://spoc-exam.icve.com.cn/exam/examflow_sendManyAnswer.action"
    post = session.post(url=url, data=params, headers=HEADERS)
    return post.json()

def submit_exam_answers(session, exam_record_id):
    ''' 提交考试答案 '''
    params = {
        "examRecordId": exam_record_id
    }
    url = "https://spoc-exam.icve.com.cn/exam/examflow_complete.action"
    post = session.post(url=url, params=params, headers=HEADERS)
    return post.json()

def openLearnResItem(id, type, w=None, c=None):
    try:
        query_course_item_info = learning_time_query_course_item_info(session, id)
        # item_info_item_title = query_course_item_info['item']['title']
        # info_item_column_name = query_course_item_info['item']['columnName']
        # logger.info("\t\t\t\t [%s]: %s", info_item_column_name, item_info_item_title)
        course_id = query_course_item_info['item']['courseId']
        item_id = query_course_item_info['item']['id']
        # time_save_learning_time = learning_time_save_learning_time(session, course_id, item_id)
        # print(time_save_learning_time)
        if type == "video" or type == 'courseware':
            time.sleep(10)
            # 查询视频总时长
            video_resources = query_video_resources(session, id)
            data_video_time = video_resources['data']['videoTime']
            if not data_video_time:
                return
            # logger.debug(video_resources)
            undo_time = get_undo_time(session, course_id, item_id, data_video_time)
            video_learn_record_detail(session, course_id, item_id, data_video_time)
            logger.debug(video_resources)
            data_video_time_seconds = time_to_seconds(data_video_time)
            space = 120
            start_time = int(data_video_time_seconds - undo_time)
            end_time = int(start_time + space)
            for untime in range(0, int(undo_time), space):
                if end_time > data_video_time_seconds:
                    end_time = data_video_time_seconds
                    # end_time = start_time + (data_video_time_seconds % space)
                    # if end_time == start_time:
                    #     end_time = data_video_time_seconds
                learning_time_save_course_item_learn_record(session, course_id, item_id)
                aes = get_aes(session, course_id, item_id, data_video_time, start_time=start_time, end_time=end_time)
                learn_time_long_record = learning_time_save_video_learn_time_long_record(session, aes, item_id)
                logger.info("\t\t\t\t ~~~~>执行结果: %s, 视频总时长: %s, 当前进行时长: %s ~ %s",
                            learn_time_long_record['info'], data_video_time_seconds, start_time, end_time)
                start_time = start_time + space
                end_time = start_time + space
                time.sleep(space / 2)
        elif type == "topic":
            time.sleep(10)
            # 讨论
            if topic_content_all is None or topic_content_all == '' or '#' not in topic_content_all:
                logger.info("--> 没有获取到讨论回复模板，不执行讨论。")
            else:
                topic_content_list = topic_content_all.split('#')[1:]  # 获取井号分隔后的子串列表
                topic_content = random.choice(topic_content_list)  # 随机选择一个子串
                action = course_topic_action(session, course_id, item_id, topic_content)
                logger.info("\t\t\t\t ~~~~>执行结果: %s, 回复内容: %s", action['success'], topic_content)
        elif type == "audio":
            # logger.debug(video_resources)
            audio_time = content_audio(session, course_id, item_id)
            audio_time_sec = time_to_seconds(audio_time)
            start_time = 0
            end_time = audio_time_sec
            time.sleep(audio_time_sec / 1.5 + 10)
            aes = get_aes(session, course_id, item_id, audio_time, audio=True, start_time=start_time, end_time=end_time)
            learn_detail_record = learning_time_save_audio_learn_detail_record(session, aes, item_id)
            logger.info("\t\t\t\t ~~~~>执行结果: %s --- %s", learn_detail_record['data']['timeRecordResult']['msg'],
                        learn_detail_record['data']['detailRecordResult']['msg'])
        elif type == "exam":
            # 如果开启AI答题功能，则调用AI处理
            if use_ai_answer and ai_exam_handler:
                # 获取考试id
                exam_id = get_exam_info_by_item_id(session, item_id)
                time.sleep(random.randint(1, 2))
                exam_info = get_exam_record_info_before_exam(session, exam_id)
                # data.examCount
                if exam_info['data']['examCount'] > 0:
                    logger.info('\t\t\t\t\t 考试次数: %s，已考过不再考试，跳过...', exam_info['data']['examCount'])
                    return
                # 获取考试记录
                time.sleep(random.randint(1, 2))
                exam_record_info = get_exam_record_info(session, exam_id)
                exam_record_id = exam_record_info.get("data", {}).get("examRecordId")
                logger.info('\t\t\t\t\t 获取答题记录: %s...', exam_record_id)
                # 如果考试记录不存在，则创建考试记录
                if not exam_record_info.get("data") or not exam_record_id:
                    time.sleep(random.randint(1, 2))
                    # 创建考试记录
                    logger.info('\t\t\t\t\t 创建答题记录: %s', exam_id)
                    create_exam_record(session, exam_id)
                    time.sleep(random.randint(1, 2))
                    exam_record_info = get_exam_record_info(session, exam_id)
                    exam_record_id = exam_record_info.get("data").get("examRecordId")
                time.sleep(random.randint(1, 2))
                # 获取考试试卷信息
                exam_paper_info = get_exam_paper_info(session, exam_record_id)
                questionCount = exam_paper_info['data']['questionCount']
                pageCount = exam_paper_info['data']['pageCount']
                logger.info('\t\t\t\t\t 获取考试试卷信息，共 %s 个题目, 共 %s 页', questionCount, pageCount)
                if exam_paper_info['retCode'] != '0':
                    logger.error('\t\t\t\t\t 获取考试试卷信息失败: %s', exam_paper_info)
                    return
                answerCount = 0
                for page in range(1, pageCount + 1):
                    exam_page_html = get_exam_page_html(session, exam_record_id, page)
                    if not exam_page_html:
                        logger.error('\t\t\t\t\t 获取考试页面html失败: %s', exam_record_id)
                        continue
                    questions = parse_exam_questions(exam_page_html)
                    logger.info('\t\t\t\t\t 🤖 开始AI智能答题，当前处理题目数量 %s，页码: %s', len(questions), page)
                    for idx, question in enumerate(questions, 1):
                        text = question.get('text', '')
                        text = text[:50] + '...' if len(text) > 80 else text
                        logger.info('\t\t\t\t\t\t 📝 [%d/%d] %s (%s分) %s', 
                                    idx, 
                                    len(questions),
                                    question.get('type', ''), 
                                    question.get('score', '0'), 
                                    text)
                    logger.info('\t\t\t\t\t 🤖 AI思考中，请稍等，题目数量较多将耗费一定时间...')

                    logger.debug(f'\t\t\t\t\t 🤖 AI思考开始，题目: {questions}')
                    start_time = time.time()
                    ai_answers = ai_exam_handler.process_exam(questions, use_auto_submit)
                    end_time = time.time()
                    logger.debug(f'\t\t\t\t\t 🤖 AI思考完成，结果: {ai_answers}')
                    
                    if ai_answers:
                        logger.info(f'\t\t\t\t\t ✅ AI答题成功，生成{len(ai_answers)}个答案，共{questionCount}个题目，耗时: {end_time - start_time}秒')
                        # 输出AI答案结果
                        # logger.info("\t\t\t\t\t 🎯 AI答题结果: %s", json.dumps(ai_answers))
                        # 保存答案 
                        save_result = save_exam_answers(session, exam_record_id, ai_answers)
                        if save_result['retCode'] == '0':
                            answerCount += len(ai_answers)
                            logger.info(f'\t\t\t\t\t ✅ 保存 {len(ai_answers)} 个答案，结果: {save_result["data"]["saveDate"]}')
                        else:
                            logger.info(f'\t\t\t\t\t ❌ 保存答案结果，将取消自动提交: {save_result["retMsg"]}')
                    else:
                        logger.debug('\t\t\t\t\t ❌ AI答题失败，输出原始题目 %s', json.dumps(questions))
                # 如果保存答案成功，则自动提交
                if use_auto_submit:
                    logger.info(f'\t\t\t\t\t ✅ 准备自动提交答案...')
                    time.sleep(random.randint(1, 2))
                    if answerCount == questionCount:
                        submit = submit_exam_answers(session, exam_record_id)
                        logger.info(f'\t\t\t\t\t ✅ 自动提交结果: {submit["retMsg"]}')
                        time.sleep(random.randint(1, 2))
                        exam_info = get_exam_record_info_before_exam(session, exam_id)
                        if exam_info.get('data').get('lastScore'):
                            logger.info(f'\t\t\t\t\t\t ✅ 分数: {exam_info["data"]["lastScore"]}')
                            time.sleep(random.randint(1, 2))
                    else:
                        logger.info(f'\t\t\t\t\t ❌ 自动提交取消，答案数量不一致，共{questionCount}个题目，仅保存{answerCount}个答案，请手动检查后自行提交')

                    
            else:
                logger.info('\t\t\t\t\t 🤖 未开启AI答题功能，跳过...')
                
        elif type == "homework":
            logger.info("\t\t\t\t ~~~~>执行结果: 附件作业跳过。")
        else:
            time.sleep(10)
            course_item_learn_record = learning_time_save_course_item_learn_record(session, course_id, item_id)
            logger.info("\t\t\t\t ~~~~>执行结果: %s", course_item_learn_record['errorMsg'])
    except Exception as e:
        logger.exception(e)


def load_mooc(session, token):
    session.get(f"https://mooc.icve.com.cn/?token=${token}", headers=HEADERS)


def get_xpath_text(dom, xpath, index=0):
    if index == -1:
        return dom.xpath(xpath)
    return dom.xpath(xpath)[index]


def get_undo_time(session, courseId, itemId, videoTotalTime):
    url = 'https://course.icve.com.cn/learnspace/learn/learn/templateeight/include/video_learn_record_detail.action'
    params = f'params.courseId={courseId}&params.itemId={itemId}&params.videoTotalTime={videoTotalTime}'
    html_content = session.post(url, params=params, headers=HEADERS).text
    tree = html.fromstring(html_content)
    undo_divs = tree.xpath("//div[@class='trace_undo']")
    total_width = 100.0
    total_undo_width = 0.0
    for div in undo_divs:
        style = div.get("style")
        widthVal = float(style.split("width:")[1].split("%")[0])
        total_undo_width += widthVal
    remaining_percentage = total_undo_width / total_width
    time_obj = datetime.datetime.strptime(videoTotalTime, "%H:%M:%S")
    total_time_seconds = time_obj.hour * 3600 + time_obj.minute * 60 + time_obj.second
    return total_time_seconds * remaining_percentage


def run(username, password, topic_content, jump_content, type_value, is_ai_answer, is_auto_submit):
    separator = "*" * 40
    logger.info(separator)
    logger.info(f"运行信息")
    logger.info(separator)
    logger.info(f"* 登录账号: {username}")
    logger.info(f"* 评论配置: {topic_content if topic_content is not None else ''}")
    logger.info(f"* 跳过课程: {jump_content if jump_content is not None else ''}")
    logger.info(f"* 课程类型: {type_value}")
    logger.info(f"* AI智能答题: {'✅ 已启用' if is_ai_answer else '❌ 未启用'}")
    logger.info(f"* AI答题自动提交: {'✅ 已启用' if is_auto_submit else '❌ 未启用'}")
    logger.info(separator)
    logger.info("开始执行")
    logger.info(separator)

    global topic_content_all
    global user
    global use_ai_answer
    global use_auto_submit
    global ai_exam_handler
    
    use_ai_answer = is_ai_answer
    use_auto_submit = is_auto_submit
    
    jump_list = []
    if jump_content is not None and '#' in jump_content:
        jump_list = jump_content.split('#')[1:]
    topic_content_all = topic_content
    user = username
    token = auth(session, username, password)
    # 如果开启AI答题功能，初始化AI处理器
    if use_ai_answer:
        try:
            logger.info("🤖 初始化AI答题处理器...")
            from ai.ai_exam_handler import AIExamHandler
            ai_exam_handler = AIExamHandler(token, verbose=False, auto_delete_chat=True)
            
            # 检查AI处理器是否正常初始化
            if ai_exam_handler is None:
                logger.error("❌ AI答题处理器初始化返回None，将关闭AI答题功能")
                use_ai_answer = False
                ai_exam_handler = None
            else:
                ai_exam_handler.ai_handler.cleanup_all_chats()
                
                # 加载AI体
                if ai_exam_handler.load_agents():
                    logger.info("✅ AI答题处理加载成功")
                else:
                    logger.error("❌ AI答题处理器加载失败，将关闭AI答题功能")
                    use_ai_answer = False
                    ai_exam_handler = None
        except Exception as e:
            logger.info(f"❌ AI处理初始化失败: {e}")
            use_ai_answer = False
            ai_exam_handler = None
    
    load_mooc(session, token)
    logger.info(f"\t>>> 课程获取中...")
    mooc_select_mooc_course = student_mooc_select_mooc_course(session, token, type_value)
    logger.info(f"\t>>> ↓ ↓ ↓ 获取到以下课程 ↓ ↓ ↓")
    for mooc_course_item in mooc_select_mooc_course['data']:
        logger.info(f"\t\t* {mooc_course_item[0]} - {mooc_course_item[1]} - {mooc_course_item[15]}")
    logger.info(f"\t>>> 课程获取完毕! \n\n")
    if 'data' not in mooc_select_mooc_course:
        logger.info("未查询到需要学习的课程！")
        exit(0)
    for course in mooc_select_mooc_course['data']:
        course_id = course[6]
        # learning_time = learning_time_query_learning_time(session, course_id)
        logger.info("【%s】 - %s %s %s", course[0], course[1], course[2], course[3])
        if any(s in course[0] for s in jump_list):
            logger.info("\t匹配到过滤条件: %s - 跳过", course[0])
            continue
        # 进入课程
        sign_learn(session, course_id, type_value)
        html_page_course = courseware_index(session, course_id)
        # logger.debug(html_page_course)
        mooc_html = etree.HTML(html_page_course)
        # learnMenu 章根节点
        root_menu_item = get_xpath_text(mooc_html, "//div[@id='learnMenu']")
        # print(html.tostring(root_menu_item))
        # 章
        chapter = get_xpath_text(root_menu_item,
                                 "./div[contains(concat(' ', normalize-space(@class), ' '), ' s_chapter ')]", index=-1)
        section = get_xpath_text(root_menu_item, "./div[@class='s_sectionlist']", index=-1)

        # 节
        for i in range(len(chapter)):
            logger.info("\t %s", get_xpath_text(chapter[i], "@title"))
            s_section = get_xpath_text(section[i],
                                       "./div[contains(concat(' ', normalize-space(@class), ' '), ' s_section ')]",
                                       index=-1)
            s_sectionwrap = get_xpath_text(section[i], "./div[@class='s_sectionwrap']", index=-1)
            for j in range(len(s_section)):
                logger.info("\t\t %s", get_xpath_text(s_section[j], "@title"))
                s_pointwrap = get_xpath_text(s_sectionwrap[j], "./div[contains(@class, 's_pointwrap')]", index=-1)
                if len(s_pointwrap) > 0:
                    for m in range(len(s_pointwrap)):
                        s_point = get_xpath_text(s_pointwrap[m], "./div[contains(@class, 's_point')]", index=-1)
                        for k in range(len(s_point)):
                            isCompletestate = int(get_xpath_text(s_point[k], "./@completestate")) == 1
                            logger.info("\t\t\t %s",
                                        get_xpath_text(s_point[k], "./div[contains(@class, 's_pointti')]/text()"))
                            if not isCompletestate:
                                eval(get_xpath_text(s_point[k], "./@onclick").replace(";", ""))
                            else:
                                logger.info("\t\t\t\t ~~~~>执行结果: %s", "已完成")

                else:
                    s_point = get_xpath_text(s_sectionwrap[j], "./div[contains(@class, 's_point')]", index=-1)
                    for k in range(len(s_point)):
                        isCompletestate = int(get_xpath_text(s_point[k], "./@completestate")) == 1
                        logger.info("\t\t\t %s",
                                    get_xpath_text(s_point[k], "./div[contains(@class, 's_pointti')]/text()"))
                        if not isCompletestate:
                            eval(get_xpath_text(s_point[k], "./@onclick").replace(";", ""))
                        else:
                            logger.info("\t\t\t\t ~~~~>执行结果: %s", "已完成")

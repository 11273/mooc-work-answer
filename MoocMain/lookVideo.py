# -*- coding: utf-8 -*-
# @Time : 2020/12/26 15:17
# @Author : Melon
# @Site : 
# @File : lookVideo.py
# @Software: PyCharm
import random
import time

import requests

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36',
}


def getCourseOpenList(cookies):
    time.sleep(0.25)
    url = "https://mooc.icve.com.cn/portal/Course/getMyCourse?isFinished=0&pageSize=5000"
    result = requests.post(url=url, headers=headers, cookies=cookies).json()
    return result['list']


def getProcessList(cookies, course_id):
    time.sleep(0.25)
    url = "https://mooc.icve.com.cn/study/learn/getProcessList"
    result = requests.post(url=url, data={'courseOpenId': course_id}, headers=headers, cookies=cookies).json()
    return result['proces']['moduleList']


def getTopicByModuleId(cookies, course_id, module_id):
    time.sleep(0.25)
    url = "https://mooc.icve.com.cn/study/learn/getTopicByModuleId"
    data = {
        'courseOpenId': course_id,
        'moduleId': module_id
    }
    result = requests.post(url=url, data=data, headers=headers, cookies=cookies).json()
    return result['topicList']


def getCellByTopicId(cookies, course_id, topic_id):
    time.sleep(0.25)
    url = "https://mooc.icve.com.cn/study/learn/getCellByTopicId"
    data = {
        'courseOpenId': course_id,
        'topicId': topic_id
    }
    result = requests.post(url=url, data=data, headers=headers, cookies=cookies).json()
    return result['cellList']


def viewDirectory(cookies, course_open_id, cell_id):
    time.sleep(0.25)
    url = "https://mooc.icve.com.cn/study/learn/viewDirectory"
    data = {
        'courseOpenId': course_open_id,
        'cellId': cell_id
    }
    result = requests.post(url=url, data=data, headers=headers, cookies=cookies).json()
    return result['courseCell']


def statStuProcessCellLogAndTimeLong(cookies, course_open_id, cell_id, video_time_total_long):
    time.sleep(1.25)
    url = "https://mooc.icve.com.cn/study/learn/statStuProcessCellLogAndTimeLong"
    if video_time_total_long != 0:
        video_time_total_long += random.randint(20, 100)
    data = {
        'courseOpenId': course_open_id,
        'cellId': cell_id,
        'auvideoLength': video_time_total_long,
        'videoTimeTotalLong': video_time_total_long
    }
    result = requests.post(url=url, data=data, headers=headers, cookies=cookies).json()
    return result


def statStuProcess(cookies, info, category_name, cell_name):
    course_open_id = info['CourseOpenId']
    view_id = info['Id']
    video_time_long = info['VideoTimeLong']
    result_is_ok = statStuProcessCellLogAndTimeLong(cookies, course_open_id, view_id, video_time_long)
    if result_is_ok['code'] == 1 and result_is_ok['isStudy'] is True:
        print("\t\t\t\t~~~~>刷课成功~", "\t\t类型：" + category_name, "\t\t\t" + cell_name)
    else:
        print("\t\t\t\t~~~~>ERROR~", "\t\t类型：" + category_name, "\t\t\t" + cell_name)


def start(cookies, is_continue_work):
    course_list = getCourseOpenList(cookies)
    print("*" * 25, '待刷的课程(需要跳过的课程请参考此处课程名)', "*" * 25)
    for course_item in course_list:
        if course_item['courseName'] in is_continue_work:
            print('* 【pass】  ', '总进度:', str(course_item['process']) + '%\t\t课程名:', course_item['courseName'])
        else:
            print('*\t\t\t', '总进度:', str(course_item['process']) + '%\t\t课程名:', course_item['courseName'])
    print("*" * 90, '\n')
    for i in range(3, 0, -1):
        print("等待刷课(秒):", i)
        time.sleep(1)
    for course_item in course_list:
        if course_item['courseName'] in is_continue_work:
            continue
        print("\n* 进入课程：【%s】" % course_item['courseName'])
        module_list1 = getProcessList(cookies, course_item['courseOpenId'])
        for module_list1_i in module_list1:
            if module_list1_i['percent'] == 100:
                print("\t~跳过(进度100%)~: ", module_list1_i['name'])
                continue
            print("\t" + module_list1_i['name'])
            module_list2 = getTopicByModuleId(cookies, course_item['courseOpenId'], module_list1_i['id'])
            for module_list2_i in module_list2:
                if module_list2_i['studyStatus'] == 1:
                    print("\t\t~跳过已刷章节~: ", module_list2_i['name'])
                    continue
                print("\t\t" + module_list2_i['name'])
                module_list3 = getCellByTopicId(cookies, course_item['courseOpenId'], module_list2_i['id'])
                for module_list3_i in module_list3:
                    if not len(module_list3_i['childNodeList']):
                        category_name = module_list3_i['categoryName']
                        cell_name = module_list3_i['cellName']
                        # 如果课程完成-不刷课
                        if module_list3_i['isStudyFinish'] is True:
                            print("\t\t\t\t~~~~>课程已完成，跳过~\t\t类型：" + category_name + "\t\t名称：" + cell_name)
                            continue
                        info = viewDirectory(cookies, module_list3_i['courseOpenId'], module_list3_i['Id'])
                        statStuProcess(cookies, info, category_name, cell_name)
                    else:
                        for module_list4_i in module_list3_i['childNodeList']:
                            category_name = module_list4_i['categoryName']
                            cell_name = module_list4_i['cellName']
                            if module_list4_i['isStudyFinish'] is True:
                                print("\t\t\t\t~~~~>课程已完成，跳过~\t\t类型：" + category_name + "\t\t名称：" + cell_name)
                                continue
                            info = viewDirectory(cookies, module_list4_i['courseOpenId'], module_list4_i['Id'])
                            statStuProcess(cookies, info, category_name, cell_name)
    course_list = getCourseOpenList(cookies)
    print("*" * 40, '刷课已完成', "*" * 40)
    for course_item in course_list:
        print('*\t', '总进度:', str(course_item['process']) + '%\t\t课程名:', course_item['courseName'])
    print("*" * 90, '\n')

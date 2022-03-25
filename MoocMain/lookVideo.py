# -*- coding: utf-8 -*-
# @Time : 2020/12/26 15:17
# @Author : Melon
# @Site : 
# @File : lookVideo.py
# @Software: PyCharm
import json
import random
import time
import traceback

import requests

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36',
}


# 1.获取所有课程，拿到id-------->
def getCourseOpenList(cookies):
    """
    获取所有课程
    :param cookies: cookies
    :return:
    """
    url = "https://mooc.icve.com.cn/portal/Course/getMyCourse?isFinished=0"
    result = json.loads(requests.post(url=url, headers=headers, cookies=cookies).text)
    return result['list']


# 2.得到一级目录-------->
def getProcessList(cookies, courseId):
    """
    得到一级目录
    :param cookies: cookies
    :param courseId: gtjkawksy5jf7raso8gdq
    :return:
    """
    url = "https://mooc.icve.com.cn/study/learn/getProcessList"
    result = json.loads(requests.post(url=url, data={'courseOpenId': courseId}, headers=headers, cookies=cookies).text)
    return result['proces']['moduleList']


# 3.得到二级目录-------->
def getTopicByModuleId(cookies, courseId, moduleId):
    """
    得到二级目录
    :param cookies: cookies
    :param courseId: courseOpenId
    :param moduleId: moduleId
    :return:
    """
    url = "https://mooc.icve.com.cn/study/learn/getTopicByModuleId"
    data = {
        'courseOpenId': courseId,
        'moduleId': moduleId
    }
    result = json.loads(requests.post(url=url, data=data, headers=headers, cookies=cookies).text)
    return result['topicList']


# 4.获得三级目录（详细信息）--------->
def getCellByTopicId(cookies, courseId, topicId):
    """
    获得三级目录（详细信息）
    :param cookies: cookies
    :param courseId: courseOpenId
    :param topicId: topicId
    :return:
    """
    url = "https://mooc.icve.com.cn/study/learn/getCellByTopicId"
    data = {
        'courseOpenId': courseId,
        'topicId': topicId
    }
    result = json.loads(requests.post(url=url, data=data, headers=headers, cookies=cookies).text)
    return result['cellList']


# 5.拿到学习时长等信息---------->
def viewDirectory(cookies, courseOpenId, cellId):
    """
    拿到学习时长等信息
    :param cookies: cookies
    :param courseOpenId: courseOpenId
    :param cellId: cellId
    :return:
    """
    time.sleep(1)
    url = "https://mooc.icve.com.cn/study/learn/viewDirectory"
    data = {
        'courseOpenId': courseOpenId,
        'cellId': cellId
    }
    result = requests.post(url=url, data=data, headers=headers, cookies=cookies)
    result = json.loads(result.text)
    return result['courseCell']


# 6.开始刷课--------->
def statStuProcessCellLogAndTimeLong(cookies, courseOpenId, cellId, videoTimeTotalLong):
    """
    开始刷课
    :param cookies: cookies
    :param courseOpenId: courseOpenId
    :param cellId: cellId
    :param videoTimeTotalLong: videoTimeTotalLong
    :return:
    """
    time.sleep(1.5)
    url = "https://mooc.icve.com.cn/study/learn/statStuProcessCellLogAndTimeLong"
    if videoTimeTotalLong != 0:
        videoTimeTotalLong += random.randint(20, 100)
    data = {
        'courseOpenId': courseOpenId,
        'cellId': cellId,
        'auvideoLength': videoTimeTotalLong,
        'videoTimeTotalLong': videoTimeTotalLong
    }
    result = json.loads(requests.post(url=url, data=data, headers=headers, cookies=cookies).text)
    return result


def start(cookies):
    try:
        course = getCourseOpenList(cookies)
    except Exception as e:
        traceback.print_exc()
        print("异常course = getCourseOpenList(cookies)，3S后重试")
        time.sleep(3)
        course = getCourseOpenList(cookies)
        pass
    for i in course:
        print("可刷 的课程有：" + i['courseName'])
    print("------------------------------------------------------------3S后将开始刷课")
    time.sleep(3)
    for i in course:
        # if i['courseName'] != "妇科护理":
        #     continue
        print("进入课程：" + i['courseName'])
        time.sleep(1)
        # 一级目录
        try:
            moduleList1 = getProcessList(cookies=cookies, courseId=i[
                'courseOpenId'])
        except Exception as e:
            traceback.print_exc()
            print("异常moduleList1 = getProcessList(cookies=cookies, courseId=i['courseOpenId'])，3S后重试")
            time.sleep(3)
            moduleList1 = getProcessList(cookies=cookies, courseId=i['courseOpenId'])
            pass
        for j in moduleList1:
            time.sleep(0.25)
            if j['percent'] == 100:
                print("\t跳过课程: " + j['name'] + '课程已刷进度 100%')
                continue
            print("\t" + j['name'])
            # 二级目录
            try:
                moduleList2 = getTopicByModuleId(cookies=cookies, courseId=i['courseOpenId'], moduleId=j['id'])
            except Exception as e:
                traceback.print_exc()
                print(
                    "异常moduleList2 = getTopicByModuleId(cookies=cookies, courseId=i['courseOpenId'], moduleId=j['id'])，3S后重试")
                time.sleep(3)
                moduleList2 = getTopicByModuleId(cookies=cookies, courseId=i['courseOpenId'], moduleId=j['id'])
                pass
            for k in moduleList2:
                time.sleep(0.25)
                if k['studyStatus'] == 1:
                    print("\t\t跳过已刷章节: " + k['name'])
                    continue
                print("\t\t" + k['name'])
                # 三级目录
                try:
                    moduleList3 = getCellByTopicId(cookies=cookies, courseId=i['courseOpenId'], topicId=k['id'])
                except Exception as e:
                    traceback.print_exc()
                    print(
                        "异常moduleList3 = getCellByTopicId(cookies=cookies, courseId=i['courseOpenId'], topicId=k['id'])，3S后重试")
                    time.sleep(3)
                    moduleList3 = getCellByTopicId(cookies=cookies, courseId=i['courseOpenId'], topicId=k['id'])
                    pass
                for m in moduleList3:
                    time.sleep(0.25)
                    print("\t\t\t" + m['cellName'])
                    # 如果只有三级目录
                    if not len(m['childNodeList']):
                        # =================================================================================================================================
                        # 如果课程完成-不刷课
                        if m['isStudyFinish'] is True:
                            print(
                                "\t\t\t\t" + "\t类型：" + m['categoryName'] + "\t\t------课程完成，不刷课-------\t\t" + m[
                                    'cellName'])
                            continue
                        # 拿课程信息
                        try:
                            info = viewDirectory(cookies=cookies, courseOpenId=m['courseOpenId'], cellId=m['Id'])
                        except:
                            traceback.print_exc()
                            print(
                                "异常info = viewDirectory(cookies=cookies, courseOpenId=m['courseOpenId'], cellId=m['Id'])，3S后重试")
                            time.sleep(3)
                            info = viewDirectory(cookies=cookies, courseOpenId=m['courseOpenId'], cellId=m['Id'])
                            pass
                        # 将信息拿去刷课
                        if not m['categoryName'] == "视频" and not m['categoryName'] == "音频":
                            # 如果不是视频或者音频
                            isOK = statStuProcessCellLogAndTimeLong(cookies=cookies, courseOpenId=info['CourseOpenId'],
                                                                    cellId=info['Id'],
                                                                    videoTimeTotalLong=0)
                        # 四级目录(最终)
                        else:
                            # 是视频或者音频
                            isOK = statStuProcessCellLogAndTimeLong(cookies=cookies, courseOpenId=info['CourseOpenId'],
                                                                    cellId=info['Id'],
                                                                    videoTimeTotalLong=info['VideoTimeLong'])
                        if isOK['code'] == 1 and isOK['isStudy'] is True:
                            print("\t\t\t\t" + "\t类型：" + m['categoryName'] + "\t\t-----刷课OK----\t\t" + m['cellName'])
                        else:
                            print("\t\t\t\t" + "\t类型：" + m['categoryName'] + "\t\t-----ERROR----\t\t" + m['cellName'])
                    else:
                        # =================================================================================================================================
                        for n in m['childNodeList']:
                            time.sleep(0.5)
                            # 如果课程完成-不刷课
                            if n['isStudyFinish'] is True:
                                print("\t\t\t\t" + "\t类型：" + n[
                                    'categoryName'] + "\t\t------课程完成，不刷课-------\t\t" + n['cellName'])
                                continue
                            # 拿课程信息

                            try:
                                info = viewDirectory(cookies=cookies, courseOpenId=n['courseOpenId'], cellId=n['Id'])
                            except:
                                traceback.print_exc()
                                print(
                                    "异常info = viewDirectory(cookies=cookies, courseOpenId=m['courseOpenId'], cellId=m['Id'])，3S后重试")
                                time.sleep(3)
                                info = viewDirectory(cookies=cookies, courseOpenId=n['courseOpenId'], cellId=n['Id'])
                                pass
                            # 将信息拿去刷课
                            if not n['categoryName'] == "视频" and not n['categoryName'] == "音频":
                                # 如果不是视频或者音频
                                isOK = statStuProcessCellLogAndTimeLong(cookies=cookies,
                                                                        courseOpenId=info['CourseOpenId'],
                                                                        cellId=info['Id'],
                                                                        videoTimeTotalLong=0)
                            else:
                                # 是视频或者音频
                                isOK = statStuProcessCellLogAndTimeLong(cookies=cookies,
                                                                        courseOpenId=info['CourseOpenId'],
                                                                        cellId=info['Id'],
                                                                        videoTimeTotalLong=info['VideoTimeLong'])
                            if isOK['code'] == 1 and isOK['isStudy'] is True:
                                print(
                                    "\t\t\t\t" + "\t类型：" + n['categoryName'] + "\t\t-----刷课OK----\t\t" + n['cellName'])
                            else:
                                print(
                                    "\t\t\t\t" + "\t类型：" + n['categoryName'] + "\t\t-----ERROR----\t\t" + n['cellName'])

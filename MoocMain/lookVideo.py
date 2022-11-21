# -*- coding: utf-8 -*-
# @Time : 2020/12/26 15:17
# @Author : Melon
# @Site : 
# @File : lookVideo.py
# @Software: PyCharm
import asyncio
import random
import time

import aiohttp

from MoocMain.log import Logger

logger = Logger(__name__).get_log()
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36',
}


async def getCourseOpenList(session):
    await asyncio.sleep(0.25)
    url = "https://mooc.icve.com.cn/portal/Course/getMyCourse?isFinished=0&pageSize=5000"
    async with session.post(url=url, headers=headers) as resp:
        data = await resp.json(content_type=None)
        return data['list']


async def getProcessList(session, course_id):
    await asyncio.sleep(0.25)
    url = "https://mooc.icve.com.cn/study/learn/getProcessList"
    async with session.post(url=url, data={'courseOpenId': course_id}, headers=headers) as resp:
        data = await resp.json(content_type=None)
        return data['proces']['moduleList']


async def getTopicByModuleId(session, course_id, module_id):
    await asyncio.sleep(0.25)
    url = "https://mooc.icve.com.cn/study/learn/getTopicByModuleId"
    data = {
        'courseOpenId': course_id,
        'moduleId': module_id
    }
    async with session.post(url=url, data=data, headers=headers) as resp:
        data = await resp.json(content_type=None)
        return data['topicList']


async def getCellByTopicId(session, course_id, topic_id):
    await asyncio.sleep(0.25)
    url = "https://mooc.icve.com.cn/study/learn/getCellByTopicId"
    data = {
        'courseOpenId': course_id,
        'topicId': topic_id
    }
    async with session.post(url=url, data=data, headers=headers) as resp:
        data = await resp.json(content_type=None)
        return data['cellList']


async def viewDirectory(session, course_open_id, cell_id):
    # await asyncio.sleep(0.1)
    url = "https://mooc.icve.com.cn/study/learn/viewDirectory"
    data = {
        'courseOpenId': course_open_id,
        'cellId': cell_id
    }
    async with session.post(url=url, data=data, headers=headers) as resp:
        data = await resp.json(content_type=None)
        return data['courseCell']


async def statStuProcessCellLogAndTimeLong(session, course_open_id, cell_id, video_time_total_long):
    await asyncio.sleep(0.25)
    url = "https://mooc.icve.com.cn/study/learn/statStuProcessCellLogAndTimeLong"
    if video_time_total_long != 0:
        video_time_total_long += random.randint(20, 100)
    data = {
        'courseOpenId': course_open_id,
        'cellId': cell_id,
        'auvideoLength': video_time_total_long,
        'videoTimeTotalLong': video_time_total_long
    }
    async with session.post(url=url, data=data, headers=headers) as resp:
        data = await resp.json(content_type=None)
        return data


async def statStuProcess(session, info, category_name, cell_name):
    course_open_id = info['CourseOpenId']
    view_id = info['Id']
    video_time_long = info['VideoTimeLong']
    result_is_ok = await statStuProcessCellLogAndTimeLong(session, course_open_id, view_id, video_time_long)
    if result_is_ok['code'] == 1 and result_is_ok['isStudy'] is True:
        return "\t\t\t\t~~~~>刷课成功~" + "\t\t类型：" + category_name + "\t\t\t" + cell_name
    else:
        return "\t\t\t\t~~~~>ERROR~" + "\t\t类型：" + category_name + "\t\t\t" + cell_name


async def start(session, is_continue_work):
    err_n = 5
    while err_n > 0:
        try:
            async with aiohttp.ClientSession(cookies=session.cookies.get_dict()) as session:
                course_list = await getCourseOpenList(session)
                for i in range(3, 0, -1):
                    logger.info("等待刷课(秒): %s", i)
                    await asyncio.sleep(1)
                for course_item in course_list:
                    if course_item['courseName'] in is_continue_work:
                        continue
                    logger.info("\n* 进入课程：【%s】", course_item['courseName'])
                    module_list1 = await getProcessList(session, course_item['courseOpenId'])
                    for module_list1_i in module_list1:
                        if module_list1_i['percent'] == 100:
                            logger.info("\t~跳过(进度100%%)~: %s", module_list1_i['name'])
                            continue
                        logger.info("\t %s", module_list1_i['name'])
                        module_list2 = await getTopicByModuleId(session, course_item['courseOpenId'], module_list1_i['id'])

                        for module_list2_i in module_list2:
                            if module_list2_i['studyStatus'] == 1:
                                logger.info("\t\t~跳过已刷章节~: %s", module_list2_i['name'])
                                continue
                            logger.info("\t\t %s", module_list2_i['name'])
                            module_list3 = await getCellByTopicId(session, course_item['courseOpenId'], module_list2_i['id'])
                            tasks = []
                            logger.info("\t\t\t [🎉🎉🎉 正在批量刷小节: 【%s】, 检测中, 等待任务创建...]", module_list2_i['name'])
                            for module_list3_i in module_list3:
                                if not len(module_list3_i['childNodeList']):
                                    category_name = module_list3_i['categoryName']
                                    cell_name = module_list3_i['cellName']
                                    # 如果课程完成-不刷课
                                    if module_list3_i['isStudyFinish'] is True:
                                        logger.info("\t\t\t\t~~~~>课程已完成，跳过~\t\t类型：%s\t\t名称：%s", category_name, cell_name)
                                        continue
                                    info = await viewDirectory(session, module_list3_i['courseOpenId'], module_list3_i['Id'])
                                    tasks.append(statStuProcess(session, info, category_name, cell_name))
                                else:
                                    for module_list4_i in module_list3_i['childNodeList']:
                                        category_name = module_list4_i['categoryName']
                                        cell_name = module_list4_i['cellName']
                                        if module_list4_i['isStudyFinish'] is True:
                                            logger.info("\t\t\t\t~~~~>课程已完成，跳过~\t\t类型：%s\t\t名称：%s", category_name, cell_name)
                                            continue
                                        info = await viewDirectory(session, module_list4_i['courseOpenId'], module_list4_i['Id'])
                                        tasks.append(statStuProcess(session, info, category_name, cell_name))
                            logger.info("\t\t\t ["
                                        "🚀🚀🚀 批量刷小节: 【%s】, 检测完成, 执行中...]", module_list2_i['name'])
                            result = await asyncio.gather(*tasks)
                            for i in result:
                                logger.info(i)
                            logger.info("\t\t\t [🚩🚩🚩 批量刷小节: 【%s】, 执行完成]", module_list2_i['name'])
                course_list = await getCourseOpenList(session)
                logger.info('%s 刷课已完成 %s', "*" * 40, "*" * 40)
                for course_item in course_list:
                    logger.info('*\t总进度: %s %%\t\t课程名: %s', str(course_item['process']), course_item['courseName'])
                logger.info("*" * 90)
                break
        except Exception as e:
            err_n -= 1
            sleep_int = random.randint(10, 30)
            logger.error('程序出现异常，延时 %ss 后重试，剩余重试次数: %s，等待重试 %s', sleep_int, err_n, e)
            time.sleep(sleep_int)
            continue


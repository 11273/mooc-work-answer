# -*- coding: utf-8 -*-
# @Time : 2021/11/2 16:41
# @Author : Melon
# @Site : 
# @Note : 
# @File : StartWork.py
# @Software: PyCharm
import textwrap
import time

import MoocMain.initMooc as MoocInit
import NewMoocMain.init_mooc as NewMoocInit
from MoocMain.log import Logger
from ZYKMoocMain.main import ZYKMoocHandler
from update import check_for_updates

logger = Logger(__name__).get_log()

APP_VERSION = 'dev' if 'TAG_NAME' in '${TAG_NAME}' else '${TAG_NAME}'

border = '*' * 80
logger.info(border)
logger.info(f'应用程序启动，版本: {APP_VERSION}')
logger.info('开源支持: https://github.com/11273/mooc-work-answer')
logger.info(border)

# ***************************************** 检查更新 ***************************************

check_for_updates(APP_VERSION)

# ****************************************** 配置 ******************************************

# 小号退出所有课程
is_withdraw_course = None

# 做作业
is_work_exam_type0 = None

# 做测验
is_work_exam_type1 = None

# 考试
is_work_exam_type2 = None

# 大于90分的不进行再次作答
is_work_score = None


# ****************************************** 结束 ******************************************

def run_model(
        customize=False,
        i_is_look_video=True,
        i_is_withdraw_course=False,
        i_is_work_exam_type0=True,
        i_is_work_exam_type1=True,
        i_is_work_exam_type2=True,
        i_is_work_score=90):
    global is_look_video
    global is_withdraw_course
    global is_work_exam_type0
    global is_work_exam_type1
    global is_work_exam_type2
    global is_work_score

    is_look_video = (True if input('* 大号开启刷课 [y/n]: ') == 'y' else False) if customize else i_is_look_video
    is_withdraw_course = (
        True if input('* 小号退所有课 [y/n]: ') == 'y' else False) if customize else i_is_withdraw_course
    is_work_exam_type0 = (True if input('* 做作业 [y/n]: ') == 'y' else False) if customize else i_is_work_exam_type0
    is_work_exam_type1 = (True if input('* 做测验 [y/n]: ') == 'y' else False) if customize else i_is_work_exam_type1
    is_work_exam_type2 = (True if input('* 做考试 [y/n]: ') == 'y' else False) if customize else i_is_work_exam_type2
    is_work_score = (
        int(input('* 大于指定分数不再次作答  (默认90 输入数字): ') or 90)) if customize else i_is_work_score


if __name__ == '__main__':
    time.sleep(1)
    print('\n')
    # 账号1(大号)
    old = int(input('新旧版账号密码部分不互通: 1.旧版 or 2.新版 or 3.课堂版 or 4.资源库: ')) or 1
    try:
        if old == 1:
            logger.info('\n')
            logger.info('%s【运行须知】%s', '*' * 50, '*' * 50)
            logger.info('\n===> 运行模式选择(序号)：')
            logger.info('*推荐(默认) \t【1】通用模式(大号：刷课+作业+测验+考试，小号：不退课)')
            logger.info('\t\t\t【2】严格模式(大号：刷课+作业+测验+考试，小号：退课)')
            logger.info('\t\t\t【3】答题模式(大号：作业+测验+考试，小号：不退课)')
            logger.info('\t\t\t【4】刷课模式(大号：刷课，小号：不退课)')
            logger.info('\t\t\t【5】自定义')
            logger.info('*' * 110)
            time.sleep(0.5)
            model = int(input("请输入运行模式: ")) or 1
            # 账号1(大号)
            username1 = input('请输入大号账号: ')  # 账号
            password1 = input('请输入大号密码: ')  # 密码
            # 账号2(小号)
            username2 = input('(可选-答题需要)请输入小号账号: ')  # 账号
            password2 = input('(可选-答题需要)请输入小号密码: ')  # 密码
            if model == 2:
                logger.info('\n当前-->【2】严格模式')
                run_model(i_is_withdraw_course=True)
            elif model == 3:
                logger.info('\n当前-->【3】答题模式')
                run_model(i_is_look_video=False)
            elif model == 4:
                logger.info('\n当前-->【4】刷课模式')
                run_model(i_is_work_exam_type0=False, i_is_work_exam_type1=False, i_is_work_exam_type2=False)
            elif model == 5:
                logger.info('\n当前-->【5】自定义')
                run_model(customize=True)
            else:
                logger.info('\n当前-->【1】通用模式')
                run_model()
            MoocInit.run(
                username1=username1,
                password1=password1,
                username2=username2,
                password2=password2,
                is_withdraw_course=is_withdraw_course,
                is_work_exam_type0=is_work_exam_type0,
                is_work_exam_type1=is_work_exam_type1,
                is_work_exam_type2=is_work_exam_type2,
                is_work_score=is_work_score,
            )
        elif old == 4:
            username = input('请输入账号: ')  # 账号
            password = input('请输入密码: ')  # 密码
            jump = int(input('是否有需要跳过的课程 1.是 or 2.否: ') or 2)
            jump_content = None
            if jump == 1:
                print(
                    '\t请输入跳过课程名(模糊匹配), 例如\n\t\t输入多个文本随机井号后面的: #设计#思想道德#技术\n\t\t输入单个将固定跳过一个课程: #思想')
                jump_content = input('请输入需要跳过的课程关键字(例：#电商#商务英语): ') or ''
            ZYKMoocHandler(username, password, jump_content)
        else:
            # 账号1(大号)
            username1 = input('请输入账号: ')  # 账号
            password1 = input('请输入密码: ')  # 密码
            topic = int(input('是否自动讨论回复 1.是 or 2.否: ') or 2)
            topic_content = None
            if topic == 1:
                print(
                    '\t请输入讨论回复内容,回复的不包括井号(默认随机), 例如\n\t\t输入多个文本随机井号后面的: #好#加油#积极响应\n\t\t输入单个将固定回复统一内容: #好')
                topic_content = input('请输入回车默认(#好#加油#积极响应): ') or '#好#加油#积极响应'
            jump = int(input('是否有需要跳过的课程 1.是 or 2.否: ') or 2)
            jump_content = None
            if jump == 1:
                print(
                    '\t请输入跳过课程名(模糊匹配), 例如\n\t\t输入多个文本随机井号后面的: #设计#思想道德#技术\n\t\t输入单个将固定跳过一个课程: #思想')
                jump_content = input('请输入需要跳过的课程关键字(#电商): ') or ''
            NewMoocInit.run(username=username1, password=password1, topic_content=topic_content,
                            jump_content=jump_content, type_value=old)
        logger.info("┃✅本次程序运行完成，正常结束 ✅┃")
    except KeyboardInterrupt:
        logger.info(f"┃❌ 用户手动终止程序，正在安全退出...┃")
    except Exception as e:
        logger.exception(f"┃⛔ 发生错误，请检查输入或提交 Github 反馈 ⛔┃ {e} ")
    finally:
        # 包裹日志信息
        message = textwrap.dedent("""
            ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
            ┃ ✅ 程序结束，如遇错误请重新运行                   
            ┃ 🔄 多次重复错误请提交 Github 反馈！               
            ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
        """)
        logger.info(message)
        input()

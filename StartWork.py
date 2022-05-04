# -*- coding: utf-8 -*-
# @Time : 2021/11/2 16:41
# @Author : Melon
# @Site : 
# @Note : 
# @File : StartWork.py
# @Software: PyCharm

import MoocMain.initMooc as mooc_init

print('=' * 106, '\n' + '=' * 20, '程序运行中!开源支持 By https://github.com/11273/mooc-work-answer', '=' * 20, '\n' + '=' * 106, '\n')

# ****************************************** 配置 ******************************************
# 账号1(大号)
username1 = input('请输入大号账号: ')  # 账号
password1 = input('请输入大号密码: ')  # 密码
# 账号2(小号)
username2 = input('(可选)请输入小号账号: ')  # 账号
password2 = input('(可选)请输入小号密码: ')  # 密码

# 账号1(大号)刷课
is_look_video = True if input('大号开启刷课 默认n [y/n]: ') == 'y' else False

# 小号退出所有课程
is_withdraw_course = True if input('小号退出所有课程 默认n [y/n]: ') == 'y' else False

# 做作业
is_work_exam_type0 = True if input('做作业 默认n [y/n]: ') == 'y' else False

# 做测验
is_work_exam_type1 = True if input('做测验 默认n [y/n]: ') == 'y' else False

# 考试
is_work_exam_type2 = True if input('做考试 默认n [y/n]: ') == 'y' else False

# 大于90分的不进行再次作答
is_work_score = int(input('大于指定分数的不进行再次作答  (默认90 输入数字): ') or 90)

# 需要跳过的课程，填写方式例： ['大学语文', '高等数学']
is_continue_work = []

# ****************************************** 结束 ******************************************

if __name__ == '__main__':
    mooc_init.run(
        username1=username1,
        password1=password1,
        username2=username2,
        password2=password2,
        is_look_video=is_look_video,
        is_withdraw_course=is_withdraw_course,
        is_work_exam_type0=is_work_exam_type0,
        is_work_exam_type1=is_work_exam_type1,
        is_work_exam_type2=is_work_exam_type2,
        is_work_score=is_work_score,
        is_continue_work=is_continue_work,
    )

# -*- coding: utf-8 -*-
# @Time : 2021/11/2 16:41
# @Author : Melon
# @Site : 
# @Note : 
# @File : StartWork.py
# @Software: PyCharm

import MoocMain.initMooc as mooc_init

# ****************************************** 配置 ******************************************
# 账号1(大号)
username1 = ""  # 账号
password1 = ""  # 密码
# 账号2(小号)
username2 = ""  # 账号
password2 = ""  # 密码

# 账号1(大号)刷课
is_look_video = True

# 小号退出所有课程
is_withdraw_course = False

# 做作业
is_work_exam_type0 = True

# 做测验
is_work_exam_type1 = True

# 考试
is_work_exam_type2 = True

# 大于90分的不进行再次作答
is_work_score = 90

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

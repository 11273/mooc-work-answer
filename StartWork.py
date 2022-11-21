# -*- coding: utf-8 -*-
# @Time : 2021/11/2 16:41
# @Author : Melon
# @Site : 
# @Note : 
# @File : StartWork.py
# @Software: PyCharm
import time

import MoocMain.initMooc as MoocInit
from MoocMain.log import Logger

logger = Logger(__name__).get_log()

logger.info('=' * 110)
logger.info('%s【v2.0.1 】 程序运行!开源支持 By https://github.com/11273/mooc-work-answer %s', '=' * 20, '=' * 20)
logger.info('=' * 110)

# ****************************************** 结束 ******************************************

if __name__ == '__main__':
    time.sleep(1)
    print('\n')
    # 账号1(大号)
    username1 = input('请输入账号: ')  # 账号
    password1 = input('请输入密码: ')  # 密码
    MoocInit.run(username1=username1, password1=password1)

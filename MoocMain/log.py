# -*- coding: utf-8 -*-
# @Time : 2022/5/23 10:44
# @Author : Melon
# @Site : 
# @Note : 
# @File : log.py
# @Software: PyCharm
import datetime
import logging
from logging.handlers import TimedRotatingFileHandler


class Logger:
    def __init__(self, name):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level=logging.DEBUG)

        # 控制台
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        self.logger.addHandler(ch)
        # 文件
        formatter = logging.Formatter(
            '[%(asctime)s][%(thread)d][%(filename)s][line: %(lineno)d][%(levelname)s] :: %(message)s')
        file_name = './mooc-work-answer-log_{t}.log'.format(t=datetime.datetime.now().strftime('%Y-%m-%d'))
        fh = logging.FileHandler(file_name, encoding='utf-8')
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)

    def get_log(self):
        return self.logger

# -*- coding: utf-8 -*-
# @Time : 2022/5/23 10:44
# @Author : Melon
# @Site :
# @Note :
# @File : log.py
# @Software: PyCharm
import datetime
import logging
import sys


def is_dev_mode() -> bool:
    """命令行是否带 -dev / --dev"""
    return any(arg in ("-dev", "--dev") for arg in sys.argv[1:])


def _console_formatter() -> logging.Formatter:
    """控制台格式：-dev 保留 [时间戳] ::；正式模式只输出消息本身"""
    if is_dev_mode():
        return logging.Formatter('[%(asctime)s] :: %(message)s')
    return logging.Formatter('%(message)s')


class Logger:
    def __init__(self, name):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level=logging.DEBUG)

        # 同名模块可能多次 Logger()，避免重复挂控制台 handler
        has_console = any(type(h) is logging.StreamHandler for h in self.logger.handlers)
        if not has_console:
            ch = logging.StreamHandler()
            ch.setLevel(logging.INFO)
            ch.setFormatter(_console_formatter())
            self.logger.addHandler(ch)

        # 文件日志始终带完整上下文，便于排查
        if not any(isinstance(h, logging.FileHandler) for h in self.logger.handlers):
            formatter = logging.Formatter(
                '[%(asctime)s][%(thread)d][%(filename)s][line: %(lineno)d][%(levelname)s] :: %(message)s')
            file_name = './mooc-work-answer-log_{t}.log'.format(t=datetime.datetime.now().strftime('%Y-%m-%d'))
            fh = logging.FileHandler(file_name, encoding='utf-8')
            fh.setLevel(logging.DEBUG)
            fh.setFormatter(formatter)
            self.logger.addHandler(fh)

    def get_log(self):
        return self.logger

# -*- coding: utf-8 -*-
# @Time : 2021/11/2 16:41
# @Author : Melon
# @Site : 
# @Note : 
# @File : StartWork.py
# @Software: PyCharm

import textwrap
import time
from typing import Optional, Tuple, Dict, Any

import MoocMain.initMooc as MoocInit
import NewMoocMain.init_mooc as NewMoocInit
from MoocMain.log import Logger
from ZYKMoocMain.main import ZYKMoocHandler
from update import check_for_updates

# ****************************************** 常量定义 ******************************************

APP_VERSION = 'dev' if 'TAG_NAME' in '${TAG_NAME}' else '${TAG_NAME}'
BORDER_WIDTH = 60
SUB_BORDER_WIDTH = 50

# 版本选项
VERSION_OPTIONS = {
    1: "MOOC",
    2: "课堂版", 
    3: "资源库"
}

# ****************************************** 初始化 ******************************************

logger = Logger(__name__).get_log()

# 用户配置存储（用于排查问题）
user_config: Dict[str, Any] = {}

def print_startup_info():
    """打印启动信息"""
    border = '*' * 80
    logger.info(border)
    logger.info(f'应用程序启动，版本: {APP_VERSION}')
    logger.info('开源支持: https://github.com/11273/mooc-work-answer')
    logger.info(border)
    
    # 检查更新
    check_for_updates(APP_VERSION)

def record_config(key: str, value: Any, sensitive: bool = False):
    """记录用户配置（非敏感信息）"""
    if not sensitive:
        user_config[key] = value
        logger.info(f"配置记录: {key} = {value}")
    else:
        user_config[key] = "***敏感信息已隐藏***"
        logger.info(f"配置记录: {key} = ***敏感信息已隐藏***")

def log_user_config():
    """记录完整的用户配置"""
    logger.info("=" * 60)
    logger.info("【用户配置汇总】")
    for key, value in user_config.items():
        logger.info(f"  {key}: {value}")
    logger.info("=" * 60)

# ****************************************** 界面函数 ******************************************

def print_section_header(title: str, description: str = "", width: int = BORDER_WIDTH):
    """打印节标题"""
    logger.info('\n' + '=' * width)
    logger.info(f'【{title}】')
    if description:
        logger.info(f'说明：{description}')
    logger.info('=' * width)

def print_subsection_header(title: str, description: str = "", width: int = SUB_BORDER_WIDTH):
    """打印子节标题"""
    logger.info('\n' + '-' * width)
    logger.info(f'【{title}】')
    if description:
        logger.info(f'说明：{description}')
    logger.info('-' * width)

def get_user_choice(prompt: str, default: str = 'n') -> bool:
    """获取用户的 y/n 选择"""
    response = input(f'* {prompt} [y/n] (默认{default}): ').lower().strip()
    choice = response == 'y'
    record_config(prompt, choice)
    return choice

def get_version_choice() -> int:
    """获取用户选择的版本"""
    print_section_header("版本选择")
    
    for key, value in VERSION_OPTIONS.items():
        logger.info(f'  {key}. {value}')
    logger.info('=' * BORDER_WIDTH)
    
    while True:
        try:
            choice = int(input(f'* 请选择版本 [1-{len(VERSION_OPTIONS)}] (默认1): ') or 1)
            if choice in VERSION_OPTIONS:
                record_config("选择版本", f"{choice} - {VERSION_OPTIONS[choice]}")
                return choice
            else:
                logger.warning(f'❌ 请输入 1-{len(VERSION_OPTIONS)} 之间的数字')
        except ValueError:
            logger.warning('❌ 请输入有效的数字')

def get_account_info() -> Tuple[str, str]:
    """获取用户账号信息"""
    print_section_header("账号配置", "请输入您的登录账号和密码")
    
    username = input('* 账号: ').strip()
    password = input('* 密码: ').strip()
    
    while not username or not password:
        logger.warning('❌ 账号和密码不能为空，请重新输入')
        if not username:
            username = input('* 账号: ').strip()
        if not password:
            password = input('* 密码: ').strip()
    
    # 记录账号信息（密码为敏感信息）
    record_config("账号", username)
    record_config("密码", password, sensitive=True)
    
    return username, password

def get_skip_course_config() -> Optional[str]:
    """获取跳过课程配置"""
    print_section_header("跳过课程配置", "可以设置跳过指定的课程（模糊匹配）")
    
    skip_courses = get_user_choice("是否需要跳过课程")
    
    if skip_courses:
        print_subsection_header("跳过课程关键字设置")
        logger.info('示例：')
        logger.info('  多个关键字随机: #设计#思想道德#技术')
        logger.info('  单个关键字固定: #思想')
        logger.info('-' * SUB_BORDER_WIDTH)
        
        keywords = input('* 请输入关键字 (例：#电商#商务英语): ').strip()
        final_keywords = keywords if keywords else None
        record_config("跳过课程关键字", final_keywords or "无")
        return final_keywords
    
    record_config("跳过课程关键字", "无")
    return None

def get_topic_reply_config() -> Optional[str]:
    """获取讨论回复配置"""
    print_section_header("讨论回复配置", "可以设置自动回复讨论内容")
    
    enable_reply = get_user_choice("是否启用自动讨论回复")
    
    if enable_reply:
        print_subsection_header("讨论回复内容设置", "回复内容不包括井号，井号仅用于分隔")
        logger.info('示例：')
        logger.info('  多个内容随机: #好#加油#积极响应')
        logger.info('  单个内容固定: #好')
        logger.info('-' * SUB_BORDER_WIDTH)
        
        content = input('* 请输入回复内容 (默认:#好#加油#积极响应): ').strip()
        final_content = content if content else '#好#加油#积极响应'
        record_config("讨论回复内容", final_content)
        return final_content
    
    record_config("讨论回复内容", "未启用")
    return None

def get_ai_answer_config() -> Tuple[bool, bool]:
    """获取AI答题配置"""
    print_section_header("AI答题功能配置")
    logger.info('⚠️  注意：AI答题功能可能存在不准确的情况，请谨慎使用！')
    logger.info('⚠️  隐私：功能基于当前平台AI，启用则默认接受此程序操作您的账号，请谨慎使用！')
    logger.info('⚠️  建议：重要考试建议人工检查后再提交')
    logger.info('=' * BORDER_WIDTH)
    
    enable_ai = get_user_choice("是否启用AI答题功能")
    auto_submit = False
    
    if enable_ai:
        print_subsection_header("AI自动提交配置", "如果AI全部填完题目，将自动提交；否则不提交，需要人工处理")
        auto_submit = get_user_choice("是否启用AI自动提交")
    
    record_config("AI自动提交", auto_submit if enable_ai else "未启用AI答题")
    return enable_ai, auto_submit

# ****************************************** 主程序 ******************************************

def handle_resource_library(version: int):
    """处理资源库版本"""
    username, password = get_account_info()
    skip_keywords = get_skip_course_config()
    
    logger.info(f"┃🚀 启动{VERSION_OPTIONS[version]}版本┃")
    log_user_config()  # 记录完整配置
    ZYKMoocHandler(username, password, skip_keywords)

def handle_mooc_or_classroom(version: int):
    """处理MOOC或课堂版"""
    username, password = get_account_info()
    topic_content = get_topic_reply_config()
    skip_keywords = get_skip_course_config()
    ai_answer, auto_submit = get_ai_answer_config()
    
    logger.info(f"┃🚀 启动{VERSION_OPTIONS[version]}版本┃")
    log_user_config()  # 记录完整配置
    NewMoocInit.run(
        username=username, 
        password=password, 
        topic_content=topic_content,
        jump_content=skip_keywords, 
        type_value=version, 
        is_ai_answer=ai_answer, 
        is_auto_submit=auto_submit
    )

def print_exit_message():
    """打印退出信息"""
    message = textwrap.dedent("""
        ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
        ┃ ✅ 程序结束，如遇错误请重新运行                   
        ┃ 🔄 多次重复错误请提交 Github 反馈！               
        ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
    """)
    logger.info(message)
    input('按回车键退出...')

def main():
    """主函数"""
    print_startup_info()
    time.sleep(1)
    logger.info('\n')
    
    try:
        # 记录程序启动时间和版本
        record_config("程序版本", APP_VERSION)
        record_config("启动时间", time.strftime("%Y-%m-%d %H:%M:%S"))
        
        version = get_version_choice()
        
        if version == 3:  # 资源库
            handle_resource_library(version)
        else:  # MOOC 或 课堂版
            handle_mooc_or_classroom(version)
        
        logger.info("┃✅ 本次程序运行完成，正常结束 ✅┃")
        
    except KeyboardInterrupt:
        logger.info("┃❌ 用户手动终止程序，正在安全退出...┃")
        record_config("程序状态", "用户手动终止")
    except Exception as e:
        logger.exception(f"┃⛔ 发生错误，请检查输入或提交 Github 反馈 ⛔┃ {e}")
        record_config("程序状态", f"异常终止: {str(e)}")
    finally:
        record_config("结束时间", time.strftime("%Y-%m-%d %H:%M:%S"))
        print_exit_message()

if __name__ == '__main__':
    main()

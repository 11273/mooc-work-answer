# -*- coding: utf-8 -*-
# @Time : 2021/11/2 16:41
# @Author : Melon
# @Site : 
# @Note : 
# @File : StartWork.py
# @Software: PyCharm

import re
import sys
import textwrap
import time
from time import sleep
from typing import Optional, Tuple, Dict, Any

# import MoocMain.initMooc as MoocInit
from MoocMain.log import Logger, is_dev_mode
import NewMoocMain.init_mooc as NewMoocInit
from ZYKMoocMain.main import ZYKMoocHandler
from AIMoocMain.main import AIMoocHandler
from update import check_for_updates

# ****************************************** 常量定义 ******************************************

# CI（simple-template-renderer）会把下面的占位符替换成发布 tag，例如 v1.2.3
_RELEASE_TAG_PLACEHOLDER = "${TAG_NAME}"


def _read_pyproject_version() -> str:
    """读取 pyproject.toml 里的 version（源码运行时用）"""
    try:
        from pathlib import Path
        text = Path(__file__).resolve().parent.joinpath("pyproject.toml").read_text(encoding="utf-8")
        for line in text.splitlines():
            s = line.strip()
            if s.startswith("version") and "=" in s:
                return s.split("=", 1)[1].strip().strip('"').strip("'") or "0.0.0"
    except Exception:
        pass
    return "0.0.0"


def _resolve_app_version() -> str:
    """发布构建显示 git tag；源码运行显示 pyproject 版本"""
    tag = _RELEASE_TAG_PLACEHOLDER  # CI 注入后这里就是 v1.2.3
    if tag and not str(tag).startswith("${"):
        return str(tag)
    return _read_pyproject_version()


# 是否为 CI 打包的发布版（源码运行为 False，不检查更新）
IS_RELEASE_BUILD = bool(_RELEASE_TAG_PLACEHOLDER) and not str(_RELEASE_TAG_PLACEHOLDER).startswith("${")
APP_VERSION = _resolve_app_version()
BORDER_WIDTH = 60
SUB_BORDER_WIDTH = 50

# 命令行：python StartWork.py -dev → 过程日志 + summary/json/raw；正式模式干净输出
IS_DEV = is_dev_mode()

# 版本选项
VERSION_OPTIONS = {
    0: "常规 MOOC / AI 优课",
    1: "资源库"
}

# 功能选项
WORK_MODE_OPTIONS = {
    1: "学习管理（刷课/进度）",
    2: "导出题目（作业/测验/考试，含正确答案）"
}

# 导出范围选项（与接口 categoryId 一致：1作业 2考试 3测验）
EXPORT_CATEGORY_OPTIONS = {
    0: "全部（作业+考试+测验）",
    1: "仅作业",
    2: "仅考试",
    3: "仅测验"
}

# 导出文档格式
EXPORT_FORMAT_OPTIONS = {
    1: "Markdown（.md）",
    2: "Word（.docx）",
    3: "Markdown + Word",
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

    # 发布构建才检查更新；源码运行 release_build=False 跳过
    check_for_updates(APP_VERSION, release_build=IS_RELEASE_BUILD)

def record_config(key: str, value: Any, sensitive: bool = False):
    """记录用户配置（非敏感信息），不打印日志"""
    if not sensitive:
        user_config[key] = value
    else:
        user_config[key] = "***敏感信息已隐藏***"

def log_user_config():
    """记录完整的用户配置；仅 -dev 输出"""
    if not IS_DEV:
        return
    logger.info("=" * 60)
    logger.info("【用户配置汇总】")
    for key, value in user_config.items():
        logger.info(f"  {key}: {value}")
    logger.info("=" * 60)

# ****************************************** 界面函数 ******************************************

def print_section_header(title: str, description: str = "", width: int = BORDER_WIDTH):
    """打印节标题；生产模式不画上方分隔线"""
    logger.info('')
    if IS_DEV:
        logger.info('=' * width)
    logger.info(f'【{title}】')
    if description:
        logger.info(f'说明：{description}')
    if IS_DEV:
        logger.info('=' * width)

def print_subsection_header(title: str, description: str = "", width: int = SUB_BORDER_WIDTH):
    """打印子节标题；生产模式不画上方分隔线"""
    logger.info('')
    if IS_DEV:
        logger.info('-' * width)
    logger.info(f'【{title}】')
    if description:
        logger.info(f'说明：{description}')
    if IS_DEV:
        logger.info('-' * width)

def get_user_choice(prompt: str, default: str = 'n') -> bool:
    """获取用户的 y/n 选择"""
    sleep(0.2)
    response = input(f'* {prompt} [y/n] (默认{default}): ').strip().lower() or default
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
            sleep(0.2)
            choice = int(input(f'* 请选择版本 [0-{len(VERSION_OPTIONS)-1}] (默认0): ') or 0)
            if choice in VERSION_OPTIONS:
                record_config("选择版本", f"{choice} - {VERSION_OPTIONS[choice]}")
                return choice
            else:
                logger.warning(f'❌ 请输入 0-{len(VERSION_OPTIONS)-1} 之间的数字')
        except ValueError:
            logger.warning('❌ 请输入有效的数字')

def get_work_mode_choice() -> int:
    """获取功能模式：学习管理 / 导出题目"""
    print_section_header("功能选择")

    for key, value in WORK_MODE_OPTIONS.items():
        logger.info(f'  {key}. {value}')
    logger.info('=' * BORDER_WIDTH)

    while True:
        try:
            sleep(0.2)
            raw = input(f'* 请选择功能 [1-{len(WORK_MODE_OPTIONS)}] (默认1): ').strip() or '1'
            choice = int(raw)
            if choice in WORK_MODE_OPTIONS:
                record_config("功能模式", f"{choice} - {WORK_MODE_OPTIONS[choice]}")
                return choice
            logger.warning(f'❌ 请输入 1-{len(WORK_MODE_OPTIONS)} 之间的数字')
        except ValueError:
            logger.warning('❌ 请输入有效的数字')

def get_export_category_choice() -> int:
    """获取题目导出范围"""
    print_section_header(
        "导出范围",
        "常规 MOOC（ai.icve.com.cn）；正式模式只输出 md 到 tiku/课程名/；加 -dev 额外输出 json/raw/summary",
    )

    for key, value in EXPORT_CATEGORY_OPTIONS.items():
        logger.info(f'  {key}. {value}')
    logger.info('=' * BORDER_WIDTH)

    while True:
        try:
            sleep(0.2)
            raw = input(f'* 请选择范围 [0-{len(EXPORT_CATEGORY_OPTIONS)-1}] (默认3 仅测验): ').strip() or '3'
            choice = int(raw)
            if choice in EXPORT_CATEGORY_OPTIONS:
                record_config("导出范围", f"{choice} - {EXPORT_CATEGORY_OPTIONS[choice]}")
                return choice
            logger.warning(f'❌ 请输入 0-{len(EXPORT_CATEGORY_OPTIONS)-1} 之间的数字')
        except ValueError:
            logger.warning('❌ 请输入有效的数字')

def get_course_selection(course_rows: list) -> list:
    """列出课程并让用户多选，返回选中的课程行"""
    print_section_header(
        "选择课程",
        "可输入编号：all 全部 / 1,3 多选 / 1-3 区间",
    )
    if not course_rows:
        logger.error("❌ 未获取到课程列表")
        return []

    for idx, course in enumerate(course_rows, start=1):
        name = course.get("courseName", "未知课程")
        info = course.get("courseInfoName", "")
        logger.info(f'  {idx}. {name}' + (f'（{info}）' if info else ''))
    logger.info('=' * BORDER_WIDTH)
    logger.info(f'* 共 {len(course_rows)} 门课程，输入 all 导出全部')

    while True:
        sleep(0.2)
        raw = input(f'* 请选择课程编号 [1-{len(course_rows)}] / all / 1,3 / 1-3 (默认 all): ').strip() or 'all'
        if raw.lower() in ('all', 'a', '*', '全部'):
            picked = list(range(1, len(course_rows) + 1))
        else:
            picked = []
            ok = True
            for part in re.split(r'[,，;；\s]+', raw):
                if not part:
                    continue
                if '-' in part:
                    left, right = part.split('-', 1)
                    try:
                        start, end = int(left), int(right)
                    except ValueError:
                        ok = False
                        break
                    if start > end:
                        start, end = end, start
                    picked.extend(range(start, end + 1))
                else:
                    try:
                        picked.append(int(part))
                    except ValueError:
                        ok = False
                        break
            if not ok or not picked:
                logger.warning(f'❌ 请输入有效编号，例如 all 或 1,3 或 1-3')
                continue
            # 去重 + 过滤越界
            seen = set()
            tmp = []
            for n in picked:
                if 1 <= n <= len(course_rows) and n not in seen:
                    seen.add(n)
                    tmp.append(n)
            picked = tmp
            if not picked:
                logger.warning(f'❌ 编号超出范围 1-{len(course_rows)}')
                continue

        selected = [course_rows[i - 1] for i in picked]
        names = [c.get("courseName", "") for c in selected]
        record_config("导出课程选择", f"{picked} -> {names}")
        for i, c in enumerate(selected, start=1):
            logger.info(f'    ✔ [{i}] {c.get("courseName", "")}')
        return selected

def get_export_format_choice() -> str:
    """选择导出文档格式：md / docx / both"""
    print_section_header("导出格式", "选择题目导出的文档格式")
    for key, value in EXPORT_FORMAT_OPTIONS.items():
        logger.info(f'  {key}. {value}')
    logger.info('=' * BORDER_WIDTH)

    while True:
        try:
            sleep(0.2)
            raw = input(f'* 请选择格式 [1-{len(EXPORT_FORMAT_OPTIONS)}] (默认1 Markdown): ').strip() or '1'
            choice = int(raw)
            if choice == 1:
                fmt = "md"
            elif choice == 2:
                fmt = "docx"
            elif choice == 3:
                fmt = "both"
            else:
                logger.warning(f'❌ 请输入 1-{len(EXPORT_FORMAT_OPTIONS)} 之间的数字')
                continue
            record_config("导出格式", f"{choice} - {EXPORT_FORMAT_OPTIONS[choice]}")
            return fmt
        except ValueError:
            logger.warning('❌ 请输入有效的数字')

def get_quiz_export_mode() -> str:
    """获取章节测验导出模式"""
    print_section_header(
        "测验导出模式",
        "仅在导出范围包含「测验」时生效；作业/考试始终按单份文件导出",
    )
    options = {
        '1': ("single", "单个/多个章节测验（手动选择）"),
        '2': ("per_chapter", "所有章节测验（每个章节一个文件）"),
        '3': ("merged", "所有章节测验（所有章节一个文件）"),
    }
    for key, (_, label) in options.items():
        logger.info(f'  {key}. {label}')
    logger.info('=' * BORDER_WIDTH)

    while True:
        sleep(0.2)
        raw = input('* 请选择模式 [1-3] (默认2 每章一个文件): ').strip() or '2'
        if raw in options:
            mode, label = options[raw]
            record_config("测验导出模式", f"{raw} - {label}")
            return mode
        logger.warning('❌ 请输入 1-3 之间的数字')

def get_selected_quiz_exam_ids(client, selected_courses: list, quiz_mode: str):
    """single 模式下列出章节测验供多选，返回 exam_id 列表；其他模式返回 []"""
    if quiz_mode != 'single':
        return []

    from AIMoocMain.export_questions import collect_quiz_catalog

    print_section_header("选择章节测验", "可输入编号：all 全部 / 1,3 多选 / 1-3 区间")
    catalog = collect_quiz_catalog(client, selected_courses, category_id=3)
    if not catalog:
        logger.warning("⚠️ 所选课程下未找到章节测验")
        return []

    for idx, row in enumerate(catalog, start=1):
        logger.info(f'  {idx}. [{row["course"]}] {row["paper_name"]}')
    logger.info('=' * BORDER_WIDTH)
    logger.info(f'* 共 {len(catalog)} 份章节测验，输入 all 导出全部')

    while True:
        sleep(0.2)
        raw = input(f'* 请选择测验编号 [1-{len(catalog)}] / all / 1,3 / 1-3 (默认 all): ').strip() or 'all'
        if raw.lower() in ('all', 'a', '*', '全部'):
            picked = list(range(1, len(catalog) + 1))
        else:
            picked = []
            ok = True
            for part in re.split(r'[,，;；\s]+', raw):
                if not part:
                    continue
                if '-' in part:
                    left, right = part.split('-', 1)
                    try:
                        start, end = int(left), int(right)
                    except ValueError:
                        ok = False
                        break
                    if start > end:
                        start, end = end, start
                    picked.extend(range(start, end + 1))
                else:
                    try:
                        picked.append(int(part))
                    except ValueError:
                        ok = False
                        break
            if not ok or not picked:
                logger.warning('❌ 请输入有效编号，例如 all 或 1,3 或 1-3')
                continue
            seen = set()
            tmp = []
            for n in picked:
                if 1 <= n <= len(catalog) and n not in seen:
                    seen.add(n)
                    tmp.append(n)
            picked = tmp
            if not picked:
                logger.warning(f'❌ 编号超出范围 1-{len(catalog)}')
                continue

        exam_ids = [catalog[i - 1]['exam_id'] for i in picked]
        names = [catalog[i - 1]['paper_name'] for i in picked]
        record_config("导出章节测验选择", f"{picked} -> {names}")
        return exam_ids

def get_login_info() -> Tuple[str, str, str]:
    """获取用户登录信息，返回(username, password, token)"""
    # 默认选择 OAuth 登录
    # record_config("登录方式", "OAuth浏览器登录")
    # print_section_header("OAuth登录", "将打开浏览器进行安全登录")
    
    logger.info('⚠️  注意：')
    logger.info('  - 程序将自动打开浏览器')
    logger.info('  - 请在浏览器中完成登录')
    logger.info('  - 支持扫码、短信等多种登录方式')
    logger.info('  - 登录成功后会自动获取token')
    logger.info('=' * BORDER_WIDTH)

    sleep(0.2)
    # 提示用户按回车继续
    input('* 按回车键继续并打开浏览器...')
    
    # 执行OAuth登录
    try:
        from NewMoocMain.oauth_login import oauth_login
        logger.info("🔐 正在启动OAuth登录...")
        token = oauth_login(timeout=300)
        
        if token:
            logger.info("✅ OAuth登录成功")
            record_config("OAuth登录", "成功")
            return "", "", token  # 返回空的用户名密码和token
        else:
            logger.error("❌ OAuth登录失败")
            record_config("OAuth登录", "失败")
            
            # 询问是否重试
            if get_user_choice("是否重试OAuth登录", "y"):
                return get_login_info()  # 重新选择
            else:
                logger.error("❌ 无法继续，程序退出")
                sleep(0.2)
                input('程序退出')
                exit(0)
                
    except Exception as e:
        logger.error(f"❌ OAuth登录异常: {e}")
        record_config("OAuth登录", f"异常: {str(e)}")
        
        # 询问是否重试
        if get_user_choice("是否重试OAuth登录", "y"):
            return get_login_info()  # 重新选择
        else:
            logger.error("❌ 无法继续，程序退出")
            sleep(0.2)
            input('程序退出')
            exit(0)

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
        sleep(0.2)
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
        sleep(0.2)
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
    username, password, token = get_login_info()
    skip_keywords = get_skip_course_config()
    
    logger.info(f"┃🚀 启动{VERSION_OPTIONS[version]}版本┃")
    log_user_config()  # 记录完整配置
    
    # 根据登录方式调用不同的参数
    if token:
        ZYKMoocHandler(jump_content=skip_keywords, token=token)
    else:
        ZYKMoocHandler(username, password, skip_keywords)

def handle_mooc_or_classroom(version: int):
    """处理MOOC或课堂版"""
    username, password, token = get_login_info()
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
        is_auto_submit=auto_submit,
        token=token
    )

def handle_ai_mooc(version: int):
    """处理AI MOOC"""
    username, password, token = get_login_info()
    skip_keywords = get_skip_course_config()

    logger.info(f"┃🚀 启动{VERSION_OPTIONS[version]}版本┃")
    log_user_config()  # 记录完整配置
    AIMoocHandler(jump_content=skip_keywords, token=token, username=username, password=password)

def handle_export_questions(version: int):
    """导出题目（作业/测验/考试，含正确答案）"""
    if version != 0:
        logger.error("❌ 题目导出目前仅支持「常规 MOOC / AI 优课」，请重新选择版本 0")
        return

    username, password, token = get_login_info()

    # 复用同一 client：登录 → 拉课程 → 选择 → 传给导出器（避免二次 OAuth）
    from AIMoocMain.api import AIMoocApi
    from AIMoocMain.export_questions import QuizExportHandler

    client = AIMoocApi(token=token, username=username, password=password)
    courses = client.my_course_list(page_size=9999)
    course_rows = courses.get("rows", []) if isinstance(courses, dict) else []
    if not course_rows:
        logger.error("❌ 未获取到课程列表，无法导出")
        return
    logger.info(f"📚 获取课程成功，共 {len(course_rows)} 门")

    selected_courses = get_course_selection(course_rows)
    if not selected_courses:
        logger.error("❌ 未选择课程，已取消导出")
        return

    # 选择课程后选择 md / word
    export_format = get_export_format_choice()

    category_choice = get_export_category_choice()
    # categoryId: 1=作业 2=考试 3=测验（与 EXPORT_CATEGORY_OPTIONS 键一致）
    category_ids = [1, 2, 3] if category_choice == 0 else [category_choice]

    quiz_mode = "per_chapter"
    selected_exam_ids: list = []
    if 3 in category_ids:
        quiz_mode = get_quiz_export_mode()
        if quiz_mode == "single":
            selected_exam_ids = get_selected_quiz_exam_ids(client, selected_courses, quiz_mode)
            if not selected_exam_ids:
                logger.warning("⚠️ 未选中任何章节测验，将只导出作业/考试（若有）")
                # 若只导出测验且没选中，则取消
                if category_ids == [3]:
                    logger.error("❌ 导出范围仅测验且未选中测验，已取消")
                    return

    logger.info(f"┃🚀 启动题目导出（{VERSION_OPTIONS[version]}）┃")
    # 过程/配置日志仅 -dev；正式模式安静导出
    if IS_DEV:
        logger.info("📦 输出目录: tiku/<课程名>/")
        logger.info(f"⚙️ 测验模式: {quiz_mode}")
        logger.info(f"📄 导出格式: {export_format}")
        log_user_config()

    QuizExportHandler(
        client=client,
        course_rows=selected_courses,
        category_ids=category_ids,
        quiz_mode=quiz_mode,
        selected_exam_ids=selected_exam_ids,
        output_dir="tiku",
        dev_mode=IS_DEV,
        export_format=export_format,
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
    sleep(0.2)
    input('按回车键退出...')

def main():
    """主函数"""
    print_startup_info()
    time.sleep(1)

    try:
        # 记录程序启动时间和版本
        record_config("程序版本", APP_VERSION)
        record_config("启动时间", time.strftime("%Y-%m-%d %H:%M:%S"))
        
        work_mode = get_work_mode_choice()
        version = get_version_choice()

        if work_mode == 2:  # 导出题目
            handle_export_questions(version)
        elif version == 1:  # 资源库
            handle_resource_library(version)
        elif version == 0:
            handle_ai_mooc(version)
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

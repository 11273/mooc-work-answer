#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
职教云考试解析工具函数
"""

import re
from lxml import html
from typing import List, Dict, Any

# 填空题空格标记
BLANK_MARKER = '※~_~_~_~_※'


def clean_text(text: str) -> str:
    """清理文本中的多余空白字符"""
    if not text:
        return ''
    text = text.replace('\xa0', ' ').replace('\u200b', '')
    text = re.sub(r'[\r\n]+', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def parse_exam_questions(html_content: str) -> List[Dict[str, Any]]:
    """
    解析职教云考试页面的题目
    
    Args:
        html_content: 考试页面HTML内容
        
    Returns:
        题目列表，每个题目包含：
        - id: 题目ID
        - number: 题号
        - type: 题型（单选题/多选题/判断题/填空题）
        - text: 题目文本
        - score: 分数
        - options: 选项列表（选择题）
        - blank_count: 空格数（填空题）
    """
    tree = html.fromstring(html_content)
    questions = []
    
    # 题型映射
    type_map = {
        'singlechoice': '单选题',
        'multichoice': '多选题',
        'fillblank': '填空题',
        'bijudgement': '判断题'
    }
    
    # 获取所有题目元信息
    question_inputs = tree.xpath('//input[@name="questionId"]')
    question_info = {}
    for q_input in question_inputs:
        qid = q_input.get('value')
        question_info[qid] = {
            'number': q_input.get('questionnum'),
            'answer_type': q_input.get('answertype'),
        }
    
    # 解析每个题目
    for q_content in tree.xpath('//div[contains(@class, "q_content")]'):
        try:
            # 获取题目ID
            qid = q_content.xpath('.//input[@name="quesId"]/@value')[0]
            info = question_info.get(qid, {})
            answer_type = info.get('answer_type', '')
            
            question = {
                'id': qid,
                'number': info.get('number', ''),
                'type': type_map.get(answer_type, answer_type),
                'answer_type': answer_type
            }
            
            # 填空题特殊处理
            if answer_type == 'fillblank':
                # 获取填空题内容
                fillblank_text = q_content.xpath('.//span[@name="fillblankTitle"]')[0].text_content()
                question['text'] = clean_text(fillblank_text)
                question['blank_count'] = fillblank_text.count(BLANK_MARKER)
                
                # 获取分数
                score_text = q_content.xpath('.//span[@class="answerOption"]/text()')[-1]
                score_match = re.search(r'（(\d+)\s*分）', score_text)
                question['score'] = score_match.group(1) if score_match else '0'
                
            else:  # 选择题和判断题
                # 获取题目文本和分数
                title_text = clean_text(q_content.xpath('.//div[@class="divQuestionTitle"]')[0].text_content())
                
                # 提取分数
                score_match = re.search(r'（(\d+)\s*分）', title_text)
                question['score'] = score_match.group(1) if score_match else '0'
                
                # 提取题目文本（去除题号和分数）
                text_match = re.match(r'\d+、(.+?)（\d+\s*分）', title_text)
                if text_match:
                    question['text'] = clean_text(text_match.group(1))
                else:
                    question['text'] = re.sub(r'^\d+、|（\d+\s*分）', '', title_text).strip()
                
                # 获取选项
                question['options'] = []
                for opt in q_content.xpath('.//div[@class="q_option"]'):
                    option_value = opt.xpath('.//input/@value')[0]
                    option_text = clean_text(opt.xpath('.//div[contains(@class, "_off")]')[0].text_content())
                    
                    # 分离选项标签和内容
                    opt_match = re.match(r'([A-Z])．(.+)', option_text)
                    if opt_match:
                        question['options'].append({
                            'value': option_value,
                            'label': opt_match.group(1),
                            'text': clean_text(opt_match.group(2))
                        })
                    else:
                        # 判断题特殊处理
                        label = '正确' if '正确' in option_text else '错误'
                        question['options'].append({
                            'value': option_value,
                            'label': label,
                            'text': label
                        })
            
            # 获取音频资源（如果有）
            audio_path = q_content.xpath('.//input[@name="resourcePath"]/@value')
            if audio_path and audio_path[0]:
                question['audio_path'] = audio_path[0]
            
            questions.append(question)
            
        except Exception as e:
            print(f"解析题目失败: {e}")
            continue
    
    return questions


def get_question_stats(questions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """获取题目统计信息"""
    stats = {
        'total': len(questions),
        'by_type': {},
        'total_score': 0
    }
    
    for q in questions:
        q_type = q['type']
        score = int(q.get('score', 0))
        
        if q_type not in stats['by_type']:
            stats['by_type'][q_type] = {'count': 0, 'score': 0}
        
        stats['by_type'][q_type]['count'] += 1
        stats['by_type'][q_type]['score'] += score
        stats['total_score'] += score
    
    return stats


def display_questions(questions: List[Dict[str, Any]], show_options: bool = True) -> None:
    """打印题目信息"""
    if not questions:
        print("没有找到题目")
        return
    
    # 按题型分组
    grouped = {}
    for q in questions:
        q_type = q['type']
        if q_type not in grouped:
            grouped[q_type] = []
        grouped[q_type].append(q)
    
    # 显示统计
    stats = get_question_stats(questions)
    print(f"\n题目总数: {stats['total']}, 总分: {stats['total_score']}分")
    print("题型分布:", end='')
    for q_type, info in stats['by_type'].items():
        print(f"  {q_type}: {info['count']}题/{info['score']}分", end='')
    print("\n")
    
    # 显示题目
    for q_type, qs in grouped.items():
        print(f"\n{'='*20} {q_type} {'='*20}")
        for q in qs:
            print(f"\n{q['number']}. {q['text']} ({q['score']}分)")
            
            if q['type'] == '填空题':
                print(f"   空格数: {q['blank_count']}")
            elif show_options and 'options' in q:
                for opt in q['options']:
                    print(f"   {opt['label']}. {opt['text']}")

# 使用示例
if __name__ == '__main__':
    # 示例用法
    print("职教云考试解析工具")
    print("使用方法:")
    print("questions = parse_exam_questions(html_content)")
    print("display_questions(questions)")

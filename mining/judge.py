import os
import json
import requests
import time
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("DEEPSEEK_API_KEY")
API_URL = "https://api.deepseek.com/v1/chat/completions"

def llm_judge_t0(record, max_retries=3):
    rid = record.get("record_id", "Unknown")
    content = record.get("content", "")[:1000] 
    
    prompt = f"""
    你是一个教育 AI 数据分析师。请严格依据“T0 教育相关性”标准，判断以下文本属于哪一类。

    【四大分类目标（只能选一个）】
    1. EDUCATION_DIRECT：可见原文明确涉及教学、学习、实验实践、教育管理/评价，或明确的职业教育、成人学习。能够指出教育参与者、教育任务、教育机构行动或教育产品使用语境。
    2. EDUCATION_WEAK：存在可解释的教育联系，但当前片段主要是泛技术、供给宣传、研究标题、新闻标题，不能稳定确认具体教育活动。
    3. NON_EDUCATION：可见原文足以确认主题不属于教育活动（包括通用软件工程、娱乐、普通商业、仅表示机器学习训练等）。
    4. UNKNOWN：正文为空、只有无法解释的元数据、链接或标题不足以判断。

    【边界规则】
    - 空正文必须选 UNKNOWN。
    - 只有教育机构名/标题，选 WEAK 或 UNKNOWN。
    - AI tutor 产品说明，若明确教学用途选 DIRECT；只有名称为 WEAK/UNKNOWN。
    - 机器学习 training，没有教育活动时选 NON_EDUCATION。
    - 教育新闻/论文可为 DIRECT，但这不代表它是真实需求。

    【严格输出 JSON 格式】
    {{
        "t0_label": "EDUCATION_DIRECT/EDUCATION_WEAK/NON_EDUCATION/UNKNOWN",
        "evidence": "支持判断的原文逐字片段，若 UNKNOWN 填 NO_VISIBLE_CONTENT",
        "reason": "一句话解释为什么选此分类",
        "D1": 1, 
        "is_opportunity": "1/0/REVIEW",
        "function": "若明确有AI需求且是DIRECT，从16类选1；否则填'无'",
        "industry": "若明确有AI需求且是DIRECT，从30类选1；否则填'无'"
    }}

    文本内容：{content}
    """

    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    data = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "response_format": {"type": "json_object"}
    }
    
    for attempt in range(max_retries):
        try:
            r = requests.post(API_URL, headers=headers, json=data, timeout=40)
            resp_json = r.json()
            res_dict = json.loads(resp_json["choices"][0]["message"]["content"])
            usage = resp_json.get("usage", {})
            return res_dict, usage
        except Exception as e:
            if attempt == max_retries - 1:
                return {"t0_label": "UNKNOWN", "evidence": "API ERROR", "reason": "报错"}, {"total_tokens": 0}
            time.sleep(3)
import os
import json
import requests
import time
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("DEEPSEEK_API_KEY")
API_URL = "https://api.deepseek.com/v1/chat/completions"

FUNC_LIST = "图像识别, 语义分析, 语音处理, 文本生成, 对话问答, 推荐系统, 知识检索, 数据挖掘, 多模态融合, 智能体编排, 自动化流程, 预测分析, 审核审查, 搜索匹配, 翻译转写, 视频理解"
IND_LIST = "金融, 教育, 医疗, 法律, 电商, 零售, 房地产, 制造, 物流, 游戏, 餐饮, 农业, 政务, 汽车, 家居, 交通, 能源, 通信, 娱乐, 体育, 旅游, 保险, 建筑, 环保, 科研, 人力资源, 媒体出版, 营销广告, 外贸, 其他"

def llm_judge(record, max_retries=3):
    title = record.get("title", "")
    content = record.get("content", "")[:1200] # 截断防超长
    
    prompt = f"""
    你是一个严谨的教育 AI 研究专家。请严格按照以下 V0.2 标准，对文本进行判别。

    【四大核心场景】
    S1教师教学支持, S2学生学习支持, S3实验与实践教学, S4教育管理与评价, OTHER_EDUCATION(其他教育), NOT_EDUCATION(非教育)

    【证据类型 E1-E5】
    E1: 用户直接需求, E2: 机构需求, E3: 学术研究, E4: 市场供给(产品), E5: 技术可行性(代码/开源)

    【判别维度 D1-D6 (取值1/0/U)】
    D1 教育相关性, D2 问题明确性, D3 需求真实性, D4 AI核心性, D5 应用可行性, D6 未满足程度。

    【判别决策流】
    1. 若 D1=0，判定 0 (NOT_EDUCATION_RELATED)。
    2. 若 D2=0，判定 0 (NO_CONCRETE_PROBLEM)。不能只有泛泛趋势或纯产品宣传。
    3. 若 D3=0，判定 0 (NO_SUPPORTING_EVIDENCE)。论文不能当直接需求。
    4. 若 D4=0，判定 0 (AI_NOT_CORE)。传统软件能解决的不算。
    5. 若 D1-D4 中有 U，判定 REVIEW。
    6. 只有 D1-D4 均为 1，且 D5/D6 有依据，才判 1。

    【输出格式要求（严格输出 JSON）】
    {{
        "scenario": "S1/S2/S3/S4/OTHER_EDUCATION/NOT_EDUCATION",
        "evidence_type": "E1/E2/E3/E4/E5",
        "D1": 1, "D2": 1, "D3": 0, "D4": 1, "D5": 1, "D6": 0,
        "is_opportunity": "1/0/REVIEW",
        "reason_code": "命中 0 或 REVIEW 的原因代码",
        "confidence": 0.85,
        "function": "若为机会，从16类中选1；否则填'无'",
        "industry": "若为机会，从30类中选1；否则填'无'"
    }}
    
    功能类别：{FUNC_LIST}
    行业类别：{IND_LIST}
    Reason Codes可选: NOT_EDUCATION_RELATED, NO_CONCRETE_PROBLEM, NO_SUPPORTING_EVIDENCE, AI_NOT_CORE, EXISTING_SOLUTION_SUFFICIENT, INSUFFICIENT_EVIDENCE, REVIEW_OTHER.

    文本标题：{title}
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
            usage_dict = {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
                "is_cached": False
            }
            
            # 返回极其丰富的维度数据
            return res_dict, usage_dict
            
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"[LLM Error] {record['record_id']} 失败: {e}")
                # 彻底失败时，回退到 REVIEW 状态，绝不强行判 0/1
                fallback = {
                    "scenario": "NOT_EDUCATION", "evidence_type": "E5", 
                    "D1": "U", "D2": "U", "D3": "U", "D4": "U", "D5": "U", "D6": "U",
                    "is_opportunity": "REVIEW", "reason_code": "INSUFFICIENT_EVIDENCE",
                    "confidence": 0.0, "function": "无", "industry": "无"
                }
                return fallback, {"total_tokens": 0, "is_cached": False}
            time.sleep(3)
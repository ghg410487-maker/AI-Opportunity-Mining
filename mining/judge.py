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

EXCLUDE_WORDS = ["教程", "入门", "保姆级", "广告", "招生", "包过", "购买", "原价", "限时", "点击链接", "tutorial", "buy now", "discount"]

def llm_judge(record, max_retries=3):
    title = record.get("title", "")
    content = record.get("content", "")[:800] 
    
    # 前置黑名单过滤
    text_lower = (title + " " + content).lower()
    if any(neg in text_lower for neg in EXCLUDE_WORDS):
        return 0, 0.1, "无", "无", "直接排除(教程/广告)", {"total_tokens": 0, "is_cached": True}
    
    # 把曹的4条核心逻辑写进 Prompt
    prompt = f"""
    你是一个资深的 AI 产品分析师。请严格依据以下规则，判断给定文本是否构成真实的“AI应用机会”。

    【赛题核心规则】
    1. 有真实需求：必须面向明确终端用户或业务场景，有具体的寻解、吐槽信号。
    2. AI是核心：AI必须是解决该问题的核心手段。
    3. 技术可落地：用现有成熟技术即可实现。
    4. 排除：纯知识科普、广告、仅以AI为噱头的营销内容。

    【特别注意（重要）】
    - 只有教育相关性，没有具体问题：不能认定为机会。
    - 有具体问题，但没有可靠证据（纯猜测、无事实）：不能认定机会，需标记。
    - 有真实需求，但传统软件就能更好解决（比如只是要个Excel表格、普通官网展示）：不能算作 AI 核心机会。
    - 已有产品，但仍有明确未满足需求：依然算作新机会。

    【输出格式要求】
    请输出纯 JSON：
    {{
        "is_opportunity": 1 或 0,
        "confidence": 0.0~1.0 的数值,
        "function": "从功能类别列表选一，若不是机会填'无'",
        "industry": "从行业列表选一，若不是机会填'无'",
        "audit_status": "判断理由分类"
    }}
    
    audit_status 必须从以下选项选一个：
    - "有效机会"
    - "无具体问题(仅有相关性)"
    - "证据不足(待核实)"
    - "传统软件更优(非AI核心)"
    - "教程/广告(排除)"

    功能类别列表：{FUNC_LIST}
    行业列表：{IND_LIST}

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
            r = requests.post(API_URL, headers=headers, json=data, timeout=30)
            resp_json = r.json()
            res_dict = json.loads(resp_json["choices"][0]["message"]["content"])
            
            usage = resp_json.get("usage", {})
            usage_dict = {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
                "is_cached": False
            }
            
            return (
                int(res_dict.get("is_opportunity", 0)),
                float(res_dict.get("confidence", 0.0)),
                str(res_dict.get("function", "无")),
                str(res_dict.get("industry", "无")),
                str(res_dict.get("audit_status", "未知")),
                usage_dict
            )
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"[LLM Error] {record['record_id']} 失败: {e}")
                return 0, 0.0, "无", "无", "API失败", {"total_tokens": 0, "is_cached": False}
            time.sleep(2)
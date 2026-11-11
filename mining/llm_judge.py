import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("DEEPSEEK_API_KEY")
API_URL = "https://api.deepseek.com/v1/chat/completions"

FUNC_LIST = "图像识别, 语义分析, 语音处理, 文本生成, 对话问答, 推荐系统, 知识检索, 数据挖掘, 多模态融合, 智能体编排, 自动化流程, 预测分析, 审核审查, 搜索匹配, 翻译转写, 视频理解"
IND_LIST = "金融, 教育, 医疗, 法律, 电商, 零售, 房地产, 制造, 物流, 游戏, 餐饮, 农业, 政务, 汽车, 家居, 交通, 能源, 通信, 娱乐, 体育, 旅游, 保险, 建筑, 环保, 科研, 人力资源, 媒体出版, 营销广告, 外贸, 其他"

def llm_judge(record):
    title = record.get("title", "")
    content = record.get("content", "")[:800] 
    
    prompt = f"""
    你是一个专业的 AI 数据分析师。请判断以下文本是否构成“AI应用机会”。
    规则：
    1. 有真实需求（用户求助、痛点、寻找工具等）。
    2. AI是核心（必须利用AI来解决）。
    3. 技术可落地。
    4. 排除：纯教程、纯科普、广告、仅以AI为噱头的营销内容。

    如果构成机会，请给出 0~1 的置信度，并从以下分类中选一个【功能类别】和【所属行业】：
    功能类别（只能选其一）：{FUNC_LIST}
    所属行业（只能选其一）：{IND_LIST}

    文本标题：{title}
    文本内容：{content}

    请严格输出纯 JSON，不要包含 Markdown 标记：
    {{"is_opportunity": 1, "confidence": 0.85, "function": "对话问答", "industry": "教育"}}
    （注意：如果不是机会，function 和 industry 填 "无"，confidence 填 0.1 即可）
    """

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "response_format": {"type": "json_object"}
    }
    
    try:
        r = requests.post(API_URL, headers=headers, json=data, timeout=30)
        resp_json = r.json()
        result = resp_json["choices"][0]["message"]["content"]
        res_dict = json.loads(result)
        
        # 提取 Token 消耗
        usage = resp_json.get("usage", {})
        usage_dict = {
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0)
        }
        
        return (
            int(res_dict.get("is_opportunity", 0)),
            float(res_dict.get("confidence", 0.0)),
            str(res_dict.get("function", "无")),
            str(res_dict.get("industry", "无")),
            usage_dict  # 返回消耗情况
        )
    except Exception as e:
        print(f"[LLM Error] {e}")
        return 0, 0.0, "无", "无", {"total_tokens": 0}
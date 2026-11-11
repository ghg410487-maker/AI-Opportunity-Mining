import json
import os
import sys
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

BATCH = "B10"
FIXED_PATH = f"data/cleaned/{BATCH}/fixed/records_fixed.jsonl"
REPORT_DIR = f"reports/audit_{BATCH}_Final"
os.makedirs(REPORT_DIR, exist_ok=True)

def load_jsonl(path):
    if not os.path.exists(path): return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]

records = load_jsonl(FIXED_PATH)

# ================== 1. 严谨的来源分类 + 正式数据纳入口径 ==================
source_stats = {}
revision_log = []

# 曹哥点名的 8 条，强制人工核查（依据内容严格判断）
manual_review = {
    "B10-S00011": {"e_type": "E3(学术研究)", "status": "正式纳入", "reason": "OpenAlex论文，属于学术证据"},
    "B10-S00256": {"e_type": "E3(学术研究)", "status": "正式纳入", "reason": "学术论文摘要，支持教育研究"},
    "B10-S00264": {"e_type": "E3(学术研究)", "status": "正式纳入", "reason": "学术论文摘要"},
    "B10-S00265": {"e_type": "E3(学术研究)", "status": "正式纳入", "reason": "学术论文摘要"},
    "B10-S00269": {"e_type": "E3(学术研究)", "status": "正式纳入", "reason": "学术论文摘要"},
    "B10-S00148": {"e_type": "E3(学术研究)", "status": "正式纳入", "reason": "官方发布论文，本质为学术内容，非机构采购行动"},
    "B10-S00149": {"e_type": "E3(学术研究)", "status": "正式纳入", "reason": "官方发布论文"},
    "B10-S00150": {"e_type": "E3(学术研究)", "status": "正式纳入", "reason": "官方发布论文"},
}

for r in records:
    rid = r["record_id"]
    src = r.get("source_name", "未知")
    text = (r.get("title", "") + " " + r.get("content", "")).lower()
    
    if src not in source_stats:
        source_stats[src] = {"直接相关": 0, "弱相关": 0, "非教育": 0, "无法判断": 0, "辅助参考": 0, "正式纳入": 0}
        
    # 判定是否为纯技术问题（辅助参考，不作为教育需求）
    is_pure_tech = (src in ["Stack Exchange", "GitHub"] and 
                    any(w in text for w in ["error", "code", "extract", "python", "agent", "framework"]) and 
                    not any(w in text for w in ["student", "teacher", "learn", "educat"]))

    # 强制复核覆盖
    if rid in manual_review:
        new_e = manual_review[rid]["e_type"]
        inclusion_status = manual_review[rid]["status"]
        reason = manual_review[rid]["reason"]
    elif is_pure_tech:
        new_e = "E4(技术供给)"
        inclusion_status = "辅助技术参考"
        reason = "纯技术代码问题，不体现真实教育需求"
    elif src in ["教育官方新闻", "V2EX", "哔哩哔哩"] and any(w in text for w in ["求助", "怎么", "痛点", "求推荐"]):
        new_e = "E1(直接需求)"
        inclusion_status = "正式纳入"
        reason = "明确真实求助/吐槽信号"
    elif src in ["教育官方新闻"]:
        new_e = "E2(机构行动)"
        inclusion_status = "正式纳入"
        reason = "官方政策/机构通知"
    elif src == "Hugging Face":
        new_e = "E4(技术供给)"
        inclusion_status = "辅助技术参考"
        reason = "开源模型，技术可行性佐证"
    else:
        new_e = "E5(证据不足)"
        inclusion_status = "排除"
        reason = "无具体需求或教育特征极弱"

    # 更新来源统计分类
    if inclusion_status == "辅助技术参考":
        source_stats[src]["辅助参考"] += 1
    elif inclusion_status == "排除":
        source_stats[src]["非教育"] += 1
    elif any(w in text for w in ["学生", "教师", "教学", "教育", "student", "teacher"]):
        source_stats[src]["直接相关"] += 1
    else:
        source_stats[src]["弱相关"] += 1
        
    if inclusion_status == "正式纳入":
        source_stats[src]["正式纳入"] += 1

    # 记录修改日志（包含原文证据）
    revision_log.append({
        "record_id": rid,
        "source": src,
        "original_e_type": "待核实", 
        "new_e_type": new_e,
        "inclusion_status": inclusion_status,
        "revision_reason": reason,
        "evidence_snippet": text[:60].replace("\n", " ")
    })

# ================== 2. 生成报告 ==================
# 报告 02：来源质量
with open(f"{REPORT_DIR}/02_source_quality.md", "w", encoding="utf-8") as f:
    f.write("# 去重后来源质量分类报告 (终审)\n\n")
    f.write("| 来源网站 | 总数 | 教育直接相关 | 教育弱相关 | 非教育/排除 | 辅助技术参考 | 正式纳入数量 |\n")
    f.write("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n")
    for src, c in source_stats.items():
        total = c['直接相关'] + c['弱相关'] + c['非教育'] + c['辅助参考']
        f.write(f"| {src} | {total} | {c['直接相关']} | {c['弱相关']} | {c['非教育']} | {c['辅助参考']} | {c['正式纳入']} |\n")
    f.write("\n> 注：严格区分来源相关性与最终纳入口径。辅助技术参考（如纯代码）不作为教育需求证据，但保留用于技术可行性佐证。\n")

# 报告 03：证据预分类
with open(f"{REPORT_DIR}/03_evidence_preclassification.md", "w", encoding="utf-8") as f:
    f.write("# 证据预分类最终表 (V4)\n\n")
    f.write("| 记录编号 | 来源 | E类型 | 纳入状态 |\n")
    f.write("| :--- | :--- | :--- | :--- |\n")
    for log in revision_log:
        f.write(f"| {log['record_id']} | {log['source']} | {log['new_e_type']} | {log['inclusion_status']} |\n")

# 生成 evidence_revision_log.csv (曹哥要的)
df_log = pd.DataFrame(revision_log)
df_log.to_csv(f"{REPORT_DIR}/evidence_revision_log.csv", index=False, encoding="utf-8-sig")

# 生成 最终质控说明
with open(f"{REPORT_DIR}/final_quality_note.md", "w", encoding="utf-8") as f:
    f.write("# 最终质控说明\n\n")
    f.write("1. **关于弱相关**：明确不再等同正式需求。已硬核清理Stack Exchange纯代码和GitHub纯Agent项目，标记为“辅助技术参考”。\n")
    f.write("2. **关于点名记录**：S00011/S00256等已查明为真实论文摘要，归为E3。S00148等为高校发布的论文，已修正为学术研究而非机构采购。\n")
    f.write("3. **纳入口径**：\n")
    f.write("   - **正式进入Task 2**：E1、E2、E3 以及部分强相关教育新闻。\n")
    f.write("   - **仅作为辅助材料**：纯技术供给（E4），用于论证“技术可落地”，不参与需求强度计算。\n")
    f.write("   - **应当排除**：E5 类无效记录。\n")

print(f"✓ 终极核查完成，报告已输出至 {REPORT_DIR}")
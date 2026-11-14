from __future__ import annotations

import ast
import csv
import html
import json
import re
import sqlite3
from collections import Counter
from datetime import datetime
from pathlib import Path
from .core import normalized_text

DDL = """
CREATE TABLE IF NOT EXISTS normalizations(
 record_pk INTEGER PRIMARY KEY, heat_metrics_raw TEXT, heat_metrics TEXT,
 raw_content TEXT, cleaned_content TEXT, cleaning_actions TEXT,
 short_text_class TEXT, normalized_at TEXT,
 FOREIGN KEY(record_pk) REFERENCES records(pk));
CREATE TABLE IF NOT EXISTS annotations(
 record_pk INTEGER PRIMARY KEY, scene_primary TEXT, scene_secondary TEXT,
 source_relevance TEXT, e_type TEXT, quality_level TEXT,
 review_status TEXT NOT NULL DEFAULT 'PENDING', evidence_excerpt TEXT,
 label_reason TEXT, reviewer TEXT, reviewed_at TEXT, label_origin TEXT NOT NULL DEFAULT 'PENDING',
 CHECK(label_origin IN ('HUMAN','MACHINE','PENDING')),
 FOREIGN KEY(record_pk) REFERENCES records(pk));
"""

NULL_WORDS={"null","none","na","n/a","未知","缺失"}
NOT_PUBLIC_WORDS={"未公开","not_public","private","不可见"}
FAILED_WORDS={"抓取失败","fetch_failed","failed","error","timeout"}

def ensure(db: sqlite3.Connection): db.executescript(DDL)

def parse_heat_metrics(raw: str, platform: str) -> dict:
    """Safely parse JSON/Python literal heat data; never executes input."""
    raw=(raw or "").strip()
    if not raw: return {"parse_status":"EMPTY","platform":platform,"metrics":[]}
    value=None; mode=""
    try: value=json.loads(raw); mode="JSON"
    except (json.JSONDecodeError,TypeError):
        try: value=ast.literal_eval(raw); mode="PYTHON_LITERAL"
        except (ValueError,SyntaxError,TypeError): return {"parse_status":"FAILED","platform":platform,"metrics":[],"error":"unsupported literal"}
    if not isinstance(value,dict): return {"parse_status":"FAILED","platform":platform,"metrics":[],"error":"root is not an object"}
    metrics=[]
    for name,item in value.items():
        status="VALUE"
        normalized=item
        if item is None: status="NULL"
        elif isinstance(item,(int,float)) and not isinstance(item,bool) and item==0: status="ZERO"
        elif isinstance(item,str):
            word=item.strip().lower()
            if word in NULL_WORDS: status="NULL"; normalized=None
            elif word in NOT_PUBLIC_WORDS: status="NOT_PUBLIC"; normalized=None
            elif word in FAILED_WORDS: status="FETCH_FAILED"; normalized=None
        metrics.append({"platform":platform,"metric_name":str(name),"value":normalized,"status":status})
    return {"parse_status":"OK","source_format":mode,"platform":platform,"metrics":metrics}

def clean_content(raw: str) -> tuple[str,list[dict]]:
    """Conservative deterministic cleaning; returns text and auditable actions."""
    text=raw or ""; actions=[]
    if re.match(r"^\s*window\.webAbTest\s*=",text,re.I):
        return "",[{"action":"REMOVE_SCRIPT_ONLY_CONTENT","reason":"content begins with window.webAbTest assignment","removed_chars":len(text)}]
    before=text
    text,n=re.subn(r"<script\b[^>]*>.*?</script\s*>"," ",text,flags=re.I|re.S)
    if n: actions.append({"action":"REMOVE_SCRIPT_BLOCKS","count":n,"removed_chars":len(before)-len(text)})
    before=text; text=html.unescape(text)
    if text!=before: actions.append({"action":"DECODE_HTML_ENTITIES","changed":True})
    before=text; text,n=re.subn(r"</?[a-zA-Z][^>]*>"," ",text)
    if n: actions.append({"action":"REMOVE_HTML_TAGS","count":n,"removed_chars":len(before)-len(text)})
    kept=[]; removed=[]
    nav=re.compile(r"^(?:首页|登录|注册|打开APP|相关推荐|返回顶部|加载更多|扫码下载|关注|举报|分享)$",re.I)
    template=re.compile(r"^(?:点赞|收藏|评论|转发)\s*[:：]?\s*\d*\s*$")
    for line in re.split(r"[\r\n]+",text):
        line=line.strip()
        if not line: continue
        if nav.fullmatch(line): removed.append((line,"NAVIGATION"))
        elif template.fullmatch(line): removed.append((line,"INTERACTION_TEMPLATE"))
        else: kept.append(line)
    if removed: actions.append({"action":"REMOVE_TEMPLATE_LINES","count":len(removed),"items":[{"text":x,"type":t} for x,t in removed]})
    cleaned=re.sub(r"[ \t\u00a0]+"," ","\n".join(kept)).strip()
    if cleaned!=text.strip() and not actions: actions.append({"action":"NORMALIZE_WHITESPACE"})
    return cleaned,actions

def compact_length(text: str) -> int: return len(re.sub(r"\s+","",text or ""))

def classify_short(raw: str, cleaned: str, source: str) -> str:
    raw=(raw or "").strip(); cleaned=(cleaned or "").strip()
    if not cleaned: return "MEANINGLESS_RESIDUE"
    if re.search(r"window\.webAbTest|javascript:|^\{.*\}$",cleaned,re.I|re.S): return "PAGE_METADATA"
    if re.search(r"(?:CSDN博客|知乎专栏|北京大学|清华大学|研究院|公共服务平台)$",cleaned) or "\u00a0" in raw: return "TITLE"
    if source in {"教育论坛","Stack Exchange"} and compact_length(cleaned)>=8: return "MEANINGFUL_SHORT_COMMENT"
    if compact_length(cleaned)>=15 and re.search(r"[。！？.!?]$",cleaned): return "SUMMARY_FRAGMENT"
    if re.search(r"(?:首页|登录|注册|APP|浏览|点赞|收藏|评论|转发)",cleaned): return "PAGE_METADATA"
    return "UNDETERMINED"

def normalize_all(db: sqlite3.Connection) -> dict:
    ensure(db); rows=db.execute("SELECT pk,source_name,heat_metrics,content FROM records ORDER BY pk").fetchall(); counts=Counter(); short=Counter()
    for r in rows:
        heat=parse_heat_metrics(r["heat_metrics"],r["source_name"] or "UNKNOWN")
        cleaned,actions=clean_content(r["content"] or "")
        short_class=None
        if (r["content"] or "").strip() and len(normalized_text(r["content"] or ""))<30:
            short_class=classify_short(r["content"] or "",cleaned,r["source_name"] or "")
            short[short_class]+=1
        counts[heat["parse_status"]]+=1
        db.execute("""INSERT INTO normalizations(record_pk,heat_metrics_raw,heat_metrics,raw_content,cleaned_content,cleaning_actions,short_text_class,normalized_at)
          VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(record_pk) DO UPDATE SET heat_metrics_raw=excluded.heat_metrics_raw,heat_metrics=excluded.heat_metrics,raw_content=excluded.raw_content,cleaned_content=excluded.cleaned_content,cleaning_actions=excluded.cleaning_actions,short_text_class=excluded.short_text_class,normalized_at=excluded.normalized_at""",
          (r["pk"],r["heat_metrics"],json.dumps(heat,ensure_ascii=False,separators=(",",":")),r["content"],cleaned,json.dumps(actions,ensure_ascii=False),short_class,datetime.now().astimezone().isoformat(timespec="seconds")))
        db.execute("INSERT OR IGNORE INTO annotations(record_pk,review_status,label_origin) VALUES(?,'PENDING','PENDING')",(r["pk"],))
    for name in ("MEANINGFUL_SHORT_COMMENT","TITLE","SUMMARY_FRAGMENT","PAGE_METADATA","MEANINGLESS_RESIDUE","UNDETERMINED"): short.setdefault(name,0)
    for name in ("MEANINGFUL_SHORT_COMMENT","TITLE","SUMMARY_FRAGMENT","PAGE_METADATA","MEANINGLESS_RESIDUE","UNDETERMINED"): short.setdefault(name,0)
    db.commit(); return {"records":len(rows),"heat_parse_status":dict(counts),"short_text_threshold":"non-empty normalized_text length < 30","short_text_count":sum(short.values()),"short_classes":dict(short)}

def export_normalization(db: sqlite3.Connection, output: Path) -> dict:
    ensure(db); output.mkdir(parents=True,exist_ok=True)
    q="""SELECT r.record_id,r.batch_id,r.source_name,r.source_url,n.heat_metrics_raw,n.heat_metrics,n.raw_content,n.cleaned_content,n.cleaning_actions,n.short_text_class FROM records r JOIN normalizations n ON n.record_pk=r.pk ORDER BY r.pk"""
    rows=list(db.execute(q)); fields=rows[0].keys() if rows else []
    with (output/"normalized_records.csv").open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(dict(r) for r in rows)
    with (output/"heat_metrics_comparison.csv").open("w",encoding="utf-8-sig",newline="") as f:
        fields2=["record_id","batch_id","source_name","heat_metrics_raw","heat_metrics"]; w=csv.DictWriter(f,fieldnames=fields2); w.writeheader(); w.writerows({k:r[k] for k in fields2} for r in rows)
    with (output/"content_cleaning_comparison.csv").open("w",encoding="utf-8-sig",newline="") as f:
        fields2=["record_id","batch_id","source_name","raw_content","cleaned_content","cleaning_actions"]; w=csv.DictWriter(f,fieldnames=fields2); w.writeheader(); w.writerows({k:r[k] for k in fields2} for r in rows)
    short=[r for r in rows if r["short_text_class"]]
    with (output/"short_text_audit_185.csv").open("w",encoding="utf-8-sig",newline="") as f:
        fields2=["record_id","batch_id","source_name","raw_content","cleaned_content","short_text_class"]; w=csv.DictWriter(f,fieldnames=fields2); w.writeheader(); w.writerows({k:r[k] for k in fields2} for r in short)
    ann=list(db.execute("""SELECT r.record_id,r.batch_id,a.scene_primary,a.scene_secondary,a.source_relevance,a.e_type,a.quality_level,a.review_status,a.evidence_excerpt,a.label_reason,a.reviewer,a.reviewed_at,a.label_origin FROM records r JOIN annotations a ON a.record_pk=r.pk ORDER BY r.pk"""))
    with (output/"annotation_template.csv").open("w",encoding="utf-8-sig",newline="") as f:
        af=ann[0].keys() if ann else []; w=csv.DictWriter(f,fieldnames=af); w.writeheader(); w.writerows(dict(r) for r in ann)
    write_reports(db,output,rows)
    return {"normalized_records":len(rows),"short_text_records":len(short),"output":str(output.resolve())}

def write_reports(db: sqlite3.Connection, output: Path, rows) -> None:
    metric_status=Counter(); parse_status=Counter(); numeric_mismatches=0
    action_types=Counter(); changed=0
    for r in rows:
        heat=json.loads(r["heat_metrics"]); parse_status[heat["parse_status"]]+=1
        for metric in heat.get("metrics",[]): metric_status[metric["status"]]+=1
        try:
            original=ast.literal_eval(r["heat_metrics_raw"])
            rebuilt={m["metric_name"]:m["value"] for m in heat.get("metrics",[])}
            for key,value in original.items():
                if isinstance(value,(int,float)) and not isinstance(value,bool) and rebuilt.get(str(key))!=value: numeric_mismatches+=1
        except Exception: pass
        actions=json.loads(r["cleaning_actions"] or "[]")
        if r["raw_content"]!=r["cleaned_content"]: changed+=1
        for action in actions: action_types[action["action"]]+=1
    for key in ("VALUE","ZERO","NULL","NOT_PUBLIC","FETCH_FAILED"): metric_status.setdefault(key,0)
    heat_report=f"""# 热度字段规范化报告\n\n- 记录数：{len(rows)}\n- 安全解析状态：`{json.dumps(dict(parse_status),ensure_ascii=False)}`\n- 指标值状态：`{json.dumps(dict(metric_status),ensure_ascii=False)}`\n- 原始数值与规范化数值不一致：{numeric_mismatches}\n- `ZERO` 表示真实数值 0；`NULL` 表示原值 `None/null`；`NOT_PUBLIC` 与 `FETCH_FAILED` 仅在原文明确表达时使用，不从 `None` 猜测。\n- 原始文本保存在 `heat_metrics_raw`；标准 JSON 保存在 `heat_metrics`，每个指标均包含平台、指标名、值和状态。\n"""
    (output/"heat_metrics_normalization_report.md").write_text(heat_report,encoding="utf-8")
    clean_report=f"""# 正文清洗报告\n\n- 总记录数：{len(rows)}\n- 清洗前后发生变化：{changed}\n- 清理动作：`{json.dumps(dict(action_types),ensure_ascii=False)}`\n- 清洗为确定性保守规则；原始正文保存在 `raw_content`，结果保存在 `cleaned_content`，动作保存在 `cleaning_actions`。\n- 未使用 AI 补写；未覆盖输入 CSV；未自动删除任何记录。\n"""
    template_flagged=db.execute("SELECT COUNT(DISTINCT record_pk) FROM issues WHERE issue_type='TEMPLATE_POLLUTION'").fetchone()[0]
    clean_report += f"- 审计标记的页面互动模板记录：{template_flagged}；仅删除独立模板行，嵌入自然语言的词语保留待人工复核，避免误删用户表达。\n"
    (output/"content_cleaning_report.md").write_text(clean_report,encoding="utf-8")
    rel=list(db.execute("""SELECT x.*,a.content left_raw,b.content right_raw,n1.cleaned_content left_clean,n2.cleaned_content right_clean FROM duplicate_relations x JOIN records a ON a.pk=x.left_pk JOIN records b ON b.pk=x.right_pk LEFT JOIN normalizations n1 ON n1.record_pk=a.pk LEFT JOIN normalizations n2 ON n2.record_pk=b.pk"""))
    original=[r for r in rel if "cleaned" not in r["run_id"]]; cleaned=[r for r in rel if "cleaned" in r["run_id"]]
    with (output/"dedup_cleaned_candidates.csv").open("w",encoding="utf-8-sig",newline="") as f:
        fields=["left_record_id","right_record_id","duplicate_type","score","evidence","confirmation_status","left_cleaned_content","right_cleaned_content"]
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
        for r in cleaned:
            left_id=db.execute("SELECT record_id FROM records WHERE pk=?",(r["left_pk"],)).fetchone()[0]; right_id=db.execute("SELECT record_id FROM records WHERE pk=?",(r["right_pk"],)).fetchone()[0]
            w.writerow({"left_record_id":left_id,"right_record_id":right_id,"duplicate_type":r["duplicate_type"],"score":r["score"],"evidence":r["evidence"],"confirmation_status":r["confirmation_status"],"left_cleaned_content":r["left_clean"],"right_cleaned_content":r["right_clean"]})
    polluted_before=sum("window.webAbTest" in (r["left_raw"] or "") or "window.webAbTest" in (r["right_raw"] or "") for r in original)
    polluted_after=sum("window.webAbTest" in (r["left_clean"] or "") or "window.webAbTest" in (r["right_clean"] or "") for r in cleaned)
    dedup_report=f"""# 去重清洗前后对比\n\n| 指标 | 清洗前 | 清洗后 |\n| --- | ---: | ---: |\n| 候选关系 | {len(original)} | {len(cleaned)} |\n| 脚本污染相关候选 | {polluted_before} | {polluted_after} |\n| URL 精确重复 | {sum(r['duplicate_type']=='URL_EXACT' for r in original)} | {sum(r['duplicate_type']=='URL_EXACT' for r in cleaned)} |\n| 正文 SHA256 重复 | {sum(r['duplicate_type']=='CONTENT_SHA256' for r in original)} | {sum(r['duplicate_type']=='CONTENT_SHA256' for r in cleaned)} |\n| 近似文本候选 | {sum(r['duplicate_type']=='TEXT_SIMILAR' for r in original)} | {sum(r['duplicate_type']=='TEXT_SIMILAR' for r in cleaned)} |\n| 转载候选 | {sum(r['duplicate_type']=='REPRINT_CANDIDATE' for r in original)} | {sum(r['duplicate_type']=='REPRINT_CANDIDATE' for r in cleaned)} |\n\n所有关系均为 `PENDING`，不自动删除记录；不同用户表达不会因为主题相同而合并。\n"""
    (output/"dedup_before_after_report.md").write_text(dedup_report,encoding="utf-8")

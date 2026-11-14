from __future__ import annotations

import csv
import hashlib
import html
import json
import re
import sqlite3
import time
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

SCENES = {"S1", "S2", "S3", "S4"}
E_TYPES = {"E1", "E2", "E3", "E4", "E5"}
QUALITY = {"Q0", "Q1", "Q2", "Q3", "Q4"}
OFFICIAL_FIELDS = ["record_id", "source_name", "source_url", "published_at", "content", "scene_primary", "e_type"]
INTERNAL_FIELDS = ["batch_id", "original_source_url", "collected_at", "raw_content", "content_status", "content_type", "content_hash", "duplicate_group", "heat_metrics", "scene_secondary", "quality_level", "review_status", "review_reason"]
ALIASES = {
    "record_id": ["record_id", "id", "原始编号", "记录编号", "编号", "序号"],
    "batch_id": ["batch_id", "batch", "采集批次号", "批次号", "批次"],
    "source_name": ["source_name", "source", "来源网站名称", "来源名称", "来源", "平台", "网站"],
    "source_url": ["source_url", "url", "来源链接", "链接", "网址"],
    "original_source_url": ["original_source_url", "origin_url", "原始来源", "原文链接"],
    "published_at": ["published_at", "publish_time", "发布时间", "发布日期"],
    "collected_at": ["collected_at", "collect_time", "采集时间"],
    "content": ["content", "text", "正文", "内容", "摘要"],
    "raw_content": ["raw_content", "raw", "原始正文"],
    "content_status": ["content_status", "正文状态"],
    "content_type": ["content_type", "内容类型"],
    "heat_metrics": ["heat_metrics", "heat", "热度指标（点赞数、评论数、收藏数、转发量等）", "热度指标", "热度", "互动量"],
    "scene_primary": ["scene_primary", "scene", "一级场景", "场景"],
    "scene_secondary": ["scene_secondary", "二级场景"],
    "e_type": ["e_type", "evidence_type", "证据类型"],
    "quality_level": ["quality_level", "quality", "证据质量"],
    "review_status": ["review_status", "审核状态", "标注状态"],
    "review_reason": ["review_reason", "审核原因", "备注"],
}

DDL = """
CREATE TABLE IF NOT EXISTS imports(import_id INTEGER PRIMARY KEY, file_path TEXT, file_hash TEXT UNIQUE, batch_id TEXT, imported_at TEXT, raw_rows INTEGER, success_rows INTEGER, invalid_rows INTEGER, duplicate_rows INTEGER, missing_fields INTEGER);
CREATE TABLE IF NOT EXISTS records(pk INTEGER PRIMARY KEY, import_id INTEGER, source_row INTEGER, record_id TEXT, original_record_id TEXT, batch_id TEXT, source_name TEXT, source_url TEXT, normalized_url TEXT, original_source_url TEXT, published_at TEXT, collected_at TEXT, content TEXT, raw_content TEXT, content_status TEXT, content_type TEXT, content_hash TEXT, duplicate_group TEXT, heat_metrics TEXT, scene_primary TEXT, scene_secondary TEXT, e_type TEXT, quality_level TEXT, review_status TEXT, review_reason TEXT, label_origin TEXT, raw_json TEXT, UNIQUE(import_id, source_row));
CREATE INDEX IF NOT EXISTS idx_records_record_id ON records(record_id);
CREATE INDEX IF NOT EXISTS idx_records_url ON records(normalized_url);
CREATE INDEX IF NOT EXISTS idx_records_hash ON records(content_hash);
CREATE TABLE IF NOT EXISTS issues(issue_id INTEGER PRIMARY KEY, record_pk INTEGER, record_id TEXT, issue_type TEXT, severity TEXT, reason TEXT, suggestion TEXT, run_id TEXT, UNIQUE(record_pk, issue_type, run_id));
CREATE TABLE IF NOT EXISTS duplicate_relations(relation_id INTEGER PRIMARY KEY, left_pk INTEGER, right_pk INTEGER, master_pk INTEGER, duplicate_type TEXT, score REAL, evidence TEXT, duplicate_group TEXT, confirmation_status TEXT DEFAULT 'PENDING', run_id TEXT, UNIQUE(left_pk,right_pk,duplicate_type,run_id));
CREATE TABLE IF NOT EXISTS runs(run_id TEXT PRIMARY KEY, command TEXT, started_at TEXT, finished_at TEXT, status TEXT, details TEXT);
"""

def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row
    db.executescript(DDL)
    columns={r[1] for r in db.execute("PRAGMA table_info(duplicate_relations)")}
    if "master_pk" not in columns: db.execute("ALTER TABLE duplicate_relations ADD COLUMN master_pk INTEGER")
    return db

def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def clean_text(value) -> str:
    if value is None: return ""
    return str(value).strip()

def normalized_text(value: str) -> str:
    value = html.unescape(clean_text(value))
    value = unicodedata.normalize("NFKC", value).lower()
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", "", value)

def normalize_url(value: str) -> str:
    value = clean_text(value)
    if not value: return ""
    try:
        p = urlsplit(value if "://" in value else "https://" + value)
        if not p.netloc: return ""
        query = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True) if not k.lower().startswith(("utm_", "spm", "from"))]
        return urlunsplit((p.scheme.lower(), p.netloc.lower(), p.path.rstrip("/") or "/", urlencode(query), ""))
    except ValueError:
        return ""

def content_hash(content: str) -> str:
    text = normalized_text(content)
    return hashlib.sha256(text.encode("utf-8")).hexdigest() if text else ""

def infer_batch(path: Path, supplied: str | None) -> str:
    if supplied: return supplied.upper()
    match = re.search(r"\bB\d+\b", path.stem, re.I)
    return match.group(0).upper() if match else "UNKNOWN"

def choose(row: dict, key: str) -> str:
    lower = {clean_text(k).lower(): v for k, v in row.items()}
    for alias in ALIASES[key]:
        if alias.lower() in lower and clean_text(lower[alias.lower()]): return clean_text(lower[alias.lower()])
    return ""

def read_rows(path: Path):
    if path.suffix.lower() == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            yield from csv.DictReader(f)
    elif path.suffix.lower() in {".jsonl", ".ndjson"}:
        with path.open("r", encoding="utf-8-sig") as f:
            for line in f:
                if line.strip():
                    try: yield json.loads(line)
                    except json.JSONDecodeError: yield None
    else: raise ValueError("仅支持 CSV、JSONL/NDJSON")

def import_file(db: sqlite3.Connection, path: Path, batch: str | None = None) -> dict:
    path = path.resolve(); digest = file_sha256(path); batch_id = infer_batch(path, batch)
    previous = db.execute("SELECT * FROM imports WHERE file_hash=?", (digest,)).fetchone()
    if previous: return {**dict(previous), "protected": True}
    stats = dict(raw_rows=0, success_rows=0, invalid_rows=0, duplicate_rows=0, missing_fields=0)
    cur = db.execute("INSERT INTO imports(file_path,file_hash,batch_id,imported_at,raw_rows,success_rows,invalid_rows,duplicate_rows,missing_fields) VALUES(?,?,?,?,0,0,0,0,0)", (str(path), digest, batch_id, now()))
    import_id = cur.lastrowid
    try:
        for line_no, row in enumerate(read_rows(path), 2 if path.suffix.lower() == ".csv" else 1):
            stats["raw_rows"] += 1
            if not isinstance(row, dict): stats["invalid_rows"] += 1; continue
            original_id = choose(row, "record_id")
            rid = original_id or f"{batch_id}-{line_no}"
            values = {k: choose(row, k) for k in ALIASES}
            missing = sum(not values[k] for k in OFFICIAL_FIELDS if k not in {"scene_primary", "e_type"})
            stats["missing_fields"] += missing
            content = values["content"]; raw = values["raw_content"] or content
            nurl = normalize_url(values["source_url"])
            chash = content_hash(content)
            row_batch = values["batch_id"].upper() or batch_id
            exists = db.execute("SELECT 1 FROM records WHERE record_id=? AND batch_id=?", (rid, row_batch)).fetchone()
            if exists: stats["duplicate_rows"] += 1
            status = values["review_status"].upper()
            label_origin = "HUMAN" if status in {"HUMAN_CONFIRMED", "CONFIRMED", "APPROVED", "人工确认", "已审核"} else ("MACHINE" if status == "MACHINE_PRECLASSIFIED" or values["scene_primary"] or values["e_type"] else "UNCLASSIFIED")
            db.execute("""INSERT INTO records(import_id,source_row,record_id,original_record_id,batch_id,source_name,source_url,normalized_url,original_source_url,published_at,collected_at,content,raw_content,content_status,content_type,content_hash,heat_metrics,scene_primary,scene_secondary,e_type,quality_level,review_status,review_reason,label_origin,raw_json) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (import_id,line_no,rid,original_id,row_batch,values["source_name"],values["source_url"],nurl,values["original_source_url"],values["published_at"],values["collected_at"],content,raw,values["content_status"],values["content_type"],chash,values["heat_metrics"],values["scene_primary"],values["scene_secondary"],values["e_type"],values["quality_level"],values["review_status"],values["review_reason"],label_origin,json.dumps(row, ensure_ascii=False, default=str)))
            stats["success_rows"] += 1
        db.execute("UPDATE imports SET raw_rows=?,success_rows=?,invalid_rows=?,duplicate_rows=?,missing_fields=? WHERE import_id=?", (*stats.values(), import_id))
        db.commit()
    except Exception:
        db.rollback(); raise
    return {"import_id": import_id, "file_path": str(path), "file_hash": digest, "batch_id": batch_id, **stats, "protected": False}

def parse_date(value: str):
    if not value: return None
    try: return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError: return None

def audit(db: sqlite3.Connection, batch: str | None = None) -> dict:
    run_id = "audit-" + datetime.now().strftime("%Y%m%d%H%M%S%f")
    rows = db.execute("SELECT * FROM records" + (" WHERE batch_id=?" if batch else ""), ((batch.upper(),) if batch else ())).fetchall()
    issue_defs = []
    def add(r, kind, severity, reason, suggestion): issue_defs.append((r["pk"], r["record_id"], kind, severity, reason, suggestion, run_id))
    for r in rows:
        content = clean_text(r["content"]); normalized = normalized_text(content)
        if not content: add(r,"EMPTY_CONTENT","ERROR","正文为空","回到原页面重新采集；不可用 AI 补写")
        elif len(normalized) < 30: add(r,"SHORT_CONTENT","WARNING",f"规范化正文仅 {len(normalized)} 字符","人工检查正文获取状态；只标记不删除")
        title = ""
        try: title = clean_text(json.loads(r["raw_json"]).get("title", ""))
        except Exception: pass
        if title and normalized == normalized_text(title): add(r,"TITLE_ONLY","WARNING","正文与标题完全相同","重新提取正文或标记为仅标题")
        if re.search(r"&(?:nbsp|amp|lt|gt|quot|#\d+);", content, re.I): add(r,"HTML_ENTITY","WARNING","存在 HTML 实体残留","执行实体解码后复核")
        if re.search(r"</?[a-z][^>]*>", content, re.I): add(r,"HTML_TAG","WARNING","存在 HTML 标签残留","使用正文提取器清理标签")
        if re.search(r"<script|javascript:|function\s*\(|window\.|document\.|__NEXT_DATA__", content, re.I): add(r,"SCRIPT_RESIDUE","ERROR","存在 JavaScript/网页脚本残留","重新进行正文抽取并保留原快照")
        if re.search(r"window\.webAbTest", content, re.I): add(r,"WINDOW_WEBABTEST","ERROR","存在 window.webAbTest 网页脚本残留","重新提取正文，不得用 AI 补写")
        if len(content) > 10000: add(r,"OVERSIZED_CONTENT","WARNING",f"正文长度 {len(content)}，可能是超长 Issue 或页面整体抓取","人工检查正文边界，不自动截断")
        if re.search(r"点赞\s*\d*|收藏\s*\d*|评论\s*\d*|相关推荐|打开APP", content): add(r,"TEMPLATE_POLLUTION","WARNING","疑似页面互动或模板文本污染","清洗模板噪声并人工抽查")
        if not r["source_url"] or not r["normalized_url"]: add(r,"INVALID_URL","ERROR","URL 缺失或无法规范化","补录可追溯来源 URL")
        if re.search(r"news\.google\.com/(?:rss/)?articles/", r["source_url"] or "", re.I): add(r,"GOOGLE_NEWS_REDIRECT","WARNING","来源为 Google News 跳转链接，非最终原文 URL","解析并保存最终来源，同时保留原跳转链接")
        if not r["collected_at"]: add(r,"MISSING_COLLECTED_AT","WARNING","采集时间缺失","从批次日志或文件元数据补录")
        elif not parse_date(r["collected_at"]): add(r,"ABNORMAL_COLLECTED_AT","WARNING","采集时间无法解析","核对原始采集日志，不自动推测")
        if r["published_at"]:
            pd = parse_date(r["published_at"])
            if not pd or pd.year < 1990 or pd.year > datetime.now().year + 1: add(r,"ABNORMAL_PUBLISHED_AT","WARNING","发布时间无法解析或超出合理范围","核对原页面发布时间")
        if r["original_source_url"] and not normalize_url(r["original_source_url"]): add(r,"UNRESOLVED_ORIGINAL_SOURCE","WARNING","原始来源无法解析","人工核对转载来源")
        if not r["heat_metrics"]: add(r,"MISSING_HEAT_METRICS","INFO","热度指标缺失","保留缺失状态，不推测热度")
        else:
            try: json.loads(r["heat_metrics"])
            except Exception: add(r,"INVALID_HEAT_METRICS","WARNING","热度字段不是合法 JSON","转换为 JSON 对象并保留原值")
    for col, kind in (("normalized_url","DUPLICATE_URL"),("content_hash","DUPLICATE_CONTENT_HASH")):
        groups = defaultdict(list)
        for r in rows:
            if r[col]: groups[r[col]].append(r)
        for key, group in groups.items():
            if len(group) > 1:
                for r in group: add(r,kind,"WARNING",f"{col} 与另外 {len(group)-1} 条记录相同","运行 deduplicate 建立关系，人工决定主记录")
    db.executemany("INSERT INTO issues(record_pk,record_id,issue_type,severity,reason,suggestion,run_id) VALUES(?,?,?,?,?,?,?)", issue_defs)
    db.commit()
    return {"run_id": run_id, "records_checked": len(rows), "issues": len(issue_defs), "by_type": dict(Counter(x[2] for x in issue_defs))}

def ngrams(text: str, n=3):
    text = normalized_text(text)
    return {text[i:i+n] for i in range(max(0, len(text)-n+1))}

def deduplicate(db: sqlite3.Connection, threshold: float = .82, content_source: str = "original") -> dict:
    if content_source not in {"original","cleaned"}: raise ValueError("content_source 必须是 original 或 cleaned")
    if content_source == "cleaned":
        rows=db.execute("SELECT r.*,n.cleaned_content AS dedup_content FROM records r JOIN normalizations n ON n.record_pk=r.pk ORDER BY r.pk").fetchall()
    else: rows=db.execute("SELECT r.*,r.content AS dedup_content FROM records r ORDER BY r.pk").fetchall()
    run_id = f"dedup-{content_source}-" + datetime.now().strftime("%Y%m%d%H%M%S%f"); pairs = {}
    def relation(a,b,kind,score,evidence):
        key=(min(a["pk"],b["pk"]),max(a["pk"],b["pk"]),kind); pairs[key]=(a,b,kind,score,evidence)
    for col, kind in (("normalized_url","URL_EXACT"),):
        groups=defaultdict(list)
        for r in rows:
            if r[col]: groups[r[col]].append(r)
        for value, group in groups.items():
            for i in range(len(group)):
                for j in range(i+1,len(group)): relation(group[i],group[j],kind,1.0,f"{col}={value}")
    hash_groups=defaultdict(list)
    for r in rows:
        digest=content_hash(r["dedup_content"])
        if digest: hash_groups[digest].append(r)
    for value,group in hash_groups.items():
        for i in range(len(group)):
            for j in range(i+1,len(group)): relation(group[i],group[j],"CONTENT_SHA256",1.0,f"cleaned_content_hash={value}")
    buckets=defaultdict(list); grams={}; normalized_cache={}
    for r in rows:
        text=normalized_text(r["dedup_content"])
        if len(text)>=30:
            grams[r["pk"]]=ngrams(text); normalized_cache[r["pk"]]=text
            middle=max(0,len(text)//2-6)
            for key in {text[:12], text[middle:middle+12], text[-12:]}: buckets[key].append(r)
    candidate_sets=[]
    for group in buckets.values():
        if len(group)<=300: candidate_sets.append(group)
        else:
            # 超大同质桶采用规范化文本排序后的局部窗口，避免 O(n²) 退化。
            ordered=sorted(group,key=lambda r:normalized_cache[r["pk"]])
            for i in range(len(ordered)): candidate_sets.append(ordered[i+1:i+11]+[ordered[i]])
    seen=set()
    for group in candidate_sets:
        for i in range(len(group)):
            for j in range(i+1,len(group)):
                a,b=group[i],group[j]; key=(a["pk"],b["pk"])
                if key in seen: continue
                seen.add(key); ga,gb=grams[a["pk"]],grams[b["pk"]]; score=len(ga&gb)/max(1,len(ga|gb))
                if score>=threshold and a["content_hash"]!=b["content_hash"]: relation(a,b,"TEXT_SIMILAR",score,f"char-3gram Jaccard={score:.4f}")
                if score>=.65 and (a["source_name"]!=b["source_name"] or a["original_source_url"] or b["original_source_url"]): relation(a,b,"REPRINT_CANDIDATE",score,"跨来源且文本高度重合/含原始来源字段")
    for a,b,kind,score,evidence in pairs.values():
        group="DG-"+hashlib.sha1(f"{min(a['pk'],b['pk'])}-{max(a['pk'],b['pk'])}".encode()).hexdigest()[:10]
        left=min(a["pk"],b["pk"]); right=max(a["pk"],b["pk"])
        db.execute("INSERT INTO duplicate_relations(left_pk,right_pk,master_pk,duplicate_type,score,evidence,duplicate_group,confirmation_status,run_id) VALUES(?,?,?,?,?,?,?,'PENDING',?)", (left,right,left,kind,score,evidence,group,run_id))
        db.execute("UPDATE records SET duplicate_group=COALESCE(duplicate_group,?) WHERE pk IN (?,?)",(group,a["pk"],b["pk"]))
    db.commit(); return {"run_id":run_id,"content_source":content_source,"records_checked":len(rows),"candidate_relations":len(pairs),"by_type":dict(Counter(v[2] for v in pairs.values()))}

def pct(n,d): return round(100*n/d,2) if d else 0.0

def analyze(db: sqlite3.Connection) -> dict:
    rows=db.execute("SELECT * FROM records").fetchall(); total=len(rows)
    latest_issue={r["record_pk"] for r in db.execute("SELECT record_pk FROM issues WHERE severity='ERROR'")}
    dupe={r["left_pk"] for r in db.execute("SELECT left_pk FROM duplicate_relations")} | {r["right_pk"] for r in db.execute("SELECT right_pk FROM duplicate_relations")}
    def distribution(field, allowed=None):
        c=Counter((clean_text(r[field]) or "UNCLASSIFIED") for r in rows)
        if allowed:
            for x in allowed: c.setdefault(x,0)
        return dict(sorted(c.items()))
    sources={}
    for source,group in _groups(rows,"source_name").items():
        sources[source]={"count":len(group),"complete_rate":pct(sum(bool(r["content"]) and len(normalized_text(r["content"]))>=30 for r in group),len(group)),"valid_rate":pct(sum(r["pk"] not in latest_issue for r in group),len(group)),"duplicate_rate":pct(sum(r["pk"] in dupe for r in group),len(group))}
    batches={}
    for b,g in _groups(rows,"batch_id").items(): batches[b]={"count":len(g),"valid_rate":pct(sum(r["pk"] not in latest_issue for r in g),len(g)),"exception_rate":pct(sum(r["pk"] in latest_issue for r in g),len(g)),"sources":dict(Counter(r["source_name"] or "UNKNOWN" for r in g))}
    scene_details={}
    for scene in sorted(SCENES):
        group=[r for r in rows if r["scene_primary"]==scene]
        scene_details[scene]={"count":len(group),"coverage_rate":pct(len(group),total),"quality":dict(Counter(r["quality_level"] or "UNCLASSIFIED" for r in group)),"sources":dict(Counter(r["source_name"] or "UNKNOWN" for r in group)),"label_origin":dict(Counter(r["label_origin"] for r in group))}
    return {"generated_at":now(),"total_records":total,"sources":sources,"scenes":distribution("scene_primary",SCENES),"scene_details":scene_details,"evidence_types":distribution("e_type",E_TYPES),"quality_levels":distribution("quality_level",QUALITY),"review_status":distribution("review_status"),"label_origin":distribution("label_origin"),"content_status":distribution("content_status"),"batches":batches}

def _groups(rows, field):
    out=defaultdict(list)
    for r in rows: out[clean_text(r[field]) or "UNKNOWN"].append(r)
    return out

def report(db: sqlite3.Connection, output: Path) -> dict:
    output.mkdir(parents=True,exist_ok=True); data=analyze(db)
    def write(name,title,body): (output/name).write_text(f"# {title}\n\n生成时间：{data['generated_at']}\n\n{body}\n",encoding="utf-8")
    write("00_overview.md","EduMine 数据概览",f"- 记录总数：{data['total_records']}\n- 来源数：{len(data['sources'])}\n- 批次数：{len(data['batches'])}\n- 人工/机器/未分类：`{json.dumps(data['label_origin'],ensure_ascii=False)}`")
    imports=[dict(r) for r in db.execute("SELECT * FROM imports ORDER BY import_id")]
    write("01_import_audit.md","导入审计","```json\n"+json.dumps(imports,ensure_ascii=False,indent=2)+"\n```")
    issue_counts=dict(Counter(r[0] for r in db.execute("SELECT issue_type FROM issues")))
    write("02_content_quality.md","正文质量审计","```json\n"+json.dumps(issue_counts,ensure_ascii=False,indent=2)+"\n```")
    dcounts=dict(Counter(r[0] for r in db.execute("SELECT duplicate_type FROM duplicate_relations")))
    write("03_duplicate_audit.md","重复审计","候选关系均需人工确认。\n\n```json\n"+json.dumps(dcounts,ensure_ascii=False,indent=2)+"\n```")
    write("04_source_distribution.md","来源分布","```json\n"+json.dumps(data["sources"],ensure_ascii=False,indent=2)+"\n```")
    write("05_scene_distribution.md","场景分布","人工标注、机器预分类和尚未分类分开统计。\n\n```json\n"+json.dumps({"distribution":data["scenes"],"details":data["scene_details"]},ensure_ascii=False,indent=2)+"\n```")
    write("06_evidence_distribution.md","证据分布","```json\n"+json.dumps({k:data[k] for k in ("evidence_types","quality_levels","review_status","label_origin")},ensure_ascii=False,indent=2)+"\n```")
    write("07_batch_comparison.md","批次对比","```json\n"+json.dumps(data["batches"],ensure_ascii=False,indent=2)+"\n```")
    with (output/"08_exception_records.csv").open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.writer(f); w.writerow(["record_id","issue_type","severity","reason","suggestion","run_id"])
        w.writerows(db.execute("SELECT record_id,issue_type,severity,reason,suggestion,run_id FROM issues ORDER BY issue_id"))
    (output/"analysis.json").write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
    return {"output":str(output.resolve()),"files":9,"total_records":data["total_records"]}

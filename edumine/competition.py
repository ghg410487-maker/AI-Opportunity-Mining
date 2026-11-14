"""Competition Tasks 2-5 minimal, traceable and dependency-free pipeline."""
from __future__ import annotations

import ast
import csv
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

from .baselines import TfidfVectorizerLite, kmeans_sparse, normalize_text, t0_rule_predict

FUNCTION_LABELS=("图像识别","语义分析","语音处理","文本生成","对话问答","推荐系统","知识检索","数据挖掘","多模态融合","智能体编排","自动化流程","预测分析","审核审查","搜索匹配","翻译转写","视频理解")
INDUSTRY_LABELS=("金融","教育","医疗","法律","电商","零售","房地产","制造","物流","游戏","餐饮","农业","政务","汽车","家居","交通","能源","通信","娱乐","体育","旅游","保险","建筑","环保","科研","人力资源","媒体出版","营销广告","外贸","其他")
RESULT2_HEADER=("采集批次号","记录编号","是否构成机会","机会置信度","功能类别","所属行业")
RESULT3_HEADER=("采集批次号","主题簇编号","主题簇名称","功能类别","所属行业","簇内机会记录数","来源网站数","簇内机会记录编号")
RESULT4_HEADER=("采集批次号","主题簇编号","主题簇名称","功能类别","所属行业","机会价值分","优先级")

SENTENCE_SPLIT=re.compile(r"(?<=[。！？!?；;])|\n+")
USERS=("教师","老师","学生","家长","教务","学校","高校","培训机构","研究人员","开发者","用户","管理员")
TASK_WORDS=("教学","学习","备课","批改","评价","考试","测验","练习","辅导","管理","生成","推荐","识别","分析","检索","答疑","实验","培训")
PAIN_WORDS=("痛点","困难","耗时","效率低","不足","问题","无法","缺少","压力","危险","成本高","冲突","繁琐","滞后","负担","不准确","不方便")
SOLUTION_WORDS=("系统","平台","工具","产品","软件","模型","助手","智能体","方案","项目","应用")
AI_WORDS=("人工智能","ai","大模型","llm","gpt","智能体","机器学习","深度学习","自然语言","计算机视觉","推荐算法")
UNMET_WORDS=("未满足","仍然","缺少","无法","不足","痛点","急需","希望","需要","亟待","困扰","负担")
EXTRACTION_FIELDS=("record_id","source_id","source_name","source_url","user","task","pain","existing_solution","evidence_excerpt","extraction_method","llm_used","validation_status")

def load_result1(path):
    with Path(path).open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))

def _sentences(text):
    return [x.strip() for x in SENTENCE_SPLIT.split(text or "") if x.strip()]

def _first_matching(sentences,words):
    return next((s for s in sentences if any(w.lower() in s.lower() for w in words)),"")

def _user_text(text):
    low=(text or "").lower(); found=[u for u in USERS if u.lower() in low]
    return "、".join(found[:4]) if found else "未明确"

def extract_need(record):
    text=record["内容"] or ""; sentences=_sentences(text); low=text.lower()
    users=[u for u in USERS if u.lower() in low]
    task=_first_matching(sentences,TASK_WORDS)
    pain=_first_matching(sentences,PAIN_WORDS)
    existing=_first_matching(sentences,SOLUTION_WORDS)
    evidence=pain or task or (sentences[0] if sentences else text)
    return {"record_id":record["记录编号"],"source_id":record["记录编号"],"source_name":record["来源网站名称"],"source_url":record["来源链接"],"user":"、".join(users[:4]) if users else "未明确","task":task[:240],"pain":pain[:240],"existing_solution":existing[:240],"evidence_excerpt":evidence[:320],"extraction_method":"RULE_V1","llm_used":False,"validation_status":"PASS" if evidence else "EMPTY_EVIDENCE"}

def validate_extraction(value,record):
    missing=[k for k in EXTRACTION_FIELDS if k not in value]
    if missing:return False,f"missing_fields={missing}"
    if value["record_id"]!=record["记录编号"] or value["source_id"]!=record["记录编号"]:return False,"record_id_mismatch"
    evidence=value.get("evidence_excerpt") or ""
    if evidence and evidence not in (record.get("内容") or ""):return False,"evidence_not_in_source"
    return True,"PASS"

class CachedNeedExtractor:
    """Rule-first extractor with an optional validated and cached LLM fallback.

    llm_callable is deliberately dependency-injected. The baseline run passes None,
    so it makes zero network/API calls. A future caller may supply a function that
    accepts a record and returns a dict; only schema-valid, source-grounded results
    are accepted and cached.
    """
    def __init__(self,cache_path,llm_callable=None):
        self.cache_path=Path(cache_path); self.llm_callable=llm_callable; self.cache={}
        if self.cache_path.exists():
            for line in self.cache_path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    obj=json.loads(line); self.cache[obj["cache_key"]]=obj["value"]

    def extract(self,record):
        rule=extract_need(record); ok,_=validate_extraction(rule,record)
        needs_fallback=(not ok) or (not rule["task"] and not rule["pain"] and len(record.get("内容", ""))>=30)
        if not needs_fallback or self.llm_callable is None:return rule
        key=hashlib.sha256((record["记录编号"]+"\n"+record.get("内容","")).encode("utf-8")).hexdigest()
        if key in self.cache:return self.cache[key]
        candidate=self.llm_callable(record); candidate.update(record_id=record["记录编号"],source_id=record["记录编号"],source_name=record["来源网站名称"],source_url=record["来源链接"],extraction_method="LLM_FALLBACK_V1",llm_used=True)
        valid,reason=validate_extraction(candidate,record)
        if not valid:return {**rule,"validation_status":"LLM_REJECTED:"+reason}
        candidate["validation_status"]="PASS"
        self.cache_path.parent.mkdir(parents=True,exist_ok=True)
        with self.cache_path.open("a",encoding="utf-8") as f:f.write(json.dumps({"cache_key":key,"value":candidate},ensure_ascii=False)+"\n")
        self.cache[key]=candidate; return candidate

def _function_label(text):
    rules=[("图像识别",("图像","图片","视觉","拍照","ocr")),("语音处理",("语音","口语","音频")),("文本生成",("生成","写作","教案","作文")),("对话问答",("问答","答疑","聊天","助手","tutor")),("推荐系统",("推荐","个性化","精准匹配")),("知识检索",("检索","搜索","知识库")),("数据挖掘",("数据挖掘","学情分析","数据分析")),("多模态融合",("多模态","图文","视频和文本")),("智能体编排",("智能体","agent")),("自动化流程",("自动","批改","排课","流程")),("预测分析",("预测","预警")),("审核审查",("审核","审查","评分","评价")),("搜索匹配",("匹配","选课")),("翻译转写",("翻译","转写")),("视频理解",("视频理解","视频分析")),("语义分析",("语义","文本分析","自然语言"))]
    low=text.lower()
    for label,words in rules:
        if any(w in low for w in words):return label
    return "语义分析"

def judge_task2(record,extraction):
    text=record["内容"] or ""; low=text.lower(); t0=t0_rule_predict(text)
    education={"EDUCATION_DIRECT":2,"EDUCATION_WEAK":1,"NON_EDUCATION":0,"UNKNOWN":0}[t0]
    problem=2 if extraction["pain"] and extraction["task"] else (1 if extraction["task"] else 0)
    direct_demand=any(x in low for x in ("我希望","我们需要","希望能够","急需","困扰","负担","用户反馈","老师希望","学生需要","家长希望"))
    demand=2 if direct_demand else (1 if extraction["pain"] and extraction["user"]!="未明确" else 0)
    ai_hits=sum(w in low for w in AI_WORDS); ai_core=2 if ai_hits and extraction["task"] else (1 if ai_hits else 0)
    feasible=2 if ai_hits and extraction["existing_solution"] else (1 if ai_hits or extraction["existing_solution"] else 0)
    unmet=2 if any(w in low for w in UNMET_WORDS) and extraction["pain"] else (1 if extraction["pain"] else 0)
    scores={"education_relevance":education,"problem_clarity":problem,"demand_authenticity":demand,"ai_core":ai_core,"feasibility":feasible,"unmet_degree":unmet}
    if education==0 or (demand==0 and ai_core==0):status="0"
    elif min(problem,demand,ai_core,feasible,unmet)>=1 and sum(scores.values())>=8:status="1"
    else:status="REVIEW"
    decisive=sum(v in (0,2) for v in scores.values())/6
    confidence=round(.55+.4*decisive,4)
    return {"t0_label":t0,"dimension_scores":scores,"opportunity_status":status,"opportunity_confidence":confidence,"function_category":_function_label(text) if status=="1" else "","industry":"教育" if status=="1" else "","decision_version":"task2_rule_v1","decision_reason":f"六维得分={scores}；T0仅作教育相关性门控，不代表真实机会。"}

def _parse_heat(raw):
    try:
        obj=ast.literal_eval(raw) if raw else {}
        vals=[float(v) for v in obj.values() if isinstance(v,(int,float)) and v>=0]
        return sum(math.log1p(v) for v in vals)
    except Exception:return 0.0

def run_tasks_2_to_5(records, output_dir):
    output_dir=Path(output_dir); output_dir.mkdir(parents=True,exist_ok=True)
    extractor=CachedNeedExtractor(output_dir/"extraction_cache.jsonl",llm_callable=None)
    internal=[]; extracts=[]
    for r in records:
        e=extractor.extract(r); d=judge_task2(r,e); extracts.append(e)
        internal.append({"batch_id":r["采集批次号"],"record_id":r["记录编号"],"source_name":r["来源网站名称"],"source_url":r["来源链接"],"content":r["内容"],"heat_raw":r["热度指标（点赞数、评论数、收藏数、转发量等）"],**d})
    with (output_dir/"task2_extractions_1984.jsonl").open("w",encoding="utf-8") as f:
        for x in extracts:f.write(json.dumps(x,ensure_ascii=False)+"\n")
    fields=["batch_id","record_id","source_name","source_url","t0_label","education_relevance","problem_clarity","demand_authenticity","ai_core","feasibility","unmet_degree","opportunity_status","opportunity_confidence","function_category","industry","decision_version","decision_reason"]
    with (output_dir/"task2_internal_1984.csv").open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for x in internal:
            flat={**x,**x["dimension_scores"]}
            w.writerow({k:flat.get(k,"") for k in fields})
    resolved=[x for x in internal if x["opportunity_status"] in ("0","1")]; blocked=[x for x in internal if x["opportunity_status"]=="REVIEW"]
    with (output_dir/"result2_resolved_subset.csv").open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.writer(f);w.writerow(RESULT2_HEADER)
        for x in resolved:w.writerow([x["batch_id"],x["record_id"],x["opportunity_status"],x["opportunity_confidence"],x["function_category"],x["industry"]])
    with (output_dir/"result2_export_blockers.csv").open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.writer(f);w.writerow(["记录编号","内部状态","阻断原因"])
        for x in blocked:w.writerow([x["record_id"],"REVIEW","需人工/增强算法定稿；严格模式不映射为官方1或0"])

    opportunities=[x for x in internal if x["opportunity_status"]=="1"]
    assignments=[]; clusters=[]
    if opportunities:
        vec=TfidfVectorizerLite((2,4),6000); X=vec.fit_transform([x["content"] for x in opportunities])
        k=1 if len(opportunities)<4 else min(8,max(2,round(math.sqrt(len(opportunities)/2))))
        a=kmeans_sparse(X,k)
        for x,c in zip(opportunities,a):assignments.append((x,c))
        for c in sorted(set(a)):
            xs=[x for x,j in assignments if j==c]; funcs=Counter(x["function_category"] for x in xs); func=funcs.most_common(1)[0][0]
            users=Counter(_user_text(x["content"]) for x in xs); user=users.most_common(1)[0][0]
            clusters.append({"batch_id":"ALL","cluster_id":f"T3-C{c+1:03d}","cluster_name":f"{user}-{func}机会","function_category":func,"industry":"教育","records":xs,"record_ids":[x["record_id"] for x in xs],"source_count":len({x['source_name'] for x in xs})})
    with (output_dir/"result3.csv").open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.writer(f);w.writerow(RESULT3_HEADER)
        for c in clusters:w.writerow([c["batch_id"],c["cluster_id"],c["cluster_name"],c["function_category"],c["industry"],len(c["records"]),c["source_count"],";".join(c["record_ids"])])

    raw=[]
    for c in clusters:
        raw.append({**c,"source_diversity":c["source_count"],"scale":math.log1p(len(c["records"])),"demand":sum(x["dimension_scores"]["demand_authenticity"] for x in c["records"])/len(c["records"]),"unmet":sum(x["dimension_scores"]["unmet_degree"] for x in c["records"])/len(c["records"]),"feasibility":sum(x["dimension_scores"]["feasibility"] for x in c["records"])/len(c["records"])})
    def norm(field,value):
        vals=[x[field] for x in raw]
        if not vals:return 0
        lo,hi=min(vals),max(vals)
        return 50.0 if hi==lo else 100*(value-lo)/(hi-lo)
    for x in raw:
        dims={f:round(norm(f,x[f]),2) for f in ("source_diversity","scale","demand","unmet","feasibility")}
        x["score_dimensions"]=dims;x["opportunity_value_score"]=round(.25*dims["source_diversity"]+.20*dims["scale"]+.20*dims["demand"]+.20*dims["unmet"]+.15*dims["feasibility"],2)
    raw.sort(key=lambda x:(-x["opportunity_value_score"],x["cluster_id"]))
    with (output_dir/"result4.csv").open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.writer(f);w.writerow(RESULT4_HEADER)
        for rank,x in enumerate(raw,1):w.writerow([x["batch_id"],x["cluster_id"],x["cluster_name"],x["function_category"],x["industry"],x["opportunity_value_score"],rank])

    plans=output_dir/"plans";plans.mkdir(exist_ok=True); recommendations=[]
    ext={x["record_id"]:x for x in extracts}
    for rank,x in enumerate(raw[:5],1):
        sample=x["records"][:8]; users=Counter(ext[r["record_id"]]["user"] for r in sample).most_common(3); pains=[ext[r["record_id"]]["pain"] for r in sample if ext[r["record_id"]]["pain"]][:5]
        rec={"rank":rank,"cluster_id":x["cluster_id"],"cluster_name":x["cluster_name"],"score":x["opportunity_value_score"],"target_users":[u for u,_ in users],"pain_evidence":pains,"record_ids":x["record_ids"]}
        recommendations.append(rec)
        (plans/f"{rank:02d}_{x['cluster_id']}.md").write_text(f"# {x['cluster_name']} 策划案（规则生成草案）\n\n- 目标用户：{'、'.join(rec['target_users']) or '待核'}\n- 核心痛点：{'；'.join(pains) or '待补充真实需求证据'}\n- 建议功能：围绕{x['function_category']}建立最小可验证功能。\n- 技术路线：规则与结构化抽取 → 可复现基线 → 人工复核 → 必要时LLM增强。\n- 周期：2周MVP验证；第1周数据/原型，第2周用户验证/评估。\n- 子任务：证据复核、原型、离线指标、用户反馈、风险审计。\n- 依据记录：{';'.join(x['record_ids'][:20])}\n- 机会价值分：{x['opportunity_value_score']}（程序公式，不是LLM打分）\n\n> 本草案只基于规则判别为1的记录；仍需核验真实需求和原文证据。\n",encoding="utf-8")
    (output_dir/"recommendations.json").write_text(json.dumps(recommendations,ensure_ascii=False,indent=2),encoding="utf-8")

    cluster_by={r["record_id"]:x for x in raw for r in x["records"]}
    with (output_dir/"unified_records.jsonl").open("w",encoding="utf-8") as f:
        for x,e in zip(internal,extracts):
            c=cluster_by.get(x["record_id"])
            obj={"schema_version":"competition_mvp_v1","record":{"batch_id":x["batch_id"],"record_id":x["record_id"],"source_name":x["source_name"],"source_url":x["source_url"]},"task2":{"t0_label":x["t0_label"],"dimensions":x["dimension_scores"],"status":x["opportunity_status"],"confidence":x["opportunity_confidence"],"function_category":x["function_category"],"industry":x["industry"]},"extraction":e,"task3":None if not c else {"cluster_id":c["cluster_id"],"cluster_name":c["cluster_name"]},"task4":None if not c else {"score":c["opportunity_value_score"],"dimensions":c["score_dimensions"]},"task5":None if not c else {"recommended":any(r["cluster_id"]==c["cluster_id"] for r in recommendations)}}
            f.write(json.dumps(obj,ensure_ascii=False)+"\n")
    return {"task2_processed":len(internal),"status_distribution":dict(Counter(x["opportunity_status"] for x in internal)),"t0_distribution":dict(Counter(x["t0_label"] for x in internal)),"resolved_subset_rows":len(resolved),"official_full_export_ready":not blocked,"official_export_blockers":len(blocked),"task3_opportunity_records":len(opportunities),"task3_clusters":len(clusters),"task4_rows":len(raw),"task5_recommendations":len(recommendations)}

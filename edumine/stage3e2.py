"""Stage 3E-2 diagnostics and conservative Task 2 improvement.

This module is deliberately additive: it never rewrites frozen inputs or the
stage3e1 decision.  The v2 decision remains an experimental candidate.
"""
from __future__ import annotations

import re
from collections import Counter

from .competition import AI_WORDS, TASK_WORDS, extract_need, t0_rule_predict

DIMENSIONS=("education_relevance","problem_clarity","demand_authenticity","ai_core","feasibility","unmet_degree")
STRONG_PAIN=("耗时","效率低","效率不高","负担","无法","缺少","不足","困难","难以","繁琐","滞后","不准确","错误率","风险","压力","成本高","困扰","亟待","急需","薄弱")
DIRECT_DEMAND=("我希望","我们需要","希望能够","急需","亟待","用户反馈","访谈发现","调研发现","老师希望","教师希望","学生需要","家长希望","实际使用","一线教师","采购需求","招标")
SUPPLY_CUES=("产品发布","解决方案","项目旨在","平台提供","系统提供","功能包括","产品功能","新品","赋能","宣传","课程介绍","教程")
REAL_USE=("已上线","投入使用","实际应用","用户反馈","试点","部署","开源","github","采购","招标","案例","实测")
GENERIC_QUESTION=re.compile(r"(^|[，。；：\s])问题([，。；：\s]|$)|提出问题|生成.*问题|回答问题")

def evidence_level(text):
    raw=(text or "").strip(); clean=re.sub(r"\s+","",raw)
    if not clean:return "EMPTY_CONTENT"
    if "&nbsp;" in raw or len(clean)<=60:return "TITLE_LIKE"
    if len(clean)<160:return "SHORT_CONTENT"
    return "SUBSTANTIVE_CONTENT"

def _has(text,words):return any(w.lower() in text.lower() for w in words)

def judge_task2_v2(record, extraction=None):
    """Conservative six-dimension candidate focused on grounded demand evidence."""
    text=record.get("内容","") or ""; low=text.lower(); extraction=extraction or extract_need(record)
    t0=t0_rule_predict(text); edu={"EDUCATION_DIRECT":2,"EDUCATION_WEAK":1,"NON_EDUCATION":0,"UNKNOWN":0}[t0]
    task_hit=_has(text,TASK_WORDS); strong_pain=_has(text,STRONG_PAIN)
    generic_only=bool(GENERIC_QUESTION.search(text)) and not strong_pain
    problem=2 if task_hit and strong_pain else (1 if task_hit or strong_pain else 0)
    if generic_only and not task_hit:problem=0
    direct=_has(text,DIRECT_DEMAND); user_specific=extraction.get("user")!="未明确"
    supply_only=_has(text,SUPPLY_CUES) and not direct and not _has(text,("反馈","访谈","调研","实际使用","采购","招标"))
    demand=2 if direct else (1 if user_specific and strong_pain and not supply_only else 0)
    ai_hit=_has(low,AI_WORDS)
    ai_core=2 if ai_hit and task_hit else (1 if ai_hit else 0)
    feasible=2 if ai_hit and _has(text,REAL_USE) else (1 if ai_hit or extraction.get("existing_solution") else 0)
    unmet=2 if strong_pain and direct else (1 if strong_pain and not supply_only else 0)
    scores=dict(zip(DIMENSIONS,(edu,problem,demand,ai_core,feasible,unmet)))
    level=evidence_level(text)
    if edu==0 or (demand==0 and ai_core==0):status="0"
    elif level=="EMPTY_CONTENT":status="REVIEW"
    elif min(problem,demand,ai_core,feasible,unmet)>=1 and sum(scores.values())>=9:status="1"
    else:status="REVIEW"
    return {"t0_label":t0,"dimension_scores":scores,"opportunity_status":status,
            "decision_version":"task2_rule_v2_candidate","evidence_level":level,
            "flags":{"generic_question_only":generic_only,"supply_only":supply_only,
                     "direct_demand_evidence":direct,"strong_pain_evidence":strong_pain},
            "decision_reason":f"v2六维得分={scores}；证据层级={level}；供给声明={supply_only}。"}

def review_root_cause(scores, text, flags=None):
    """Return multi-label causes plus one deterministic primary cause."""
    flags=flags or {}; level=evidence_level(text); causes=[]
    if level in ("EMPTY_CONTENT","TITLE_LIKE"):causes.append("TEXT_INSUFFICIENT")
    if int(scores["demand_authenticity"])==0:causes.append("DEMAND_EVIDENCE_MISSING")
    if int(scores["problem_clarity"])==0:causes.append("PROBLEM_UNCLEAR")
    if int(scores["ai_core"])==0:causes.append("AI_CORE_UNCLEAR")
    blockers=sum(int(scores[d])==0 for d in DIMENSIONS[1:])
    if blockers>=3:causes.append("TRUE_INDETERMINATE")
    if blockers==0 and sum(int(scores[d]) for d in DIMENSIONS)>=7:causes.append("RULE_TOO_STRICT_CANDIDATE")
    if flags.get("supply_only"):causes.append("SUPPLY_NOT_DEMAND")
    order=("TRUE_INDETERMINATE","TEXT_INSUFFICIENT","DEMAND_EVIDENCE_MISSING","PROBLEM_UNCLEAR","AI_CORE_UNCLEAR","SUPPLY_NOT_DEMAND","RULE_TOO_STRICT_CANDIDATE")
    primary=next((x for x in order if x in causes),"OTHER_BOUNDARY")
    return primary,causes

def ngram_set(text,n=3):
    s=re.sub(r"\s+","",(text or "").lower())
    return {s[i:i+n] for i in range(max(0,len(s)-n+1))}

def jaccard(a,b):
    return len(a&b)/len(a|b) if a or b else 0.0

def evidence_quality(record, decision, extraction):
    """Transparent 0-100 evidence quality, not an opportunity label."""
    level={"EMPTY_CONTENT":0,"TITLE_LIKE":8,"SHORT_CONTENT":18,"SUBSTANTIVE_CONTENT":25}[decision["evidence_level"]]
    grounded=20 if extraction.get("evidence_excerpt") and extraction["evidence_excerpt"] in (record.get("内容") or "") else 0
    demand=12.5*decision["dimension_scores"]["demand_authenticity"]
    direct=15 if decision["flags"]["direct_demand_evidence"] else 0
    use=15 if _has(record.get("内容", ""),REAL_USE) else 0
    return round(min(100,level+grounded+demand+direct+use),2)

"""Approval-gated official export and Task 2-4 consistency checks."""
from __future__ import annotations
import csv,hashlib,json
from collections import Counter
from pathlib import Path

RESULT2_HEADER=("采集批次号","记录编号","是否构成机会","机会置信度","功能类别","所属行业")
RESULT3_HEADER=("采集批次号","主题簇编号","主题簇名称","功能类别","所属行业","簇内机会记录数","来源覆盖","簇内机会记录")
RESULT4_HEADER=("采集批次号","主题簇编号","主题簇名称","功能类别","所属行业","机会价值分","优先级")

def sha256(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read_csv(path):
    with Path(path).open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def write_csv(path,rows,header):
    with Path(path).open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=header,extrasaction="ignore");w.writeheader();w.writerows(rows)

def validate_result2(rows,master_ids,function_labels,industry_labels):
    errors=[];ids=[x.get("记录编号","") for x in rows]
    if len(rows)!=len(master_ids):errors.append(f"row_count={len(rows)} expected={len(master_ids)}")
    if len(set(ids))!=len(ids):errors.append("duplicate_record_id")
    if set(ids)!=set(master_ids):errors.append("record_id_coverage_mismatch")
    for x in rows:
        rid=x.get("记录编号","");label=x.get("是否构成机会","")
        if label not in ("0","1"):errors.append(f"{rid}:illegal_label={label}");continue
        try:c=float(x.get("机会置信度",""));assert 0<=c<=1
        except Exception:errors.append(f"{rid}:illegal_confidence")
        if label=="1":
            if x.get("功能类别") not in function_labels:errors.append(f"{rid}:illegal_function")
            if x.get("所属行业") not in industry_labels:errors.append(f"{rid}:illegal_industry")
        elif x.get("功能类别") or x.get("所属行业"):errors.append(f"{rid}:zero_must_have_blank_categories")
    return errors

def build_official_result2(master,machine,stable,resolved,approval,function_labels,industry_labels):
    """Returns rows only when every REVIEW has an explicitly approved record decision."""
    if approval.get("approval_status")!="APPROVED_BY_OWNER":return None,["owner_approval_not_approved"]
    decisions={x["record_id"]:x for x in approval.get("record_decisions",[])};stable_by={x["record_id"]:x for x in stable};resolved_by={x["记录编号"]:x for x in resolved};machine_by={x["record_id"]:x for x in machine};out=[];block=[]
    for r in master:
        rid=r["记录编号"];m=machine_by.get(rid);d=decisions.get(rid)
        if not m:block.append(f"{rid}:missing_machine");continue
        status=m["opportunity_status"]
        if status=="REVIEW":
            if not d or d.get("final_label") not in ("0","1") or not d.get("decision_basis"):block.append(f"{rid}:review_unresolved");continue
            status=d["final_label"]
        source=d or resolved_by.get(rid) or stable_by.get(rid,{})
        confidence=source.get("official_confidence",source.get("机会置信度",source.get("opportunity_confidence","")))
        function=source.get("function_category",source.get("功能类别","")) if status=="1" else ""
        industry=source.get("industry",source.get("所属行业","")) if status=="1" else ""
        out.append({"采集批次号":r["采集批次号"],"记录编号":rid,"是否构成机会":status,"机会置信度":confidence,"功能类别":function,"所属行业":industry})
    if block:return None,block
    errors=validate_result2(out,[x["记录编号"] for x in master],function_labels,industry_labels)
    return (None,errors) if errors else (out,[])

def validate_task34(result2,result3,result4,function_labels,industry_labels):
    errors=[];opps={x["记录编号"] for x in result2 if x["是否构成机会"]=="1"};seen=set()
    for c in result3:
        cid=c["主题簇编号"]
        if cid in seen:errors.append(f"duplicate_cluster={cid}")
        seen.add(cid);ids=[x for x in c["簇内机会记录"].split("；") if x]
        if any(x not in opps for x in ids):errors.append(f"{cid}:references_non_opportunity")
        if int(c["簇内机会记录数"])!=len(ids):errors.append(f"{cid}:record_count_mismatch")
        if c["功能类别"] not in function_labels or c["所属行业"] not in industry_labels:errors.append(f"{cid}:illegal_category")
    ids4=[x["主题簇编号"] for x in result4]
    if set(ids4)!=seen or len(ids4)!=len(set(ids4)):errors.append("result4_cluster_mismatch")
    return errors

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs/research_stage3/stage3e4"
EXP = ROOT / "experiments/stage3e4"


def read_csv(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader(); w.writerows(rows)


def sha(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def b(v):
    return str(v).strip().lower() == "true"


def main():
    DOC.mkdir(parents=True, exist_ok=True); EXP.mkdir(parents=True, exist_ok=True)
    master_p = ROOT / "data/frozen/result1_Final_All.csv"
    v1_p = ROOT / "results/stage3e1/task2_internal_1984.csv"
    v2_p = ROOT / "results/stage3e2/task2_v2_internal_1984.csv"
    queue_p = ROOT / "docs/research_stage3/stage3e3/review601_disposition_queue.csv"
    human_p = ROOT / "experiments/datasets/stage3e3/guo_stage3e1_opp42_submit_20261114.csv"
    master, v1, v2, queue, human = map(read_csv, (master_p, v1_p, v2_p, queue_p, human_p))
    bym = {r["记录编号"]: r for r in master}; byv1 = {r["record_id"]: r for r in v1}; byv2 = {r["record_id"]: r for r in v2}; byh = {r["record_id"]: r for r in human}
    assert len(master) == len(bym) == 1984
    assert len(v2) == len(byv2) == 1984
    assert len(queue) == 601 and len({r["record_id"] for r in queue}) == 601
    assert {r["record_id"] for r in queue} == {r["record_id"] for r in v2 if r["opportunity_status"] == "REVIEW"}

    audit = []
    group_counts = Counter()
    for q in queue:
        rid = q["record_id"]; x = byv2[rid]
        group = q["disposition_category"]
        rule = q["proposed_action"]
        group_counts[group] += 1
        support = f"D1={x['education_relevance']};D2={x['problem_clarity']};D3={x['demand_authenticity']};D4={x['ai_core']};D5={x['feasibility']};D6={x['unmet_degree']};supply_only={x['supply_only']};strong_pain={x['strong_pain_evidence']}"
        audit.append({
            "record_id": rid, "v2_original_label": "REVIEW", "review_reason": x["decision_reason"],
            "evidence_level": x["evidence_level"], "source_name": x["source_name"],
            "disposition_group": group, "proposed_rule": rule, "supporting_evidence": support,
            "proposed_official_label": "", "confidence_basis": "", "owner_approval_status": "PENDING_APPROVAL"
        })
    write_csv(EXP / "review601_audit.csv", audit, list(audit[0]))

    rules = []
    candidates = {
        "BROAD_SUPPLY_ONLY_QUEUE31": [byv2[x["record_id"]] for x in queue if x["disposition_category"] == "REUSABLE_EXCLUSION_CANDIDATE_SUPPLY_ONLY"],
        "REFINED_SUPPLY_WITHOUT_STRONG_PAIN_QUEUE27": [byv2[x["record_id"]] for x in queue if x["disposition_category"] == "REUSABLE_EXCLUSION_CANDIDATE_SUPPLY_ONLY" and not b(byv2[x["record_id"]]["strong_pain_evidence"])],
        "BROAD_GENERIC_QUESTION_QUEUE3": [byv2[x["record_id"]] for x in queue if x["disposition_category"] == "REUSABLE_EXCLUSION_CANDIDATE_GENERIC_QUESTION"],
    }
    for name, xs in candidates.items():
        overlap = [byh[x["record_id"]] for x in xs if x["record_id"] in byh]
        hc = Counter(x["human_opportunity_decision"] for x in overlap)
        safe = name == "REFINED_SUPPLY_WITHOUT_STRONG_PAIN_QUEUE27" and hc.get("1", 0) == 0
        rules.append({"rule_id": name, "review_hits": len(xs), "human42_overlap": len(overlap), "human_1": hc.get("1", 0), "human_0": hc.get("0", 0), "human_insufficient": hc.get("INSUFFICIENT", 0), "automatic_use_recommended": "NO", "assessment": "PROMISING_OWNER_APPROVAL_REQUIRED" if safe else "UNSAFE_CONFLICT_OR_INSUFFICIENT_VALIDATION"})
    write_csv(EXP / "exclusion_rule_evaluation.csv", rules, list(rules[0]))

    positives = {r["record_id"] for r in human if r["human_opportunity_decision"] == "1"}
    fn = []
    for rid in sorted(positives):
        x = byv2[rid]
        if x["opportunity_status"] != "1":
            fn.append({"record_id": rid, "human_label": "1", "v1_status": byv1[rid]["opportunity_status"], "v2_status": x["opportunity_status"], "evidence_level": x["evidence_level"], "D1": x["education_relevance"], "D2": x["problem_clarity"], "D3": x["demand_authenticity"], "D4": x["ai_core"], "D5": x["feasibility"], "D6": x["unmet_degree"], "supply_only": x["supply_only"], "analysis": "v2将独立需求证据缺失或总分阈值作为阻断；需区分文本未呈现与需求不存在"})
    write_csv(EXP / "human42_false_negative_8.csv", fn, list(fn[0]))
    assert len(fn) == 8

    priority = []
    recovered = {
        "SUPER_part8-S00007": "https://github.com/zijian-optics/SolaireEPDA",
        "SUPER_part6-S00170": "https://github.com/QwenStorm/xl-frontend",
        "SUPER_part5-S00068": "https://github.com/harrytted/ai-agent-interview-playbook",
        "SUPER_part4-S00008": "https://github.com/tanle-mtr/ChinaStudyFree",
        "SUPER_part16-S00003": "https://github.com/ceilf6/Auto_courseGrabber",
    }
    high = [x for x in v2 if x["opportunity_status"] == "REVIEW" and int(x["problem_clarity"]) >= 1 and int(x["ai_core"]) >= 1 and (int(x["demand_authenticity"]) >= 1 or b(x["strong_pain_evidence"]))]
    for x in sorted(high, key=lambda z: z["record_id"]):
        rid = x["record_id"]; ok = rid in recovered
        priority.append({"record_id": rid, "source_name": x["source_name"], "evidence_level": x["evidence_level"], "priority": "P0" if ok else "P1", "retrieval_status": "RECOVERED_PUBLIC_ORIGINAL" if ok else "PENDING", "retrieved_at": "2026-11-14" if ok else "", "actual_url": recovered.get(rid, x["source_url"]), "recovered_source_type": "ORIGINAL_GITHUB_README_OR_ABOUT" if ok else "", "d3_sufficiency_after_recovery": "NOT_ESTABLISHED" if ok else "", "owner_approval_status": "PENDING_APPROVAL"})
    present={x['record_id'] for x in priority}
    for rid,url in recovered.items():
        if rid in present: continue
        x=byv2[rid]
        priority.append({"record_id": rid, "source_name": x["source_name"], "evidence_level": x["evidence_level"], "priority": "RECOVERY_TRIAL", "retrieval_status": "RECOVERED_PUBLIC_ORIGINAL", "retrieved_at": "2026-11-14", "actual_url": url, "recovered_source_type": "ORIGINAL_GITHUB_README_OR_ABOUT", "d3_sufficiency_after_recovery": "NOT_ESTABLISHED", "owner_approval_status": "PENDING_APPROVAL"})
    write_csv(EXP / "priority_evidence_recovery.csv", priority, list(priority[0]))
    assert len(high) == 27 and len(priority) == 32

    approval = {"approval_version": "stage3e4_result2_policy_pending_v1", "approval_status": "PENDING_APPROVAL", "selected_policy": "", "approved_by": "", "approved_at": "", "confidence_semantics_approved": False, "record_decisions": [], "notes": "No REVIEW is mapped until owner approval; decisions must be record-specific and auditable."}
    (DOC / "owner_result2_approval_template.json").write_text(json.dumps(approval, ensure_ascii=False, indent=2), encoding="utf-8")
    summary = {"master_rows": len(master), "v2_counts": Counter(x["opportunity_status"] for x in v2), "review_rows": len(queue), "review_groups": group_counts, "rule_evaluation": rules, "human42_counts": Counter(x["human_opportunity_decision"] for x in human), "human_positive_v2_not_1": len(fn), "high_impact_priority_rows": len(high), "recovery_audit_rows": len(priority), "public_original_recovered": 5, "official_export_ready": False, "formal_result2_written": False}
    (EXP / "stage3e4_run_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

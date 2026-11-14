from __future__ import annotations
import csv, hashlib, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
def rows(p):
    with p.open(encoding="utf-8-sig", newline="") as f: return list(csv.DictReader(f))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest().upper()
checks=[]
def ck(name, ok, detail=""):
    checks.append({"check":name,"status":"PASS" if ok else "FAIL","detail":detail})

master=ROOT/'data/frozen/result1_Final_All.csv'; queue=ROOT/'experiments/stage3e4/review601_audit.csv'; approval=ROOT/'docs/research_stage3/stage3e4/owner_result2_approval_template.json'; summary=ROOT/'experiments/stage3e4/stage3e4_run_summary.json'
m=rows(master); q=rows(queue); a=json.loads(approval.read_text(encoding='utf-8')); s=json.loads(summary.read_text(encoding='utf-8'))
ck('frozen_master_1984_unique',len(m)==1984 and len({x['记录编号'] for x in m})==1984,sha(master))
ck('review601_exact_unique',len(q)==601 and len({x['record_id'] for x in q})==601)
ck('review601_unlabeled',all(not x['proposed_official_label'] and x['owner_approval_status']=='PENDING_APPROVAL' for x in q))
ck('approval_gate_pending',a['approval_status']=='PENDING_APPROVAL' and not a['record_decisions'])
ck('formal_result2_absent',not (ROOT/'results/stage3e4/result2.csv').exists())
ck('human_false_negative_count',len(rows(ROOT/'experiments/stage3e4/human42_false_negative_8.csv'))==8)
ck('priority_recovery_count',len(rows(ROOT/'experiments/stage3e4/priority_evidence_recovery.csv'))==32 and s['high_impact_priority_rows']==27)
ck('summary_consistent',s['review_rows']==601 and not s['official_export_ready'])
human=ROOT/'experiments/datasets/stage3e3/guo_stage3e1_opp42_submit_20261114.csv'
ck('human42_unchanged',human.exists() and sha(human)=='B5EC97AE970885B90F8239D71B6AE52DD615AC05467645460A170D095036A914')
source_queue=ROOT/'docs/research_stage3/stage3e3/review601_disposition_queue.csv'
ck('source_review_queue_unchanged',sha(source_queue)=='F43364E4C3E0659D4A8A08825D0D21A0AE8AE854E126AE1AB9EC1D75932C634A')
v2=ROOT/'results/stage3e2/task2_v2_internal_1984.csv'
ck('v2_machine_layer_unchanged',sha(v2)=='EE1DE611986E4B0F3ADD7DB0B908A9D523581CDAFA0DC330DB469F732ABA5D32')
rec=rows(ROOT/'experiments/stage3e4/priority_evidence_recovery.csv'); recovered=[x for x in rec if x['retrieval_status']=='RECOVERED_PUBLIC_ORIGINAL']
ck('recovered_sources_not_overclaimed',len(recovered)==5 and all(x['recovered_source_type']=='ORIGINAL_GITHUB_README_OR_ABOUT' and x['d3_sufficiency_after_recovery']=='NOT_ESTABLISHED' for x in recovered))
ck('task34_entry_ready',(ROOT/'scripts/recompute_task34_stage3e4.py').exists())
out=ROOT/'experiments/stage3e4/stage3e4_validation.json';out.write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(checks,ensure_ascii=False,indent=2));sys.exit(0 if all(x['status']=='PASS' for x in checks) else 1)

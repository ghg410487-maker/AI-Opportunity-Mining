from __future__ import annotations
import csv,json,sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];DOC=ROOT/'docs/research_stage3/stage3e3';EXP=ROOT/'experiments/stage3e3';PRIVATE=ROOT/'experiments/datasets/stage3e3'
def read(p):
    with Path(p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
comp=read(DOC/'guo42_v1_v2_comparison.csv');summary=json.loads((EXP/'guo42_ingestion_summary.json').read_text(encoding='utf-8'));merged=read(PRIVATE/'locked_evaluation_126_with_guo42_private.csv')
checks={'guo42_rows':len(comp)==42,'guo42_unique':len({x['record_id'] for x in comp})==42,'human_12_29_1':Counter(x['human_decision'] for x in comp)==Counter({'1':12,'0':29,'INSUFFICIENT':1}),'v2_12_30_0':Counter(x['v2_status'] for x in comp)==Counter({'1':12,'REVIEW':30}),'reasons_complete':summary['empty_reasons']==0,'evidence_quality_missing_preserved':summary['empty_evidence_quality']==42,'merged_126':len(merged)==126,'merged_human_42':sum(x['review_status']=='VERIFIED' for x in merged)==42,'merged_pending_84':sum(x['review_status']=='PENDING' for x in merged)==84,'guo_source_sha_preserved':summary['source_sha256']=='b5ec97ae970885b90f8239d71b6ae52dd615ac05467645460a170d095036a914'}
result={'passed':all(checks.values()),'checks':checks,'overall_metrics_status':'PENDING_REMAINING_84','official_result2_status':'BLOCKED_601'}
(EXP/'handoff_revision_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=False,indent=2));sys.exit(0 if result['passed'] else 1)

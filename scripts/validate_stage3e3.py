from __future__ import annotations
import csv,hashlib,json,sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];DOC=ROOT/'docs/research_stage3/stage3e3';EXP=ROOT/'experiments/stage3e3';PRIVATE=ROOT/'experiments/datasets/stage3e3';RES=ROOT/'results/stage3e3'
def read(p):
    with Path(p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
private=read(PRIVATE/'locked_evaluation_126_private.csv');blind=read(PRIVATE/'locked_evaluation_126_guo_blind.csv');public=read(DOC/'locked_evaluation_126_manifest.csv');review=read(DOC/'review601_disposition_queue.csv');cl=read(EXP/'clustering_comparison.csv');score=read(EXP/'task4_full_sensitivity.csv')
checks={'evaluation_126':len(private)==126,'evaluation_unique':len({x['record_id'] for x in private})==126,'sampling_42_each':Counter(x['sampling_group'] for x in private)==Counter({'V1_OPPORTUNITY_CENSUS':42,'V1_0_STRATIFIED':42,'V1_REVIEW_STRATIFIED':42}),'human_pending':all(x['review_status']=='PENDING' and not x['human_opportunity_label'] for x in private),'blind_no_predictions':all('v1_status_hidden_from_reviewer' not in x and 'v2_status_hidden_from_reviewer' not in x and 'sampling_group' not in x for x in blind),'blind_ids_match':{x['record_id'] for x in blind}=={x['record_id'] for x in private},'public_no_raw':all('content' not in x and 'source_url' not in x for x in public),'review_601':len(review)==601,'review_no_final_labels':all(not x['final_official_label'] and x['owner_approval_status']=='PENDING' for x in review),'cluster_runs_40':len(cl)==40,'cluster_domains':{x['feature'] for x in cl}=={'CHAR','HYBRID'} and {x['k'] for x in cl}=={'3','4','5','6'},'score_rows_90':len(score)==90,'config_exists':(DOC/'final_algorithm_config.json').exists(),'frozen_sha':hashlib.sha256((ROOT/'data/frozen/result1_Final_All.csv').read_bytes()).hexdigest()=='44c75335b3795c746ffc603b339bf6aa4d2e6945e38ebd0a8bcb9d39c9ff0a52','paid_api_calls_zero':json.loads((EXP/'stage3e3_run_summary.json').read_text(encoding='utf-8'))['paid_api_calls']==0}
result={'passed':all(checks.values()),'checks':checks,'official_full_result2_ready':False,'official_blockers':601,'human_metrics_status':'PENDING_HUMAN_REVIEW'}
(EXP/'end_to_end_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
targets=[]
for folder in (DOC,EXP,RES):targets.extend(p for p in folder.glob('*') if p.is_file() and p.name!='SHA256SUMS.txt')
(DOC/'SHA256SUMS.txt').write_text('\n'.join(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(ROOT).as_posix()}" for p in sorted(targets))+'\n',encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2));sys.exit(0 if result['passed'] else 1)

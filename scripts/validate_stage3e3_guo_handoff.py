from __future__ import annotations
import csv,json,sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];P=ROOT/'experiments/datasets/stage3e3';E=ROOT/'experiments/stage3e3'
def read(p):
    with Path(p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
required=[P/'locked_evaluation_126_guo_blind.csv',P/'locked_evaluation_126_with_guo42_private.csv',P/'locked_evaluation_remaining84_guo_blind.csv']
missing=[str(p.relative_to(ROOT)) for p in required if not p.exists()]
if missing:
    print(json.dumps({'passed':None,'status':'SKIPPED_PRIVATE_INPUT_NOT_PRESENT','missing':missing,'note':'公开仓库按设计不包含第三方原文盲审文件；请在受控本地环境运行完整验证。'},ensure_ascii=False,indent=2))
    sys.exit(0)
b=read(P/'locked_evaluation_126_guo_blind.csv');m=read(P/'locked_evaluation_126_with_guo42_private.csv');r=read(P/'locked_evaluation_remaining84_guo_blind.csv');q=read(E/'q_length_proxy_42.csv');c=read(E/'cluster5_guo_initial_audit.csv')
done={x['record_id'] for x in m if x['review_status']=='VERIFIED'};forbidden={'sampling_group','stratum','stratum_population_N','stratum_sample_n','inclusion_probability','sample_weight','v1_status_hidden_from_reviewer','v2_status_hidden_from_reviewer','opportunity_status','machine_prediction'}
checks={'blind126_unique':len(b)==len({x['eval_id'] for x in b})==len({x['record_id'] for x in b})==126,'mapped42_84':Counter(x['review_status'] for x in m)==Counter({'PENDING':84,'VERIFIED':42}),'remaining84_unique':len(r)==len({x['eval_id'] for x in r})==len({x['record_id'] for x in r})==84,'no_completed_reissued':not(done&{x['record_id'] for x in r}),'same_locked_subset':{x['record_id'] for x in r}==({x['record_id'] for x in b}-done),'blind_no_leakage':not forbidden.intersection(r[0]),'q_proxy_31_8_3':Counter(x['q_length_proxy'] for x in q)==Counter({'Q3':31,'Q2':8,'Q1':3}),'q_formal_blank':all(not x['formal_human_evidence_quality'] and x['is_proxy_only']=='YES' for x in q),'cluster_counts':[(x['human_confirmed_1'],x['human_rejected_0'],x['human_insufficient']) for x in c]==[('4','3','0'),('3','11','0'),('1','6','0'),('0','5','0'),('4','4','1')],'c004_paused':next(x for x in c if x['cluster_id']=='T3-C004')['confirmed_support_status']=='NO_CONFIRMED_SUPPORT_PAUSE_RECOMMENDATION'}
result={'passed':all(checks.values()),'checks':checks};(E/'guo_handoff_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=False,indent=2));sys.exit(0 if result['passed'] else 1)

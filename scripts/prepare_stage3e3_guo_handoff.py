from __future__ import annotations
import csv,hashlib,json,sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];PRIVATE=ROOT/'experiments/datasets/stage3e3';EXP=ROOT/'experiments/stage3e3';DOC=ROOT/'docs/research_stage3/stage3e3'
def read(p):
    with Path(p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def write(p,rows,fields=None):
    fields=fields or list(rows[0]);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
blind=read(PRIVATE/'locked_evaluation_126_guo_blind.csv');mapped=read(PRIVATE/'locked_evaluation_126_with_guo42_private.csv');mapped_by={x['record_id']:x for x in mapped}
assert len(blind)==len(mapped)==126 and len({x['eval_id'] for x in blind})==len({x['record_id'] for x in blind})==126
completed={x['record_id'] for x in mapped if x['review_status']=='VERIFIED'};remaining=[x for x in blind if x['record_id'] not in completed]
assert len(completed)==42 and len(remaining)==84 and all(x['review_status']=='PENDING' for x in remaining)
forbidden={'sampling_group','stratum','stratum_population_N','stratum_sample_n','inclusion_probability','sample_weight','v1_status_hidden_from_reviewer','v2_status_hidden_from_reviewer','opportunity_status','machine_prediction'}
assert not forbidden.intersection(blind[0])
remaining_path=PRIVATE/'locked_evaluation_remaining84_guo_blind.csv';write(remaining_path,remaining)

# Length-only proxy for the 42 audited v1 opportunities; never backfills human quality.
master={x['记录编号']:x for x in read(ROOT/'data/frozen/result1_Final_All.csv')};v1=read(ROOT/'results/stage3e1/task2_internal_1984.csv');ids=[x['record_id'] for x in v1 if x['opportunity_status']=='1']
q=[]
for rid in ids:
    n=len((master[rid]['内容'] or '').strip());proxy='Q1' if n<80 else ('Q2' if n<200 else 'Q3')
    q.append({'record_id':rid,'content_length_chars':n,'q_length_proxy':proxy,'proxy_rule':'Q1:<80;Q2:80-199;Q3:>=200','formal_human_evidence_quality':'','is_proxy_only':'YES'})
write(EXP/'q_length_proxy_42.csv',q)
assert Counter(x['q_length_proxy'] for x in q)==Counter({'Q3':31,'Q2':8,'Q1':3})

# Sidecar cluster audit; original result3/result4 remain untouched.
clusters=read(ROOT/'results/stage3e1/result3.csv');human={x['record_id']:x for x in read(PRIVATE/'guo_stage3e1_opp42_submit_20261114.csv')};audit=[]
for c in clusters:
    members=c['簇内机会记录编号'].split(';');dist=Counter(human[i]['human_opportunity_decision'] for i in members)
    cid=c['主题簇编号'];audit.append({'cluster_id':cid,'machine_topic_name':c['主题簇名称'],'machine_record_count':len(members),'human_confirmed_1':dist['1'],'human_rejected_0':dist['0'],'human_insufficient':dist['INSUFFICIENT'],'confirmed_support_status':'NO_CONFIRMED_SUPPORT_PAUSE_RECOMMENDATION' if dist['1']==0 else 'HAS_INITIAL_CONFIRMED_SUPPORT','duplicate_machine_name_flag':'YES' if c['主题簇名称']=='学生-文本生成机会' else 'NO','owner_decision_status':'PENDING','note':'旁路人工审计；不修改机器聚类或评分'})
write(EXP/'cluster5_guo_initial_audit.csv',audit)

manifest={'delivery_id':'stage3e3_guo_remaining84_v1','locked_set_unchanged':True,'original_blind_126':{'path':str((PRIVATE/'locked_evaluation_126_guo_blind.csv').relative_to(ROOT)),'rows':126,'sha256':sha(PRIVATE/'locked_evaluation_126_guo_blind.csv')},'private_mapping_with_42':{'path':str((PRIVATE/'locked_evaluation_126_with_guo42_private.csv').relative_to(ROOT)),'verified':42,'pending':84,'sha256':sha(PRIVATE/'locked_evaluation_126_with_guo42_private.csv')},'controlled_delivery_remaining84':{'path':str(remaining_path.relative_to(ROOT)),'rows':84,'sha256':sha(remaining_path)},'privacy':'All three files contain third-party text and are gitignored; do not push to public GitHub.','forbidden_columns_absent':True,'q_length_proxy_distribution':dict(Counter(x['q_length_proxy'] for x in q))}
(EXP/'guo126_controlled_delivery_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(manifest,ensure_ascii=False,indent=2))

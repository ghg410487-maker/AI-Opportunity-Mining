from __future__ import annotations
import argparse,csv,hashlib,json,shutil,sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DEFAULT=Path(r'E:\xwechat_files\wxid_r4to3bbty1yu22_ff68\msg\file\2026-11\guo_stage3e1_opp42_submit_20261114.csv')
PRIVATE=ROOT/'experiments/datasets/stage3e3';DOC=ROOT/'docs/research_stage3/stage3e3';EXP=ROOT/'experiments/stage3e3'
def read(p):
    with Path(p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def write(p,rows,fields=None):
    fields=fields or list(rows[0]);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)
ap=argparse.ArgumentParser();ap.add_argument('--input',default=str(DEFAULT));a=ap.parse_args();src=Path(a.input)
if not src.exists():print(json.dumps({'status':'MISSING','required_path':str(src)},ensure_ascii=False));sys.exit(2)
rows=read(src);required={'record_id','human_opportunity_decision','human_review_reason','human_evidence_quality','reviewer','reviewed_at','review_status'}
if len(rows)!=42 or not required<=set(rows[0]) or len({x['record_id'] for x in rows})!=42:raise ValueError('郭42条文件行数、字段或record_id唯一性不合格')
dist=Counter(x['human_opportunity_decision'] for x in rows)
if dist!=Counter({'1':12,'0':29,'INSUFFICIENT':1}):raise ValueError(f'人工分布与交接预期不一致: {dist}')
v1={x['record_id']:x for x in read(ROOT/'results/stage3e1/task2_internal_1984.csv')};v2={x['record_id']:x for x in read(ROOT/'results/stage3e2/task2_v2_internal_1984.csv')}
if any(i not in v1 or v1[i]['opportunity_status']!='1' for i in (x['record_id'] for x in rows)):raise ValueError('存在非v1机会候选或无法匹配ID')
PRIVATE.mkdir(parents=True,exist_ok=True);private=PRIVATE/'guo_stage3e1_opp42_submit_20261114.csv';shutil.copyfile(src,private)
out=[]
for x in rows:
    z=v2[x['record_id']];reason=x['human_review_reason'];kind='PASS' if reason.startswith('D1–D6=PASS') else (reason.split('｜',1)[0] if '｜' in reason else 'INSUFFICIENT')
    out.append({'record_id':x['record_id'],'human_decision':x['human_opportunity_decision'],'v1_status':'1','v2_status':z['opportunity_status'],'error_type':kind,'review_status':x['review_status'],'reviewed_at':x['reviewed_at'],'evidence_quality_status':'MISSING' if not x['human_evidence_quality'].strip() else 'PRESENT'})
write(DOC/'guo42_v1_v2_comparison.csv',out)
locked=read(PRIVATE/'locked_evaluation_126_private.csv');human={x['record_id']:x for x in rows};merged=[]
for x in locked:
    y=dict(x);h=human.get(x['record_id'])
    if h:
        y['human_opportunity_label']=h['human_opportunity_decision'];y['human_reason']=h['human_review_reason'];y['human_evidence']='';y['reviewer_id']=h['reviewer'];y['review_status']='VERIFIED';y['human_evidence_quality']=h['human_evidence_quality'];y['human_reviewed_at']=h['reviewed_at']
    else:
        y['human_evidence_quality']='';y['human_reviewed_at']=''
    merged.append(y)
write(PRIVATE/'locked_evaluation_126_with_guo42_private.csv',merged)
cross=Counter((x['human_decision'],x['v2_status']) for x in out)
summary={'source_path':str(src),'private_copy':str(private.relative_to(ROOT)),'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'rows':42,'unique_record_ids':42,'human_distribution':dict(dist),'empty_reasons':sum(not x['human_review_reason'].strip() for x in rows),'empty_evidence_quality':sum(not x['human_evidence_quality'].strip() for x in rows),'review_status':dict(Counter(x['review_status'] for x in rows)),'v2_distribution':dict(Counter(x['v2_status'] for x in out)),'v2_human_cross':{f'{a}|{b}':n for (a,b),n in cross.items()},'v1_candidate_confirmation_determinate':12/41,'v1_candidate_confirmation_all42_lower_bound':12/42,'v2_retained_human_opportunities':4,'v2_human_opportunities_total':12,'v2_opportunity_retention_rate':4/12,'v2_positive_precision_on_this_audit':4/12,'error_types':dict(Counter(x['error_type'] for x in out)),'scope_warning':'该42条均由v1预测为1，只支持候选精确率审计，不支持全量Accuracy/Recall/Macro-F1。'}
(EXP/'guo42_ingestion_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False,indent=2))

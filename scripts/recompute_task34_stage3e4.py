from __future__ import annotations
import argparse,csv,json,math,sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from edumine.baselines import TfidfVectorizerLite,kmeans_sparse
from edumine.competition import FUNCTION_LABELS,INDUSTRY_LABELS,_function_label
from edumine.stage3e4 import RESULT3_HEADER,RESULT4_HEADER,read_csv,validate_task34,write_csv
ap=argparse.ArgumentParser();ap.add_argument('--result1',default=str(ROOT/'data/frozen/result1_Final_All.csv'));ap.add_argument('--approved-result2',required=True);ap.add_argument('--output-dir',default=str(ROOT/'results/stage3e4/task34_candidate'));ap.add_argument('--k',type=int,default=5);a=ap.parse_args()
if not Path(a.approved_result2).exists():print(json.dumps({'status':'BLOCKED','reason':'approved_result2_missing'},ensure_ascii=False));sys.exit(2)
master=read_csv(a.result1);by={x['记录编号']:x for x in master};r2=read_csv(a.approved_result2);opps=[x for x in r2 if x['是否构成机会']=='1'];texts=[by[x['记录编号']]['内容'] for x in opps]
if not opps:print(json.dumps({'status':'BLOCKED','reason':'no_approved_opportunities'},ensure_ascii=False));sys.exit(2)
X=TfidfVectorizerLite((2,4),6000).fit_transform(texts);assign=kmeans_sparse(X,min(a.k,len(opps)));r3=[]
for c in sorted(set(assign)):
 xs=[x for x,z in zip(opps,assign) if z==c];func=Counter(x['功能类别'] or _function_label(by[x['记录编号']]['内容']) for x in xs).most_common(1)[0][0];sources=sorted({by[x['记录编号']]['来源网站名称'] for x in xs});cid=f'F-C{c+1:03d}'
 r3.append({'采集批次号':'ALL','主题簇编号':cid,'主题簇名称':f'{func}机会主题候选{c+1}','功能类别':func,'所属行业':'教育','簇内机会记录数':len(xs),'来源覆盖':'；'.join(sources),'簇内机会记录':'；'.join(x['记录编号'] for x in xs)})
raw=[{'c':c,'source':len(c['来源覆盖'].split('；')),'size':len(c['簇内机会记录'].split('；'))} for c in r3];r4=[]
for x in raw:
 score=round(60*x['source']/max(z['source'] for z in raw)+40*x['size']/max(z['size'] for z in raw),2);c=x['c'];r4.append({'采集批次号':c['采集批次号'],'主题簇编号':c['主题簇编号'],'主题簇名称':c['主题簇名称'],'功能类别':c['功能类别'],'所属行业':c['所属行业'],'机会价值分':score,'优先级':0})
for rank,x in enumerate(sorted(r4,key=lambda z:-z['机会价值分']),1):x['优先级']=rank
errors=validate_task34(r2,r3,r4,set(FUNCTION_LABELS),set(INDUSTRY_LABELS));out=Path(a.output_dir);out.mkdir(parents=True,exist_ok=True);write_csv(out/'result3_candidate_needs_theme_review.csv',r3,RESULT3_HEADER);write_csv(out/'result4_candidate.csv',r4,RESULT4_HEADER);report={'status':'READY_CANDIDATE_NEEDS_THEME_REVIEW' if not errors else 'FAILED','opportunities':len(opps),'clusters':len(r3),'errors':errors,'historical_baselines_overwritten':False};(out/'task234_consistency.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=False,indent=2));sys.exit(0 if not errors else 1)

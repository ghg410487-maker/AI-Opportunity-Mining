from __future__ import annotations

import csv, hashlib, json, math, random, sys
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from edumine.baselines import TfidfVectorizerLite, kmeans_sparse
from edumine.competition import _function_label, extract_need, load_result1
from edumine.stage3e2 import DIMENSIONS, evidence_quality, judge_task2_v2, ngram_set, jaccard, review_root_cause

DATA=ROOT/'data/frozen/result1_Final_All.csv'; V1=ROOT/'results/stage3e1'; RES=ROOT/'results/stage3e2'; EXP=ROOT/'experiments/stage3e2'; DOC=ROOT/'docs/research_stage3/stage3e2'
for p in (RES,EXP,DOC):p.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read_csv(p):
    with Path(p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def write_csv(p,rows,fields):
    with Path(p).open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)

records=load_result1(DATA); by_id={r['记录编号']:r for r in records}
v1rows=read_csv(V1/'task2_internal_1984.csv'); v1by={r['record_id']:r for r in v1rows}
extracts={x['record_id']:x for x in map(json.loads,(V1/'task2_extractions_1984.jsonl').read_text(encoding='utf-8').splitlines())}

# REVIEW diagnostics from the frozen v1 baseline.
reviews=[r for r in v1rows if r['opportunity_status']=='REVIEW']; blocker=[]
for d in DIMENSIONS:
    blocker.append({'dimension':d,'blocked_count':sum(int(r[d])<1 for r in reviews),'blocked_rate':round(sum(int(r[d])<1 for r in reviews)/len(reviews),6)})
write_csv(DOC/'review_dimension_blockers.csv',blocker,['dimension','blocked_count','blocked_rate'])
co=[]
for a in DIMENSIONS:
    for b in DIMENSIONS:
        co.append({'dimension_a':a,'dimension_b':b,'joint_blocked_count':sum(int(r[a])<1 and int(r[b])<1 for r in reviews)})
write_csv(DOC/'review_coblocker_matrix.csv',co,['dimension_a','dimension_b','joint_blocked_count'])

root_rows=[]
for r in reviews:
    rec=by_id[r['record_id']]; scores={d:int(r[d]) for d in DIMENSIONS}; primary,causes=review_root_cause(scores,rec['内容'])
    root_rows.append({'record_id':r['record_id'],'source_name':r['source_name'],'source_url':r['source_url'],'evidence_level':judge_task2_v2(rec,extracts[r['record_id']])['evidence_level'],'primary_root_cause':primary,'all_root_causes':'|'.join(causes),'blocked_dimensions':'|'.join(d for d in DIMENSIONS if scores[d]<1),'content_length':len(rec['内容'] or ''),'human_review_status':'PENDING','human_root_cause':'','human_review_note':''})
write_csv(DOC/'review_root_causes_595.csv',root_rows,list(root_rows[0]))
cross=[]
for source in sorted({x['source_name'] for x in root_rows}):
    for level in ('TITLE_LIKE','SHORT_CONTENT','SUBSTANTIVE_CONTENT','EMPTY_CONTENT'):
        subset=[x for x in root_rows if x['source_name']==source and x['evidence_level']==level]
        if not subset:continue
        for d in DIMENSIONS:
            cross.append({'source_name':source,'evidence_level':level,'dimension':d,'group_records':len(subset),'blocked_count':sum(d in x['blocked_dimensions'].split('|') for x in subset)})
write_csv(DOC/'review_blockers_by_source_evidence.csv',cross,['source_name','evidence_level','dimension','group_records','blocked_count'])

# Deterministic stratified sample by primary cause; human outcome remains blank.
rng=random.Random(20261114); buckets=defaultdict(list)
for x in root_rows:buckets[x['primary_root_cause']].append(x)
sample=[]
for key,xs in sorted(buckets.items()):
    rng.shuffle(xs); sample.extend(xs[:min(10,len(xs))])
if len(sample)<60:
    remaining=[x for x in root_rows if x not in sample];rng.shuffle(remaining);sample.extend(remaining[:60-len(sample)])
sample=sample[:60]
sample_rows=[]
for x in sample:
    rec=by_id[x['record_id']]; sample_rows.append({**x,'content_excerpt':(rec['内容'] or '')[:500],'algorithm_analysis':f"主因候选={x['primary_root_cause']}；阻断维度={x['blocked_dimensions']}。该判断仅为规则归因假设。"})
write_csv(DOC/'review_sample_analysis.csv',sample_rows,list(sample_rows[0]))

# v2 candidate, transition table, additive unified v1.1.
v2rows=[]; unified_v1=[json.loads(x) for x in (V1/'unified_records.jsonl').read_text(encoding='utf-8').splitlines()]
with (RES/'unified_records_v1_1.jsonl').open('w',encoding='utf-8') as uf:
    for old,rec in zip(unified_v1,records):
        ext=extracts[rec['记录编号']]; d=judge_task2_v2(rec,ext); q=evidence_quality(rec,d,ext); s=d['dimension_scores']
        row={'record_id':rec['记录编号'],'source_name':rec['来源网站名称'],'source_url':rec['来源链接'],'evidence_level':d['evidence_level'],**s,'opportunity_status':d['opportunity_status'],'decision_version':d['decision_version'],'evidence_quality_score':q,'decision_reason':d['decision_reason'],'generic_question_only':d['flags']['generic_question_only'],'supply_only':d['flags']['supply_only'],'direct_demand_evidence':d['flags']['direct_demand_evidence'],'strong_pain_evidence':d['flags']['strong_pain_evidence']}
        v2rows.append(row); new=dict(old);new['schema_version']='competition_mvp_v1.1';new['task2_v2_candidate']={'t0_label':d['t0_label'],'dimensions':s,'status':d['opportunity_status'],'decision_version':d['decision_version'],'evidence_level':d['evidence_level'],'evidence_quality_score':q,'flags':d['flags']};uf.write(json.dumps(new,ensure_ascii=False)+'\n')
write_csv(RES/'task2_v2_internal_1984.csv',v2rows,list(v2rows[0]))
trans=[]
for x in v2rows:
    old=v1by[x['record_id']]['opportunity_status']; trans.append({'record_id':x['record_id'],'baseline_status':old,'improved_status':x['opportunity_status'],'transition':old+'->'+x['opportunity_status'],'evidence_level':x['evidence_level'],'evidence_quality_score':x['evidence_quality_score'],'human_review_status':'PENDING','human_verified_correct':''})
write_csv(EXP/'task2_v1_v2_transition.csv',trans,list(trans[0]))

# Legal official subset only; REVIEW remains blocked.
resolved=[x for x in v2rows if x['opportunity_status'] in ('0','1')]; blocked2=[x for x in v2rows if x['opportunity_status']=='REVIEW']
with (RES/'result2_v2_resolved_subset.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.writer(f);w.writerow(['采集批次号','记录编号','是否构成机会','机会置信度','功能类别','所属行业'])
    for x in resolved:
        base=v1by[x['record_id']];w.writerow([by_id[x['record_id']]['采集批次号'],x['record_id'],x['opportunity_status'],base['opportunity_confidence'],_function_label(by_id[x['record_id']]['内容']) if x['opportunity_status']=='1' else '','教育' if x['opportunity_status']=='1' else ''])
write_csv(RES/'result2_v2_export_blockers.csv',[{'record_id':x['record_id'],'internal_status':'REVIEW','reason':'证据或维度未决；不得映射为官方1'} for x in blocked2],['record_id','internal_status','reason'])

# Guo independent verification pack for all 42 v1 opportunities.
cluster_rows=read_csv(V1/'result3.csv'); cluster_by={rid:c['主题簇编号'] for c in cluster_rows for rid in c['簇内机会记录编号'].split(';') if rid}
guo=[]
for r in v1rows:
    if r['opportunity_status']!='1':continue
    rec=by_id[r['record_id']];ext=extracts[r['record_id']];v2=next(x for x in v2rows if x['record_id']==r['record_id']); risks=[]
    if v2['generic_question_only']:risks.append('GENERIC_QUESTION_FALSE_PAIN')
    if v2['supply_only']:risks.append('SUPPLY_CLAIM_NO_INDEPENDENT_DEMAND')
    if int(v2['demand_authenticity'])<1:risks.append('DEMAND_EVIDENCE_MISSING')
    if v2['evidence_level']!='SUBSTANTIVE_CONTENT':risks.append('LIMITED_TEXT')
    if r['record_id']=='SUPER_part3-S00017':risks.append('KNOWN_T0_CONFLICT_OWNER_REVIEW_REQUIRED')
    guo.append({'record_id':r['record_id'],'source_name':r['source_name'],'source_url':r['source_url'],'cluster_id':cluster_by.get(r['record_id'],''),'original_content':rec['内容'],'user':ext['user'],'task':ext['task'],'pain':ext['pain'],'existing_solution':ext['existing_solution'],'evidence_excerpt':ext['evidence_excerpt'],'baseline_D1_D6':'/'.join(r[d] for d in DIMENSIONS),'baseline_status':'1','v2_D1_D6':'/'.join(str(v2[d]) for d in DIMENSIONS),'v2_candidate_status':v2['opportunity_status'],'evidence_level':v2['evidence_level'],'risk_flags':'|'.join(risks) or 'NO_AUTOMATIC_RISK_FLAG','guo_verified_opportunity':'','guo_verified_reason':'','guo_evidence_assessment':'','verification_status':'PENDING'})
write_csv(DOC/'guo_opportunity42_verification.csv',guo,list(guo[0]))

# Cluster diagnostics and k sweep on the unchanged v1 42 opportunities.
opp=[r for r in records if v1by[r['记录编号']]['opportunity_status']=='1']; texts=[r['内容'] for r in opp]
vec=TfidfVectorizerLite((2,4),6000);X=vec.fit_transform(texts)
def dot(a,b):return sum(v*b.get(k,0) for k,v in a.items())
def silhouette(assign):
    vals=[]
    for i,a in enumerate(assign):
        same=[1-dot(X[i],X[j]) for j in range(len(X)) if i!=j and assign[j]==a]
        others=[]
        for c in set(assign)-{a}:
            ds=[1-dot(X[i],X[j]) for j in range(len(X)) if assign[j]==c]
            if ds:others.append(sum(ds)/len(ds))
        aa=sum(same)/len(same) if same else 0;bb=min(others) if others else 0
        vals.append((bb-aa)/max(aa,bb) if max(aa,bb)>0 and same else 0)
    return sum(vals)/len(vals)
def rand_index(a,b):
    pairs=list(combinations(range(len(a)),2));return sum((a[i]==a[j])==(b[i]==b[j]) for i,j in pairs)/len(pairs)
ks=[]
for k in range(2,9):
    runs=[kmeans_sparse(X,k,seed=20261114+s) for s in range(3)]; st=sum(rand_index(a,b) for a,b in combinations(runs,2))/3
    a=runs[0]; singles=sum(len({opp[i]['来源网站名称'] for i,x in enumerate(a) if x==c})==1 for c in set(a))
    ks.append({'k':k,'silhouette_proxy':round(silhouette(a),6),'seed_stability_rand_index':round(st,6),'min_cluster_size':min(Counter(a).values()),'single_source_clusters':singles})
write_csv(EXP/'cluster_k_sweep.csv',ks,list(ks[0]))
audit=[]
for c in cluster_rows:
    ids=c['簇内机会记录编号'].split(';');rs=[by_id[x] for x in ids];grams=[ngram_set(x['内容']) for x in rs];pairs=[jaccard(a,b) for a,b in combinations(grams,2)]
    sources=Counter(x['来源网站名称'] for x in rs);maxshare=max(sources.values())/len(rs)
    audit.append({'cluster_id':c['主题簇编号'],'cluster_name':c['主题簇名称'],'sample_size':len(rs),'source_count':len(sources),'dominant_source_share':round(maxshare,4),'source_independence':'LOW' if len(sources)==1 else ('HIGH' if len(sources)>=3 and maxshare<=.7 else 'MEDIUM'),'mean_pairwise_char3_jaccard':round(sum(pairs)/len(pairs),6) if pairs else 0,'exact_content_duplicates':len(rs)-len({hashlib.sha256(x['内容'].encode()).hexdigest() for x in rs}),'risk_flagged_records':sum(next(g for g in guo if g['record_id']==x)['risk_flags']!='NO_AUTOMATIC_RISK_FLAG' for x in ids),'record_ids':';'.join(ids)})
write_csv(DOC/'cluster5_audit.csv',audit,list(audit[0]))

# Task4 evidence constraint and sensitivity, preserving original score.
result4=read_csv(V1/'result4.csv'); quality={x['record_id']:float(x['evidence_quality_score']) for x in v2rows}; sens=[]; constrained=[]
for r in result4:
    ids=next(c['簇内机会记录编号'].split(';') for c in cluster_rows if c['主题簇编号']==r['主题簇编号']);q=sum(quality[x] for x in ids)/len(ids);base=float(r['机会价值分'])
    for lam in (0,.25,.5,.75,1):sens.append({'cluster_id':r['主题簇编号'],'lambda':lam,'ordinary_score':base,'evidence_quality':round(q,2),'constrained_score':round(base*(1-lam*(1-q/100)),2)})
    constrained.append({**r,'evidence_quality':round(q,2),'constraint_lambda':.5,'evidence_constrained_score':round(base*(1-.5*(1-q/100)),2)})
for lam in (0,.25,.5,.75,1):
    subset=sorted([x for x in sens if x['lambda']==lam],key=lambda x:-x['constrained_score'])
    for rank,x in enumerate(subset,1):x['rank']=rank
write_csv(EXP/'task4_score_sensitivity.csv',sens,['cluster_id','lambda','ordinary_score','evidence_quality','constrained_score','rank'])
write_csv(RES/'result4_evidence_constrained.csv',constrained,list(constrained[0]))

stats={'input_rows':len(records),'input_sha256':sha(DATA),'baseline_status':dict(Counter(x['opportunity_status'] for x in v1rows)),'v2_status':dict(Counter(x['opportunity_status'] for x in v2rows)),'transitions':dict(Counter(x['transition'] for x in trans)),'review_blockers':{x['dimension']:x['blocked_count'] for x in blocker},'review_primary_causes':dict(Counter(x['primary_root_cause'] for x in root_rows)),'review_evidence_levels':dict(Counter(x['evidence_level'] for x in root_rows)),'review_sources':dict(Counter(x['source_name'] for x in root_rows)),'guo_candidates':len(guo),'guo_pending':sum(x['verification_status']=='PENDING' for x in guo),'cluster_k_sweep':ks,'paid_api_calls':0,'human_review_results_available':False,'human_review_note':'郭独立核验尚未提交；不得将算法状态变化解释为准确率变化。'}
(EXP/'stage3e2_metrics.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2),encoding='utf-8')

manifest={'run_id':'stage3e2-20261114-v1','schema_version':'competition_mvp_v1.1','frozen_input_sha256':sha(DATA),'frozen_input_rows':len(records),'baseline_artifacts_preserved':True,'paid_api_calls':0,'outputs':{}}
for p in sorted(list(RES.glob('*'))+list(EXP.glob('*'))+list(DOC.glob('*.csv'))):
    if p.is_file():manifest['outputs'][str(p.relative_to(ROOT))]=sha(p)
(RES/'run_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
sum_lines=[]
for p in sorted(list(RES.glob('*'))+list(EXP.glob('*'))+list(DOC.glob('*'))):
    if p.is_file() and p.name!='SHA256SUMS.txt':sum_lines.append(f"{sha(p)}  {p.relative_to(ROOT).as_posix()}")
(DOC/'SHA256SUMS.txt').write_text('\n'.join(sum_lines)+'\n',encoding='utf-8')
print(json.dumps(stats,ensure_ascii=False,indent=2))

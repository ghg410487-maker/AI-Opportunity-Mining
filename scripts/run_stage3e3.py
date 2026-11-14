from __future__ import annotations
import csv,hashlib,json,math,random,sys,time
from collections import Counter,defaultdict
from itertools import combinations
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from edumine.baselines import TfidfVectorizerLite,kmeans_sparse
from edumine.competition import judge_task2,load_result1
from edumine.stage3e2 import DIMENSIONS,evidence_level
from edumine.stage3e2 import judge_task2_v2
from edumine.stage3e3 import DOMAIN_TERMS,hybrid_vectors,kendall_tau,rand_index,silhouette_proxy,weighted_score

DATA=ROOT/'data/frozen/result1_Final_All.csv';E1=ROOT/'results/stage3e1';E2=ROOT/'results/stage3e2'
DOC=ROOT/'docs/research_stage3/stage3e3';EXP=ROOT/'experiments/stage3e3';PRIVATE=ROOT/'experiments/datasets/stage3e3';RES=ROOT/'results/stage3e3'
for p in (DOC,EXP,PRIVATE,RES):p.mkdir(parents=True,exist_ok=True)
def readcsv(p):
    with Path(p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def writecsv(p,rows,fields=None):
    fields=fields or list(rows[0])
    with Path(p).open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

records=load_result1(DATA);by={r['记录编号']:r for r in records};v1=readcsv(E1/'task2_internal_1984.csv');v1by={x['record_id']:x for x in v1};v2=readcsv(E2/'task2_v2_internal_1984.csv');v2by={x['record_id']:x for x in v2}
extracts={x['record_id']:x for x in map(json.loads,(E1/'task2_extractions_1984.jsonl').read_text(encoding='utf-8').splitlines())}
bench={}
for name,fn in [('v1',judge_task2),('v2',judge_task2_v2)]:
    times=[]
    for _ in range(3):
        start=time.perf_counter()
        for r in records:fn(r,extracts[r['记录编号']])
        times.append(time.perf_counter()-start)
    bench[name]={'runs':3,'records_per_run':len(records),'median_seconds':round(sorted(times)[1],6),'records_per_second':round(len(records)/sorted(times)[1],2),'paid_api_calls':0}
(EXP/'task2_compute_benchmark.json').write_text(json.dumps(bench,ensure_ascii=False,indent=2),encoding='utf-8')

# Locked evaluation set: census of 42 v1 opportunities + probability samples of 0/REVIEW.
def stratified_sample(status,n,seed):
    pool=[x for x in v1 if x['opportunity_status']==status];groups=defaultdict(list)
    for x in pool:groups[(x['source_name'],evidence_level(by[x['record_id']]['内容']))].append(x)
    if len(groups)>n:raise ValueError('sample size cannot cover every stratum')
    target={k:n*len(xs)/len(pool) for k,xs in groups.items()};alloc={k:1 for k in groups}
    while sum(alloc.values())<n:
        eligible=[k for k,xs in groups.items() if alloc[k]<len(xs)]
        k=max(eligible,key=lambda z:(target[z]-alloc[z],len(groups[z]),z));alloc[k]+=1
    rng=random.Random(seed);out=[]
    for k,xs in sorted(groups.items()):
        rng.shuffle(xs);take=min(alloc[k],len(xs));p=take/len(xs) if xs else 0
        out.extend((x,k,p,len(xs),take) for x in xs[:take])
    assert len(out)==n
    return out
selected=[]
for x in [x for x in v1 if x['opportunity_status']=='1']:selected.append((x,(x['source_name'],evidence_level(by[x['record_id']]['内容'])),1.0,1,1,'V1_OPPORTUNITY_CENSUS'))
for status,seed in [('0',202611150),('REVIEW',202611151)]:
    for x,k,p,N,nn in stratified_sample(status,42,seed):selected.append((x,k,p,N,nn,f'V1_{status}_STRATIFIED'))
eval_rows=[]
for i,(x,k,p,N,nn,design) in enumerate(selected,1):
    r=by[x['record_id']];z=v2by[x['record_id']]
    eval_rows.append({'eval_id':f'E3E-{i:03d}','record_id':x['record_id'],'source_name':x['source_name'],'source_url':x['source_url'],'evidence_level':k[1],'sampling_group':design,'stratum':f'{x["opportunity_status"]}|{k[0]}|{k[1]}','stratum_population_N':N,'stratum_sample_n':nn,'inclusion_probability':round(p,8),'sample_weight':round(1/p,8),'v1_status_hidden_from_reviewer':x['opportunity_status'],'v2_status_hidden_from_reviewer':z['opportunity_status'],'content':r['内容'],'human_opportunity_label':'','human_reason':'','human_evidence':'','reviewer_id':'','review_status':'PENDING'})
writecsv(PRIVATE/'locked_evaluation_126_private.csv',eval_rows)
blind=[{k:v for k,v in x.items() if k not in ('sampling_group','stratum','stratum_population_N','stratum_sample_n','inclusion_probability','sample_weight','v1_status_hidden_from_reviewer','v2_status_hidden_from_reviewer')} for x in eval_rows]
random.Random(202611152).shuffle(blind)
for i,x in enumerate(blind,1):x['blind_order']=i
writecsv(PRIVATE/'locked_evaluation_126_guo_blind.csv',blind)
public=[{k:v for k,v in x.items() if k not in ('content','source_url','v1_status_hidden_from_reviewer','v2_status_hidden_from_reviewer')} for x in eval_rows]
writecsv(DOC/'locked_evaluation_126_manifest.csv',public)

# Human metrics intentionally pending.
metric_state={'evaluation_set_id':'stage3e3_locked_126_v1','rows':126,'opportunity_census':42,'nonop_probability_sample':42,'review_probability_sample':42,'completed_human_labels':0,'metrics_status':'PENDING_HUMAN_REVIEW','reportable_now':['sampling design','prediction distributions','runtime/cost'],'not_reportable_now':['Precision','Recall','Macro-F1','opportunity precision'],'recall_condition':'Only after all probability-sampled strata are labeled and weighted estimates are used.','paid_api_calls':0}
(EXP/'fair_evaluation_status.json').write_text(json.dumps(metric_state,ensure_ascii=False,indent=2),encoding='utf-8')

# REVIEW 601 disposition diagnostics; no automatic final mapping.
review=[x for x in v2 if x['opportunity_status']=='REVIEW'];disp=[]
for x in review:
    title=x['evidence_level']=='TITLE_LIKE';short=x['evidence_level']=='SHORT_CONTENT';d3=int(x['demand_authenticity']);d6=int(x['unmet_degree'])
    if title or short:cat='SUPPLEMENT_SOURCE_PRIORITY';action='优先补取正文；补证前保持REVIEW'
    elif x['supply_only']=='True' and d3==0 and d6==0:cat='REUSABLE_EXCLUSION_CANDIDATE_SUPPLY_ONLY';action='提交负责人批准排除规则；不得自动转0'
    elif x['generic_question_only']=='True' and d3==0:cat='REUSABLE_EXCLUSION_CANDIDATE_GENERIC_QUESTION';action='核验是否仅研究/教程问题；负责人批准后方可批量排除'
    elif d3==0 and d6==0:cat='DEMAND_AND_UNMET_MISSING';action='抽查用户证据；无证据仍保持REVIEW'
    elif int(x['ai_core'])==0:cat='AI_CORE_UNCLEAR';action='核验AI是否为核心实现而非背景词'
    else:cat='BOUNDARY_MANUAL_REVIEW';action='按D1-D6证据逐条复核'
    disp.append({'record_id':x['record_id'],'source_name':x['source_name'],'evidence_level':x['evidence_level'],'D3':d3,'D6':d6,'supply_only':x['supply_only'],'generic_question_only':x['generic_question_only'],'disposition_category':cat,'proposed_action':action,'owner_approval_status':'PENDING','final_official_label':''})
writecsv(DOC/'review601_disposition_queue.csv',disp)

# Task 3 char baseline vs word/char hybrid, k=3..6, 5 seeds.
opps=[by[x['record_id']] for x in v1 if x['opportunity_status']=='1'];texts=[x['内容'] for x in opps]
features={'CHAR':TfidfVectorizerLite((2,4),6000).fit_transform(texts),'HYBRID':hybrid_vectors(texts)};cl_rows=[];assignment_rows=[]
for feat,X in features.items():
    for k in range(3,7):
        runs=[kmeans_sparse(X,k,seed=20261114+s) for s in range(5)]
        stability=sum(rand_index(a,b) for a,b in combinations(runs,2))/10
        for seed,a in enumerate(runs):
            sources=[];names=[]
            for c in sorted(set(a)):
                ids=[i for i,z in enumerate(a) if z==c];src=len({opps[i]['来源网站名称'] for i in ids});sources.append(src)
                counts=Counter(t for i in ids for t in DOMAIN_TERMS if t in opps[i]['内容']);top=[t for t,_ in counts.most_common(2)];names.append('-'.join(top) if top else f'主题{c+1}')
                for i in ids:assignment_rows.append({'feature':feat,'k':k,'seed':seed,'cluster':c+1,'record_id':opps[i]['记录编号'],'theme_candidate':names[-1]})
            cl_rows.append({'feature':feat,'k':k,'seed':seed,'silhouette_proxy':round(silhouette_proxy(X,a),6),'cross_seed_stability':round(stability,6),'min_cluster_size':min(Counter(a).values()),'single_source_clusters':sum(s==1 for s in sources),'mean_sources_per_cluster':round(sum(sources)/len(sources),4),'unique_theme_ratio':round(len(set(names))/len(names),4)})
writecsv(EXP/'clustering_comparison.csv',cl_rows);writecsv(EXP/'clustering_assignments.csv',assignment_rows)

# Task 4 reconstruct dimensions, perturb weights, source balance, missing-demand impact.
clusters=readcsv(E1/'result3.csv');base_result=readcsv(E1/'result4.csv');base_score={x['主题簇编号']:float(x['机会价值分']) for x in base_result}
raw=[]
for c in clusters:
    ids=c['簇内机会记录编号'].split(';');xs=[v1by[i] for i in ids]
    by_source=defaultdict(list)
    for x in xs:by_source[x['source_name']].append(x)
    raw.append({'cluster_id':c['主题簇编号'],'source_diversity':len(by_source),'scale':math.log1p(len(xs)),'demand':sum(int(x['demand_authenticity']) for x in xs)/len(xs),'unmet':sum(int(x['unmet_degree']) for x in xs)/len(xs),'feasibility':sum(int(x['feasibility']) for x in xs)/len(xs),'source_balanced_scale':math.log1p(len(by_source)),'source_balanced_demand':sum(sum(int(x['demand_authenticity']) for x in ys)/len(ys) for ys in by_source.values())/len(by_source),'source_balanced_unmet':sum(sum(int(x['unmet_degree']) for x in ys)/len(ys) for ys in by_source.values())/len(by_source),'source_balanced_feasibility':sum(sum(int(x['feasibility']) for x in ys)/len(ys) for ys in by_source.values())/len(by_source),'demand_evidence_coverage':sum(int(x['demand_authenticity'])>0 for x in xs)/len(xs)})
def norm(rows,key):
    vals=[x[key] for x in rows];lo=min(vals);hi=max(vals);return {x['cluster_id']:(50 if hi==lo else 100*(x[key]-lo)/(hi-lo)) for x in rows}
dims={k:norm(raw,k) for k in ('source_diversity','scale','demand','unmet','feasibility')};balanced={k:norm(raw,'source_balanced_'+k if k!='source_diversity' else k) for k in ('source_diversity','scale','demand','unmet','feasibility')}
weights={'source_diversity':.25,'scale':.20,'demand':.20,'unmet':.20,'feasibility':.15};scenarios={'BASELINE':weights}
for key in weights:
    for factor,label in ((1.2,'PLUS20'),(.8,'MINUS20')):
        w={**weights,key:weights[key]*factor};s=sum(w.values());scenarios[f'{key}_{label}']={k:v/s for k,v in w.items()}
base_order=[x['主题簇编号'] for x in sorted(base_result,key=lambda z:int(z['优先级']))];score_rows=[]
for name,w in scenarios.items():
    vals={cid:weighted_score({k:dims[k][cid] for k in weights},w) for cid in base_order};order=sorted(vals,key=lambda x:-vals[x])
    for rank,cid in enumerate(order,1):score_rows.append({'experiment':'WEIGHT_PERTURBATION','scenario':name,'cluster_id':cid,'score':round(vals[cid],4),'rank':rank,'kendall_tau_vs_baseline':round(kendall_tau(base_order,order),4),'top3_overlap':len(set(base_order[:3])&set(order[:3]))})
for mode in ('SOURCE_BALANCED','MISSING_DEMAND_PENALTY'):
    vals={}
    for x in raw:
        cid=x['cluster_id'];dd={k:(balanced[k][cid] if mode=='SOURCE_BALANCED' else dims[k][cid]) for k in weights}
        if mode=='MISSING_DEMAND_PENALTY':dd['demand']*=x['demand_evidence_coverage']
        vals[cid]=weighted_score(dd,weights)
    order=sorted(vals,key=lambda x:-vals[x])
    for rank,cid in enumerate(order,1):score_rows.append({'experiment':mode,'scenario':mode,'cluster_id':cid,'score':round(vals[cid],4),'rank':rank,'kendall_tau_vs_baseline':round(kendall_tau(base_order,order),4),'top3_overlap':len(set(base_order[:3])&set(order[:3]))})
# Append lambda sensitivity produced in 3E-2.
for x in readcsv(ROOT/'experiments/stage3e2/task4_score_sensitivity.csv'):
    score_rows.append({'experiment':'EVIDENCE_LAMBDA','scenario':'lambda='+x['lambda'],'cluster_id':x['cluster_id'],'score':x['constrained_score'],'rank':x['rank'],'kendall_tau_vs_baseline':'','top3_overlap':''})
writecsv(EXP/'task4_full_sensitivity.csv',score_rows)

config={'config_id':'stage3e3_algorithm_freeze_candidate_v1','freeze_target_date':'2026-11-17','task2':{'production':'task2_rule_v1','candidate':'task2_rule_v2_candidate','promotion_gate':'locked_126 human review + owner approval','internal_states':['1','0','REVIEW'],'official_mapping':{'1':'1','0':'0','REVIEW':'BLOCK_EXPORT'}},'task3':{'production':'char_tfidf_kmeans_k5','comparison':'hybrid_char_domain_terms_k3_to_k6','promotion_gate':'human theme consistency review'},'task4':{'production':'five_dimension_weighted_v1','weights':weights,'audit_candidate':'evidence_constraint_lambda_0.5','promotion_gate':'owner weight approval'},'interface':{'stable':'competition_mvp_v1','additive_candidate':'competition_mvp_v1.1','zhao_action':'No breaking change; candidate fields feature-flagged'},'paid_api_calls':0}
(DOC/'final_algorithm_config.json').write_text(json.dumps(config,ensure_ascii=False,indent=2),encoding='utf-8')

summary={'frozen_input_sha256':sha(DATA),'evaluation':metric_state,'review601_categories':dict(Counter(x['disposition_category'] for x in disp)),'task2_compute_benchmark':bench,'cluster_experiments':len(cl_rows),'scoring_rows':len(score_rows),'official_full_result2_ready':False,'official_blocker_count':601,'private_evaluation_path':str((PRIVATE/'locked_evaluation_126_private.csv').relative_to(ROOT)),'paid_api_calls':0}
(EXP/'stage3e3_run_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False,indent=2))

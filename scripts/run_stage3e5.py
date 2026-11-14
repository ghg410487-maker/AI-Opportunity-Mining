from __future__ import annotations
import csv, hashlib, json, math, shutil, zipfile
from collections import Counter, defaultdict
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]; DOC=ROOT/'docs/research_stage3/stage3e5'; EXP=ROOT/'experiments/stage3e5'; PRIV=ROOT/'experiments/datasets/stage3e5'
SRC=Path(r'E:\xwechat_files\wxid_r4to3bbty1yu22_ff68\msg\file\2026-11')
P84=SRC/'guo_remaining84_submit_20261114.csv'; PX=SRC/'locked_evaluation_remaining84_guo_blind.xlsx'; PC=SRC/'guo_G2_cluster5_review_official(1).csv'; PM=SRC/'guo_G2_cluster5_explanation.md'
EXPECTED84='A385E3B92F25D15EC59F12816E7BCE2EF5EE3808A18CC9D4F37F27EE3EC39377'

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def read(p):
    with Path(p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def write(p,rows,fields=None):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);fields=fields or list(rows[0])
    with p.open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)
def xlsx_rows(p):
    ns={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
    with zipfile.ZipFile(p) as z:
        ss=[]
        if 'xl/sharedStrings.xml' in z.namelist():
            root=ET.fromstring(z.read('xl/sharedStrings.xml'))
            for si in root.findall('m:si',ns):ss.append(''.join(t.text or '' for t in si.iter('{%s}t'%ns['m'])))
        wb=ET.fromstring(z.read('xl/workbook.xml')); rel=ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
        rmap={x.attrib['Id']:x.attrib['Target'] for x in rel}
        sheet=wb.find('m:sheets/m:sheet',ns); target=rmap[sheet.attrib['{%s}id'%ns['r']]]; target='xl/'+target.lstrip('/') if not target.startswith('xl/') else target
        root=ET.fromstring(z.read(target)); table=[]
        for row in root.findall('.//m:sheetData/m:row',ns):
            vals={}
            for c in row.findall('m:c',ns):
                ref=c.attrib['r']; col=''.join(ch for ch in ref if ch.isalpha()); v=c.find('m:v',ns); inline=c.find('m:is/m:t',ns)
                val='' if v is None and inline is None else (inline.text or '' if inline is not None else v.text or '')
                if c.attrib.get('t')=='s' and val!='':val=ss[int(val)]
                vals[col]=val
            table.append(vals)
        def n(col):
            x=0
            for ch in col:x=x*26+ord(ch)-64
            return x
        cols=sorted(table[0],key=n); hdr=[table[0].get(c,'') for c in cols]
        return [{h:r.get(c,'') for h,c in zip(hdr,cols)} for r in table[1:] if any(r.values())]
def f1(tp,fp,fn):
    p=tp/(tp+fp) if tp+fp else None;r=tp/(tp+fn) if tp+fn else None
    return p,r,(2*p*r/(p+r) if p is not None and r is not None and p+r else None)
def fmt(x):return 'NA' if x is None else f'{x:.4f}'

DOC.mkdir(parents=True,exist_ok=True);EXP.mkdir(parents=True,exist_ok=True);PRIV.mkdir(parents=True,exist_ok=True)
assert sha(P84)==EXPECTED84
manifest=read(ROOT/'docs/research_stage3/stage3e3/locked_evaluation_126_manifest.csv'); assert len(manifest)==126 and len({x['eval_id'] for x in manifest})==126 and len({x['record_id'] for x in manifest})==126
by_eval={x['eval_id']:x for x in manifest};by_rec={x['record_id']:x for x in manifest}
master=read(ROOT/'data/frozen/result1_Final_All.csv');bm={x['记录编号']:x for x in master}
h42=read(ROOT/'experiments/datasets/stage3e3/guo_stage3e1_opp42_submit_20261114.csv');h84=read(P84); assert len(h84)==84 and len({x['eval_id'] for x in h84})==84 and len({x['record_id'] for x in h84})==84
ids42={x['record_id'] for x in h42};ids84={x['record_id'] for x in h84};assert not ids42&ids84 and ids42|ids84==set(by_rec)
assert all(x['eval_id'] in by_eval and by_eval[x['eval_id']]['record_id']==x['record_id'] for x in h84)
blind_csv=read(ROOT/'experiments/datasets/stage3e3/locked_evaluation_remaining84_guo_blind.csv'); blind_x=xlsx_rows(PX)
bx={x.get('eval_id',''):x for x in blind_x};bc={x['eval_id']:x for x in blind_csv};assert set(bx)==set(bc)=={x['eval_id'] for x in h84}
immutable=['eval_id','record_id','source_name','source_url','original_title','original_text','evidence_type']
xlsx_mismatch=[]
for eid in bx:
    for k in immutable:
        if k in bx[eid] and k in bc[eid] and str(bx[eid][k])!=str(bc[eid][k]):xlsx_mismatch.append(f'{eid}:{k}')

combined=[]
for x in h42:
    m=by_rec[x['record_id']];lab=x['human_opportunity_decision']
    combined.append({**m,'human_label_original':lab,'human_reason_original':x['human_review_reason'],'human_evidence_original':x['human_evidence_quality'],'reviewer_id_original':x['reviewer'],'review_status_original':x['review_status'],'normalized_review_status':'COMPLETED','submission_batch':'ORIGINAL42'})
for x in h84:
    m=by_eval[x['eval_id']];combined.append({**m,'human_label_original':x['human_opportunity_label'],'human_reason_original':x['human_reason'],'human_evidence_original':x['human_evidence'],'reviewer_id_original':x['reviewer_id'],'review_status_original':x['review_status'],'normalized_review_status':'COMPLETED','submission_batch':'REMAINING84'})
combined=sorted(combined,key=lambda z:z['eval_id']);write(PRIV/'locked_evaluation_126_human_private.csv',combined)
for x in combined:x['source_name']=bm[x['record_id']]['来源网站名称']
write(PRIV/'locked_evaluation_126_human_private.csv',combined)
counts=Counter(x['human_label_original'] for x in combined);assert counts=={'0':98,'1':14,'INSUFFICIENT':14}

v1=read(ROOT/'results/stage3e1/task2_internal_1984.csv');v2=read(ROOT/'results/stage3e2/task2_v2_internal_1984.csv');b1={x['record_id']:x for x in v1};b2={x['record_id']:x for x in v2}
detail=[];metrics={}
for version,bv in [('v1',b1),('v2',b2)]:
    tp=fp=tn=fn=0; abst_pos=abst_neg=0; wtp=wfp=wtn=wfn=wabp=wabn=0.0;dec=0
    by_source=defaultdict(Counter);by_evidence=defaultdict(Counter)
    for x in combined:
        pred=bv[x['record_id']]['opportunity_status'];lab=x['human_label_original'];w=float(x['sample_weight'])
        detail.append({'eval_id':x['eval_id'],'record_id':x['record_id'],'human_label':lab,'sample_weight':w,'sampling_group':x['sampling_group'],'source_name':x['source_name'],'evidence_level':x['evidence_level'],f'{version}_prediction':pred})
        if lab not in ('0','1'):continue
        key=f'h{lab}_p{pred}';by_source[x['source_name']][key]+=1;by_evidence[x['evidence_level']][key]+=1
        if pred=='REVIEW':
            if lab=='1':abst_pos+=1;wabp+=w
            else:abst_neg+=1;wabn+=w
        else:
            dec+=1
            if lab=='1' and pred=='1':tp+=1;wtp+=w
            elif lab=='0' and pred=='1':fp+=1;wfp+=w
            elif lab=='0' and pred=='0':tn+=1;wtn+=w
            elif lab=='1' and pred=='0':fn+=1;wfn+=w
    p,r,F=f1(tp,fp,fn);wp,wr,wF=f1(wtp,wfp,wfn)
    metrics[version]={'tp':tp,'fp':fp,'tn':tn,'fn':fn,'review_human1':abst_pos,'review_human0':abst_neg,'conditional_precision':p,'conditional_recall':r,'conditional_f1':F,'selective_coverage_112':dec/112,'review_coverage_112':(abst_pos+abst_neg)/112,'weighted_tp':wtp,'weighted_fp':wfp,'weighted_tn':wtn,'weighted_fn':wfn,'weighted_review_human1':wabp,'weighted_review_human0':wabn,'weighted_conditional_precision':wp,'weighted_conditional_recall':wr,'weighted_conditional_f1':wF,'source_errors':by_source,'evidence_errors':by_evidence}
write(PRIV/'v1_v2_human126_detail_private.csv',detail)

ins=[x for x in combined if x['human_label_original']=='INSUFFICIENT'];assert len(ins)==14
ins_rows=[]
for x in ins:ins_rows.append({'eval_id':x['eval_id'],'record_id':x['record_id'],'source_name':x['source_name'],'evidence_level':x['evidence_level'],'v1_status':b1[x['record_id']]['opportunity_status'],'v2_status':b2[x['record_id']]['opportunity_status'],'human_status':'INSUFFICIENT','reason':x['human_reason_original']})
write(PRIV/'insufficient14_private.csv',ins_rows)

positives=[x for x in combined if x['human_label_original']=='1'];boundary=[]
for x in positives:
    z=b2[x['record_id']]
    boundary.append({'record_id':x['record_id'],'submission_batch':x['submission_batch'],'human_original_label':'1','human_original_reason':x['human_reason_original'],'evidence_level':x['evidence_level'],'D2_problem_clarity':z['problem_clarity'],'D3_demand_authenticity':z['demand_authenticity'],'D4_ai_core':z['ai_core'],'D6_unmet_degree':z['unmet_degree'],'supply_only':z['supply_only'],'direct_demand_evidence':z['direct_demand_evidence'],'strong_pain_evidence':z['strong_pain_evidence'],'boundary_focus':'SUPPLY_SELF_REPORT_PRIORITY' if x['record_id'] in {'SUPER_part10-S00275','B12-S00181','B11-S00550','B12-S00013'} else 'STANDARD_POSITIVE_REVIEW','owner_final_label':'','owner_final_reason':'','review_status':'PENDING_OWNER_REVIEW'})
write(PRIV/'human_positive14_boundary_review.csv',boundary)

clusters=read(PC);assert len(clusters)==5 and len({x['cluster_id'] for x in clusters})==5
assert sum(int(x['human_positive_count']) for x in clusters)==12 and sum(int(x['human_negative_count']) for x in clusters)==29 and sum(int(x['insufficient_count']) for x in clusters)==1 and sum(int(x['machine_record_count']) for x in clusters)==42
write(PRIV/'cluster5_official_human_review_preserved.csv',clusters)

q4=read(EXP.parent/'stage3e4/review601_audit.csv');q5=[];human_by={x['record_id']:x for x in combined};cand27=[]
for q in q4:
    rid=q['record_id'];h=human_by.get(rid);z=b2[rid]
    row={**q,'human126_overlap':'YES' if h else 'NO','human126_label':h['human_label_original'] if h else '','human126_reason':h['human_reason_original'] if h else '','stage3e5_review_status':'PENDING_OWNER_APPROVAL'};q5.append(row)
    if q['disposition_group']=='REUSABLE_EXCLUSION_CANDIDATE_SUPPLY_ONLY' and str(z['strong_pain_evidence']).lower()!='true':
        text=bm[rid]['内容'];cand27.append({'record_id':rid,'source_name':q['source_name'],'evidence_level':q['evidence_level'],'content_sha256':hashlib.sha256(text.encode('utf-8')).hexdigest().upper(),'rule_evidence_excerpt':text[:240].replace('\n',' '),'supply_only':z['supply_only'],'strong_pain_evidence':z['strong_pain_evidence'],'human126_label':h['human_label_original'] if h else '','proposed_label':'0','owner_final_label':'','owner_final_reason':'','approval_status':'PENDING_APPROVAL'})
write(PRIV/'review601_stage3e5_private.csv',q5);write(PRIV/'narrow_exclusion27_owner_workbench_private.csv',cand27);assert len(cand27)==27

summary={'input84_sha256':sha(P84),'xlsx_sha256':sha(PX),'cluster_review_sha256':sha(PC),'manifest_rows':126,'remaining84_rows':84,'xlsx_rows':len(blind_x),'xlsx_csv_immutable_mismatches':xlsx_mismatch,'human_counts':counts,'combined_sha256':sha(PRIV/'locked_evaluation_126_human_private.csv'),'metrics':metrics,'insufficient_v1':Counter(x['v1_status'] for x in ins_rows),'insufficient_v2':Counter(x['v2_status'] for x in ins_rows),'candidate27_human_overlap':Counter(x['human126_label'] for x in cand27 if x['human126_label']),'review601_owner_approved':0,'review601_pending':601,'cluster_counts':[{'cluster_id':x['cluster_id'],'positive':int(x['human_positive_count']),'negative':int(x['human_negative_count']),'insufficient':int(x['insufficient_count']),'decision':x['recommendation_decision']} for x in clusters]}
for key,group in [('broad31','REUSABLE_EXCLUSION_CANDIDATE_SUPPLY_ONLY'),('generic3','REUSABLE_EXCLUSION_CANDIDATE_GENERIC_QUESTION')]:
    xs=[x for x in q5 if x['disposition_group']==group]; summary[key]={'count':len(xs),'human_overlap':dict(Counter(x['human126_label'] for x in xs if x['human126_label']))}
summary['candidate27_nonempty_content']=sum(bool(bm[x['record_id']]['内容'].strip()) for x in cand27)
(EXP/'stage3e5_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2,default=lambda x:dict(x)),encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False,indent=2,default=lambda x:dict(x)))

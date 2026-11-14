from __future__ import annotations
import argparse,csv,json,sys
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(p):
    with Path(p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
ap=argparse.ArgumentParser();ap.add_argument('--input',default=str(ROOT/'experiments/datasets/stage3e3/locked_evaluation_126_private.csv'));ap.add_argument('--output',default=str(ROOT/'experiments/stage3e3/human_metrics.json'));a=ap.parse_args()
rows=read(a.input);valid={'0','1'};complete=all(x['human_opportunity_label'] in valid and x['review_status']=='COMPLETED' for x in rows)
result={'evaluation_set_id':'stage3e3_locked_126_v1','rows':len(rows),'complete':complete,'metrics_status':'READY' if complete else 'PENDING_HUMAN_REVIEW','completed_rows':sum(x['human_opportunity_label'] in valid for x in rows),'required_rows':len(rows),'warning':'42 opportunity records alone support only v1 candidate precision audit; weighted overall metrics require all probability-sampled strata.'}
if complete:
    for version,key in [('v1','v1_status_hidden_from_reviewer'),('v2','v2_status_hidden_from_reviewer')]:
        cm=defaultdict(float)
        for x in rows:
            y=x['human_opportunity_label'];pred='1' if x[key]=='1' else '0';w=float(x['sample_weight']);cm[(y,pred)]+=w
        tp,fp,fn,tn=cm[('1','1')],cm[('0','1')],cm[('1','0')],cm[('0','0')]
        precision=tp/(tp+fp) if tp+fp else 0;recall=tp/(tp+fn) if tp+fn else 0
        f1=2*precision*recall/(precision+recall) if precision+recall else 0
        p0=tn/(tn+fn) if tn+fn else 0;r0=tn/(tn+fp) if tn+fp else 0;f0=2*p0*r0/(p0+r0) if p0+r0 else 0
        result[version]={'weighted_precision_opportunity':precision,'weighted_recall_opportunity':recall,'weighted_f1_opportunity':f1,'weighted_macro_f1':(f1+f0)/2,'review_coverage':sum(float(x['sample_weight']) for x in rows if x[key]=='REVIEW')/sum(float(x['sample_weight']) for x in rows),'weighted_confusion':{'tp':tp,'fp':fp,'fn':fn,'tn':tn}}
Path(a.output).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=False,indent=2));sys.exit(0 if complete else 2)

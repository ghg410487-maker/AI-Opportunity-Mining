import csv
import json
import sys
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from edumine.competition import FUNCTION_LABELS, INDUSTRY_LABELS, RESULT2_HEADER, RESULT3_HEADER, RESULT4_HEADER

R=ROOT/'results/stage3e1'; E=ROOT/'experiments/stage3e1'
def read(name):
    with (R/name).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
task2=read('task2_internal_1984.csv'); resolved=read('result2_resolved_subset.csv'); blockers=read('result2_export_blockers.csv'); r3=read('result3.csv'); r4=read('result4.csv')
extracts=[json.loads(x) for x in (R/'task2_extractions_1984.jsonl').read_text(encoding='utf-8').splitlines() if x]
unified=[json.loads(x) for x in (R/'unified_records.jsonl').read_text(encoding='utf-8').splitlines() if x]
ids={x['record_id'] for x in task2}; opp={x['record_id'] for x in task2 if x['opportunity_status']=='1'}
cluster_ids=set(); clustered=set()
for x in r3:
    cluster_ids.add(x['主题簇编号']);clustered.update(filter(None,x['簇内机会记录编号'].split(';')))
checks={
'task2_rows_1984':len(task2)==1984,'task2_unique':len(ids)==1984,'extractions_1984':len(extracts)==1984,'unified_1984':len(unified)==1984,
'status_domain':set(x['opportunity_status'] for x in task2)<={'0','1','REVIEW'},'resolved_plus_blockers':len(resolved)+len(blockers)==1984,
'resolved_header':list(resolved[0])==list(RESULT2_HEADER),'resolved_domain':set(x['是否构成机会'] for x in resolved)<={'0','1'},
'function_domain':all((not x['功能类别']) or x['功能类别'] in FUNCTION_LABELS for x in resolved),'industry_domain':all((not x['所属行业']) or x['所属行业'] in INDUSTRY_LABELS for x in resolved),
'clusters_only_opportunities':clustered==opp,'result3_header':list(r3[0])==list(RESULT3_HEADER),'result4_header':list(r4[0])==list(RESULT4_HEADER),'result3_result4_clusters':cluster_ids=={x['主题簇编号'] for x in r4},
'review_never_in_resolved':not ({x['记录编号'] for x in resolved}&{x['记录编号'] for x in blockers})}
report={'passed':all(checks.values()),'checks':checks,'status_distribution':dict(Counter(x['opportunity_status'] for x in task2)),'t0_distribution':dict(Counter(x['t0_label'] for x in task2)),'rows':{'task2':len(task2),'resolved':len(resolved),'blockers':len(blockers),'result3':len(r3),'result4':len(r4)}}
(E/'end_to_end_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2));raise SystemExit(0 if report['passed'] else 1)

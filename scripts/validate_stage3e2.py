from __future__ import annotations
import csv, hashlib, json, sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def rows(p):
    with Path(p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def lines(p):return [json.loads(x) for x in Path(p).read_text(encoding='utf-8').splitlines()]
old=lines(ROOT/'results/stage3e1/unified_records.jsonl');new=lines(ROOT/'results/stage3e2/unified_records_v1_1.jsonl')
old2=rows(ROOT/'results/stage3e1/task2_internal_1984.csv');new2=rows(ROOT/'results/stage3e2/task2_v2_internal_1984.csv')
guo=rows(ROOT/'docs/research_stage3/stage3e2/guo_opportunity42_verification.csv')
roots=rows(ROOT/'docs/research_stage3/stage3e2/review_root_causes_595.csv')
blocked=rows(ROOT/'results/stage3e2/result2_v2_export_blockers.csv');resolved=rows(ROOT/'results/stage3e2/result2_v2_resolved_subset.csv')
checks={
 'v1_1984':len(old)==1984,'v1_1_1984':len(new)==1984,'task2_v2_1984':len(new2)==1984,
 'unique_v2':len({x['record_id'] for x in new2})==1984,
 'additive_contract':all({k:v for k,v in a.items() if k!='schema_version'}=={k:v for k,v in b.items() if k not in ('schema_version','task2_v2_candidate')} for a,b in zip(old,new)),
 'schema_v1_1':all(x['schema_version']=='competition_mvp_v1.1' and 'task2_v2_candidate' in x for x in new),
 'root_rows_595':len(roots)==595,'guo_42':len(guo)==42,'guo_all_pending':all(x['verification_status']=='PENDING' and not x['guo_verified_opportunity'] for x in guo),
 'resolved_plus_blocked':len(resolved)+len(blocked)==1984,
 'official_domain':{x['是否构成机会'] for x in resolved}<={'0','1'},
 'official_one_fields':all(x['功能类别'] and x['所属行业']=='教育' for x in resolved if x['是否构成机会']=='1'),
 'review_not_exported':not ({x['record_id'] for x in blocked}&{x['记录编号'] for x in resolved}),
}
result={'passed':all(checks.values()),'checks':checks,'v2_status':dict(Counter(x['opportunity_status'] for x in new2)),'resolved_rows':len(resolved),'blocked_rows':len(blocked),'paid_api_calls':0}
(ROOT/'experiments/stage3e2/end_to_end_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
targets=[]
for folder in (ROOT/'results/stage3e2',ROOT/'experiments/stage3e2',ROOT/'docs/research_stage3/stage3e2'):
    targets.extend(p for p in folder.glob('*') if p.is_file() and p.name!='SHA256SUMS.txt')
(ROOT/'docs/research_stage3/stage3e2/SHA256SUMS.txt').write_text('\n'.join(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(ROOT).as_posix()}" for p in sorted(targets))+'\n',encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2));sys.exit(0 if result['passed'] else 1)

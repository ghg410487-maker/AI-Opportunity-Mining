from __future__ import annotations
import csv,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];E=ROOT/'experiments/stage3e5';P=ROOT/'experiments/datasets/stage3e5'
def read(p):
    with Path(p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
checks=[]
def ck(n,v,d=''):checks.append({'check':n,'status':'PASS' if v else 'FAIL','detail':d})
s=json.loads((E/'stage3e5_summary.json').read_text(encoding='utf-8'))
c=read(P/'locked_evaluation_126_human_private.csv');q=read(P/'review601_stage3e5_private.csv');w=read(P/'narrow_exclusion27_owner_workbench_private.csv')
ck('input84_hash',s['input84_sha256']=='A385E3B92F25D15EC59F12816E7BCE2EF5EE3808A18CC9D4F37F27EE3EC39377')
ck('human126_unique',len(c)==126 and len({x['eval_id'] for x in c})==126 and len({x['record_id'] for x in c})==126)
ck('human_distribution',sum(x['human_label_original']=='1' for x in c)==14 and sum(x['human_label_original']=='0' for x in c)==98 and sum(x['human_label_original']=='INSUFFICIENT' for x in c)==14)
ck('original_status_preserved',all(x['review_status_original']=='VERIFIED' and x['normalized_review_status']=='COMPLETED' for x in c))
ck('xlsx_csv_identity',s['xlsx_rows']==84 and not s['xlsx_csv_immutable_mismatches'])
ck('review601_unique',len(q)==601 and len({x['record_id'] for x in q})==601)
ck('review601_pending',all(x['stage3e5_review_status']=='PENDING_OWNER_APPROVAL' and not x['proposed_official_label'] for x in q))
ck('candidate27_unique',len(w)==27 and len({x['record_id'] for x in w})==27)
ck('candidate27_not_approved',all(not x['owner_final_label'] and x['approval_status']=='PENDING_APPROVAL' for x in w))
ck('insufficient14',len(read(P/'insufficient14_private.csv'))==14)
ck('positive_boundary14',len(read(P/'human_positive14_boundary_review.csv'))==14)
ck('cluster5_counts',sum(x['positive'] for x in s['cluster_counts'])==12 and sum(x['negative'] for x in s['cluster_counts'])==29 and sum(x['insufficient'] for x in s['cluster_counts'])==1)
ck('formal_result2_absent',not (ROOT/'results/stage3e5/result2.csv').exists())
ck('frozen_master_hash',sha(ROOT/'data/frozen/result1_Final_All.csv')=='44C75335B3795C746FFC603B339BF6AA4D2E6945E38EBD0A8BCB9D39C9FF0A52')
ck('stage3e4_exporter_preserved',(ROOT/'scripts/export_official_stage3e4.py').exists())
(E/'stage3e5_validation.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(checks,ensure_ascii=False,indent=2));sys.exit(0 if all(x['status']=='PASS' for x in checks) else 1)

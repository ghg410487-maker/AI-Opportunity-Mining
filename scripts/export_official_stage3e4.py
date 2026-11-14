from __future__ import annotations
import argparse,csv,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from edumine.competition import FUNCTION_LABELS,INDUSTRY_LABELS
from edumine.stage3e4 import RESULT2_HEADER,build_official_result2,read_csv,sha256,write_csv
ap=argparse.ArgumentParser();ap.add_argument('--result1',default=str(ROOT/'data/frozen/result1_Final_All.csv'));ap.add_argument('--machine',default=str(ROOT/'results/stage3e2/task2_v2_internal_1984.csv'));ap.add_argument('--stable',default=str(ROOT/'results/stage3e1/task2_internal_1984.csv'));ap.add_argument('--resolved',default=str(ROOT/'results/stage3e2/result2_v2_resolved_subset.csv'));ap.add_argument('--approval',default=str(ROOT/'docs/research_stage3/stage3e4/owner_result2_approval_template.json'));ap.add_argument('--template');ap.add_argument('--output-dir',default=str(ROOT/'results/stage3e4'));a=ap.parse_args()
paths=[Path(x) for x in (a.result1,a.machine,a.stable,a.resolved,a.approval)];missing=[str(x) for x in paths if not x.exists()]
if missing:print(json.dumps({'status':'BLOCKED','reasons':['missing_input'],'missing':missing},ensure_ascii=False,indent=2));sys.exit(2)
if not a.template or not Path(a.template).exists():print(json.dumps({'status':'BLOCKED','reasons':['official_result2_template_missing_or_not_supplied']},ensure_ascii=False,indent=2));sys.exit(2)
with Path(a.template).open(encoding='utf-8-sig',newline='') as f:header=next(csv.reader(f))
if tuple(header)!=RESULT2_HEADER:print(json.dumps({'status':'BLOCKED','reasons':['official_template_header_mismatch'],'actual':header,'expected':RESULT2_HEADER},ensure_ascii=False,indent=2));sys.exit(2)
master,machine,stable,resolved=map(read_csv,paths[:4]);approval=json.loads(paths[4].read_text(encoding='utf-8'));rows,block=build_official_result2(master,machine,stable,resolved,approval,set(FUNCTION_LABELS),set(INDUSTRY_LABELS));out=Path(a.output_dir);out.mkdir(parents=True,exist_ok=True)
audit={'status':'BLOCKED' if block else 'READY','blocker_count':len(block),'blockers':block[:100],'input_hashes':{str(p):sha256(p) for p in paths+[Path(a.template)]},'approval_version':approval.get('approval_version'),'formal_filename_written':False}
if block:
    (out/'official_export_blocked.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(audit,ensure_ascii=False,indent=2));sys.exit(2)
write_csv(out/'result2_candidate_approved.csv',rows,RESULT2_HEADER);audit['candidate_path']='result2_candidate_approved.csv';audit['formal_filename_written']=False;(out/'official_export_validation.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(audit,ensure_ascii=False,indent=2))

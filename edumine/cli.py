import argparse
import json
import sys
import uuid
from pathlib import Path
from .core import analyze, audit, connect, deduplicate, import_file, report
from .normalization import export_normalization, normalize_all
from .competition import load_result1, run_tasks_2_to_5

def parser():
    p=argparse.ArgumentParser(prog="python -m edumine",description="EduMine V0.1 教育 AI 多源数据审计与分析工具箱")
    p.add_argument("--db",default="data/processed/edumine.sqlite3",help="SQLite 数据库路径")
    sub=p.add_subparsers(dest="command",required=True)
    x=sub.add_parser("import"); x.add_argument("--input",required=True,nargs="+"); x.add_argument("--batch")
    x=sub.add_parser("audit"); x.add_argument("--batch")
    x=sub.add_parser("deduplicate"); x.add_argument("--threshold",type=float,default=.82); x.add_argument("--content-source",choices=["original","cleaned"],default="original")
    x=sub.add_parser("normalize"); x.add_argument("--output",default="reports/normalization")
    sub.add_parser("analyze")
    x=sub.add_parser("report"); x.add_argument("--output",default="reports/latest")
    x=sub.add_parser("competition-mvp"); x.add_argument("--input",default="data/frozen/result1_Final_All.csv"); x.add_argument("--output",default="results/competition-mvp")
    return p

def main(argv=None):
    args=parser().parse_args(argv); db=connect(Path(args.db))
    run_id=f"cli-{uuid.uuid4().hex}"
    started=__import__("datetime").datetime.now().astimezone().isoformat(timespec="seconds")
    db.execute("INSERT INTO runs(run_id,command,started_at,status) VALUES(?,?,?,'RUNNING')",(run_id,args.command,started)); db.commit()
    try:
        if args.command=="import": result=[import_file(db,Path(p),args.batch) for p in args.input]
        elif args.command=="audit": result=audit(db,args.batch)
        elif args.command=="deduplicate": result=deduplicate(db,args.threshold,args.content_source)
        elif args.command=="normalize": result={"normalization":normalize_all(db),"export":export_normalization(db,Path(args.output))}
        elif args.command=="analyze": result=analyze(db)
        elif args.command=="report": result=report(db,Path(args.output))
        else: result=run_tasks_2_to_5(load_result1(Path(args.input)),Path(args.output))
        finished=__import__("datetime").datetime.now().astimezone().isoformat(timespec="seconds")
        db.execute("UPDATE runs SET finished_at=?,status='SUCCESS',details=? WHERE run_id=?",(finished,json.dumps(result,ensure_ascii=False,default=str),run_id)); db.commit()
        print(json.dumps(result,ensure_ascii=False,indent=2)); return 0
    except Exception as e:
        finished=__import__("datetime").datetime.now().astimezone().isoformat(timespec="seconds")
        db.execute("UPDATE runs SET finished_at=?,status='FAILED',details=? WHERE run_id=?",(finished,str(e),run_id)); db.commit()
        print(json.dumps({"error":type(e).__name__,"message":str(e)},ensure_ascii=False),file=sys.stderr); return 1
    finally: db.close()

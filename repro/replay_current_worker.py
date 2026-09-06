"""Container routing only. Existing Judge modules retain business scoring."""
import hashlib,json,subprocess,sys
from pathlib import Path
R=Path('/work');rows=json.loads((R/'selected.json').read_text())
if len(sys.argv)>1:
 r=next(x for x in rows if x['case']==sys.argv[1]);root=R/'fixed/new6' if r['route']=='fixed-34374' else R/'current/snapshots'/r['snapshot']/'new6'
 sys.path.insert(0,str(root/'repro'));from score import run_case
 c=r['case'];run_case({'task':r['task'],'task_root':r['task_root'],'answer':str(R/'cases'/c/'answer.xlsx'),'input_dir':str(R/'cases'/c/'input')},R/'scores'/c)
else:
 if any(r['route']=='fixed-34374' for r in rows):
  sys.path.insert(0,str(R/'fixed/new6/offline_judge_repair'));from freeze import verify
  verify()
 if any(r['route']=='current-reader-snapshot' for r in rows):
  for rel,h in json.loads((R/'current-files.json').read_text()).items():assert hashlib.sha256((R/'current'/rel).read_bytes()).hexdigest()==h,rel
 status=[]
 for r in rows:
  c=r['case'];p=subprocess.run([sys.executable,__file__,c],capture_output=True,text=True);logs=R/'logs';logs.mkdir(exist_ok=True);(logs/(c+'.txt')).write_text(p.stdout+'\n'+p.stderr);status.append({'case':c,'returncode':p.returncode});(R/'execution-status.json').write_text(json.dumps(status,indent=2));print(c,p.returncode,flush=True)
 raise SystemExit(0 if all(x['returncode']==0 for x in status) else 1)

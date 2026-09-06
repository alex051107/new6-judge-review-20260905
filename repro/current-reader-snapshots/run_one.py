from pathlib import Path
import sys,json
R=Path('/work');r=next(x for x in json.loads((R/'selected.json').read_text()) if x['case']==sys.argv[1]);sys.path.insert(0,str(R/'snapshots'/r['snapshot']/'new6/repro'))
from score import run_case
c=r['case'];res=run_case({'task':r['task'],'task_root':r['task_root'],'answer':str(R/'cases'/c/'answer.xlsx'),'input_dir':str(R/'cases'/c/'input')},R/'runs'/c)
print(json.dumps({'case':c,'status':res['evaluation_status'],'criteria':res.get('criterion_scores')}))

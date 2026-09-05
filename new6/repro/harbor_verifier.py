"""Use the same offline scoring adapter for Harbor; no reference reaches the agent."""
import json
from pathlib import Path
import sys
sys.path.insert(0, '/tests/new6/repro')
from score import run_case
p = Path('/logs/verifier')
p.mkdir(parents=True, exist_ok=True)
(p/'reward.txt').write_text('0\n')
task_id=json.loads(Path('/tests/adapter.json').read_text())['task_id']
aliases={'FIN':'A1','MACRO':'A2','RETAIL':'B1','LABOUR':'B2','COST':'C1','PARCEL':'C2'}
try:
    r=run_case({'task':aliases[task_id.split('-')[2]],'task_root':'tasks/'+task_id,
        'answer':'/app/output/answer.xlsx','input_dir':'/app/input'},p/'offline')
except Exception as exc:
    r={'evaluation_status':'JUDGE_ERROR','normalized_score':None,'pass':None,'error':str(exc)}
r['harbor_transport_reward_is_not_status']=True
r['sample_countable']=r['evaluation_status'] in ('SCORED','OUTPUT_MISSING','MALFORMED_OUTPUT')
if r['evaluation_status']=='SCORED': (p/'reward.txt').write_text(str(r['normalized_score'])+'\n')
(p/'judge-result.json').write_text(json.dumps(r,indent=2,ensure_ascii=False))
print(json.dumps(r,ensure_ascii=False))

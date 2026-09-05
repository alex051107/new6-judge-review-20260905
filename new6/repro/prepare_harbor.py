"""Prepare an optional fresh run. Never starts Harbor or reads a secret."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from build_harbor import build
p=argparse.ArgumentParser()
p.add_argument('--out',type=Path,required=True)
p.add_argument('--agent-image',required=True,help='Your tested Claude Code 2.1.251 image; must include bash, node, git, curl, Python, openpyxl and PDF tooling')
p.add_argument('--parallel',type=int,choices=[1,2,3],default=1)
a=p.parse_args()
out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
tasks=json.loads((ROOT/'repro/suite.json').read_text())['tasks']
paths=[build(Path(t).name,out/'tasks',runtime_image=a.agent_image,verifier_image='new6-judge:20260905') for t in tasks.values()]
config={'job_name':'new6-fresh','jobs_dir':str(out/'jobs'),'n_attempts':1,
'n_concurrent_trials':a.parallel,'retry':{'max_retries':0},
'agents':[{'name':'claude-code','model_name':'claude-opus-5','override_timeout_sec':1200,
'kwargs':{'version':'2.1.251','max_budget_usd':'10','disallowed_tools':'WebSearch'},
'env':{'ANTHROPIC_API_KEY':'${ANTHROPIC_API_KEY}','ANTHROPIC_BASE_URL':'https://api.zcloudapi.com','ANTHROPIC_MAX_RETRIES':'0'}}],
'environment':{'type':'docker','delete':True},'tasks':[{'path':str(x)} for x in paths]}
(out/'job.json').write_text(json.dumps(config,indent=2))
print('Prepared only; zero API calls. Review job.json before any paid execution.')

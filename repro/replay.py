#!/usr/bin/env python3
"""Offline replay only. Never starts an agent or reads an API credential."""
import argparse, concurrent.futures, json, pathlib, subprocess, sys, statistics
ROOT=pathlib.Path(__file__).resolve().parents[1]
MANIFEST=json.loads((ROOT/'release.json').read_text())
def write(p,obj):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def score(task,answer,inputs,out,image):
 package=ROOT/MANIFEST['tasks'][task]['path'];out=out.resolve();out.mkdir(parents=True,exist_ok=False)
 cmd=['docker','run','--rm','--network','none','--cpus','2','--memory','4g','-v',f'{package.resolve()}/tests:/tests:ro','-v',f'{answer.resolve()}:/app/output/answer.xlsx:ro','-v',f'{inputs.resolve()}:/app/input:ro','-v',f'{out}:/logs/verifier',image,'python','/tests/run_verifier.py']
 try:
  p=subprocess.run(cmd,capture_output=True,text=True,timeout=690)
  (out/'stdout.txt').write_text(p.stdout);(out/'stderr.txt').write_text(p.stderr)
  r=json.loads((out/'judge-result.json').read_text())
 except Exception as e:r={'evaluation_status':'JUDGE_EXECUTION_PENDING','score_decimal':None,'pass':None,'error':type(e).__name__+': '+str(e)};write(out/'judge-result.json',r)
 return r

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=['verify','actual','score']);p.add_argument('--suite',choices=['reference','calibration'],default='reference');p.add_argument('--repeat',type=int,default=1);p.add_argument('--task',choices=list(MANIFEST['tasks']));p.add_argument('--answer',type=pathlib.Path);p.add_argument('--input-dir',type=pathlib.Path);p.add_argument('--out',type=pathlib.Path,required=True);p.add_argument('--image',default='new6-judge:20260905');p.add_argument('--workers',type=int,choices=[1,2],default=1);p.add_argument('--scored-only',action='store_true');p.add_argument('--limit',type=int);a=p.parse_args()
 if a.repeat<1 or a.repeat>10:p.error('repeat must be 1..10')
 out=a.out.resolve()
 if out.exists() and any(out.iterdir()):p.error('out must be a new or empty directory')
 out.mkdir(parents=True,exist_ok=True)
 runtime=subprocess.run(['docker','run','--rm','--network','none',a.image,'sh','-c','python --version && libreoffice --version && python -m pip freeze'],capture_output=True,text=True,check=True).stdout
 expected=['Python 3.11.16','LibreOffice 7.4.7.2','openpyxl==3.1.5','et_xmlfile==2.0.0','lxml==6.0.1']
 if not all(x.lower().replace('_','-') in runtime.lower().replace('_','-') for x in expected):raise RuntimeError('Runtime differs from pinned environment: '+runtime)
 (out/'runtime.txt').write_text(runtime)
 jobs=[]
 if a.mode=='score':
  if not a.task or not a.answer:p.error('score requires --task and --answer')
  inputs=a.input_dir or ROOT/MANIFEST['tasks'][a.task]['path']/'data/input_files'
  jobs=[{'id':'submission','task':a.task,'answer':str(a.answer.resolve()),'inputs':str(inputs.resolve())}]
 elif a.mode=='actual':
  for row in json.loads((ROOT/'results/trials.json').read_text()):
   if row['eligible_for_score_replay'] and (not a.scored_only or row['status']=='SCORED') and (not a.task or row['task']==a.task):jobs.append({'id':row['id'],'task':row['task'],'answer':row['answer'],'inputs':row['input_dir']})
 else:
  for task,info in MANIFEST['tasks'].items():
   if a.task and task!=a.task:continue
   package=ROOT/info['path'];inner=package/'tests/new6/tasks'/info['task_id']
   if a.suite=='reference':jobs.append({'id':task+'-reference','task':task,'answer':str(package/'solution/reference.xlsx'),'inputs':str(package/'data/input_files'),'expected_status':'SCORED','expected_score':'1'})
   else:
    for case in json.loads((ROOT/'repro/calibration.json').read_text())[task]:jobs.append({**case,'id':task+'-'+case['name'],'task':task,'answer':str(inner/case['path']),'inputs':str(package/'data/input_files')})
 if a.limit:jobs=jobs[:a.limit]
 if not jobs:raise ValueError('No applicable workbooks')
 work=[(j,i) for i in range(1,a.repeat+1) for j in jobs]
 def run(work):
  j,i=work;d=out/f'run-{i}'/j['id'];ans=ROOT/j['answer'];inp=ROOT/j['inputs']
  if not ans.is_file():raise FileNotFoundError(ans)
  r=score(j['task'],ans,inp,d,a.image);checks=[]
  if 'expected_status' in j:checks.append(r['evaluation_status']==j['expected_status'])
  if 'expected_score' in j:checks.append(r.get('score_decimal') is not None and abs(float(r['score_decimal'])-float(j['expected_score']))<1e-12)
  for cid in j.get('lose',[]):checks.append(float(r.get('criterion_scores',{}).get(cid,1))<1)
  row={'id':j['id'],'task':j['task'],'run':i,'status':r['evaluation_status'],'score_decimal':r.get('score_decimal'),'criterion_scores':r.get('criterion_scores'),'checks_passed':all(checks) if checks else None,'receipt':str(d.relative_to(out)/'judge-result.json')}
  print(json.dumps(row),flush=True);return row
 with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers) as ex:rows=list(ex.map(run,work))
 consistency=[]
 if a.repeat>=5:
  for j in jobs:
   rr=[r for r in rows if r['id']==j['id']];fields=['total',*MANIFEST['tasks'][j['task']]['primary_weights']]
   for f in fields:
    values=[r.get('score_decimal') if f=='total' else (r.get('criterion_scores') or {}).get(f) for r in rr];values=[float(v) for v in values if v is not None];sd=statistics.stdev(values) if len(values)==a.repeat else None
    consistency.append({'id':j['id'],'criterion':f,'n':len(values),'stddev':sd,'below_0_05':sd<.05 if sd is not None else None})
 result={'api_calls':0,'checks':rows,'consistency':consistency,'all_assertions_passed':all(r['checks_passed'] is not False for r in rows),'runtime':'runtime.txt'};write(out/'receipt.json',result)
 return 0 if result['all_assertions_passed'] else 1
if __name__=='__main__':sys.exit(main())

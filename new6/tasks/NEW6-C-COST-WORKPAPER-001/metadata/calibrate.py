from pathlib import Path
from decimal import Decimal
import json,sys,time,shutil
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'tests'))
from evaluate import evaluate
cases=json.loads((P/'fixtures/manifest.json').read_text())['cases'];rows=[]
for case in cases:
 t=time.monotonic();r=evaluate(P/'fixtures'/case['file'],P/'metadata/calibration'/case['name'],True);s=r.get('criterion_scores',{})
 checks=[{'id':'status','ok':r['evaluation_status']==case['status']}]
 for id in case['lose']:checks.append({'id':id+'_loses','ok':id in s and Decimal(s[id])<1})
 for id in case['preserve']:checks.append({'id':id+'_preserved','ok':id in s and Decimal(s[id])==1})
 if case['status']=='SCORED':checks.append({'id':'same_facts_three_profiles','ok':all(p['criterion_scores']==s for p in r['profiles'].values())})
 row=dict(name=case['name'],status=r['evaluation_status'],score=r.get('score_decimal'),criterion_scores=s,checks=checks,passed=all(c['ok'] for c in checks),seconds=round(time.monotonic()-t,2));rows.append(row)
 receipt=dict(task_version='new6-c1-v1.0-falmouth',judge_version='new6-c1-facts-v1.0',status='PASS' if len(rows)==len(cases) and all(x['passed'] for x in rows) else 'RUNNING' if all(x['passed'] for x in rows) else 'FAIL',calibrated_cases=len(rows),results=rows,agent_calls=0,agent_cost_usd='0')
 (P/'metadata/validation_receipt.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(row),flush=True)
 if case['name']=='reference' and row['passed']:
  (P/'metadata/reference_verification.json').write_text(json.dumps({'status':'PASS','independent_oracle':'Decimal from visually checked source facts','fact_units':{k:len(v) for k,v in r['evidence']['fact_units'].items()},'evidence':'metadata/calibration/reference/evaluation.json','reference_before_input':True},indent=2))
  shutil.copy2(P/'metadata/source/Falmouth_OCE_October2024_RevA.pdf',P/'data/input_files/Falmouth_OCE_October2024_RevA.pdf')
 if not row['passed']:raise AssertionError('Calibration failed: '+case['name'])

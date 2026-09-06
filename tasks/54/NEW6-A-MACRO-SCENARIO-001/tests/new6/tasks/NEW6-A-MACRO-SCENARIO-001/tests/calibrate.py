"""One functional calibration batch; malformed assertions abort without scoring."""
import argparse,json,sys,time
from pathlib import Path
from decimal import Decimal
from evaluate import evaluate,ROOT
p=argparse.ArgumentParser();p.add_argument('--only',nargs='*');p.add_argument('--receipt',default='verification_receipt.json');a=p.parse_args()
manifest=json.loads((ROOT/'fixtures/manifest.json').read_text());results=[]
for c in manifest['cases']:
 if a.only and c['name'] not in a.only:continue
 assert isinstance(c['name'],str) and isinstance(c['file'],str) and c['expected_status'] in ['SCORED','JUDGE_ERROR','OUTPUT_MISSING','MALFORMED_OUTPUT']
 assert isinstance(c['lose'],list) and isinstance(c['preserve'],list) and not set(c['lose'])&set(c['preserve'])
 assert all(k in ['R001','R002','R003','R004','R005','R006'] for k in c['lose']+c['preserve'])
 t=time.monotonic();r=evaluate(ROOT/'fixtures'/c['file'],ROOT/'metadata/calibration'/c['name'],completed_run=True);ok=r['evaluation_status']==c['expected_status'];scores=r.get('criterion_scores',{})
 assertions=[dict(assertion='status',expected=c['expected_status'],actual=r['evaluation_status'],ok=ok)]
 if r['evaluation_status']=='SCORED':
  for k in c['lose']:assertions.append(dict(assertion=k+'_loses',actual=scores[k],ok=Decimal(scores[k])<1))
  for k in c['preserve']:assertions.append(dict(assertion=k+'_preserved',actual=scores[k],ok=Decimal(scores[k])==1))
  assert set(scores)==set(['R001','R002','R003','R004','R005','R006'])
 row=dict(name=c['name'],status=r['evaluation_status'],score=r.get('score_decimal'),criterion_scores=scores,assertions=assertions,passed=all(x['ok'] for x in assertions),seconds=round(time.monotonic()-t,2),evidence=f'metadata/calibration/{c["name"]}/evaluation.json')
 results.append(row);print(json.dumps(row),flush=True)
 receipt=dict(status='PASS' if all(x['passed'] for x in results) else 'FAIL',calibrated_cases=len(results),results=results,agent_calls=0,agent_cost_usd='0',formal_difficulty_qualified=False)
 (ROOT/'metadata'/a.receipt).write_text(json.dumps(receipt,indent=2))
 if not row['passed']:raise AssertionError('Fixture assertion failed: '+c['name'])

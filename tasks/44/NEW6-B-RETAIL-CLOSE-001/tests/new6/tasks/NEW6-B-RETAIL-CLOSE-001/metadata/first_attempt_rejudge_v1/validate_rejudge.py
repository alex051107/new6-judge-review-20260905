from pathlib import Path
import sys,json
P=Path(__file__).resolve().parent;T=P/'new6/tasks/NEW6-B-RETAIL-CLOSE-001'
ROOT=P.parents[4];ART=ROOT/'new6/harbor_jobs/new6-first-20260905T144715Z/NEW6-B-RETAIL-CLOSE-001__42WuErq/artifacts/app'
sys.path.insert(0,str(T/'tests'))
from evaluate import evaluate
from fixture_xml import Fixture
F=P/'fixtures';F.mkdir(exist_ok=True)
base=json.loads((P/'first_attempt_receipt.json').read_text());ref=T/'solution/reference.xlsx'
cases=[('reference',ref,T/'data/input_files','reference')]
for name,fn in [('equivalent_actual_layout',lambda f:f.shift()),('wrong_invoice_amount',lambda f:f.cell('Invoice Analysis','F2',-9.95)),('missing_invoice_table',lambda f:f.clear_sheet('Invoice Analysis')),('unbound_invoice_header',lambda f:f.cell('Invoice Analysis','A1','Document key'))]:
 path=F/(name+'.xlsx');fn(Fixture(ART/'output/answer.xlsx')).save(path);cases.append((name,path,ART/'input',name))
out=[]
for name,path,inp,expect in cases:
 r=evaluate(path,inp);ok=True
 if expect=='reference':ok=r['evaluation_status']=='SCORED' and r['score_decimal']=='1.0'
 elif expect=='unbound_invoice_header':ok=r['evaluation_status']=='JUDGE_ERROR' and r['normalized_score'] is None
 else:
  ok=r['evaluation_status']=='SCORED'
  if ok:
   f=r['criterion_scores'];b=base['criterion_scores']
   if expect=='equivalent_actual_layout':ok=f==b
   else:ok=f['R003']<b['R003'] and all(f[k]==b[k] for k in b if k!='R003')
 out.append({'case':name,'assertions_passed':ok,'result':r});print(name,ok,r['evaluation_status'],r.get('normalized_score'),flush=True)
 (F/(name+'.receipt.json')).write_text(json.dumps(out[-1],indent=2))
receipt={'version':'new6-b1-v1-reader-repair-1','original_task_commit':'683cdda','first_attempt_task_version':'v1','passed':all(x['assertions_passed'] for x in out),'checks':out,'agent_api_calls':0,
 'requirement_audit':'Source-preserved missing CustomerID cells plus explicit attribution notes are reviewable; v1 never requires a second customer-only exception queue. Ambiguous count-plus-amount reconciliation rows do not become wrong scalar report claims. No v2 bridge demands applied.'}
(P/'validation_receipt.json').write_text(json.dumps(receipt,indent=2))
assert receipt['passed']

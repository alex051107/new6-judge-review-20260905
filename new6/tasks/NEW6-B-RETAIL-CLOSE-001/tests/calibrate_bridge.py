"""V2-only changed-risk calibration. Old v1 fixtures are not counted here."""
from pathlib import Path
import sys,json,shutil
from fixture_xml import Fixture
from evaluate import evaluate
T=Path(__file__).resolve().parents[1];F=T/'fixtures/v2';F.mkdir(exist_ok=True);REF=T/'solution/reference.xlsx';C={f'R{i:03}' for i in range(1,9)}
CASES=[
 ('reference_static',None,[],'SCORED'),
 ('equivalent_layout',lambda f:f.layout(),[],'SCORED'),
 ('equivalent_recoverable_prices',lambda f:f.project_register('SKU comparison',['A','B','C','D','E','F','I','J','K','L'],set(range(2,3075))),[],'SCORED'),
 ('wrong_quantity_bridge',lambda f:f.cell('Monthly bridge','B3',45947.318253921665),['R007'],'SCORED'),
 ('wrong_sku_quantity',lambda f:f.cell('SKU comparison','C2',61),['R008'],'SCORED'),
 ('mixed_bridge_claims',lambda f:f.duplicate_row('Monthly bridge',3,{'B':100}),['R007'],'SCORED'),
 ('duplicate_and_missing_sku',lambda f:f.remove_row('SKU comparison',3).duplicate_row('SKU comparison',2),['R008'],'SCORED'),
 ('unbound_bridge_header',lambda f:f.cell('Monthly bridge','B1','Change in pounds'),[],'JUDGE_ERROR'),
 ('uncached_bridge_formula',lambda f:f.cell('Monthly bridge','B3',None,formula='_xlfn.LET(x,44947.318253921665,x)',uncached=True),[],'JUDGE_ERROR'),
]
out=[]
for name,mut,loss,status in CASES:
 if len(sys.argv)>1 and name not in sys.argv[1:]:continue
 path=F/(name+'.xlsx')
 if mut:mut(Fixture(REF)).save(path)
 else:shutil.copyfile(REF,path)
 r=evaluate(path,T/'data/input_files');ok=r['evaluation_status']==status
 if ok and status=='SCORED':
  facts=r['criterion_scores'];ok=all(facts[k]<1 for k in loss) and all(facts[k]==1 for k in C-set(loss)) and all(p['criterion_scores']==facts for p in r['profiles'].values())
 elif ok:ok=r['normalized_score'] is None and r['pass'] is None
 receipt={'case':name,'task_version':'new6-b1-v2','assertions_passed':ok,'expected_status':status,'expected_losses_only':loss,'result':r};(F/(name+'.receipt.json')).write_text(json.dumps(receipt,indent=2));print(name,ok,r['evaluation_status'],r.get('criterion_scores'),r['evidence'].get('reason'),flush=True)
for name,_,_,_ in CASES:
 p=F/(name+'.receipt.json');out.append(json.loads(p.read_text()) if p.exists() else {'case':name,'assertions_passed':False,'missing':True})
summary={'task_id':T.name,'task_version':'new6-b1-v2','status':'CALIBRATION_PASSED' if all(r['assertions_passed'] for r in out) else 'CALIBRATION_FAILED','fixture_count':len(out),'failed':[r['case'] for r in out if not r['assertions_passed']],'checks':[{'case':r['case'],'passed':r['assertions_passed']} for r in out],'agent_attempts_v2':0,'checks_budget':{'planned':'One combined changed-risk runner; affected cases only after repair. Static, genuine cell relocation, recoverable weighted price columns, two independent single errors, conflicting claims, duplicate plus omitted SKU, unknown header, uncached formula.','actual':'This runner; v1 fixtures and full legacy suite deliberately not rerun because no v1 business semantics changed.','independent_reviews':0,'hashes':0},'profile_semantics':'Identical fact vector in three fixed profiles; unrounded >=0.70; no hurdles/caps.'}
(T/'metadata/validation_receipt_v2.json').write_text(json.dumps(summary,indent=2));print('V2_SUMMARY',summary['status'],summary['failed'],flush=True)

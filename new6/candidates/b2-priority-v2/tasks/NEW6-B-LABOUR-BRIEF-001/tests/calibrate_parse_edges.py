from pathlib import Path
import sys,os,json
p=Path(__file__).resolve().parents[1];sys.path[:0]=[str(p/'tests'),str(p.parents[1]/'common')]
from fixture_xml import Fixture
from evaluate import evaluate
ref=p/'fixtures/reference.xlsx';out=p/'metadata/dynamic_calibration';records=[]
for name,f,status in [('identical_live_duplicate',Fixture(ref).duplicate_row('Live screening',2),'SCORED'),('unbound_live_layout',Fixture(ref).cell('Live screening','E1','Current eligible status'),'JUDGE_ERROR')]:
 dest=p/'fixtures'/f'{name}.xlsx';f.save(dest);os.environ['NEW6_EVIDENCE_DIR']=str(out/name);r=evaluate(dest,p/'data/input_files');assert r['evaluation_status']==status,(name,r.get('evidence',{}).get('live_review_error'))
 if status=='SCORED':
  assert r['criterion_scores']['R009']<1
  assert all(r['criterion_scores'][f'R{i:03}']==1 for i in range(1,9))
 records.append({'case':name,'status':status,'passed':True});(out/(name+'.json')).write_text(json.dumps(r,indent=2))
(out/'extra_receipt.json').write_text(json.dumps(records,indent=2));print(records)

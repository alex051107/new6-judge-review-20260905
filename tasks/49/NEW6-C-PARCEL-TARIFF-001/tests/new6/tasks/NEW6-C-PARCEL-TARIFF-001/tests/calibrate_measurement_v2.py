"""One measurement-v2 calibration; reuse verified native snapshots when unchanged."""
from pathlib import Path
import json, shutil
from decimal import Decimal as D
from evaluate import ROOT,evaluate,parse,rkey,patch_xlsx

OUT=ROOT/'metadata/measurement_v2/calibration'
CASES={
 'reference':([],['R001','R002','R003','R004','R005','R006']),
 'equivalent_layout':([],['R001','R002','R003','R004','R005','R006']),
 'equivalent_formula':([],['R001','R002','R003','R004','R005','R006']),
 'constant_quotes':(['R004'],['R001','R002','R003','R005','R006']),
 'constant_offset':(['R003'],['R001','R002','R004','R005','R006']),
 'floor_weight':(['R003','R004'],['R001','R002','R005','R006']),
 'zone_shift':(['R003'],['R001','R002','R004','R005','R006']),
 'mixed_final':(['R003','R004'],['R001','R002','R005','R006']),
 'omitted_quote':(['R003','R005'],['R001','R002','R004','R006']),
 'service_grid_swap':(['R001','R003','R004'],['R002','R005','R006']),
}
def main():
 OUT.mkdir(parents=True,exist_ok=False)
 candidate=parse(ROOT/'solution/reference.xlsx');lookup={rkey(r):r for r in candidate['rates']};patches=[]
 for row in candidate['rates']:
  service,bound,unit,zone=rkey(row)
  if unit!='lb':continue
  opposite='ground' if service=='priority' else 'priority'
  other=lookup[(opposite,bound,unit,zone)]
  patches.append((*row['_cells']['usd'],other['usd']))
 assert len(patches)==160
 patch_xlsx(ROOT/'solution/reference.xlsx',ROOT/'fixtures/service_grid_swap.xlsx',patches)
 receipts=[]
 for name,(loss,keep) in CASES.items():
  assert set(loss).isdisjoint(keep) and set(loss)|set(keep)=={f'R{i:03}' for i in range(1,7)}
  path=ROOT/('solution/reference.xlsx' if name=='reference' else f'fixtures/{name}.xlsx')
  folder=OUT/name;folder.mkdir()
  previous=ROOT/f'metadata/calibration/{name}/result.json'
  if previous.exists():shutil.copy2(previous,folder/'result.json')
  result=evaluate(path,folder,completed_run=True,reuse_native=previous.exists())
  assert result['evaluation_status']=='SCORED',(name,result.get('evidence',{}))
  facts=result['criterion_scores']
  errors=[f'{c} must lose' for c in loss if not D(facts[c])<1]
  errors += [f'{c} must remain full' for c in keep if D(facts[c])!=1]
  if name=='constant_quotes':
   errors += ['static must have zero active response'] if D(facts['R004'])!=0 else []
   errors += ['primary must be .65'] if D(result['score_decimal'])!=D('.65') else []
  if not loss:assert all(D(p['score_decimal'])==1 for p in result['profiles'].values()),name
  assert result['evidence']['denominators']=={'R001':192,'R002':25,'R003':49,'R004':11,'R005':26,'R006':26},name
  assert not errors,(name,errors,facts)
  receipt={'name':name,'assertions_passed':True,'score_decimal':result['score_decimal'],'profiles':{k:v['score_decimal'] for k,v in result['profiles'].items()},'criterion_scores':facts,'native_outputs_reused':result['evidence'].get('native_outputs_reused',False),'loss':loss,'keep':keep}
  receipts.append(receipt);print(json.dumps(receipt),flush=True)
 (OUT/'receipt.json').write_text(json.dumps({'judge_version':'new6-usps-facts-v2.0-downstream-use','passed':True,'cases':receipts,'source_swap_count':160,'agent_calls':0,'old_results_preserved':True,'statement':'Calibration demonstrates criterion discrimination; not a natural failure rate or difficulty qualification'},ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()

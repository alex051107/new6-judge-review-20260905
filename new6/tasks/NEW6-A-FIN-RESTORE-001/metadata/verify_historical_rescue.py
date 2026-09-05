"""Complete economics gate for the disclosed historical financing construction."""
from pathlib import Path
import sys,json,hashlib,openpyxl
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT.parents[1]/'common'))
from runtime import recalculate_xlsx
from ooxml_edit import edit
from oracle_recompute import compute,jsonable,raw_inputs

def verify(path,kwargs):
 w=openpyxl.load_workbook(path,data_only=True)
 basis=json.loads((ROOT/'metadata/source_oracle_verification.json').read_text())['checks'];checks=[]
 for sn,review in [('Valuation output',False),('Review valuation',True)]:
  oracle=compute(**kwargs,review=review)
  for fact in basis:
   cell=fact['cell'];row,col=openpyxl.utils.cell.coordinate_to_tuple(cell);expected=oracle['rows'][col-3][fact['metric']] if col>=3 else oracle['bridge'][fact['metric']]
   actual=w[sn][cell].value
   ok=isinstance(actual,(int,float)) and abs(actual-float(expected))<=1e-8*max(1,abs(float(expected)))
   checks.append({'sheet':sn,'cell':cell,'metric':fact['metric'],'actual':actual,'oracle':str(expected),'correct':ok})
  assert len(basis)==115
  assert all(f['correct'] for f in checks),[f for f in checks if not f['correct']][:5]
 syn=w['Synthetic rating']['F5'].value;implied=w['Input sheet']['B9'].value+w['Operating lease converter']['F32'].value
 assert abs(syn-implied)<1e-7,(syn,implied)
 assert abs(w['Operating lease converter']['C15'].value-float(compute()['source_adjustments']['lease_rate']))<1e-12
 summary=w['Review summary'];base=compute(**kwargs)['bridge'];review=compute(**kwargs,review=True)['bridge']
 for cell,exp in [('B3',base['common_equity']),('B4',review['common_equity']),('B5',review['common_equity']-base['common_equity']),('B7',base['value_per_share']),('B8',review['value_per_share'])]:assert abs(summary[cell].value-float(exp))<1e-7
 return {'checks':checks,'facts_correct':len(checks),'historical_circular_formula_residual':syn-implied,'base_per_share':base['value_per_share'],'review_per_share':review['value_per_share'],'summary_facts_correct':5}

def main():
 folder=ROOT/'metadata/historical_rescue';folder.mkdir(exist_ok=True)
 source=ROOT/'metadata/source/AmazonSept18.xlsx';sha=hashlib.sha256(source.read_bytes()).hexdigest()
 expected_sha=json.loads((ROOT/'metadata/source_manifest.json').read_text())['sources'][0]['sha256'];assert sha==expected_sha
 reference=ROOT/'solution/reference.xlsx';sourcew=openpyxl.load_workbook(reference,data_only=False);results=[{'case':'baseline','native_reused_from':'metadata/reference_verification.json',**verify(reference,{})}]
 for label,cell,key,delta in [('growth_plus_1pp','B23','growth_delta',.01),('margin_minus_1pp','B24','margin_delta',-.01),('discount_plus_half_pp','B29','discount_delta',.005)]:
  case=folder/label;case.mkdir(exist_ok=True);input_path=case/'mutated.xlsx'
  original=sourcew['Input sheet'][cell].value;changed=original+delta
  edit(reference,input_path,patches={'Input sheet':{cell:changed}},clear_caches=True)
  fresh,native=recalculate_xlsx(input_path,case/'recalculated');result=verify(fresh,{key:str(delta)})
  after=openpyxl.load_workbook(fresh,data_only=False)
  invariants=[]
  for row in sourcew['Input sheet']:
   for c in row:
    if c.coordinate==cell or c.data_type=='f' or c.value is None:continue
    ok=after['Input sheet'][c.coordinate].value==c.value;invariants.append({'cell':c.coordinate,'correct':ok})
  assert all(i['correct'] for i in invariants)
  results.append({'case':label,'input_change':{'sheet':'Input sheet','cell':cell,'before':original,'after':changed,'oracle_delta':str(delta)},'native':native,'historical_and_other_input_invariants':invariants,**result})
 receipt={'status':'PASS','construction':'One disclosed fixed historical lease financing rate; original model and published facts retained privately','original_sha256_matches_download':sha,'original_source_untouched':True,'baseline_and_three_changes':results,'native_recalculations_total':4,'baseline_reused':True,'each_case_facts':230,'each_case_summary_facts':5,'no_formula_cache_substitution':True,'candidate_dynamics':['five-year growth','target operating margin','initial cost of capital'],'agent_calls':0,'difficulty_claim':'No Agent sample or formal difficulty conclusion'}
 (folder/'receipt.json').write_text(json.dumps(jsonable(receipt),indent=2));print(json.dumps({'status':'PASS','cases':len(results),'facts_per_case':230,'base_per_share':str(results[0]['base_per_share']),'review_per_share':str(results[0]['review_per_share'])},indent=2))
if __name__=='__main__':main()

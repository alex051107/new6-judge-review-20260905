from pathlib import Path
import sys,json,copy,openpyxl
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT.parents[1]/'common'))
from runtime import recalculate_xlsx
from ooxml_edit import edit
from oracle_recompute import compute
from historical_rate_basis import prepare,DERIVED

def build_reference():
 source=prepare()
 summary={'A1':'Amazon September 2018 — educational reconstruction','A3':'Base equity value','B3':"='Valuation output'!B31",'A4':'Review equity value','B4':"='Review valuation'!B31",'A5':'Review minus base equity value','B5':'=B4-B3','A7':'Base value per share','B7':"='Valuation output'!B33",'A8':'Review value per share','B8':"='Review valuation'!B33",'A10':'Review case changes only terminal operating-margin target by -2 percentage points. Lower operating cash flows lower value while reinvestment and historical inputs remain unchanged.'}
 # All source-specific controls remain in the source; the review target follows main target minus 2 pp.
 dest=ROOT/'solution/reference_unrecalculated.xlsx'
 edit(source,dest,clones={'Review valuation':('Valuation output',[("'Valuation output'!","'Review valuation'!"),("'Input sheet'!$B$24","('Input sheet'!$B$24-0.02)")])},new_sheets={'Review summary':summary},clear_caches=True)
 fresh,receipt=recalculate_xlsx(dest,ROOT/'metadata/reference_recalc');w=openpyxl.load_workbook(fresh,data_only=True)
 for name,review in [('Valuation output',False),('Review valuation',True)]:
  o=compute(review=review)
  for i,row in enumerate(o['rows'],3):
   for k,r in {'revenue':3,'margin':4,'ebit':5,'nopat':7,'reinvestment':8,'fcff':9}.items():
    v=w[name].cell(r,i).value;assert abs(v-float(row[k]))<1e-7*max(1,abs(float(row[k]))),(name,k,i,v,row[k])
  assert abs(w[name]['B31'].value-float(o['bridge']['common_equity']))<.0001
 (ROOT/'solution/reference.xlsx').write_bytes(fresh.read_bytes());(ROOT/'metadata/reference_verification.json').write_text(json.dumps({'status':'PASS','native_receipt':receipt,'oracle_cases':['base','margin_minus_2pp'],'comparison':'all annual revenue/margin/ebit/nopat/reinvestment/fcff and common equity'},indent=2))

def build_input():
 # Reference/Oracle verification is mandatory before blanking source calculation blocks.
 assert json.loads((ROOT/'metadata/reference_verification.json').read_text())['status']=='PASS'
 source=DERIVED;w=openpyxl.load_workbook(source);patch={};manifest=[]
 for sn in w.sheetnames:
  changes={}
  if sn=='Valuation output':
   coords=[f'{openpyxl.utils.get_column_letter(c)}{r}' for r in [3,5,7,8,9,10,14,39,40] for c in range(3,14) if w[sn].cell(r,c).value is not None]+[f'B{r}' for r in list(range(16,22))+list(range(23,32))+[33,35]]
   for co in coords:changes[co]=None
  if sn=='CB_DATA_':
   # Crystal Ball serialized payloads can contain undisclosed completed model states; keep original private.
   for row in w[sn]:
    for c in row:
     if c.row>=25 and c.value is not None:changes[c.coordinate]=None
  for co in changes:manifest.append({'sheet':sn,'cell':co,'original_formula_or_value':str(w[sn][co].value),'action':'clear_derived_or_embedded_completed_state'})
  if changes:patch[sn]=changes
 edit(source,ROOT/'data/input_files/AmazonSept18_restore.xlsx',patches=patch,clear_caches=True)
 (ROOT/'metadata/mutation_manifest.json').write_text(json.dumps({'source_untouched':True,'historical_input_construction':'metadata/historical_rate_basis.json','candidate_formula_and_chart_caches_cleared':True,'changes':manifest},indent=2))
 if (ROOT/'solution/reference_unrecalculated.xlsx').exists():(ROOT/'solution/reference_unrecalculated.xlsx').unlink()

if __name__=='__main__':build_reference();build_input()

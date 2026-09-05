from pathlib import Path
import sys,json,openpyxl
p=Path(__file__).resolve().parents[1];sys.path[:0]=[str(p/'metadata'),str(p.parents[1]/'common')]
from ooxml_edit import edit
from runtime import recalculate_xlsx
from oracle_recompute import compute_financed,jsonable
source=p/'metadata/configured_source.xlsx';raw=openpyxl.load_workbook(source,data_only=False);patch={'InputDataA_GeneralAssumptions':{'D60':raw['DataSummary']['A116'].value},'Submodel3s':{}}
expected=compute_financed()
for col,row in enumerate(expected,5):
 c=openpyxl.utils.get_column_letter(col)
 # Source Model3 receives independent savings and current account inputs. Its
 # untouched national-account branch derives investment, then its own capital/growth engine.
 patch['Submodel3s'][c+'6']=float(row['savings_share']);patch['Submodel3s'][c+'14']=float(row['current_account_share'])
probe=p/'metadata/financing_source_probe.xlsx';edit(source,probe,patches=patch,clear_caches=True);fresh,receipt=recalculate_xlsx(probe,p/'metadata/financing_source_probe_recalc');w=openpyxl.load_workbook(fresh,data_only=True);facts=[]
for col,row in enumerate(expected,5):
 for key,r in {'investment_share':19,'capital_output_ratio':22,'gdp_per_capita':34,'gdp_growth':32,'pc_growth':20}.items():
  if col==5 and key=='pc_growth':continue # original initial per-worker memo is unavailable; task retains Model1 historical initial growth.
  actual=w['Submodel3s'].cell(r,col).value;gold=float(row[key]);ok=isinstance(actual,(float,int)) and abs(actual-gold)<=1e-7*max(1,abs(gold));facts.append(dict(year=row['year'],metric=key,actual=actual,expected=gold,ok=ok));assert ok,facts[-1]
d={'status':'PASS','facts':facts,'fact_count':len(facts),'native_receipt':receipt,'source_method':'Official Instructions pages2–3: Model3 savings plus external sector; source Submodel3s row19 CAB branch I/Y = savings/Y minus CAB/Y; independently cross-referenced source Model2 row36 savings=investment+CAB.','project_policy':'Savings 20% in 2019 linearly to25% in2028; maximum CAB deficit4%GDP; planned investment as original scenario; unfunded planned investment deferred.','source_initial_memo_boundary':'Original Model3 initial per-worker growth memo is unavailable; source Model1 historical2019 initialization remains the task basis. No fabricated source value.'}
(p/'metadata/financing_source_verification.json').write_text(json.dumps(d,indent=2));print('Source financing gate PASS',len(facts))

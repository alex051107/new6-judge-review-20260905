from pathlib import Path
import json,sys,openpyxl,shutil
p=Path(__file__).resolve().parents[1];sys.path[:0]=[str(p/'metadata'),str(p.parents[1]/'common')]
from ooxml_edit import edit
from oracle_recompute import compute_financed
from runtime import recalculate_xlsx
old=p/'metadata/versions/v1/solution/reference.xlsx';finance={'A1':'Illustrative investment financing review','A3':'Savings in 2019','B3':.20,'A4':'Savings target','B4':.25,'A5':'Savings target year','B5':2028,'A6':'Maximum current account deficit / GDP','B6':.04,'A10':'Year','B10':'Scenario planned investment / GDP','C10':'Scenario savings / GDP','D10':'Scenario investment / GDP','E10':'Scenario financing gap / GDP','F10':'Scenario current account / GDP'};patch={'Submodel1s':{},'Scenario comparison':{'A23':'Compared with the baseline, the scenario finances only the affordable part of planned investment. The early financing gap reduces capital accumulation and growth; the constraint later ceases to bind as planned investment falls and savings rise.'}}
for year in range(2019,2036):
 r=year-2008;c=openpyxl.utils.get_column_letter(year-2019+5);inp=openpyxl.utils.get_column_letter(year-2019+9)
 finance.update({f'A{r}':year,f'B{r}':f'=InputDataB_ModelSpecAssumptions!{inp}10',f'C{r}':f'=$B$3+($B$4-$B$3)*MIN((A{r}-2019)/($B$5-2019),1)',f'D{r}':f'=MIN(B{r},C{r}+$B$6)',f'E{r}':f'=B{r}-D{r}',f'F{r}':f'=C{r}-D{r}'})
 patch['Submodel1s'][c+'10']=f"='Financing review'!D{r}"
reference_candidate=p/'solution/reference_v2_unrecalculated.xlsx';edit(old,reference_candidate,patches=patch,new_sheets={'Financing review':finance},clear_caches=True);fresh,receipt=recalculate_xlsx(reference_candidate,p/'metadata/reference_financing_recalc');w=openpyxl.load_workbook(fresh,data_only=True);facts=[]
for case,sn in [('baseline','Submodel1'),('scenario','Submodel1s')]:
 for i,row in enumerate(compute_financed(baseline=case=='baseline'),5):
  for k,r in {'investment_share':10,'capital_output_ratio':24,'gdp':52,'gdp_per_capita':33,'gdp_growth':31,'pc_growth':23}.items():
   actual=w[sn].cell(r,i).value;expected=float(row[k]);assert isinstance(actual,(int,float)) and abs(actual-expected)<1e-7*max(1,abs(expected)),(case,row['year'],k,actual,expected);facts.append([case,row['year'],k,actual,expected])
  if case=='scenario':
   for k,c in {'planned_investment_share':2,'savings_share':3,'investment_share':4,'financing_gap_share':5,'current_account_share':6}.items():
    actual=w['Financing review'].cell(row['year']-2008,c).value;expected=float(row[k]);assert abs(actual-expected)<1e-7*max(1,abs(expected)),(row['year'],k);facts.append([case,row['year'],k,actual,expected])
shutil.copy2(fresh,p/'solution/reference.xlsx');(p/'metadata/reference_verification.json').write_text(json.dumps({'status':'PASS','task_version':'new6-a2-v2.0-financing','independent_oracle_fact_count':len(facts),'facts':facts,'native_receipt':receipt},indent=2))
# Release the v2 degraded source only after independent reference and source gates.
assert json.loads((p/'metadata/financing_source_verification.json').read_text())['status']=='PASS'
base_input=p/'metadata/versions/v1/data/input_files/LTGM_Zambia_restore.xlsx';blank={'Submodel1s':{openpyxl.utils.get_column_letter(c)+'10':None for c in range(5,22)}};input_finance={k:v for k,v in finance.items() if not (k[0] in 'BCDEF' and int(''.join(x for x in k if x.isdigit()))>=11)}
for row in range(11,28):
 for col in 'BCDEF':input_finance[col+str(row)]=None
edit(base_input,p/'data/input_files/LTGM_Zambia_restore.xlsx',patches=blank,new_sheets={'Financing review':input_finance},clear_caches=True)
(p/'metadata/financing_v2_transform.json').write_text(json.dumps({'task_version':'new6-a2-v2.0-financing','archive':'metadata/versions/v1','source_method':'Model3 CAB branch savings minus current account','added_project_controls':{k:v for k,v in finance.items() if k in ['B3','B4','B5','B6']},'clear_previous_derived_cells':272,'additional_cleared_scenario_investment_cells':17,'new_blank_financing_result_cells':85,'reference_before_input':True,'baseline_unchanged':True},indent=2));print('v2 reference + input built; oracle facts',len(facts))

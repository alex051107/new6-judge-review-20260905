from pathlib import Path
import sys,json,openpyxl
p=Path(__file__).resolve().parents[1];sys.path[:0]=[str(p/'metadata'),str(p/'tests')];from ooxml_edit import edit;from evaluate import checks_for
cases=[('explanation_without_disclaimer',{'A1':'Zambia LTGM scenario comparison','A23':'Compared with the baseline, the investment scenario produces lower GDP growth as the lower investment share slows capital accumulation.'},True),('missing_explanation',{'A23':None},False)]
receipt=[]
for name,patch,wanted in cases:
 f=p/f'fixtures/{name}.xlsx';edit(p/'solution/reference.xlsx',f,patches={'Scenario comparison':patch},clear_caches=False)
 details,_,_=checks_for(openpyxl.load_workbook(f,data_only=True));fact=next(x for x in details['R006'] if x['id']=='comparison_interpretation_delivered');assert fact['ok']==wanted,(name,fact)
 for cid in ['R001','R002','R003','R005']:assert all(u['ok'] for u in details[cid]),(name,cid)
 assert all(u['ok'] for u in details['R006'] if u['id']!='comparison_interpretation_delivered')
 receipt.append({'name':name,'passed':True,'assertion':'explanation credit' if wanted else 'explanation loses only its one fact','actual_fact':fact,'preserved_criteria':['R001','R002','R003','R005'],'dynamic_scope':'unchanged formulas and input controls; prior reference dynamics reused, no native engine rerun'})
(p/'metadata/interpretation_calibration_receipt.json').write_text(json.dumps({'status':'PASS','cases':receipt,'runner_invocations':1,'native_recalculation_calls':0},ensure_ascii=False,indent=2))
print('Two interpretation checks PASS')

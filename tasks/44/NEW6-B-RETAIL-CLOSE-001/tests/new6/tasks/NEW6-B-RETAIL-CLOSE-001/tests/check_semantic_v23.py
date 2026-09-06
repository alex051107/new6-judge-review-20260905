"""Small cases for the period/role boundary, using candidate-labelled data."""
from pathlib import Path
import sys,json,openpyxl
from read_candidate import tables,visible_numbers,ParsePending
from evaluate import SPECS
T=Path(__file__).resolve().parents[1];O=T/'metadata/reader_v23';F=O/'fixtures';checks=[]
def test(name,ok):
 checks.append({'case':name,'passed':bool(ok)});print(name,bool(ok),flush=True)
 if not ok:raise AssertionError(name)
w=openpyxl.Workbook();s=w.active;s.title='Country comparison';s.append(['Period','Country','Sales rows','Sales GBP','Credit rows','Credits GBP','Exception rows','Exception GBP']);s.append(['September 2011','Test Country',2,100,1,-5,0,0]);s.append(['October 2011','Test Country',3,120,1,-8,0,0])
s=w.create_sheet('Invoice comparison');s.append(['InvoiceNo','Country','Sales rows','Sales GBP','Credit rows','Credits GBP','Exception rows','Exception GBP']);s.append(['Doc1','Test Country',3,120,1,-8,0,0])
s=w.create_sheet('Classified register');s.append(['source_row_id','Classification','Amount','SourceFile','Included']);s.append(['r1','sale',25,'retail_extract.csv',False]);s.append(['r2','sale',20,'september_extract.csv',True])
s=w.create_sheet('Exception register');s.append(['source_row_id','Classification','Amount','Treatment reason']);s.append(['r3','exception',0,'invalid price'])
s=w.create_sheet('Headline');s.append(['October sales',None,'October credits']);s.append([120,None,-8]);s.append(['Credit share was 6.7%; credits were 6.7% of sales.'])
p=F/'role_boundaries.xlsx';w.save(p);ts,text=tables(p,SPECS)
test('country_period_role_not_total_or_invoice',len(ts['countries'])==1 and all(r['count'] in [3,1] for r in ts['countries'][0]['rows']))
test('invoice_with_country_column_stays_invoice',len(ts['invoices'])==1 and all(r['invoice']=='Doc1' for r in ts['invoices'][0]['rows']))
test('separate_source_period_and_scope',len(ts['records'])==1 and len(ts['records'][0]['rows'])==1 and ts['records'][0]['rows'][0]['class']=='outside_scope')
test('exception_register_not_duplicate_main_detail',len(ts['queue'])==1 and ts['queue'][0]['rows'][0]['rowid']=='r3')
rr=[r for a in ts['report'] for r in a['rows']];claims=visible_numbers(rr,text,['signed credits','credits']);test('percentage_not_currency',claims and all(float(v)==-8 for v in claims))
s=w['Invoice comparison'];s.cell(1,9,'Sales rows');s.cell(2,9,4);p=F/'ambiguous_duplicate_role.xlsx';w.save(p)
try:tables(p,SPECS);pending=False
except ParsePending:pending=True
test('duplicate_required_header_pending',pending)
(O/'semantic_calibration.json').write_text(json.dumps({'status':'CALIBRATION_PASSED','checks':checks,'api_calls':0},indent=2))

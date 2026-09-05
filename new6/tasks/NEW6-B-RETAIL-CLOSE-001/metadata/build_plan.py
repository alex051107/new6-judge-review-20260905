from pathlib import Path
import json
TASK=Path(__file__).resolve().parents[1]
o=json.loads((TASK/'solution/oracle.json').read_text())
def numbers(row,idx):return [float(x) if i in idx and x is not None else x for i,x in enumerate(row)]
tot={r[0]:r for r in o['totals']}
report=[['Metric','Value'],['Reporting window','2011-10-01 00:00 inclusive to 2011-11-01 00:00 exclusive'],
 ['Currency','GBP'],['Gross sales',float(tot['sale'][2])],['Signed credits',float(tot['credit'][2])],
 ['Net recorded value',float(o['net_recorded_value'])],['Exception recorded amount',float(tot['exception'][2])],
 ['Source occurrences',o['source_occurrences']],['In-scope occurrences',o['source_occurrences']-tot['outside_scope'][1]],
 ['Outside-scope occurrences',tot['outside_scope'][1]],['Missing customer in scope',o['missing_customer_in_scope']],
 ['Interpretation','Recorded transaction value is not audited revenue or cash received. Credits are independent transaction documents; original sale links are not provided.'],
 ['Source','Daqing Chen (2015), Online Retail, UCI Machine Learning Repository, DOI 10.24432/C5BW33. CC BY 4.0.'],
 ['Source URL','https://archive.ics.uci.edu/dataset/352/online+retail'],
 ['Row identity','Online Retail worksheet name and original physical Excel row number, retained for every occurrence.']]
plan={'title':'October 2011 trading close','sheets':[
 {'name':'Trading report','rows':report},
 {'name':'Status totals','rows':[['Classification','Row count','Recorded amount GBP']]+[numbers(r,{2}) for r in o['totals']],
  'chart':{'category':0,'values':[2],'title':'Recorded value by treatment, GBP'}},
 {'name':'Classified records','rows':[o['classified_headers']]+[numbers(r,{4,6,10}) for r in o['classified']]},
 {'name':'Invoice totals','rows':[['InvoiceNo','Classification','Row count','Recorded amount GBP','Invoice countries']]+[numbers(r,{3}) for r in o['invoice_totals']]},
 {'name':'Country totals','rows':[['Country','Classification','Row count','Recorded amount GBP']]+[numbers(r,{3}) for r in o['country_totals']]},
 {'name':'Exception queue','rows':[['source_row_id','InvoiceNo','Classification','Issue type','Treatment reason','Recorded amount GBP']]+[numbers(r,{5}) for r in o['exceptions']]}]}
(TASK/'metadata/reference_plan.json').write_text(json.dumps(plan,ensure_ascii=False,separators=(',',':')))
receipt=next(r for r in json.loads((TASK.parents[1]/'sources/downloads_b/download_receipt.json').read_text()) if r['source_id']=='retail_uci')
manifest={'task_id':TASK.name,'source':receipt,'source_type':'real_transaction_data_reconstructed_request','rights':'UCI landing explicitly CC BY 4.0; Daqing Chen, dataset DOI 10.24432/C5BW33. Landing HTML saved under sources/downloads_b.',
 'source_workbook':'Online Retail.xlsx','original_source_rows':541909,'source_columns':o['raw_headers'][1:],
 'transformation':'All original physical rows with timestamp >= 2011-09-30 00:00 and < 2011-11-02 00:00, in original order. Add source_row_id only. ISO timestamps and exact decimal/string CSV serialization. No deduplication, cleansing or selection by errors.',
 'extract_occurrences':o['source_occurrences'],'source_gate':'PASSED','oracle_gate':'PASSED independent reversed document-first Decimal policy/grouping',
 'observed_profile':{k:o[k] for k in ['totals','missing_customer_in_scope','repeated_looking_extra_occurrences','invoices_with_country_conflict']},
 'input_files':[]}
(TASK/'metadata/source_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
(TASK/'data/input_files/source_context.md').write_text('# UCI Online Retail source\n\nDaqing Chen (2015), Online Retail, UCI Machine Learning Repository. DOI: https://doi.org/10.24432/C5BW33. Source: https://archive.ics.uci.edu/dataset/352/online+retail. Licensed CC BY 4.0: https://creativecommons.org/licenses/by/4.0/.\n\nThis is Online Retail (dataset 352), not Online Retail II. The original dataset contains transactions of a UK-based non-store retailer between 1 December 2010 and 9 December 2011. Currency is sterling. InvoiceNo identifies a transaction document; an identifier starting with C denotes cancellation. StockCode identifies an item; Description is the item name; Quantity is the quantity per transaction line; InvoiceDate is the supplied transaction timestamp; UnitPrice is the sterling unit price; CustomerID is the customer identifier; Country is customer country.\n\nThe provided extract contains every original record dated 30 September through 1 November 2011 inclusive. source_row_id is the original worksheet name plus physical worksheet row number. Timestamp serialization is ISO local as supplied, without timezone conversion. All original business-field values and repeated physical occurrences are retained. Missing CustomerID is blank.\n\nReporting policy in review_brief.md is a project-authored analytical convention. This task does not represent an actual engagement with the retailer.\n')
print('Retail source manifest and reference plan ready')

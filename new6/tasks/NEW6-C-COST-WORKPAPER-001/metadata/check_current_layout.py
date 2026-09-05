"""Focused C1 layout calibration; no paid calls and no historical receipt edits."""
from pathlib import Path
from decimal import Decimal
import json,sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'metadata'),str(ROOT/'tests')]
from ooxml_edit import edit
from evaluate import evaluate
from oracle_recompute import source

ALL=['R001','R002','R003','R004','R005','R006']
OUT=ROOT/'metadata/current_layout_validation_v11'
F=ROOT/'fixtures'

def build():
    # Published fixtures are immutable; generate only a missing fixture set.
    required=['equivalent_role_headers_reconciliation.xlsx','role_headers_wrong_reconciliation.xlsx','equivalent_exclusion_bullets.xlsx']
    if all((F/name).is_file() for name in required):return
    patches={'Elements':dict(zip(['A4','B4','C4','D4','E4'],['Element Description','Original Cost (£)','Original %','Adjusted Cost (£)','Notes / Provisional Sums'])),
      'Summary':{'A4':'Stage / Item','B4':'Original (£)','D4':'Rate/Factor','E4':'Adjusted (£)','F4':None},
      'Provisional sums':{'B4':'Amount (£)','C4':'Notes / Source'}}
    rec={'A1':'Falmouth October 2024 reconciliation, source PDF page 2',
      'A4':'Stage / Item','B4':'Source (£)','C4':'Workbook (£)','D4':'Variance (£)',
      'E4':'Source','F4':'Page'}
    for i,r in enumerate(source()['summary'],5):
        patches['Summary']['F'+str(i)]=None
        rec.update({'A'+str(i):r['label'],'B'+str(i):r['amount'],
          'C'+str(i):"=Summary!E"+str(i),'E'+str(i):r['source'],'F'+str(i):r['page']})
        if isinstance(r['amount'],(int,float)):
            rec['D'+str(i)]='=C'+str(i)+'-B'+str(i)
    edit(ROOT/'solution/reference.xlsx',F/'equivalent_role_headers_reconciliation.xlsx',patches=patches,new_sheets={'Reconciliation':rec},clear_caches=True)
    edit(F/'equivalent_role_headers_reconciliation.xlsx',F/'role_headers_wrong_reconciliation.xlsx',patches={'Reconciliation':{'C5':'=Summary!E5+1000'}},clear_caches=True)
    removal={};bullets={'A1':'M&E EXCLUSIONS (not in estimate):','A2':'Falmouth_OCE_October2024_RevA.pdf - PDF page 4'}
    for i,r in enumerate(source()['exclusions'],5):
        if r['id'].startswith('excluded_services_'):
            removal.update({c+str(i):None for c in 'ABCDE'})
            bullets['A'+str(4+int(r['id'].rsplit('_',1)[1]))]='• '+r['label']
    edit(ROOT/'solution/reference.xlsx',F/'equivalent_exclusion_bullets.xlsx',patches={'Exclusions':removal},new_sheets={'Services exclusions':bullets},clear_caches=True)

def main():
    build(); OUT.mkdir(parents=True,exist_ok=True)
    existing=json.loads((F/'manifest.json').read_text())['cases']
    wanted={'reference','wrong_printed_element','wrong_risk_base','duplicate_omission','mixed_final','static_current_answer','partial_parse','legal_formula_limit','excluded_is_zero'}
    cases=[c for c in existing if c['name'] in wanted]
    cases += [dict(name='equivalent_role_headers_reconciliation',file='equivalent_role_headers_reconciliation.xlsx',status='SCORED',lose=[],preserve=ALL),
      dict(name='role_headers_wrong_reconciliation',file='role_headers_wrong_reconciliation.xlsx',status='SCORED',lose=['R004'],preserve=[x for x in ALL if x!='R004']),
      dict(name='equivalent_exclusion_bullets',file='equivalent_exclusion_bullets.xlsx',status='SCORED',lose=[],preserve=ALL)]
    suffix='receipt.json'
    if len(sys.argv)>1:
        requested=set(sys.argv[1:]);cases=[c for c in cases if c['name'] in requested]
        if {c['name'] for c in cases}!=requested:raise ValueError('Unknown focused case')
        suffix='receipt_exclusion_repair.json'
    rows=[]
    for c in cases:
        result=evaluate(F/c['file'],OUT/c['name'],True)
        scores=result.get('criterion_scores',{})
        checks=[result['evaluation_status']==c['status']]
        checks.extend(k in scores and Decimal(scores[k])<1 for k in c['lose'])
        checks.extend(k in scores and Decimal(scores[k])==1 for k in c['preserve'])
        row=dict(name=c['name'],status=result['evaluation_status'],score=result.get('score_decimal'),facts=scores,expected=c,passed=all(checks))
        rows.append(row)
        (OUT/suffix).write_text(json.dumps({'passed':all(x['passed'] for x in rows),'completed':len(rows),'planned':len(cases),'results':rows},indent=2))
        print(json.dumps(row),flush=True)
        if not row['passed']:raise AssertionError('Focused C1 calibration failed: '+c['name'])
if __name__=='__main__':main()

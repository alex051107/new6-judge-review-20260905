"""C1 v1.2 controls/list/self-check calibration, bounded to C1."""
from pathlib import Path
from decimal import Decimal
import json,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'metadata'),str(ROOT/'tests')]
from evaluate import evaluate
from ooxml_edit import edit as _edit
from oracle_recompute import source
ALL=['R001','R002','R003','R004','R005','R006']
OUT=ROOT/'metadata/controls_notes_validation_v12'
F=ROOT/'fixtures'
def edit(source,destination,**kwargs):
    # Keep published/calibrated fixture bytes stable on selective rechecks.
    if not Path(destination).is_file():_edit(source,destination,**kwargs)

def build():
    patch={'Elements':{'J4':'Adjustment (%)'},'Summary':{'D4':None},'Provisional sums':{}}
    for i,r in enumerate(source()['elements'],5):patch['Elements'].update({'J'+str(i):0,'D'+str(i):f'=N(B{i})*(1+J{i})' if r['id']=='listing' else f'=B{i}*(1+J{i})'})
    for i,r in enumerate(source()['summary'],5):
        patch['Summary']['D'+str(i)]=None
        if r['rate'] is not None:patch['Summary']['C'+str(i)]=str(r['rate']*100)+'%'
    patch['Summary'].update({'E7':"=(E5+E6)*'Rate Controls'!C5",'E11':"=E10*'Rate Controls'!C6",'E15':"=E14*'Rate Controls'!C7"})
    rates={'A1':'Falmouth October 2024 source PDF page 2','A4':'Item','B4':'Printed rate','C4':'Working rate'}
    for i,(label,rate) in enumerate([('Main Contractors Overheads & Profit Rate',.1),('Design Development Risks Rate',.1),('Inflation Allowance Rate',.01)],5):rates.update({'A'+str(i):label,'B'+str(i):str(rate*100)+'%','C'+str(i):rate})
    notes={'A1':'Provisional sums included within elemental costs; memorandum only','A2':'Falmouth_OCE_October2024_RevA.pdf - page 4'}
    for i,r in enumerate(source()['provisional'],5):
        patch['Provisional sums'].update({col+str(i):None for col in 'ABCDE'})
        notes['A'+str(i)]='• '+r['label']+': £'+format(r['amount'],',')
    notes['A5']='• Structural appraisal of existing timbers: £2k'
    audit={'A1':'Element source reconciliation','A3':'Item','B3':'Original amount','A5':'Reconciliation Check:',
      'A6':'Expected Total (from PDF):','B6':1430225,'A7':'Calculated Total:','B7':"=SUM('Elements'!B5:B19)",'A8':'Difference:','B8':'=B7-B6'}
    dest=F/'equivalent_controls_notes.xlsx'
    edit(ROOT/'solution/reference.xlsx',dest,patches=patch,new_sheets={'Rate Controls':rates,'Allowances memo':notes,'Source check':audit},clear_caches=True)
    edit(dest,F/'controls_notes_wrong_allowance.xlsx',patches={'Allowances memo':{'A5':'• Structural appraisal of existing timbers: £2,500'}},clear_caches=True)
    edit(dest,F/'controls_notes_false_selfcheck.xlsx',patches={'Source check':{'B8':1000}},clear_caches=True)
    embedded={'Summary':{'A7':'Main Contractors Overheads & Profit (10%)','C7':None,'A11':'Design Development Risks (10%)','C11':None,'A15':'Inflation Allowance (1.00%)','C15':None},'Provisional sums':{}}
    for i,r in enumerate(source()['provisional'],5):embedded['Provisional sums']['C'+str(i)]='Included in the elemental costs shown in the Building Works Estimate.'
    dest=F/'equivalent_embedded_rates_inclusion.xlsx'
    edit(ROOT/'solution/reference.xlsx',dest,patches=embedded,clear_caches=True)
    edit(dest,F/'embedded_wrong_printed_rate.xlsx',patches={'Summary':{'A15':'Inflation Allowance (2.00%)'}},clear_caches=True)
    edit(dest,F/'included_contradictory_scope.xlsx',patches={'Provisional sums':{'C5':'Not included; add to total as an additional charge.'}},clear_caches=True)

def main():
    build();OUT.mkdir(parents=True,exist_ok=True)
    base=json.loads((F/'manifest.json').read_text())['cases']
    wanted={'reference','equivalent_formula','equivalent_layout','wrong_printed_element','wrong_risk_base','mixed_final','duplicate_omission','static_current_answer','partial_parse','legal_formula_limit','excluded_is_zero'}
    cases=[c for c in base if c['name'] in wanted]
    cases += [dict(name='equivalent_controls_notes',file='equivalent_controls_notes.xlsx',status='SCORED',lose=[],preserve=ALL),
      dict(name='controls_notes_wrong_allowance',file='controls_notes_wrong_allowance.xlsx',status='SCORED',lose=['R002'],preserve=[k for k in ALL if k!='R002']),
      dict(name='controls_notes_false_selfcheck',file='controls_notes_false_selfcheck.xlsx',status='SCORED',lose=['R004'],preserve=[k for k in ALL if k!='R004']),
      dict(name='equivalent_embedded_rates_inclusion',file='equivalent_embedded_rates_inclusion.xlsx',status='SCORED',lose=[],preserve=ALL),
      dict(name='embedded_wrong_printed_rate',file='embedded_wrong_printed_rate.xlsx',status='SCORED',lose=['R002'],preserve=[k for k in ALL if k!='R002']),
      dict(name='included_contradictory_scope',file='included_contradictory_scope.xlsx',status='SCORED',lose=['R003'],preserve=[k for k in ALL if k!='R003'])]
    if len(sys.argv)>1:
        selected=set(sys.argv[1:]);cases=[c for c in cases if c['name'] in selected]
        if {c['name'] for c in cases}!=selected:raise ValueError('Unknown case')
    rows=[]
    for c in cases:
        r=evaluate(F/c['file'],OUT/c['name'],True);scores=r.get('criterion_scores',{})
        checks=[r['evaluation_status']==c['status']]+[k in scores and Decimal(scores[k])<1 for k in c['lose']]+[k in scores and Decimal(scores[k])==1 for k in c['preserve']]
        row={'name':c['name'],'status':r['evaluation_status'],'score_decimal':r.get('score_decimal'),'facts':scores,'expected':c,'passed':all(checks)};rows.append(row)
        filename='receipt.json' if len(sys.argv)==1 else ('receipt_semantics.json' if any(x['name']=='equivalent_embedded_rates_inclusion' for x in cases) else 'receipt_repair.json')
        (OUT/filename).write_text(json.dumps({'completed':len(rows),'planned':len(cases),'passed':all(x['passed'] for x in rows),'results':rows},indent=2));print(json.dumps(row),flush=True)
        if not row['passed']:raise AssertionError(c['name'])
if __name__=='__main__':main()

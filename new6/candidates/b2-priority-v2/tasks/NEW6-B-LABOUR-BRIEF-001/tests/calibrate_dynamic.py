"""One bounded bidirectional calibration batch; no paid model requests."""
from pathlib import Path
import json,os,sys,xml.etree.ElementTree as ET
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'common'))
from runtime import recalculate_xlsx
from fixture_xml import Fixture,NS,N
from evaluate import evaluate
TASK=Path(__file__).resolve().parents[1]
OUT=TASK/'metadata/dynamic_calibration';OUT.mkdir(exist_ok=True)
reference,_=recalculate_xlsx(TASK/'solution/reference.xlsx',OUT/'reference_native',timeout=120)
def case(name,edit,lose=(),preserve=(),status='SCORED',native=True):
    dest=TASK/'fixtures'/f'{name}.xlsx'
    if edit:edit.save(dest)
    if name=='bad_file':dest.write_text('not a workbook')
    answer=dest
    if native and edit:answer,_=recalculate_xlsx(dest,OUT/name/'native',timeout=120)
    os.environ['NEW6_EVIDENCE_DIR']=str(OUT/name)
    r=evaluate(answer,TASK/'data/input_files')
    assert r['evaluation_status']==status,(name,r.get('evaluation_status'),r.get('evidence',{}).get('live_review_error'))
    if status=='SCORED':
        for k in lose:assert r['criterion_scores'][k]<1,(name,k,'should lose')
        for k in preserve:assert abs(r['criterion_scores'][k]-1)<1e-12,(name,k,r['criterion_scores'][k])
        for profile in r['profiles'].values():assert profile['criterion_scores']==r['criterion_scores']
    else:assert r['normalized_score'] is None
    (OUT/(name+'.json')).write_text(json.dumps(r,indent=2))
    return {'case':name,'status':status,'score':r.get('score_decimal'),'lose':list(lose),'preserve':list(preserve),'assertions_passed':True}
allkeys=[f'R{i:03}' for i in range(1,10)];checks=[]
checks.append(case('reference',Fixture(reference),preserve=allkeys,native=False))
# Equivalent formulas and a relocated control block with updated references.
f=Fixture(reference)
for i in range(2,298):f.cell('Live screening',f'F{i}',formula=f'IF(G{i}=0,"no",IF(G{i}<=\'Live controls\'!$B$4,"yes","no"))',uncached=True)
checks.append(case('equivalent_formula',f,preserve=allkeys))
f=Fixture(reference);root=f.root('Live controls')
for row in root.find('m:sheetData',NS):
    for c in row:c.attrib['r']=c.attrib['r'].replace('A','E').replace('B','F')
dim=root.find('m:dimension',NS)
if dim is not None:dim.attrib['ref']='E1:F5'
f.update('Live controls',root)
for name in f.sheets:
    r=f.root(name)
    for formula in r.findall('.//m:f',NS):
        if formula.text:formula.text=formula.text.replace("'Live controls'!$B$","'Live controls'!$F$")
    f.update(name,r)
checks.append(case('equivalent_control_layout',f,preserve=allkeys))
# Freeze only live formulas to their native values: static snapshot stays right.
f=Fixture(reference)
for name in ['Live screening','Live shortlist','Live controls']:
    root=f.root(name)
    for c in root.findall('.//m:c',NS):
        formula=c.find('m:f',NS)
        if formula is not None:c.remove(formula)
    f.update(name,root)
checks.append(case('static_live_snapshot',f,lose=['R009'],preserve=allkeys[:-1]))
f=Fixture(reference)
for i in range(2,298):f.cell('Live screening',f'F{i}',formula=f'IF(AND(G{i}>0,G{i}<=5),"yes","no")',uncached=True)
checks.append(case('capacity_disconnected',f,lose=['R009'],preserve=allkeys[:-1]))
f=Fixture(reference)
for i in range(2,298):
    root=f.root('Live screening');cell=next(c for c in root.findall('.//m:c',NS) if c.attrib['r']==f'E{i}');fo=cell.find('m:f',NS);fo.text=fo.text.replace(">='Live controls'!$B$2",">'Live controls'!$B$2");f.update('Live screening',root)
checks.append(case('exclusive_threshold',f,lose=['R009'],preserve=allkeys[:-1]))
checks.append(case('duplicate_screen_row',Fixture(reference).duplicate_row('Screening',2),lose=['R007'],preserve=[k for k in allkeys if k!='R007']))
checks.append(case('omit_screen_row',Fixture(reference).remove_row('Screening',2),lose=['R007','R008'],preserve=['R001','R002','R003','R004','R005','R006','R009']))
checks.append(case('contradict_live_row',Fixture(reference).duplicate_row('Live screening',2,{'F':'yes'}),lose=['R009'],preserve=allkeys[:-1]))
checks.append(case('unsupported_formula',Fixture(reference).cell('Live controls','B5',formula='_xlfn.XLOOKUP(1,{1},{5})',uncached=True),status='JUDGE_ERROR',native=False))
checks.append(case('missing_output',None,status='OUTPUT_MISSING',native=False))
checks.append(case('bad_file',None,status='MALFORMED_OUTPUT',native=False))
(OUT/'receipt.json').write_text(json.dumps({'passed':len(checks),'checks':checks,'paid_calls':0,'budget':'One source check, one fixture batch, one pinned Linux reference check; rerun affected checks after a repair only.'},indent=2))
print(json.dumps(checks,indent=2))

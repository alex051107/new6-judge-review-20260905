"""Observed natural-layout repairs, with no new Agent calls or native reruns."""
from pathlib import Path
import sys,json
TASK=Path(__file__).resolve().parents[1];sys.path.insert(0,str(TASK/'tests'))
from fixture_xml import Fixture
from evaluate import evaluate
ALL=['R001','R002','R003','R004','R005'];REF=TASK/'solution/reference.xlsx'
def build():
    cases=[]
    def add(name,fixture,lose=(),preserve=ALL,facts=None):
        path=TASK/'fixtures'/(name+'.xlsx');fixture.save(path);cases.append({'id':name,'file':str(path),'lose':list(lose),'preserve':list(preserve),'facts':facts or {}})
    f=Fixture(REF).cell('Current data','C2',65.81091174375987).cell('Current data','D2',69.74164510755926).cell('Current data','I2',3.930733363799391)
    add('equivalent_extra_precision',f)
    f=Fixture(REF)
    root=f.root('Previous shortlist')
    for d in root.findall('m:drawing',{'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}):root.remove(d)
    f.update('Previous shortlist',root)
    for n in list(f.parts):
        if '/charts/' in n and b'Previous shortlist' in f.parts[n]:del f.parts[n]
    # Remove the external-file reference: the candidate retains four historical
    # components, but demonstrably drops the earlier chart.
    f.cell('Current briefing','B15','Previous briefing, data, shortlist and exclusions remain in the historical worksheets.')
    add('missing_previous_chart_partial_credit',f,lose=['R005'],preserve=ALL[:-1],facts={'R005':(0.8+0.8+1)/3})
    f=Fixture(REF).clear_sheet('Shortlist changes').cell('Current briefing','B13','No movement explanation supplied')
    f.cell('Current exclusions','A30','E10000003').cell('Current exclusions','B30','Cambridgeshire').cell('Current exclusions','C30','Employment did not fall in the second comparison; this area is not the city of Cambridge.')
    add('distinct_authority_without_explanation',f,lose=['R001','R004'],preserve=['R002','R003','R005'])
    plan=json.loads((TASK/'metadata/reference_plan.json').read_text());moves=next(x['rows'] for x in plan['current'] if x['name']=='Shortlist changes')
    f=Fixture(REF);nextrow=30
    for i,row in enumerate(moves[1:],2):
        if row[4]=='Left':
            f.remove_row('Shortlist changes',i)
            for col,value in zip('ABC',[row[0],row[1],row[5]]):f.cell('Current exclusions',f'{col}{nextrow}',value)
            nextrow+=1
    add('equivalent_departure_explanations',f)
    for name in ['equivalent_narrative_movements','equivalent_combined_ranks','negated_movement_keywords','wrong_cumulative','overwritten_previous_data']:
        c=next(x for x in json.loads((TASK/'metadata/calibration_cases.json').read_text()) if x['id']==name)
        cases.append({**c,'file':str(TASK/c['file'])})
    cases.append({'id':'reference','file':str(REF),'preserve':ALL})
    return cases

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    cases=build();checks=[]
    for c in cases:
        x=evaluate(Path(c['file']),TASK/'data/input_files');(a.out/(c['id']+'.json')).write_text(json.dumps(x,ensure_ascii=False,indent=2))
        try:
            assert x['evaluation_status']=='SCORED',x['evidence'].get('reason')
            f=x['criterion_scores']
            for k in c.get('preserve',[]):assert f[k]==1,(k,'preserve',f[k])
            for k in c.get('lose',[]):assert f[k]<1,(k,'lose',f[k])
            for k,v in c.get('facts',{}).items():assert abs(f[k]-v)<1e-12,(k,f[k],v)
            checks.append({'id':c['id'],'passed':True,'score':x['score_decimal']})
        except AssertionError as e:checks.append({'id':c['id'],'passed':False,'error':str(e)})
    receipt={'passed':all(c['passed'] for c in checks),'checks':checks,'api_calls':0,'native_recalculations':0}
    (a.out/'receipt.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt));sys.exit(0 if receipt['passed'] else 1)

"""Version-isolated extension; original six criteria retain their original facts."""
from pathlib import Path
import json,sys,argparse
from decimal import Decimal
import evaluate_base as base
from read_candidate import tables, LOOKUP, norm, eq, population, mean, ParsePending
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'common'))
from runtime import score_profiles
TASK=Path(__file__).resolve().parents[1]
BASE_RUBRIC=json.loads((TASK/'metadata/base_rubric.json').read_text())
base.score_profiles=lambda _rubric,*args,**kwargs:score_profiles(BASE_RUBRIC,*args,**kwargs)
for scenario in ['baseline','relaxed','strict']:
    for kind in ['eligible','selected']:
        field=scenario+'_'+kind
        for label in [field,scenario+' '+kind,kind+' '+scenario,scenario+(' eligibility' if kind=='eligible' else ' selection')]:LOOKUP[norm(label)]=field
for field,aliases in {'scenario':['scenario','threshold scenario','policy scenario'], 'review_order':['review order','shortlist order','review priority','shortlist rank'], 'movement':['movement','membership change','change from baseline']}.items():
    for label in aliases:LOOKUP[norm(label)]=field
SPECS={'screen':{'code','baseline_eligible','baseline_selected','relaxed_eligible','relaxed_selected','strict_eligible','strict_selected'},
       'review':{'scenario','review_order','code','employment_change','unemployment_change'},
       'movement':{'scenario','code','movement'}}
def decision(v):
    n=norm(v)
    if n in {'yes','true','1','eligible','selected','included'}:return 'yes'
    if n in {'no','false','0','ineligible','noteligible','notselected','excluded'}:return 'no'
    if n in {'unavailable','missing','suppressed','na','notavailable'}:return 'unavailable'
    return n
def scenario(v):
    n=norm(v)
    return {'base':'baseline','baseline10pp':'baseline','relaxed05pp':'relaxed','strict20pp':'strict'}.get(n,n)
def evaluate(path,input_dir=None):
    result=base.evaluate(path,input_dir)
    if result['evaluation_status']!='SCORED':
        return score_profiles(TASK/'rubric.json',status=result['evaluation_status'],evidence=result['evidence'])
    facts=result['criterion_scores']; evidence=result['evidence']
    try:ts,text=tables(path,SPECS)
    except Exception as exc:return score_profiles(TASK/'rubric.json',status='JUDGE_ERROR',evidence={**evidence,'priority_parse_reason':str(exc)})
    # A partially bound screening/shortlist has an explicit pending outcome.
    # Absence of those outputs from an otherwise bound workbook is measurable.
    if (not ts['screen'] and any('__UNBOUND__' in x and any(k in norm(x) for k in ['baselineeligible','eligibilitybaseline','relaxedselected']) for x in text)) or (not ts['review'] and any('__UNBOUND__' in x and 'shortlist' in x.lower() and 'code' in x.lower() for x in text)):
        return score_profiles(TASK/'rubric.json',status='JUDGE_ERROR',evidence={**evidence,'priority_parse_reason':'Screening or shortlist present but not safely bound; manual parse required.'})
    truth=json.loads((TASK/'solution/priority_oracle.json').read_text())
    screen=[r for t in ts['screen'] for r in t['rows'] if r.get('code')]
    fields=list(next(iter(truth['register'].values())))
    detail=[]
    for code,expected in truth['register'].items():
        actual=[r for r in screen if str(r['code'])==code]
        for field,want in expected.items():
            okay=bool(actual) and all(decision(r.get(field))==want for r in actual)
            detail.append({'code':code,'field':field,'correct':okay,'candidate':[r.get(field) for r in actual],'expected':want})
    # Identical complete alternative final tables are legal, duplicates within
    # any one table lose population credit; contradictory tables lose facts.
    pop=mean([population([str(r['code']) for r in t['rows'] if r.get('code')],truth['register']) for t in ts['screen']])
    facts['R007']=mean([mean([x['correct'] for x in detail]),pop])
    rows=[r for t in ts['review'] for r in t['rows'] if r.get('code')]
    rankfacts=[];pops=[];self_facts=[]
    for s,expected in truth['shortlists'].items():
        actual=[r for r in rows if scenario(r.get('scenario'))==s]
        relevant=[t for t in ts['review'] if any(scenario(r.get('scenario'))==s for r in t['rows'])]
        pops.append(mean([population([str(r['code']) for r in t['rows'] if r.get('code') and scenario(r.get('scenario'))==s],[r['code'] for r in expected]) for t in relevant]))
        for ex in expected:
            matches=[r for r in actual if eq(r.get('review_order'),ex['order'])]
            for key in ['code','employment_change','unemployment_change']:
                okay=bool(matches) and all(str(r.get(key))==ex[key] if key=='code' else eq(r.get(key),ex[key]) for r in matches)
                rankfacts.append({'scenario':s,'order':ex['order'],'field':key,'correct':okay})
        for code,want in truth['register'].items():
            sr=[r for r in screen if str(r['code'])==code]
            listed=any(str(r['code'])==code for r in actual)
            self_facts.append(bool(sr) and all((decision(r.get(s+'_selected'))=='yes')==listed for r in sr))
    # Enter/leave claims may be explicit tables or recoverable from complete
    # baseline/scenario membership. Do not require a private phrasing template.
    movefacts=[]
    for t in ts['movement']:
        for r in t['rows']:
            if not r.get('code'):continue
            s=scenario(r.get('scenario'));kind={'enter':'entered','added':'entered','exit':'left','removed':'left'}.get(norm(r.get('movement')),norm(r.get('movement')))
            movefacts.append(str(r['code']) in truth['movements'].get(s,{}).get(kind,[]))
    facts['R008']=mean([mean([x['correct'] for x in rankfacts]),mean(pops),mean(self_facts),mean(movefacts) if movefacts else mean([x['correct'] for x in detail if x['field'].endswith('_selected')])])
    evidence.update(priority_screen_facts=detail,priority_shortlist_facts=rankfacts,priority_shortlist_population=pops,priority_candidate_consistency=mean(self_facts),priority_movement_claims=movefacts,priority_denominators={'screen_facts':len(detail),'shortlist_facts':len(rankfacts),'selection_consistency':len(self_facts)},priority_policy='Published baseline/relaxed/strict inclusive thresholds, two comparable indicators, five-place ranking; static accepted.')
    try:
        from dynamic_review import grade
        facts['R009'],evidence['live_review']=grade(path)
    except Exception as exc:
        return score_profiles(TASK/'rubric.json',status='JUDGE_ERROR',evidence={**evidence,'live_review_error':type(exc).__name__+': '+str(exc)})
    return score_profiles(TASK/'rubric.json',facts,evidence=evidence)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('answer',nargs='?',default='/app/output/answer.xlsx');p.add_argument('--input-dir');p.add_argument('--result');a=p.parse_args()
    out=json.dumps(evaluate(Path(a.answer),a.input_dir),indent=2)
    if a.result:Path(a.result).write_text(out)
    print(out)

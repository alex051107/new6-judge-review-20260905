"""One combined bidirectional calibration. Fixture names do not decide scores."""
from pathlib import Path
from decimal import Decimal as D
import json,sys,argparse
from evaluate import evaluate,ROOT

CASES=[
 {'name':'reference','path':'solution/reference.xlsx','kind':'full_credit','loss':[],'keep':['R001','R002','R003','R004','R005','R006']},
 {'name':'equivalent_layout','kind':'full_credit','loss':[],'keep':['R001','R002','R003','R004','R005','R006']},
 {'name':'equivalent_formula','kind':'full_credit','loss':[],'keep':['R001','R002','R003','R004','R005','R006']},
 {'name':'zone_shift','kind':'business_error','loss':['R003'],'keep':['R001','R002','R004','R005','R006']},
 {'name':'floor_weight','kind':'business_error','loss':['R003','R004'],'keep':['R001','R002','R005','R006']},
 {'name':'constant_quotes','kind':'business_error','loss':['R004'],'keep':['R001','R002','R003','R005','R006']},
 {'name':'contradictory_total','kind':'business_error','loss':['R003','R004'],'keep':['R001','R002','R005','R006']},
 {'name':'duplicate_rate','kind':'business_error','loss':['R001','R002','R003','R004'],'keep':['R005','R006']},
 {'name':'omitted_quote','kind':'business_error','loss':['R003','R005'],'keep':['R001','R002','R004','R006']},
 {'name':'mixed_final','kind':'business_error','loss':['R003','R004'],'keep':['R001','R002','R005','R006']},
 {'name':'constant_offset','kind':'business_error','loss':['R003'],'keep':['R001','R002','R004','R005','R006']},
 {'name':'wrong_page','kind':'business_error','loss':['R006'],'keep':['R001','R002','R003','R004','R005']},
 {'name':'equivalent_date','kind':'full_credit','loss':[],'keep':['R001','R002','R003','R004','R005','R006']},
 {'name':'unsupported_formula','kind':'unscorable','state':'JUDGE_ERROR','pass':None},
 {'name':'dynamic_unsupported','kind':'unscorable','state':'JUDGE_ERROR','pass':None},
 {'name':'malformed','kind':'unscorable','state':'MALFORMED_OUTPUT','pass':False},
 {'name':'missing_completed','path':'fixtures/absent.xlsx','kind':'unscorable','state':'OUTPUT_MISSING','pass':False,'completed_run':True},
 {'name':'missing_unconfirmed','path':'fixtures/absent.xlsx','kind':'unscorable','state':'INFRA_ERROR','pass':None,'completed_run':False}
]
def check_spec(c):
    assert c['kind'] in {'full_credit','business_error','unscorable'},c
    if c['kind']!='unscorable':
        ids={f'R{i:03}' for i in range(1,7)}
        assert len(set(c['loss']))==len(c['loss']) and len(set(c['keep']))==len(c['keep']),c
        assert set(c['loss'])|set(c['keep'])==ids and not set(c['loss'])&set(c['keep']),c
        assert bool(c['loss'])==(c['kind']=='business_error'),c
    else:assert c['state'] in {'JUDGE_ERROR','MALFORMED_OUTPUT','OUTPUT_MISSING','INFRA_ERROR'}

def main():
    p=argparse.ArgumentParser();p.add_argument('--only',nargs='*');p.add_argument('--reuse-native',action='store_true');a=p.parse_args();out=ROOT/'metadata/calibration';out.mkdir(exist_ok=True)
    if a.only is not None:assert a.only and len(a.only)==len(set(a.only)) and set(a.only)<={c['name'] for c in CASES},'Unknown, empty or repeated fixture selection'
    all_results=[]
    for case in CASES:
        check_spec(case)
        if a.only and case['name'] not in a.only:continue
        result=evaluate(ROOT/case.get('path',f"fixtures/{case['name']}.xlsx"),out/case['name'],case.get('completed_run',True),reuse_native=a.reuse_native)
        failures=[]
        if case['kind']=='unscorable':
            if result['evaluation_status']!=case['state'] or result['normalized_score'] is not None or result['pass'] is not case['pass']:failures.append('wrong nonbusiness status')
        elif result['evaluation_status']!='SCORED':failures.append(result['evaluation_status']+': '+str(result.get('evidence',{})))
        else:
            facts=result['criterion_scores']
            failures += [f'{k}: expected loss, got {facts[k]}' for k in case['loss'] if not D(facts[k])<1]
            failures += [f'{k}: invariant lost, got {facts[k]}' for k in case['keep'] if D(facts[k])!=1]
            for profile,res in result['profiles'].items():
                if res['pass']!=(D(res['score_decimal'])>=D('.70')):failures.append('threshold mismatch '+profile)
            if case['kind']=='full_credit' and any(D(r['score_decimal'])!=1 for r in result['profiles'].values()):failures.append('full credit not preserved')
        row={'fixture':case['name'],'type':case['kind'],'expected':case,'status':result['evaluation_status'],'score':result['normalized_score'],'profile_scores':{k:v['score_decimal'] for k,v in result['profiles'].items()},'pass':result['pass'],'criterion_scores':result.get('criterion_scores'),'assertions_passed':not failures,'failures':failures,'lost_facts':{k:[f['fact'] for f in fs if not f['correct']] for k,fs in result.get('evidence',{}).get('facts',{}).items() if any(not f['correct'] for f in fs)}}
        all_results.append(row);print(json.dumps({k:row[k] for k in ['fixture','status','score','pass','assertions_passed','failures']},ensure_ascii=False),flush=True)
        (out/('receipt'+('_'+','.join(a.only) if a.only else '')+'.json')).write_text(json.dumps({'cases':all_results,'passed':all(x['assertions_passed'] for x in all_results),'agent_samples':0,'fixture_counts_not_natural_failure_rates':True},indent=2,ensure_ascii=False))
        if failures:sys.exit(1)
if __name__=='__main__':main()

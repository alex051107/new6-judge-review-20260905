#!/usr/bin/env python3
"""Replay the final selected scored records, preserving each task's Judge."""
import argparse,csv,json,subprocess,sys
from decimal import Decimal
from pathlib import Path
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parent

def main():
    p=argparse.ArgumentParser(description=__doc__)
    g=p.add_mutually_exclusive_group(required=True);g.add_argument('--all',action='store_true');g.add_argument('--case',nargs='+')
    p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    with (REPO/'results/current-effective-v3/trials.csv').open() as f:rows=list(csv.DictReader(f))
    rows=[r for r in rows if r['status']=='SCORED' and (a.all or r['case'] in a.case)]
    if not rows or a.case and set(a.case)!={r['case'] for r in rows}:p.error('Unknown or unscored case; use qwen-final/replay.py for a Qwen pending case')
    out=a.out.resolve()
    if out.exists():p.error('--out must be a new directory')
    out.mkdir(parents=True)
    for group,script,selected in [('retained',ROOT/'replay_current.py',[r for r in rows if r['system']!='qwen']),('qwen',ROOT/'qwen-final/replay.py',[r for r in rows if r['system']=='qwen'])]:
        if selected:subprocess.run([sys.executable,str(script),'--case',*[r['case'] for r in selected],'--out',str(out/group)],check=True)
    checks=[]
    for r in rows:
        base=out/('qwen' if r['system']=='qwen' else 'retained')/'scores'/r['case']
        score=json.loads((base/'current-score.json').read_text())
        receipt=json.loads((base/('judge-result.json' if r['system']=='qwen' else 'result.json')).read_text(),parse_float=str)
        expected=json.loads(r['criterion_scores'])
        normalize=lambda v:{k:Decimal(str(x)) for k,x in v.items()}
        facts=normalize(receipt.get('criterion_scores',{}))==normalize(expected)
        total=score.get('score') is not None and abs(Decimal(score['score'])*100-Decimal(r['focus60_points']))<Decimal('1e-24')
        passed=score.get('pass')==(r['passing60'].lower()=='true')
        checks.append({'case':r['case'],'status':receipt.get('evaluation_status'),'criteria_match':facts,'total_match':total,'pass_match':passed,'match':facts and total and passed,'current_score':score.get('score')})
    result={'selected':len(checks),'matched':sum(x['match'] for x in checks),'checks':checks,'agent_calls':0,'model_api_calls':0}
    (out/'comparison.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'selected':result['selected'],'matched':result['matched']}))
    return 0 if result['matched']==result['selected'] else 1
if __name__=='__main__':raise SystemExit(main())

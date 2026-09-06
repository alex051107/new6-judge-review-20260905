#!/usr/bin/env python3
"""Merge current non-Qwen records with the complete latest Qwen cohort; no Judge calls."""
import argparse,csv,json
from collections import Counter
from decimal import Decimal,localcontext
from fractions import Fraction as F
from pathlib import Path

def text(v):
    if v is None:return None
    with localcontext() as c:
        c.prec=60
        return str(Decimal(v.numerator)/Decimal(v.denominator))
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo-root',type=Path,default=Path(__file__).resolve().parents[2])
    p.add_argument('--output-dir',type=Path,default=Path(__file__).resolve().parent)
    a=p.parse_args();base=a.repo_root/'results'
    with (base/'current-effective-v2/trials.csv').open() as f:old=list(csv.DictReader(f))
    with (base/'qwen-final-20260906/trials.csv').open() as f:new=list(csv.DictReader(f))
    assert len(new)==48 and all(r['system']=='qwen' for r in new)
    fields=list(old[0])+[k for k in new[0] if k not in old[0]]
    rows=[]
    for r in old:
        if r['system']=='qwen':continue
        r={k:r.get(k,'') for k in fields}
        if r['receipt']:r['receipt']='../current-effective-v2/'+r['receipt']
        rows.append(r)
    for r in new:
        r={k:r.get(k,'') for k in fields}
        if r['receipt']:r['receipt']='../qwen-final-20260906/'+r['receipt']
        rows.append(r)
    rows.sort(key=lambda r:(r['task'],r['system'],r['case']))
    assert len(rows)==len({r['case'] for r in rows})==len({r['trial_id'] for r in rows})==144
    for r in rows:
        if r['status']=='SCORED':
            assert r['focus60_points'] and (F(r['focus60_points'])>=70)==(r['passing60'].lower()=='true')
        else:assert not r['focus60_points']
    summary=[];strata=[]
    def summarize(rr,t,s):
        valid=[r for r in rr if r['status']=='SCORED'];v=[F(r['focus60_points']) for r in valid];o=[F(r['original_points']) for r in valid]
        return {'task':t,'display_system':s,'slots':len(rr),'n':len(valid),'unscored':len(rr)-len(valid),'status_counts':dict(Counter(r['status'] for r in rr)),'mean_original_points':text(sum(o)/len(o)) if o else None,'mean_60_points':text(sum(v)/len(v)) if v else None,'passes_60':sum(x>=70 for x in v) if v else None,'pass_at_1':None,'pass_at_8':None,'pass_k_reason':'Model identity/configuration and complete homogeneous Judge population not certified; scoring coverage is not formal difficulty acceptance.'}
    for t in ['A1','A2','B1','B2','C1','C2']:
        for s in ['GPT-5.6 sol','Opus 5','Qwen 3.8']:
            rr=[r for r in rows if r['task']==t and r['display_system']==s];summary.append(summarize(rr,t,s))
            keys={(r['config_id'],r['selected_judge_label'],r['generation_outcome_kind']) for r in rr}
            for cfg,j,g in sorted(keys):
                sr=summarize([r for r in rr if (r['config_id'],r['selected_judge_label'],r['generation_outcome_kind'])==(cfg,j,g)],t,s)
                strata.append({**sr,'config_id':cfg,'selected_judge_label':j,'generation_outcome_kind':g})
    a.output_dir.mkdir(exist_ok=True,parents=True)
    for name,data in [('trials.csv',rows),('summary.csv',summary),('stratified_summary.csv',strata)]:
        with (a.output_dir/name).open('w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows({k:json.dumps(v,ensure_ascii=False) if isinstance(v,dict) else v for k,v in r.items()} for r in data)
    (a.output_dir/'source_records.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
    (a.output_dir/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    report={'slots':144,'scored':sum(r['status']=='SCORED' for r in rows),'non_qwen_scored':sum(r['status']=='SCORED' and r['system']!='qwen' for r in rows),'qwen_scored':sum(r['status']=='SCORED' and r['system']=='qwen' for r in rows),'statuses':dict(Counter(r['status'] for r in rows)),'old_qwen_records_retained':0,'pass_decision':'Unrounded score>=70','unknown_filled_zero':False,'judge_calls':0,'model_calls':0}
    (a.output_dir/'validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()

#!/usr/bin/env python3
import json,csv,math
from collections import defaultdict,Counter
from fractions import Fraction as F
from reweight_receipt import calculate,dec,ROOT

def write(name,rows):
 with (ROOT/name).open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def main():
 records=json.loads((ROOT/'source_records.json').read_text(),parse_float=str);rows=[];weightrows=[]
 weights=json.loads((ROOT/'weights.json').read_text())['tasks']
 for t,s in weights.items():
  ww={k:F(str(v)) for k,v in s['original_weights'].items()};fg=set(s['focus']);n=sum(ww[k] for k in fg)
  for k,w in ww.items():weightrows.append({'task':t,'criterion':k,'group':'focus' if k in fg else 'other','original':dec(w),'weight_50':dec(50*w/(n if k in fg else 100-n)),'weight_60':dec((60 if k in fg else 40)*w/(n if k in fg else 100-n))})
 for r in records:
  a=calculate(r['task'],r,F('.60'));b=calculate(r['task'],r,F('.50'));z={k:v for k,v in r.items() if k!='criterion_scores'};z.update(original=a['original'],score_50=b['score'],score_60=a['score'],pass_50=b['pass'],pass_60=a['pass'],pass_original=F(a['original'])>=F('.70') if a['original'] is not None else None,response_identity='|'.join(r['observed_model_ids']) or 'REQUESTED_ONLY');rows.append(z)
 assert len(rows)==len({r['case'] for r in rows})==len({r['trial_id'] for r in rows})==144
 assert all(r['score_60'] is None for r in rows if r['status']!='SCORED')
 def aggregate(fields,overview=False):
  gs=defaultdict(list)
  for r in rows:gs[tuple(r[k] for k in fields)].append(r)
  out=[]
  for key,rr in sorted(gs.items()):
   valid=[r for r in rr if r['status']=='SCORED'];n=len(valid);o=dict(zip(fields,key));complete=n==len(rr) and all(r['judge_evaluated_this_release'] for r in rr) and len({r['trial_id'] for r in rr})==n
   identity_ok=rr[0]['system']!='qwen';eligible=not overview and complete and identity_ok
   o.update(attempts=len(rr),scored_n=n,unscored_n=len(rr)-n,missing_n=sum(r['status']=='OUTPUT_MISSING' for r in rr),judge_pending_n=sum(r['status']=='JUDGE_ERROR' for r in rr),judge_execution_error_n=sum(r['status']=='JUDGE_EXECUTION_ERROR' for r in rr),run_collection_pending_n=sum(r['status']=='RUN_OR_COLLECTION_PENDING' for r in rr),configuration_count=len({r['config_id'] for r in rr}),scope='DESCRIPTIVE_OVERVIEW_NOT_ACCEPTANCE' if overview else 'CONFIGURATION_RESPONSE_IDENTITY_STRATIFIED')
   for suffix,keyscore in [('original','original'),('50','score_50'),('60','score_60')]:
    wins=sum(bool(r['pass_'+suffix]) for r in valid)
    o['mean_'+suffix]=dec(sum(F(r[keyscore]) for r in valid)/n) if n else None;o['passes_'+suffix]=wins if n else None
    o['descriptive_pass_at_1_'+suffix]=dec(F(wins,n)) if eligible and n else None
    o['descriptive_pass_at_8_'+suffix]=dec(F(1)-F(math.comb(n-wins,8) if n-wins>=8 else 0,math.comb(n,8))) if eligible and n>=8 else None
   o['pass_k_note']='Complete same-configuration observed outcomes; requested model identity may be unverified' if eligible else 'Incomplete or mixed configuration group, or unverified Qwen identity; no estimate'
   o['formal_acceptance_pass_at_1']=None;o['formal_acceptance_pass_at_8']=None;o['formal_acceptance_reason']='Post-result weight exploration; no formal model identity/substitution and difficulty acceptance'
   out.append(o)
  return out
 write('trials.csv',rows);write('weights.csv',weightrows);write('stratified_summary.csv',aggregate(['task','task_version','system','config_id','response_identity']));overview=aggregate(['task','system'],True);write('overview.csv',overview)
 (ROOT/'analysis.json').write_text(json.dumps({'rows':rows,'overview':overview,'statuses':dict(Counter(r['status'] for r in rows))},ensure_ascii=False,indent=2)+'\n')
 (ROOT/'validation.json').write_text(json.dumps({'records':144,'statuses':dict(Counter(r['status'] for r in rows)),'judge_commit':'34374f08f331e7184010c40b401f1630a49df394','original_reconstruction_tolerance':'1e-24','api_calls':0,'agent_calls':0,'judge_calls_by_this_script':0},indent=2)+'\n');print(dict(Counter(r['status'] for r in rows)))
if __name__=='__main__':main()

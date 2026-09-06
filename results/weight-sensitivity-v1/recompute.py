#!/usr/bin/env python3
"""Recompute the frozen 60/40 table with the Python standard library only."""
import argparse,csv,json,math
from pathlib import Path
from collections import defaultdict
from fractions import Fraction as F
from reweight_receipt import calculate,dec,ROOT

def write_csv(path,rows):
 with path.open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-dir',type=Path,default=ROOT/'results');a=p.parse_args();a.output_dir.mkdir(parents=True,exist_ok=True)
 source=json.loads((ROOT/'source_records.json').read_text(),parse_float=str);trials=[];sensitivity=[];groups=defaultdict(list)
 for r in source:
  z=calculate(r['task'],r)
  assert z['original']==r['expected_original'],(r['case'],'original parity')
  assert z['score']==r['expected_score_60'],(r['case'],'60 parity')
  row={k:r[k] for k in ['case','task','task_version','system','trial_id','config_id','requested_model','observed_model_ids','model_identity_status','judge_version','judge_source_commit','answer_sha256','status']}
  row.update(score_60=z['score'],pass_60=z['pass']);trials.append(row)
  groups[(r['task'],r['task_version'],r['system'],r['config_id'],r['observed_model_ids'],r['judge_version'],r['judge_source_commit'])].append(row)
  sensitivity.append({'case':r['case'],'task':r['task'],'system':r['system'],'status':r['status'],'original':z['original'],'score_50':calculate(r['task'],r,F('.50'))['score'],'score_60':z['score'],'score_70':calculate(r['task'],r,F('.70'))['score']})
 summaries=[]
 for key,rr in sorted(groups.items()):
  scored=[r for r in rr if r['status']=='SCORED'];n=len(scored);wins=sum(r['pass_60'] for r in scored)
  # This exact member set is the only audited complete new-Judge configuration group.
  complete=(key[0]=='C1' and key[2]=='codex' and key[3]=='d8e0d8176c6e' and {r['case'] for r in rr}=={f'C1-codex-R{i:02d}' for i in range(1,9)} and n==8 and len({r['trial_id'] for r in rr})==8)
  s=dict(zip(['task','task_version','system','config_id','observed_model_ids','judge_version','judge_source_commit'],key));s.update(attempts_in_subset=len(rr),scored_n=n,pending_n=len(rr)-n,mean_score_60=dec(sum(F(r['score_60']) for r in scored)/n) if n else None,passing_60=wins if n else None,pass_at_1=dec(F(wins,n)) if complete else None,pass_at_8=dec(F(1)-F(math.comb(n-wins,8) if n-wins>=8 else 0,math.comb(n,8))) if complete else None,pass_at_k_note='Audited complete eight-trial configuration; requested model identity recorded' if complete else 'Incomplete or selected configuration subset, or unverified Qwen identity; no estimate')
  summaries.append(s)
 assert len(source)==54 and sum(r['status']=='SCORED' for r in source)==29
 assert sum(r['score_60'] is None for r in trials)==25
 write_csv(a.output_dir/'trials.csv',trials);write_csv(a.output_dir/'task_system_config.csv',summaries);write_csv(ROOT/'sensitivity.csv',sensitivity)
 validation={'records':54,'scored':29,'pending_null':25,'original_and_60_parity':'54/54 exact at recorded 48-digit representation','receipt_original_tolerance':'1e-24','agent_calls':0,'judge_calls':0,'api_calls':0,'default_focus_weight':'0.60'}
 (a.output_dir/'validation.json').write_text(json.dumps(validation,indent=2)+'\n');print(json.dumps(validation))
if __name__=='__main__':main()

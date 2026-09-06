#!/usr/bin/env python3
"""Recompute public factual credits only; no Excel, Judge, network or model calls."""
import argparse,csv,json
from pathlib import Path
from fractions import Fraction as F
from decimal import Decimal,localcontext
from collections import defaultdict
ROOT=Path(__file__).resolve().parent

def decimal(v):
 with localcontext() as c:
  c.prec=48
  return str(Decimal(v.numerator)/Decimal(v.denominator))
def write(path,rows):
 with path.open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-dir',type=Path,default=ROOT/'recomputed');a=p.parse_args()
 source=json.loads((ROOT/'source_records.json').read_text(),parse_float=str);weights=json.loads((ROOT/'weights.json').read_text());rows=[];groups=defaultdict(list)
 assert len(source)==len({r['case'] for r in source})==len({r['trial_id'] for r in source})==144
 for r in source:
  row={k:r[k] for k in ['case','task','display_system','trial_id','config_id','source_priority','selected_judge_label','selected_judge_commit','status']}
  for col in ['original_points','focus50_points','focus60_points','focus70_points','passing_original','passing50','passing60','passing70']:row[col]=None
  if r['status']=='SCORED':
   w={k:F(v) for k,v in weights[r['task']]['original_weights'].items()};fg=set(weights[r['task']]['focus']);f={k:F(str(v)) for k,v in r['criterion_scores'].items()}
   assert sum(w.values())==100 and set(f)==set(w) and fg<set(w) and all(0<=v<=1 for v in f.values())
   n=sum(w[k] for k in fg);fc=sum(w[k]*f[k] for k in fg)/n;bc=sum(w[k]*f[k] for k in w if k not in fg)/(100-n);original=sum(w[k]*f[k] for k in w)/100
   row.update(original_points=decimal(original*100),passing_original=original>=F('.70'))
   for alpha in [50,60,70]:
    s=F(alpha,100)*fc+F(100-alpha,100)*bc;row['focus'+str(alpha)+'_points']=decimal(s*100);row['passing'+str(alpha)]=s>=F('.70')
  for col in ['original_points','focus50_points','focus60_points','focus70_points','passing_original','passing50','passing60','passing70']:
   assert row[col]==r[col],(r['case'],col,'record parity')
  rows.append(row);groups[(r['task'],r['display_system'])].append(row)
 summaries=[]
 for (task,system),rr in sorted(groups.items()):
  valid=[r for r in rr if r['status']=='SCORED'];n=len(valid);s={'task':task,'display_system':system,'slots':len(rr),'n':n,'unscored':len(rr)-n}
  for suffix,col,pk in [('original','original_points','passing_original'),('50','focus50_points','passing50'),('60','focus60_points','passing60'),('70','focus70_points','passing70')]:
   s['mean_'+suffix+'_points']=decimal(sum(F(r[col]) for r in valid)/n) if n else None;s['passes_'+suffix]=sum(bool(r[pk]) for r in valid) if n else None
  summaries.append(s)
 reference={(r['task'],r['display_system']):r for r in csv.DictReader((ROOT/'summary.csv').open())}
 for s in summaries:
  expected=reference[(s['task'],s['display_system'])]
  for k,v in s.items():assert ('' if v is None else str(v))==expected[k],(s['task'],s['display_system'],k,'summary parity')
 a.output_dir.mkdir(parents=True,exist_ok=True);write(a.output_dir/'trials.csv',rows);write(a.output_dir/'summary.csv',summaries)
 validation={'records':144,'scored':sum(r['status']=='SCORED' for r in rows),'unknowns_kept_null':sum(r['status']!='SCORED' for r in rows),'trial_and_summary_parity':'EXACT at recorded 48-digit decimal representation','judge_calls':0,'model_calls':0,'excel_files_read':0}
 (a.output_dir/'validation.json').write_text(json.dumps(validation,indent=2)+'\n');print(json.dumps(validation))
if __name__=='__main__':main()

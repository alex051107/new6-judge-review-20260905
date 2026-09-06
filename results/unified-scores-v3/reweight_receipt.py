#!/usr/bin/env python3
"""Reweight existing factual credits; never evaluate a workbook or call a model."""
import argparse,json
from pathlib import Path
from fractions import Fraction as F
from decimal import Decimal,localcontext
ROOT=Path(__file__).resolve().parent

def dec(v):
 if v is None:return None
 with localcontext() as c:
  c.prec=48
  return str(Decimal(v.numerator)/Decimal(v.denominator))

def calculate(task,receipt,alpha=F('0.60')):
 spec=json.loads((ROOT/'weights.json').read_text())['tasks'][task]
 w={k:F(str(v)) for k,v in spec['original_weights'].items()};focus=set(spec['focus'])
 assert sum(w.values())==100 and focus < set(w)
 if not F(0)<=alpha<=F(1):raise ValueError('alpha must be between 0 and 1')
 status=receipt.get('evaluation_status',receipt.get('status'))
 out={'task':task,'task_version':spec['task_version'],'status':status,'alpha':dec(alpha),'source_score_decimal':receipt.get('score_decimal',receipt.get('source_score_decimal')),'original':None,'score':None,'pass':None,'focus_credit':None,'other_credit':None}
 if status!='SCORED':return out
 facts=receipt.get('criterion_scores')
 if not isinstance(facts,dict) or set(facts)!=set(w):raise ValueError('Complete frozen criterion facts required')
 f={k:F(str(v)) for k,v in facts.items()}
 if not all(0<=v<=1 for v in f.values()):raise ValueError('Credit outside [0,1]')
 fw=sum(w[k] for k in focus)
 fc=sum(w[k]*f[k] for k in focus)/fw;bc=sum(w[k]*f[k] for k in w if k not in focus)/(100-fw)
 original=sum(w[k]*f[k] for k in w)/100;s=alpha*fc+(1-alpha)*bc
 if out['source_score_decimal'] is not None and abs(original-F(str(out['source_score_decimal'])))>=F('1e-24'):raise ValueError('Receipt does not match frozen original weights')
 out.update(original=dec(original),score=dec(s),**{'pass':s>=F('0.70')},focus_credit=dec(fc),other_credit=dec(bc))
 return out

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--task',required=True);p.add_argument('--receipt',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--alpha',default='0.60');a=p.parse_args()
 r=json.loads(a.receipt.read_text(),parse_float=str)
 if isinstance(r,list):raise ValueError('Supply one existing Judge JSON receipt, not the record list')
 result=calculate(a.task,r,F(a.alpha));a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()

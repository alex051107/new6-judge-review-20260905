"""Replay only revised R002/R006 from existing native evidence; no engine/API calls."""
from pathlib import Path
from decimal import Decimal
import json,sys,openpyxl
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'metadata'),str(ROOT/'tests')]
import evaluate as e
def main():
 cases=json.loads((ROOT/'fixtures/manifest.json').read_text())['cases'];den=json.loads((ROOT/'tests/fact_contract.json').read_text())['denominators'];out=ROOT/'validation/final';out.mkdir(exist_ok=True);rows=[]
 for c in cases:
  prior=ROOT/('validation/reference_final/evaluation.json' if c['name']=='reference' else 'validation/calibration/'+c['name']+'/evaluation.json')
  x=json.loads(prior.read_text())
  if x['evaluation_status']=='SCORED' and x['evidence']['denominators']['R002']!=den['R002']:
   w=openpyxl.load_workbook(x['evidence']['base_native_receipt']['output'],data_only=True);fresh,_,_=e.checks(w)
   old_option=[u for u in x['evidence']['fact_units']['R002'] if u['id']=='option_price_change_does_not_approve_scope'];assert len(old_option)==1
   x['evidence']['fact_units']['R002']=fresh['R002']+old_option;x['evidence']['fact_units']['R006']=fresh['R006']
   x['evidence']['denominators']={k:len(v) for k,v in x['evidence']['fact_units'].items()};assert x['evidence']['denominators']==den
   x['evidence']['version_fact_replay']={'scope':['R002','R006'],'reason':'Obsolete quote disclosure is optional; displayed obsolete claims remain checked.','native_recalculations':0,'prior_evaluation':str(prior.relative_to(ROOT))}
   scores={k:str(Decimal(sum(v['ok'] for v in u))/Decimal(len(u))) for k,u in x['evidence']['fact_units'].items()}
   x=e.score_profiles(ROOT/'rubric.json',scores,evidence=x['evidence'])
  scores=x.get('criterion_scores',{});checks=[x['evaluation_status']==c['status']]
  if c['status']=='SCORED':
   checks += [Decimal(scores[k])<1 for k in c['lose']]+[Decimal(scores[k])==1 for k in c['preserve']]+[x['evidence']['denominators']==den]
  dest=out/c['name'];dest.mkdir(exist_ok=True);(dest/'evaluation.json').write_text(json.dumps(x,indent=2,default=str))
  row={'name':c['name'],'status':x['evaluation_status'],'score':x.get('score_decimal'),'facts':scores,'expected':c,'passed':all(checks)};rows.append(row)
  assert all(checks),row
 receipt={'status':'PASS','cases':len(rows),'results':rows,'fixed_denominators':den,'native_recalculations_in_this_replay':0,'api_calls':0,'reference_oracle':'validation/reference_oracle/receipt.json','actual_agent_samples':0}
 (out/'receipt.json').write_text(json.dumps(receipt,indent=2));print(json.dumps({'status':'PASS','cases':len(rows),'denominators':den,'api_calls':0}))
if __name__=='__main__':main()

"""Independent Decimal chain from verified source facts; never XLSX caches."""
from decimal import Decimal,getcontext
from pathlib import Path
import json
getcontext().prec=40
ROOT=Path(__file__).resolve().parent
D=lambda x:Decimal(str(x))
def source():return json.loads((ROOT/'source_facts.json').read_text())
def compute(changes=None):
 c=changes or {};s=source();elements={r['id']:D(r['amount'] or 0) for r in s['elements']};elements.update({k:D(v) for k,v in c.items() if k in elements})
 rates={'overheads':D(c.get('overheads_rate','.10')),'design_risk':D(c.get('design_risk_rate','.10')),'inflation':D(c.get('inflation_rate','.01'))}
 w={'building':sum(elements.values()),'preliminaries':D(c.get('preliminaries','182800'))}
 w['overheads']=(w['building']+w['preliminaries'])*rates['overheads'];w['building_estimate']=w['building']+w['preliminaries']+w['overheads'];w['base']=w['building_estimate'];w['design_risk']=w['base']*rates['design_risk'];w['inflation_excluded']=w['base']+w['design_risk'];w['inflation']=w['inflation_excluded']*rates['inflation'];w['vat_excluded']=w['inflation_excluded']+w['inflation']
 printed={r['id']:D(r['amount']) for r in s['summary'] if isinstance(r['amount'],(int,float))}
 return dict(elements=elements,working=w,rates=rates,reconciliation={k:v-printed[k] for k,v in w.items()})
def serial(x):
 if isinstance(x,Decimal):return str(x)
 if isinstance(x,dict):return {k:serial(v) for k,v in x.items()}
 return x
if __name__=='__main__':print(json.dumps(serial(compute()),indent=2))

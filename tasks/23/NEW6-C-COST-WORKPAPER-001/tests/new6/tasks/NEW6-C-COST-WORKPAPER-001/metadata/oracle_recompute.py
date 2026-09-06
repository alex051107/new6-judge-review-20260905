"""Independent Decimal review position; never reads a candidate workbook/cache."""
from decimal import Decimal,getcontext
import json
from pathlib import Path
getcontext().prec=40
ROOT=Path(__file__).resolve().parent
D=lambda v:Decimal(str(v))
def source():return json.loads((ROOT/'source_facts.json').read_text())
def compute(changes=None):
 c=changes or {};s=source();elements={r['id']:D(r['amount'] or 0) for r in s['elements']}
 original_heating=D(next(r['amount'] for r in s['provisional'] if r['id']=='heating'))
 heating=D(c.get('heating_price',458000));option=D(c.get('asbestos_option',18000))
 elements['services']=elements['services']-original_heating+heating
 rates={'overheads':D(c.get('overheads_rate','.10')),'design_risk':D(c.get('design_risk_rate','.12')),'inflation':D(c.get('inflation_rate','.01'))}
 w={'building':sum(elements.values()),'preliminaries':D(182800)}
 w['overheads']=(w['building']+w['preliminaries'])*rates['overheads']
 w['building_estimate']=w['building']+w['preliminaries']+w['overheads'];w['base']=w['building_estimate']
 w['design_risk']=w['base']*rates['design_risk'];w['inflation_excluded']=w['base']+w['design_risk']
 w['inflation']=w['inflation_excluded']*rates['inflation'];w['vat_excluded']=w['inflation_excluded']+w['inflation']
 printed={r['id']:D(r['amount']) for r in s['summary'] if isinstance(r['amount'],(int,float))}
 # Independent multiplicative identity checks the staged total, not a copied cache.
 closed_form=(sum(D(r['amount'] or 0) for r in s['elements'])-original_heating+heating+D(182800))*(1+rates['overheads'])*(1+rates['design_risk'])*(1+rates['inflation'])
 assert closed_form==w['vat_excluded']
 return {'elements':elements,'working':w,'rates':rates,'reconciliation':{k:v-printed[k] for k,v in w.items()},'current_heating':heating,'earlier_heating':D(472000),'original_heating':original_heating,'asbestos_option':option,'option_in_current_total':False}
def serial(v):
 if isinstance(v,Decimal):return str(v)
 if isinstance(v,dict):return {k:serial(x) for k,x in v.items()}
 if isinstance(v,list):return [serial(x) for x in v]
 return v
if __name__=='__main__':print(json.dumps(serial(compute()),indent=2))

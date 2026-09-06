"""One disclosed historical input breaks the source-only rating/lease cycle."""
from pathlib import Path
from decimal import Decimal as D,ROUND_HALF_UP
import json
from oracle_recompute import raw_inputs,compute,jsonable
from ooxml_edit import edit
ROOT=Path(__file__).resolve().parents[1]
DERIVED=ROOT/'metadata/source/AmazonSept18_historical_rate_fixed.xlsx'

def prepare():
 p=raw_inputs();leases=p['leases'];years=int((leases[5]/(sum(leases[:5])/5)).quantize(D(1),rounding=ROUND_HALF_UP));trials=[]
 for lower,spread in p['bands']:
  rate=p['riskfree']+spread
  debt=sum(v/(1+rate)**(i+1) for i,v in enumerate(leases[:5]))+(leases[5]/years)*(1-(1+rate)**(-years))/rate/(1+rate)**5
  adjustment=p['lease_expense']-debt/D(5+years)
  coverage=(p['ebit']+adjustment)/(p['interest']+debt*rate)
  selected=max(b for b in p['bands'] if b[0]<=coverage)
  trials.append(dict(rating_lower_bound=lower,spread=spread,rate=rate,lease_debt=debt,lease_ebit_adjustment=adjustment,coverage=coverage,selected_lower_bound=selected[0],self_consistent=selected==(lower,spread)))
 valid=[r for r in trials if r['self_consistent']];assert len(valid)==1
 fixed=valid[0]['rate'];assert fixed==compute()['source_adjustments']['lease_rate']
 note={'A1':'Historical financing basis','A3':'This reconstruction fixes the historical lease financing rate at the unique self-consistent rating/lease solution from the original September 2018 model.','A5':'Historical pre-tax lease financing rate','B5':float(fixed),'A7':'The original lease commitments, rating bands, lease present-value formulas and operating-earnings adjustments remain available in their source worksheets.','A9':'This rate is a fixed historical input for the growth, operating-margin and discount-rate review. Future forecast, cash-flow and valuation outputs remain calculation work.','A11':'Source: Aswath Damodaran, AmazonSept18.xlsx, September 2018. Project construction adjustment; the untouched original is retained separately.'}
 edit(ROOT/'metadata/source/AmazonSept18.xlsx',DERIVED,patches={'Operating lease converter':{'C15':float(fixed)}},new_sheets={'Historical financing basis':note},clear_caches=True)
 receipt={'status':'DERIVED_INPUT_DISCLOSED','source':'metadata/source/AmazonSept18.xlsx','derived':str(DERIVED.relative_to(ROOT)),'original_source_untouched':True,'changes':[{'sheet':'Operating lease converter','cell':'C15','original_formula':"='Cost of capital worksheet'!B23",'replacement':fixed,'meaning':'Historical pretax lease financing rate, independently solved from original inputs; not a cached derived forecast'}],'raw_basis':p,'tail_lease_years':years,'rating_band_trials':trials,'unique_solution':valid[0],'scope':'Only future growth, operating-margin target and cost-of-capital assumptions are declared mutable; historical lease financing basis remains fixed.'}
 (ROOT/'metadata/historical_rate_basis.json').write_text(json.dumps(jsonable(receipt),indent=2,default=str));return DERIVED
if __name__=='__main__':print(prepare())

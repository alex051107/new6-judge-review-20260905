"""Independent lookup over a separately verified PRIVATE rate table.
Does not extract PDF facts, construct an XLSX or grade a workbook.
rate JSON rows: service ('priority'/'ground'), zone (1..8), upper_oz, usd.
"""
import csv,json,argparse
from decimal import Decimal as D
from pathlib import Path

def quote(rows,service,weight,unit,zone):
    oz=D(str(weight))*(D(16) if unit=='lb' else D(1) if unit=='oz' else D('NaN'))
    if not oz.is_finite() or not D(0)<oz<=D(160) or not 1<=int(zone)<=8:
        raise ValueError('Outside declared scope')
    valid=sorted((r for r in rows if r['service']==service and int(r['zone'])==int(zone)),key=lambda r:D(str(r['upper_oz'])))
    eligible=[r for r in valid if oz<=D(str(r['upper_oz']))]
    if not eligible:raise ValueError('Required rate missing')
    return D(str(eligible[0]['usd']))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--rates',required=True);p.add_argument('--requests',required=True);a=p.parse_args()
    rates=json.loads(Path(a.rates).read_text());out=[];total=D(0)
    for r in csv.DictReader(Path(a.requests).open()):
        x=quote(rates,'priority',r['weight'],r['weight_unit'],r['zone']);y=quote(rates,'ground',r['weight'],r['weight_unit'],r['zone'])
        choice='ground' if y<=x else 'priority';value=min(x,y);total+=value
        out.append({'id':r['request_id'],'priority':str(x),'ground':str(y),'selected':choice,'selected_usd':str(value)})
    print(json.dumps({'quotes':out,'batch_total':str(total)},indent=2))

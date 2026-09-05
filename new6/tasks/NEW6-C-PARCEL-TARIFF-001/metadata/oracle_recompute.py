"""Private USPS source oracle. Exact Decimal upper-band scan; no candidate input.

Structure verified separately against the official XLSX and rendered PDF pages.
The extraction stage uses PDF text lines; XLSX is an independent second representation.
"""
from pathlib import Path
from decimal import Decimal as D
import csv, json, argparse

ROOT = Path(__file__).resolve().parents[1]

def quote(rates, weight, unit, zone):
    if unit not in ('oz', 'lb') or str(zone) not in tuple(map(str, range(1, 9))):
        return {'status': 'out_of_scope'}
    oz = D(str(weight)) * (16 if unit == 'lb' else 1)
    if not oz.is_finite() or not 0 < oz <= 160:
        return {'status': 'out_of_scope'}
    out = {'status': 'in_scope'}
    for service in ('priority', 'ground'):
        eligible = [r for r in rates if r['service'] == service and int(r['zone']) == int(zone) and D(r['upper_oz']) >= oz]
        row = min(eligible, key=lambda r: D(r['upper_oz']))
        out[service] = row['usd']
        out[service + '_band'] = (row['upper_bound'], row['weight_unit'])
    out['selected'] = 'ground' if D(out['ground']) <= D(out['priority']) else 'priority'
    out['selected_usd'] = out[out['selected']]
    return out

def compute(rates, requests):
    results = [{'request_id': r['request_id'], **quote(rates, r['weight'], r['weight_unit'], str(r['zone']))} for r in requests]
    return {'quotes': results, 'batch_total': str(sum((D(q['selected_usd']) for q in results if q['status'] == 'in_scope'), D(0)))}

def main():
    p=argparse.ArgumentParser();p.add_argument('--rates',type=Path,default=ROOT/'metadata/rates.json');p.add_argument('--requests',type=Path,default=ROOT/'data/input_files/quote_requests.csv');p.add_argument('--out',type=Path);a=p.parse_args()
    value=compute(json.loads(a.rates.read_text()),list(csv.DictReader(a.requests.open())))
    text=json.dumps(value,indent=2)
    if a.out:a.out.write_text(text)
    else:print(text)
if __name__=='__main__':main()

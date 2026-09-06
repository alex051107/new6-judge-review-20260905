#!/usr/bin/env python3
"""Compare freshly read criterion credits to the now-validated expected receipts."""
import argparse,json
from decimal import Decimal
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',required=True,type=Path);a=p.parse_args();root=Path(__file__).resolve().parent;rows=[]
for c in json.loads((a.out/'selected.json').read_text()):
 case=c['case'];fresh=a.out/'runs'/case/'result.json';expected=root/'expected-receipts'/case/'result.json'
 if not fresh.exists():rows.append({'case':case,'match':False,'reason':'missing new receipt'});continue
 f=json.loads(fresh.read_text());e=json.loads(expected.read_text());norm=lambda d:{k:Decimal(str(v))for k,v in (d or {}).items()}
 rows.append({'case':case,'status':f['evaluation_status'],'match':f['evaluation_status']==e['evaluation_status'] and norm(f.get('criterion_scores'))==norm(e.get('criterion_scores')),'criterion_scores':f.get('criterion_scores')})
r={'results':rows,'matched':sum(x['match']for x in rows),'total':len(rows)};(a.out/'comparison.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2));raise SystemExit(0 if all(x['match'] for x in rows) else 1)

"""One reader check set: matrix equivalence, isolated price error, duplication, unknown scope."""
import copy,json
from collections import Counter,defaultdict
from openpyxl import Workbook
from evaluate import ROOT,parse,rkey,dec,source_facts,ParsePending

out=ROOT/'metadata/wide_layout_repair';out.mkdir(exist_ok=True)
original=parse(ROOT/'solution/reference.xlsx')
wb=Workbook();wb.remove(wb.active)
groups=defaultdict(list)
for row in original['rates']:groups[row['service']].append(row)
for svc,rows in groups.items():
    sh=wb.create_sheet(svc)
    sh.append(['Reconstructed published prices'])
    sh.append(['Priority Mail Retail' if svc=='priority' else 'USPS Ground Advantage Retail'])
    sh.append(['Source: Notice 123 - Effective July 12, 2026'])
    sh.append([None,'Weight']+[f'Zone {z}' for z in reversed(range(1,9))])
    lookup={(dec(r['upper_bound']),r['weight_unit'],int(r['zone'])):r['usd'] for r in rows}
    for band,u in sorted({(dec(r['upper_bound']),r['weight_unit']) for r in rows}):
        sh.append([None,f'{band} {u}']+[float(lookup[band,u,z]) for z in reversed(range(1,9))])
path=out/'equivalent_wide.xlsx';wb.save(path)
good=parse(path)
expected=Counter((rkey(r),dec(r['usd'])) for r in original['rates'])
assert Counter((rkey(r),dec(r['usd'])) for r in good['rates'])==expected
bands={(r['service'],dec(r['upper_bound']),r['weight_unit']) for r in original['rates']}
facts={'R006':[]};source_facts(good,bands,facts)
assert all(r['correct'] for r in facts['R006'] if r['fact'].startswith('source_trace '))
wb['priority']['C5']=float(wb['priority']['C5'].value)+1
bad=out/'single_price.xlsx';wb.save(bad);changed=parse(bad)
observed=Counter((rkey(r),dec(r['usd'])) for r in changed['rates'])
assert sum((expected-observed).values())==1 and sum((observed-expected).values())==1
assert Counter(rkey(r) for r in changed['rates'])==Counter(rkey(r) for r in good['rates'])
wb['priority']['C5']=float(wb['priority']['C5'].value)-1
wb['priority'].append([c.value for c in wb['priority'][5]])
duplicate=out/'duplicate_band.xlsx';wb.save(duplicate);dups=parse(duplicate)
counts=Counter(rkey(r) for r in dups['rates'])
assert sum(n-1 for n in counts.values())==8
wb['priority']['A2']='Unidentified service'
unknown=out/'unknown_service.xlsx';wb.save(unknown)
try:parse(unknown)
except ParsePending:pass
else:raise AssertionError('Unknown service must remain pending')
receipt={'passed':True,'baseline_native_runs':0,'agent_calls':0,'expected_price_facts':192,'equivalent_matrix':'all rate identities and prices retained with reversed zone columns and moved weight column','single_price_error':'exactly one price differs; identities all retained','duplicate_band':'eight duplicate rate identities remain visible to multiset checks','unknown_service':'pending, not zero','source_binding':'candidate-labelled service, Retail weight/zone table and Notice123 source; no Oracle values used to locate tables'}
(out/'receipt.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt))

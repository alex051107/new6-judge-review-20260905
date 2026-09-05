"""Version 2 bridge facts. Candidate layout discovered by semantic evidence only."""
from collections import defaultdict,Counter
from decimal import Decimal
from pathlib import Path
import json,csv,re
from read_candidate import norm,num,eq,mean,population,ParsePending

COMPONENTS={
 'September net recorded value':['septembernetrecordedvalue','septembernet','sepnet','openingnet'],
 'Continuing SKU quantity effect':['continuingskuquantityeffect','continuingquantityeffect','quantityeffect','volumeeffect','quantitycontribution','continuingskuquantitycontribution','continuingskuquantityeffect'],
 'Continuing SKU price and mix effect':['continuingskupriceandmixeffect','priceandmixeffect','pricemixeffect','priceeffect','priceandmixcontribution','continuingskupricemixcontribution','continuingskupricemixeffect'],
 'New SKU effect':['newskueffect','newskucontribution','newproducts','newskus'],
 'Exited SKU effect':['exitedskueffect','exitedskucontribution','exiteffect','exitedskus'],
 'Signed credit change':['signedcreditchange','creditchange','changeincredits','creditschange'],
 'October net recorded value':['octobernetrecordedvalue','octobernet','octnet','closingnet'],
 'Net recorded value change':['netrecordedvaluechange','netchange','totalchange','changeinnetrecordedvalue'],
 'Bridge residual':['bridgeresidual','reconciliationdifference','residual','bridgedifference']}
LOOKUP={n:k for k,v in COMPONENTS.items() for n in v}
def component(v):
    n=norm(v)
    return LOOKUP.get(n,LOOKUP.get(n.removesuffix('gbp'),str(v)))

def bridge_facts(task,ts,text,input_dir):
    truth=json.loads((task/'solution/bridge_oracle.json').read_text())
    if not ts['bridge'] and any(x.startswith('__UNBOUND__') and re.search(r'bridge|effect|contribution',x,re.I) and re.search(r'\d',x) for x in text):
        raise ParsePending('A numerical bridge may be present in an unsupported layout; bind it before scoring.')
    if not ts['sku'] and any(x.startswith('__UNBOUND__') and re.search(r'sku|stockcode',x,re.I) for x in text):
        raise ParsePending('A SKU schedule may be present in an unsupported layout; bind it before scoring.')
    rows=[r for t in ts['bridge'] for r in t['rows'] if r.get('component')]
    b=defaultdict(list)
    for r in rows:b[component(r['component'])].append(r)
    units=[]
    for label,val in truth['bridge']:
        units.append(bool(b[label]) and all(eq(r.get('bridge_amount'),val,Decimal('.005')) for r in b[label]))
    relevant=[k for k in COMPONENTS if k not in ['Net recorded value change','Bridge residual']]
    self_close=[]
    if all(len(b[k])==1 and num(b[k][0].get('bridge_amount')) is not None for k in relevant):
        vals={k:num(b[k][0]['bridge_amount']) for k in relevant}
        effects=sum(v for k,v in vals.items() if k not in ['September net recorded value','October net recorded value'])
        self_close.append(abs(vals['September net recorded value']+effects-vals['October net recorded value'])<=Decimal('.04'))
    else:self_close.append(False)
    skurows=[r for t in ts['sku'] for r in t['rows'] if r.get('stock') is not None]
    sb=defaultdict(list)
    for r in skurows:sb[str(r['stock'])].append(r)
    skuchecks=[];bad=[]
    cols=['q_sep','q_oct','v_sep','v_oct','p_sep','p_oct','qty_effect','price_effect','entry_effect','exit_effect']
    cohorts={'continuing':{'continuing','retained','existing','both'},'new':{'new','newsku','entered','entry'},'exited':{'exited','exit','lost','discontinued'}}
    for ex in truth['sku_schedule']:
        cand=sb[ex[0]];these=[]
        these.append(bool(cand) and all(norm(r.get('cohort')) in cohorts[ex[1]] for r in cand))
        for j,key in enumerate(cols,2):
            if key in ['p_sep','p_oct']:continue
            wanted=ex[j]
            def check(r):
                got=r.get(key)
                if key.endswith('effect') and Decimal(wanted)==0 and got in [None,'']:return True
                inactive=(key in ['q_sep','v_sep'] and norm(r.get('cohort')) in cohorts['new']) or (key in ['q_oct','v_oct'] and norm(r.get('cohort')) in cohorts['exited'])
                if inactive and Decimal(wanted)==0 and got in [None,'']:return True
                return eq(got,wanted,Decimal('0') if key in ['q_sep','q_oct'] else Decimal('.005'))
            these.append(bool(cand) and all(check(r) for r in cand))
        skuchecks.extend(these)
        if not all(these) and len(bad)<12:bad.append(ex[0])
    expected_file=task/'metadata/v2_preparation/september_extract_private.csv'
    actual_file=Path(input_dir)/'september_extract.csv'
    try:
        def source_rows(p):
            with p.open(encoding='utf-8-sig',newline='') as f:data=list(csv.DictReader(f))
            fields=['source_row_id','InvoiceNo','StockCode','Description','Quantity','InvoiceDate','UnitPrice','CustomerID','Country']
            if any(not set(fields)<=set(r) for r in data):raise ValueError('source columns cannot be bound')
            return Counter(tuple(str(num(r[k]).normalize()) if k in ['Quantity','UnitPrice'] and num(r[k]) is not None else str(r[k] or '').replace('T',' ') if k=='InvoiceDate' else str(r[k] or '') for k in fields) for r in data)
        protected=actual_file.exists() and source_rows(actual_file)==source_rows(expected_file)
    except Exception as exc:raise ParsePending('September source preservation requires a supported reader: '+str(exc))
    r7=mean([mean(units),mean(self_close)])
    r8=mean([mean(skuchecks),population([str(r['stock']) for r in skurows],[r[0] for r in truth['sku_schedule']]),protected])
    return {'R007':r7,'R008':r8},{'version':truth['task_version'],'bridge_fact_count':len(units),'bridge_fact_results':dict(zip([r[0] for r in truth['bridge']],units)),
      'candidate_bridge_closure':self_close,'sku_count':truth['sku_count'],'sku_fact_count':len(skuchecks),'sku_mismatches':bad,'september_source_retained':protected,
      'equivalence':'Static/formula values and layouts receive the same facts; weighted prices may be recovered from sales quantities/values; blank non-applicable effects equal zero.',
      'parser_boundary':'Unbound plausible bridge/SKU evidence yields JUDGE_ERROR; no score from guessed coordinates.',
      'interpretation_boundary':'No keyword or prose-length points. Descriptive-versus-causal wording requires review when material; numeric facts do not prove causal claims.'}

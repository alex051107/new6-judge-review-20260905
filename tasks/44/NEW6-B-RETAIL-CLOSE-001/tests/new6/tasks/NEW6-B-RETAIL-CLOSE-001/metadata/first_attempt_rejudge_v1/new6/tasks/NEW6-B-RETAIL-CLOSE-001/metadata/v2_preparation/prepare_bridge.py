"""Version 2 source-derived arithmetic bridge. No candidate or evaluator reads.

Forward rational arithmetic is independently checked against reverse source-row
Decimal monthly aggregates and a distinct residual-form effect calculation.
"""
from pathlib import Path
from collections import defaultdict, Counter
from fractions import Fraction as F
from decimal import Decimal, localcontext
from datetime import datetime
import csv, json
import openpyxl

HERE=Path(__file__).resolve().parent;TASK=HERE.parents[1]
HEADERS=['source_row_id','InvoiceNo','StockCode','Description','Quantity','InvoiceDate','UnitPrice','CustomerID','Country']
SOURCE=TASK.parents[1]/'sources/downloads_b/retail_original/Online Retail.xlsx'

def txt(v):
    if v is None:return ''
    if isinstance(v,float) and v.is_integer():return str(int(v))
    return str(v)

def value(v):
    with localcontext() as c:
        c.prec=42
        return str(Decimal(v.numerator)/Decimal(v.denominator))

def run():
    sep=[];wb=openpyxl.load_workbook(SOURCE,read_only=True,data_only=True)
    for sh in wb:
        for n,row in enumerate(sh.iter_rows(min_row=2,values_only=True),2):
            if datetime(2011,9,1)<=row[4]<datetime(2011,10,1):
                sep.append(dict(zip(HEADERS,[f'{sh.title}:{n}',*[v.isoformat(sep=' ') if isinstance(v,datetime) else txt(v) for v in row]])))
    wb.close()
    with (TASK/'data/input_files/retail_extract.csv').open(newline='') as fh:
        octrows=[r for r in csv.DictReader(fh) if r['InvoiceDate']>='2011-10-01' and r['InvoiceDate']<'2011-11-01']
    by=defaultdict(lambda:[F(0),F(0)]);classes=defaultdict(lambda:[0,F(0)]);monthids={}
    for month,rows in [('Sep',sep),('Oct',octrows)]:
        monthids[month]=[r['source_row_id'] for r in rows]
        for r in rows:
            q,p=F(r['Quantity']),F(r['UnitPrice']);amount=q*p
            valid=all(r[k] for k in HEADERS[1:] if k!='CustomerID')
            c=r['InvoiceNo'].upper().startswith('C')
            kind='sale' if valid and q>0 and p>0 and not c else 'credit' if valid and q<0 and p>0 and c else 'exception'
            classes[(month,kind)][0]+=1;classes[(month,kind)][1]+=amount
            if kind=='sale':by[(month,r['StockCode'])][0]+=q;by[(month,r['StockCode'])][1]+=amount
    skus=sorted({s for m,s in by});schedule=[];effects=defaultdict(F);cohorts=Counter()
    for s in skus:
        q0,v0=by[('Sep',s)];q1,v1=by[('Oct',s)];p0=v0/q0 if q0 else None;p1=v1/q1 if q1 else None
        cohort='continuing' if q0 and q1 else 'new' if q1 else 'exited';cohorts[cohort]+=1
        volume=(q1-q0)*p0 if cohort=='continuing' else F(0)
        price=q1*(p1-p0) if cohort=='continuing' else F(0)
        new=v1 if cohort=='new' else F(0);exited=-v0 if cohort=='exited' else F(0)
        assert volume+price+new+exited==v1-v0
        # Independent residual-form calculation: revalue current volume at base price.
        if cohort=='continuing':
            assert volume==(q1*v0/q0)-v0
            assert price==v1-(q1*v0/q0)
        for k,v in [('Continuing SKU quantity effect',volume),('Continuing SKU price and mix effect',price),('New SKU effect',new),('Exited SKU effect',exited)]:effects[k]+=v
        schedule.append([s,cohort,*[value(v) if v is not None else None for v in [q0,q1,v0,v1,p0,p1,volume,price,new,exited]]])
    # Independent Decimal totals and SKU quantities, with separate policy expression.
    reverse=defaultdict(lambda:[0,Decimal(0)]);rb=defaultdict(lambda:[Decimal(0),Decimal(0)])
    for r in reversed(sep+octrows):
        m='Sep' if r['InvoiceDate'][5:7]=='09' else 'Oct';q=Decimal(r['Quantity']);p=Decimal(r['UnitPrice']);v=q*p
        complete=all(r[k]!='' for k in ['InvoiceNo','StockCode','Description','Quantity','InvoiceDate','UnitPrice','Country'])
        status='exception'
        if complete and p>0:
            if r['InvoiceNo'][:1].lower()=='c' and q<0:status='credit'
            if r['InvoiceNo'][:1].lower()!='c' and q>0:status='sale'
        reverse[(m,status)][0]+=1;reverse[(m,status)][1]+=v
        if status=='sale':rb[(m,r['StockCode'])][0]+=q;rb[(m,r['StockCode'])][1]+=v
    assert all(reverse[k][0]==v[0] and F(reverse[k][1])==v[1] for k,v in classes.items())
    assert all(F(rb[k][0])==v[0] and F(rb[k][1])==v[1] for k,v in by.items())
    sepnet=classes[('Sep','sale')][1]+classes[('Sep','credit')][1]
    octnet=classes[('Oct','sale')][1]+classes[('Oct','credit')][1]
    effects['Signed credit change']=classes[('Oct','credit')][1]-classes[('Sep','credit')][1]
    assert sum(effects.values())==octnet-sepnet
    bridge=[['September net recorded value',sepnet],*effects.items(),['October net recorded value',octnet],['Net recorded value change',octnet-sepnet],['Bridge residual',F(0)]]
    result={'task_version':'new6-b1-v2','source':'UCI Online Retail, complete September and October 2011 physical occurrences',
      'september_occurrences':len(sep),'october_occurrences':len(octrows),'sku_count':len(skus),'cohort_counts':dict(cohorts),
      'policy':'Ordinary sales only define SKU membership, quantity and weighted unit price; credits bridge separately; exception amounts excluded from both net endpoints.',
      'monthly_totals':[[*k,v[0],value(v[1])] for k,v in sorted(classes.items())],
      'sku_headers':['StockCode','Cohort','Sep sales quantity','Oct sales quantity','Sep sales value GBP','Oct sales value GBP','Sep weighted unit price','Oct weighted unit price','Quantity effect GBP','Price and mix effect GBP','New SKU effect GBP','Exited SKU effect GBP'],
      'sku_schedule':schedule,'bridge_headers':['Component','Bridge amount GBP'],'bridge':[[k,value(v)] for k,v in bridge],
      'verification':'All SKU identities close exactly as rational numbers; forward rational source totals match independent reversed Decimal classification/aggregation; full bridge residual is exactly zero.',
      'interpretation':'Descriptive arithmetic decomposition. Weighted price changes also reflect within-SKU transaction mix and do not establish causal price effects.'}
    (HERE/'bridge_oracle.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    with (HERE/'september_extract_private.csv').open('w',newline='') as fh:
        w=csv.DictWriter(fh,fieldnames=HEADERS);w.writeheader();w.writerows(sep)
    print(json.dumps({k:v for k,v in result.items() if k not in ['sku_schedule','sku_headers']},indent=2))

if __name__=='__main__':run()

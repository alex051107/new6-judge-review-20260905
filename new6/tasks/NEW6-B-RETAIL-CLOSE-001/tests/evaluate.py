"""Source-bounded static-or-formula monthly close evaluator.

Fixed occurrence facts, document/country groups and numerical reporting evidence
are assessed separately. All profiles consume exactly the same fact vector.
"""
from pathlib import Path
from collections import defaultdict,Counter
from decimal import Decimal
import sys,json,hashlib,argparse,re,csv
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'common'))
from runtime import score_profiles,output_status
from read_candidate import tables,charts,ParsePending,norm,num,eq,population,consensus_rows,mean,visible_numbers
from evaluate_bridge import bridge_facts
TASK=Path(__file__).resolve().parents[1]
SPECS={'records':{'rowid','class','amount'},
 'invoices':{'invoice','class','count','amount'},'countries':{'country','class','count','amount'},
 'queue':{'rowid','reason'},'totals':{'class','count','amount'},'report':{'metric','value'},'countries_wide':{'country','sale_amount','credit_amount','exception_amount','sale_count','credit_count','exception_count'},'reconciliation':{'description','count','amount'},'bridge':{'component','bridge_amount'},'sku':{'stock','q_sep','q_oct'},'invoices_wide':{'invoice','sale_amount','credit_amount','exception_amount','sale_count','credit_count','exception_count'},'countries_amounts':{'country','sale_amount','credit_amount','exception_amount','count'},'period_report':{'metric','oct_report','sep_report'}}
def kind(v):
    n=norm(v)
    if n in ['sale','sales','ordinarysale','ordinarysales']:return 'sale'
    if n in ['credit','credits','cancellation','creditcancellation','cancellationcredit']:return 'credit'
    if n in ['outside','outofscope','outsidescope','periodoutside','outsideperiod']:return 'outside_scope'
    if n in ['exception','exceptions','businessexception']:return 'exception'
    return str(v)
def truth_bool(v):return norm(v) in ['true','yes','1','missing'] or v is True

def evaluate(path,input_dir=None):
    evidence={'candidate':str(path),'dynamic_tests':'not applicable; correct static accepted',
      'reader':'semantic headers and occurrence IDs, no private candidate coordinates or inferred credit links'}
    status=output_status(path)
    if status:return score_profiles(TASK/'rubric.json',status=status,evidence=evidence)
    if input_dir is None:
        evidence['reason']='Post-run input directory required for source-preservation evidence.'
        return score_profiles(TASK/'rubric.json',status='JUDGE_ERROR',evidence=evidence)
    try:ts,text=tables(path,SPECS);chs=charts(path)
    except ParsePending as exc:
        evidence['reason']=str(exc);return score_profiles(TASK/'rubric.json',status='JUDGE_ERROR',evidence=evidence)
    except Exception as exc:
        evidence['reason']=type(exc).__name__+': '+str(exc);return score_profiles(TASK/'rubric.json',status='JUDGE_ERROR',evidence=evidence)
    if not any(ts.values()):
        evidence['reason']='Workbook layout needs a supported semantic or agentic reader; no candidate score inferred.'
        return score_profiles(TASK/'rubric.json',status='JUDGE_ERROR',evidence=evidence)
    if not ts['records'] and any(x.startswith('__UNBOUND__') and re.search(r'Online Retail:\d+',x) for x in text):
        evidence['reason']='Classified occurrences may be present but cannot be safely bound by the semantic reader.'
        return score_profiles(TASK/'rubric.json',status='JUDGE_ERROR',evidence=evidence)
    for section,label in [('invoices','invoice'),('countries','country')]:
        if not ts[section] and any(x.startswith('__UNBOUND__') and label in x.lower() and x.count('||')>=2 for x in text):
            evidence['reason']=f'An unbound {label} summary is present; its legitimate organization requires a supported parser.'
            return score_profiles(TASK/'rubric.json',status='JUDGE_ERROR',evidence=evidence)
    truth=json.loads((TASK/'solution/oracle.json').read_text());manifest=json.loads((TASK/'metadata/source_manifest.json').read_text())
    expected={r[0]:r for r in truth['classified']};rows,by=consensus_rows(ts['records'],'rowid')
    source_path=Path(input_dir)/'retail_extract.csv'
    try:
        with source_path.open(encoding='utf-8-sig',newline='') as fh:input_rows=list(csv.DictReader(fh))
        required=truth['raw_headers']
        if any(not set(required)<=set(r) for r in input_rows):raise ValueError('Original business fields cannot be bound in the post-run input')
    except Exception as exc:
        evidence['reason']='Post-run source facts require a supported reader: '+str(exc)
        return score_profiles(TASK/'rubric.json',status='JUDGE_ERROR',evidence=evidence)
    raw_by=defaultdict(list)
    for r in input_rows:raw_by[r['source_row_id']].append(r)
    source_fields=dict(zip(['invoice','stock','description','quantity','date','price','customer','country'],truth['raw_headers'][1:]))
    for r in rows:
        originals=raw_by.get(str(r['rowid']),[])
        if len(originals)==1:
            r['_source_linked_fields']=[]
            for field,raw_key in source_fields.items():
                if field not in r:r[field]=originals[0][raw_key];r['_source_linked_fields'].append(field)
    def source_tuple(r):
        vals=[]
        for k in required:
            v=r.get(k,'')
            if k in ['Quantity','UnitPrice']:
                parsed=num(v)
                if parsed is None:raise ValueError('Cannot safely parse source numeric business value')
                v=str(parsed.normalize())
            elif k=='InvoiceDate':v=str(v).replace('T',' ')
            else:v=str(v or '')
            vals.append(v)
        return tuple(vals)
    try:
        original_rows=[dict(zip(required,r[:9])) for r in truth['classified']]
        exact_source=hashlib.sha256(source_path.read_bytes()).hexdigest()==manifest['input_files'][0]['sha256']
        business_source_same=exact_source or Counter(source_tuple(r) for r in input_rows)==Counter(source_tuple(r) for r in original_rows)
    except Exception as exc:
        evidence['reason']='Source style/encoding changed and business-fact parity cannot be established: '+str(exc)
        return score_profiles(TASK/'rubric.json',status='JUDGE_ERROR',evidence=evidence)
    expected_totals={r[0]:r for r in truth['totals']}
    report_rows=[r for t in ts['report'] for r in t['rows'] if r.get('metric')];rep={}
    for r in report_rows:rep.setdefault(norm(r['metric']),[]).append(r.get('value'))
    aliases={'Gross sales':['gross sales','total sales','sales value'],'Signed credits':['signed credits','credits signed','credit value','total credits','credits value'],
      'Net recorded value':['net recorded value','net trading value','net recorded amount'],
      'Exception recorded amount':['exception recorded amount','exception value','exception amount','total exceptions'],
      'Source occurrences':['source occurrences','total extract rows','source row count'],
      'In-scope occurrences':['in-scope occurrences','October occurrence count','October row count'],
      'Outside-scope occurrences':['outside-scope occurrences','outside October count','outside scope count'],
      'Missing customer in scope':['missing customer in scope','unknown customer rows','missing customer rows']}
    extracted={label:visible_numbers(report_rows,text,names) for label,names in aliases.items()}
    unknown=[k for k in ['Gross sales','Signed credits','Net recorded value'] if not extracted[k]]
    if unknown:
        evidence['reason']='Numerical report claims are absent or not safely bindable from visible labels/prose: '+', '.join(unknown)
        return score_profiles(TASK/'rubric.json',status='JUDGE_ERROR',evidence=evidence)
    def report_num(label,expected):return all(eq(v,expected,Decimal('.005')) for v in extracted[label])
    def report_text(label,pred):
        explicit=rep.get(norm(label))
        return all(pred(str(v)) for v in explicit) if explicit else any(pred(str(v)) for v in text)
    expected_in_scope={rid:r for rid,r in expected.items() if r[9]!='outside_scope'}
    multiset=population([str(r['rowid']) for r in rows if str(r['rowid']) in expected_in_scope or kind(r.get('class'))!='outside_scope'],expected_in_scope)
    queue=[r for t in ts['queue'] for r in t['rows'] if r.get('rowid')];early_queue={str(r['rowid']):r for r in queue}
    attribution_noted=any('missing' in str(x).lower() and ('customerid' in norm(x) or 'customer' in str(x).lower()) for x in text)
    def attribution_traceable(r,ex):
        return attribution_noted and 'customer' in r and str(r.get('customer') or '')==str(ex[7] or '')
    scope=[];policy=[];amounts=[];missing=[];raw_facts=[];bad=[]
    fields=['invoice','stock','description','quantity','date','price','customer','country']
    for rid,ex in expected.items():
        cand=by.get(rid,[])
        scope.append((business_source_same if ex[9]=='outside_scope' and not cand else bool(cand) and all((kind(r.get('class'))=='outside_scope')==(ex[9]=='outside_scope') for r in cand)))
        if ex[9]!='outside_scope':
            policy.append(bool(cand) and all(kind(r.get('class'))==ex[9] for r in cand))
            amounts.append(bool(cand) and all(eq(r.get('amount'),ex[10],Decimal('.005')) for r in cand))
            missing.append(bool(cand) and all(truth_bool(r.get('missing_customer'))==ex[11] if 'missing_customer' in r else (not ex[11] or rid in early_queue or attribution_traceable(r,ex)) for r in cand))
        for i,key in enumerate(fields,1):
            if ex[9]=='outside_scope' and not cand:ok=business_source_same
            elif i in [4,6]:ok=bool(cand) and all(eq(r.get(key),ex[i]) for r in cand)
            elif i==5:ok=bool(cand) and all(str(r.get(key,'')).replace('T',' ')==str(ex[i]) for r in cand)
            else:ok=bool(cand) and all(str(r.get(key) or '')==str(ex[i] or '') for r in cand)
            raw_facts.append(ok)
        if cand and (any(kind(r.get('class'))!=ex[9] or not eq(r.get('amount'),ex[10],Decimal('.005')) for r in cand)) and len(bad)<25:
            bad.append({'source_row_id':rid,'expected_class':ex[9],'expected_amount':ex[10],'candidate':[{'class':r.get('class'),'amount':r.get('amount'),'location':r['_loc']} for r in cand]})
    window=report_text('Reporting window',lambda s:all(x in s for x in ['2011-10-01','2011-11-01']) or 'october 2011' in s.lower() or 'oct 2011' in s.lower())
    r1=mean([multiset,mean(scope),window])
    queue=[r for t in ts['queue'] for r in t['rows'] if r.get('rowid')]
    qe={r[0]:r for r in truth['exceptions'] if r[3]=='business_exception' or r[0] in early_queue or not (by.get(r[0]) and all(attribution_traceable(c,expected[r[0]]) for c in by[r[0]]))};qb=defaultdict(list)
    for r in queue:qb[str(r['rowid'])].append(r)
    qgood=[]
    for rid,ex in qe.items():
        cand=qb.get(rid,[])
        qgood.append(bool(cand) and all(('exception' in norm(r.get('issue')) if ex[3]=='business_exception' else ('customer' in norm(r.get('issue')) or 'attribution' in norm(r.get('issue')))) and bool(str(r.get('reason') or '').strip()) for r in cand))
    r2=mean([mean(policy),mean(amounts),mean(missing),population(list(qb.keys()) if len(queue)==len(qb) else [str(r['rowid']) for r in queue],qe),mean(qgood)])
    candidate_country_counts=Counter((str(r.get('country')),kind(r.get('class'))) for r in rows if kind(r.get('class'))!='outside_scope')
    recovered_country_counts=[]
    for region in ts['countries']:
        kept=[]
        for r in region['rows']:
            if r.get('_recover_count'):
                r['count']=candidate_country_counts[(str(r.get('country')),kind(r.get('class')))]
                recovered_country_counts.append({'country':r.get('country'),'class':r.get('class'),'count_from_candidate_detail':r['count'],'explicit_total_line_count':r.get('_wide_total_count')})
                if num(r.get('amount'))==0 and r['count']==0:continue
            kept.append(r)
        region['rows']=kept
    def group_score(name,expected_rows,keys):
        reg=ts[name];got=[r for t in reg for r in t['rows'] if all(r.get(k) is not None for k in keys)]
        target={tuple([str(r[0]),r[1]]):r for r in expected_rows};b=defaultdict(list)
        for r in got:b[(str(r[keys[0]]),kind(r['class']))].append(r)
        units=[]
        for key,ex in target.items():
            cand=b.get(key,[])
            units.extend([bool(cand) and all(eq(r.get('count'),ex[2]) for r in cand),bool(cand) and all(eq(r.get('amount'),ex[3],Decimal('.005')) for r in cand)])
        pop=mean([population([(str(r.get(keys[0])),kind(r.get('class'))) for r in t['rows'] if r.get(keys[0]) is not None],target) for t in reg])
        return mean([mean(units),pop]),got
    r3,invoice_rows=group_score('invoices',truth['invoice_totals'],['invoice','class'])
    country_source,country_rows=group_score('countries',truth['country_totals'],['country','class'])
    # Self-consistency is computed solely from delivered candidate detail.
    own=defaultdict(lambda:[0,Decimal(0)]);own_total=defaultdict(lambda:[0,Decimal(0)])
    for r in rows:
        c=kind(r.get('class'));v=num(r.get('amount'))
        if c=='outside_scope':continue
        own[(str(r.get('country')),c)][0]+=1;own[(str(r.get('country')),c)][1]+=v or Decimal(0)
        own_total[c][0]+=1;own_total[c][1]+=v or Decimal(0)
    consistent=[]
    for ex in truth['country_totals']:
        key=(ex[0],ex[1]);cand=[r for r in country_rows if (str(r.get('country')),kind(r.get('class')))==key]
        consistent.extend([bool(cand) and all(eq(r.get('count'),own[key][0]) and (not r.get('_recover_count') or eq(r.get('_wide_total_count'),sum(v[0] for k,v in own.items() if k[0]==key[0]))) for r in cand),bool(cand) and all(eq(r.get('amount'),own[key][1],Decimal('.005')) for r in cand)])
    totalrows=[r for t in ts['totals'] for r in t['rows'] if r.get('class')];overall=[]
    outside_recovered=None
    if not any(kind(r.get('class'))=='outside_scope' for r in totalrows) and business_source_same and window:
        # Public policy permits excluded occurrences to remain in the preserved original extract.
        # Recover their traceable scope facts from that delivered input, without oracle values.
        from datetime import datetime
        outside_source=[r for r in input_rows if not datetime(2011,10,1)<=datetime.fromisoformat(str(r['InvoiceDate']).replace('T',' '))<datetime(2011,11,1)]
        outside_recovered={'class':'outside_scope','count':len(outside_source),'amount':sum((num(r['Quantity'])*num(r['UnitPrice']) for r in outside_source),Decimal(0)),'_source':'preserved candidate input and explicit October reporting scope'}
        totalrows.append(outside_recovered)
    for status,ex in expected_totals.items():
        cand=[r for r in totalrows if kind(r.get('class'))==status]
        overall.extend([bool(cand) and all(eq(r.get('count'),ex[1]) for r in cand),bool(cand) and all(eq(r.get('amount'),ex[2],Decimal('.005')) for r in cand)])
    r4=mean([country_source,mean(consistent),mean(overall)])
    report_units=[report_num('Gross sales',expected_totals['sale'][2]),report_num('Signed credits',expected_totals['credit'][2]),report_num('Net recorded value',truth['net_recorded_value']),report_num('Exception recorded amount',expected_totals['exception'][2]),report_text('Currency',lambda x:'GBP' in x.upper() or 'STERLING' in x.upper() or '£' in x)]
    chart_units=[];cachechecks=[]
    for ch in chs:
        for ser in ch['series']:
            if 'amount' not in norm(ser.get('name')) and 'value' not in norm(ser.get('name')):
                evidence['reason']='Chart series amount meaning cannot be bound from labels.'
                return score_profiles(TASK/'rubric.json',status='JUDGE_ERROR',evidence=evidence)
            cats=[kind(c) for c in ser['categories']];pairs=list(zip(cats,ser['values']))
            if any(c not in expected_totals for c in cats):
                evidence['reason']='Chart may use a valid country/document/other summary; this reader currently binds treatment-category amount charts only.'
                return score_profiles(TASK/'rubric.json',status='JUDGE_ERROR',evidence=evidence)
            chart_units.append(bool(cats) and len(cats)==len(set(cats)))
            chart_units.append(len(pairs)==len(cats) and all(eq(value,expected_totals[category][2],Decimal('.005')) for category,value in pairs))
            for label in ['categories','values']:
                cache=ser[label+'_cache']
                okay=not cache or (len(cache)==len(ser[label]) and all(eq(a,b,Decimal('.005')) if label=='values' else str(a)==str(b) for a,b in zip(cache,ser[label])))
                chart_units.append(okay);cachechecks.append(okay)
    r5=mean([mean(report_units),mean(chart_units)])
    protected=[business_source_same]
    reconciliation_fallbacks=[business_source_same and multiset==1,multiset==1,business_source_same and window and all(scope),all(missing)]
    recs=[report_num(label,value) if extracted[label] else fallback for label,value,fallback in zip(['Source occurrences','In-scope occurrences','Outside-scope occurrences','Missing customer in scope'],[truth['source_occurrences'],truth['source_occurrences']-expected_totals['outside_scope'][1],expected_totals['outside_scope'][1],truth['missing_customer_in_scope']],reconciliation_fallbacks)]
    # A populated purported original-invoice link has no source authorization.
    no_fabrication=all(not str(r.get('original_invoice') or '').strip() for t in ts.values() for region in t for r in region['rows'])
    r6=mean([mean(raw_facts),mean(protected),mean(recs),no_fabrication])
    facts=dict(zip(['R001','R002','R003','R004','R005','R006'],[r1,r2,r3,r4,r5,r6]))
    try:
        extra,bridge_evidence=bridge_facts(TASK,ts,text,input_dir)
        facts.update(extra);evidence['bridge']=bridge_evidence
    except ParsePending as exc:
        evidence['reason']=str(exc);return score_profiles(TASK/'rubric.json',status='JUDGE_ERROR',evidence=evidence)
    evidence.update(candidate_tables={k:[{'sheet':t['sheet'],'header_row':t['header_row'],'row_count':len(t['rows'])} for t in v] for k,v in ts.items()},
      source_record_mismatches=bad,outside_scope_facts_recovered_from_retained_input=None if outside_recovered is None else {**outside_recovered,'amount':str(outside_recovered['amount'])},country_counts_recovered_from_candidate_detail=recovered_country_counts,candidate_country_self_consistency=mean(consistent),source_protection=protected,
      source_protection_method='exact byte identity fast-path' if exact_source else 'CSV business-value and physical-identity multiset parity',
      source_linked_output_rows=sum(bool(r.get('_source_linked_fields')) for r in rows),
      chart_cache_self_consistency=cachechecks,chart_evidence=chs,
      denominators={'source_occurrences':64415,'mandatory_delivered_in_scope_occurrences':60742,'outside_scope_occurrences_may_remain_in_original_input':3673,'invoice_class_groups':len(truth['invoice_totals']),'country_class_groups':len(truth['country_totals']),'queue_occurrences':len(qe),'raw_business_facts_direct_or_source_linked':64415*8},
      external_acceptance_gaps=['No external negative-item/agentic parser acceptance claimed','Calibration mutants are not natural Agent failures'])
    return score_profiles(TASK/'rubric.json',facts,evidence=evidence)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('answer',nargs='?',default='/app/output/answer.xlsx');p.add_argument('--input-dir');p.add_argument('--result');a=p.parse_args()
    result=evaluate(Path(a.answer),a.input_dir);out=json.dumps(result,ensure_ascii=False,indent=2)
    if a.result:Path(a.result).write_text(out)
    print(out)

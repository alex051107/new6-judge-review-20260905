"""Read an explicitly headed amount/cumulative reconciliation, without gold values."""
import re

def read(sh,sr):
    header=None
    for row in sh:
        roles={sr.norm(c.value):c.column for c in row if c.value is not None}
        if {'description','amount','cumulative'} <= set(roles):
            if any(sum(sr.norm(c.value)==role for c in row)>1 for role in ['description','amount','cumulative']):raise ValueError('Ambiguous repeated cumulative bridge column role: '+sh.title)
            header=roles;start=row[0].row;break
    if header is None:return None
    facts=[];records=[];primary={};previous=None
    def check(label,actual,expected,tolerance=1.000001):
        try:ok=abs(sr.number(actual)-sr.number(expected))<=tolerance
        except (TypeError,ValueError):ok=False
        facts.append({'meaning':label,'actual':actual,'expected_from_candidate':expected,'tolerance':tolerance,'ok':ok})
    def claim(role,r):
        if role in primary:raise ValueError('Repeated labelled cumulative bridge role requires review: '+sh.title+' / '+role)
        primary[role]=r
    for row in sh.iter_rows(min_row=start+1):
        label=str(sh.cell(row[0].row,header['description']).value or '').strip();n=sr.norm(label)
        amount=sh.cell(row[0].row,header['amount']);running=sh.cell(row[0].row,header['cumulative'])
        source=sh.cell(row[0].row,header['reference']).value if 'reference' in header else None
        r={'sheet':sh.title,'row':row[0].row,'table':start,'label':label,'context':'Amount / cumulative cost-limit bridge','cells':{},'delta_sign':1}
        if source:
            r['source']=str(source)
            page=re.search(r'\bpage\s*(\d+)\b',str(source),re.I)
            if page:r['page']=page.group(1)
        a,c=amount.value,running.value
        if n.startswith('originalcostlimit'):
            r.update(printed=a);r['cells']['printed']=amount.coordinate;claim('original',r)
            check('Original cumulative agrees with original amount',c,a);previous=c
        elif n.startswith(('currentcostlimit','currentreviewcostlimit')):
            r.update(working=c);r['cells']['working']=running.coordinate;claim('current',r)
            check('Final cumulative agrees with last displayed subtotal',c,previous)
            if a not in [None,'','-','—','–']:check('Additional current amount agrees with current cumulative',a,c)
        elif n=='totalmovement':
            r.update(delta=a);r['cells']['delta']=amount.coordinate;claim('movement',r)
        elif n=='percentagechange':
            if c not in [None,'','-','—','–']:raise ValueError('Ambiguous additional cumulative value on percentage row: '+sh.title)
            r['value']=a;r['number_format']=amount.number_format;r['cells']['value']=amount.coordinate;claim('percentage',r)
        elif n.startswith('subtotal'):
            if a not in [None,'','-','—','–']:raise ValueError('Ambiguous amount on cumulative subtotal row: '+sh.title+' / '+label)
            check(label,c,previous);r['cumulative']=c;r['cells']['cumulative']=running.coordinate;records.append(r);previous=c
        elif re.fullmatch(r'heating.*packagepricechange|ohponheatingadjustment(?:\d+)?|designdevelopmentriskratechange.*|riskallowanceandsourceroundingadjustment|inflationallowanceonadjustments(?:\d+)?|originalprintedroundingreconciliation',n):
            expected=previous+a if isinstance(previous,(int,float)) and isinstance(a,(int,float)) else None
            check(label+' cumulative',c,expected)
            r.update(increment=a,cumulative=c);r['cells'].update(increment=amount.coordinate,cumulative=running.coordinate);records.append(r);previous=c
        elif isinstance(a,(int,float)) or isinstance(c,(int,float)):
            raise ValueError('Unknown numeric cumulative bridge label: '+sh.title+' / '+label)
    if not {'original','current','movement'} <= set(primary):raise ValueError('Incomplete labelled cumulative cost-limit bridge: '+sh.title)
    original=primary['original'];current=primary['current'];movement=primary['movement']
    if 'percentage' in primary:
        before=original['printed'];after=current['working']
        expected=(after-before)/before if isinstance(before,(int,float)) and before and isinstance(after,(int,float)) else None
        pct=primary['percentage'];fmt=re.search(r'0(?:\.(0+))?%',pct['number_format'])
        tolerance=.5*10**(-len(fmt.group(1) or '')-2)+1e-9 if fmt else 1e-6
        check('Percentage change agrees with displayed original and current limits',pct['value'],expected,tolerance)
        records.append(primary['percentage'])
    current['printed']=original['printed'];current['cells']['printed']=original['cells']['printed']
    current['delta']=movement['delta'];current['cells']['delta']=movement['cells']['delta']
    for k in ['source','page']:
        if k in original:current[k]=original[k]
    return current,records,facts

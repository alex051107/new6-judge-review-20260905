"""Business-labelled charts, with exact-image visual receipts for raster charts.

Binding uses titles/series/category labels. Numerical matches never select a
meaning. Unreadable material image panels remain pending, not business failures.
"""
from pathlib import Path
from decimal import Decimal
from collections import defaultdict
import json,zipfile,hashlib,re
from read_candidate import ParsePending,norm,num,eq
from evaluate_bridge import component

def raster_charts(path,task):
    registry=json.loads((task/'metadata/reader_v23/visual_claims.json').read_text())
    out=[]
    with zipfile.ZipFile(path) as z:
        for n in z.namelist():
            if re.fullmatch(r'xl/media/[^/]+\.(?:png|jpe?g)',n,re.I):
                digest=hashlib.sha256(z.read(n)).hexdigest();entry=registry.get(digest)
                if not entry:raise ParsePending('Embedded raster illustration needs visual verification: '+n+' sha256='+digest)
                if entry.get('pending'):raise ParsePending(entry['pending']+'; image='+n+' sha256='+digest)
                for chart in entry['charts']:out.append({**chart,'chart':n,'visual_sha256':digest,'visual_receipt':'metadata/reader_v23/visual_claims.json'})
    return out

def chart_facts(charts,truth,bridge_truth,kind):
    byclass={r[0]:Decimal(r[2]) for r in truth['totals']}
    country=defaultdict(lambda:defaultdict(Decimal))
    for name,cl,count,value in truth['country_totals']:country[norm(name)][cl]+=Decimal(value)
    bridge=dict(bridge_truth['bridge'])
    # The complete source oracle already preserves September totals.
    sepnet=Decimal(bridge['September net recorded value']);sepcredits=byclass['credit']-Decimal(bridge['Signed credit change']);sepsales=sepnet-sepcredits
    def report_role(label):
        n=norm(label)
        if n in ['sales','salesgbp','salesvalue','ordinarysales','grosssales','grosssalesgbp']:return 'sale'
        if n in ['credits','creditsgbp','signedcredits','signedcreditsgbp','creditsvalue','creditssigned']:return 'credit'
        if n in ['net','netgbp','netvalue','netrecordedvalue','netrecordedvaluegbp']:return 'net'
        if n in ['exception','exceptions','exceptionamount','exceptionrecordedamount']:return 'exception'
    def period(label):
        n=norm(label)
        return 'sep' if n in ['sep','sept','september','september2011','sep2011'] else 'oct' if n in ['oct','october','october2011','oct2011'] else None
    def amount(role,month):
        if month=='sep':return {'sale':sepsales,'credit':sepcredits,'net':sepnet,'exception':Decimal(0)}[role]
        return byclass[role] if role!='net' else Decimal(truth['net_recorded_value'])
    facts=[];caches=[];bound=[]
    for chart in charts:
        title=' '.join(chart.get('titles',[]));title_norm=norm(title)
        for series in chart['series']:
            cats=series['categories'];values=series['values'];name=series.get('name','');name_norm=norm(name);binding=[]
            chart_bridge=('bridge' in title_norm or 'contribution' in title_norm or 'movementcomponent' in title_norm or 'whatchangednet' in title_norm)
            for cat in cats:
                key=norm(cat);comp=component(cat);role=report_role(cat)
                if chart_bridge and comp in bridge:expected=Decimal(bridge[comp]);semantic='bridge:'+comp
                elif key in country and ('country' in title_norm or 'countries' in title_norm or 'net' in name_norm or report_role(name)):
                    r=report_role(name) or ('net' if 'net' in title_norm else None)
                    if r is None:raise ParsePending('Country chart amount role is not explicit: '+name)
                    expected=sum(country[key].values()) if r=='net' else country[key][r];semantic='country:'+str(cat)+':'+r
                elif role and period(name):expected=amount(role,period(name));semantic='period:'+period(name)+':'+role
                elif period(cat) and (report_role(name) or 'net' in title_norm):
                    r=report_role(name) or 'net';expected=amount(r,period(cat));semantic='period:'+period(cat)+':'+r
                elif kind(cat) in byclass and (report_role(name) or 'amount' in name_norm or 'value' in name_norm):expected=byclass[kind(cat)];semantic='class:'+kind(cat)
                elif chart_bridge and key in ['bridgecomponent','component','contribution','bridgeamountgbp']:expected=None;semantic='invalid_header_in_chart_data'
                else:raise ParsePending('Chart category/amount roles need semantic verification: '+str({'title':title,'series':name,'category':cat}))
                binding.append({'category':cat,'role':semantic,'expected':str(expected) if expected is not None else None})
            tolerance=Decimal(str(series.get('display_tolerance','.005')))
            facts.append(bool(cats) and len(cats)==len({norm(c) for c in cats}))
            facts.append(len(values)==len(cats) and all(b['expected'] is not None and eq(v,b['expected'],tolerance) for v,b in zip(values,binding)))
            for label in ['categories','values']:
                cache=series.get(label+'_cache',[])
                okay=not cache or (len(cache)==len(series[label]) and all(eq(a,b,Decimal('.005')) if label=='values' else str(a)==str(b) for a,b in zip(cache,series[label])))
                facts.append(okay);caches.append(okay)
            bound.append({'chart':chart['chart'],'name':name,'binding':binding,'display_tolerance':str(tolerance),'values':values,'facts':facts[-4:]})
    return facts,caches,bound

"""Read actual labelled candidate views; no Oracle values drive region selection."""
import re,zipfile,posixpath,xml.etree.ElementTree as ET
from collections import Counter
import openpyxl
from chart_reader import ParsePending,norm,num,eq,population,mean,formula_cache_states,charts
NS={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
CODE=re.compile(r'^E\d{8}$')

def historic(s):
    return bool(re.search(r'\b(previous|prior|historical|history|archive|archived|old)\b',str(s),re.I))

def field(label):
    t=str(label or '').lower();n=norm(t)
    basic={'code':'code','geographycode':'code','authoritycode':'code','areacode':'code','onscode':'code',
      'authority':'name','localauthority':'name','authorityname':'name','geography':'name','geographyname':'name',
      'reason':'reason','exclusionreason':'reason','explanation':'reason','movement':'movement','shortlistchange':'movement',
      'previousrank':'old_rank','priorrank':'old_rank','currentrank':'rank','rank':'rank','position':'rank',
      'previouslyselected':'previous_selected','currentlyselected':'current_selected',
      'currenteligibility':'eligible','eligible':'eligible','continuedeterioration':'eligible'}
    if n in basic:return basic[n]
    metric='unemployment' if re.search(r'\bunemp|unemployment',t) else 'employment' if re.search(r'\bemp|employment',t) else None
    if not metric:return None
    if any(x in t for x in ['cumulative','overall','first to last','total change']):return metric+'_change_23_25'
    years=re.findall(r'20(\d\d)',t)
    change=any(x in t for x in ['change','delta','difference','increase','fall','rise','Δ'.lower(),'pp'])
    if change:
        if 'first' in t or 'earlier comparison' in t:return metric+'_change_23_24'
        if 'second' in t or 'latest comparison' in t:return metric+'_change_24_25'
        if len(years)==2 and years in [['23','24'],['24','25'],['23','25']]:return metric+'_change_'+'_'.join(years)
        short=re.findall(r'(?<!\d)(2[345])(?!\d)',t)
        if len(short)==2:return metric+'_change_'+'_'.join(short)
    elif len(years)==1 and years[0] in ['23','24','25']:return metric+'_20'+years[0]
    elif len(years)==2 and ('oct' in t and 'sep' in t):
        period={('21','22'):'2023',('22','23'):'2024',('23','24'):'2025'}.get(tuple(years))
        if period:return metric+'_'+period
    return None

def read(path):
    wb=openpyxl.load_workbook(path,data_only=True,read_only=True)
    regions=[];lines=[];unbound=[]
    for sheet in wb:
        context=sheet.title;active=None
        for ri,row in enumerate(sheet.iter_rows(),1):
            vals=[c.value for c in row];filled=[v for v in vals if v is not None]
            if not filled:continue
            line=' || '.join(str(v) for v in filled)
            lines.append({'sheet':sheet.title,'row':ri,'text':line,'historical':historic(sheet.title)})
            headers={field(v):ci for ci,v in enumerate(vals) if field(v)}
            if 'code' in headers and len(headers)>1:
                comparison='movement' in headers or {'old_rank','rank'}<=set(headers) or {'previous_selected','current_selected'}<=set(headers)
                old=(historic(context) or 'old_rank' in headers) and not comparison
                role='previous' if old else 'shortlist' if 'rank' in headers or re.search(r'\bshortlist\b',context,re.I) else 'data'
                if comparison:role='movement'
                elif not old and 'reason' in headers and not any('change' in k for k in headers):role='exclusions'
                active={'sheet':sheet.title,'header_row':ri,'columns':headers,'role':role,'rows':[],'context':context}
                regions.append(active);continue
            if len(filled)==1 and not CODE.fullmatch(str(filled[0])):
                context=sheet.title+' '+str(filled[0]);active=None
            codes=[v for v in filled if CODE.fullmatch(str(v))]
            if active and vals[active['columns']['code']] is not None and CODE.fullmatch(str(vals[active['columns']['code']])):
                d={k:vals[c] if c<len(vals) else None for k,c in active['columns'].items()}
                d['_loc']=f'{sheet.title}!{ri}';d['_text']=line;active['rows'].append(d)
            elif codes and not (len(filled)<=3 and any(isinstance(x,str) and len(x)>45 and re.search(r'[a-z]{3} [a-z]{3}',x,re.I) for x in filled)):
                unbound.append({'sheet':sheet.title,'row':ri,'text':line})
    wb.close()
    has_formula,empty=formula_cache_states(path)
    if has_formula:
        f=openpyxl.load_workbook(path,data_only=False,read_only=True);v=openpyxl.load_workbook(path,data_only=True,read_only=True)
        for sf,sv in zip(f,v):
            for rf,rv in zip(sf.iter_rows(),sv.iter_rows()):
                for cf,cv in zip(rf,rv):
                    if cf.data_type=='f' and cv.value is None and (sf.title,cf.coordinate) not in empty:
                        f.close();v.close();raise ParsePending('Uncached formula requires isolated native calculation: '+sf.title+'!'+cf.coordinate)
                    if cf.data_type=='f' and cv.data_type=='e':
                        # Formula error attribution needs native/environment inspection.
                        f.close();v.close();raise ParsePending('Formula error requires attribution: '+sf.title+'!'+cf.coordinate)
        f.close();v.close()
    return regions,lines,unbound

def chart_owners(path):
    rid='{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'
    def target(base,t):return t.lstrip('/') if t.startswith('/') else posixpath.normpath(posixpath.dirname(base)+'/'+t)
    def relpath(p):return posixpath.dirname(p)+'/_rels/'+posixpath.basename(p)+'.rels'
    owners={}
    with zipfile.ZipFile(path) as z:
        def rels(p):
            rp=relpath(p)
            return {a.get('Id'):target(p,a.get('Target')) for a in ET.fromstring(z.read(rp))} if rp in z.namelist() else {}
        br=rels('xl/workbook.xml')
        for sheet in ET.fromstring(z.read('xl/workbook.xml')).findall('m:sheets/m:sheet',NS):
            sp=br[sheet.get(rid)];sr=rels(sp)
            for drawing in ET.fromstring(z.read(sp)).findall('m:drawing',NS):
                dp=sr[drawing.get(rid)]
                for cp in rels(dp).values():
                    if re.search(r'/charts/.*\.xml$',cp):owners[cp]=sheet.get('name')
    return owners

def read_charts(path):
    owners=chart_owners(path)
    out=[]
    with zipfile.ZipFile(path) as z:
        for c in charts(path):
            root=ET.fromstring(z.read(c['chart']))
            title=' '.join(x.text or '' for x in root.findall('.//{http://schemas.openxmlformats.org/drawingml/2006/chart}title//{http://schemas.openxmlformats.org/drawingml/2006/main}t'))
            out.append({**c,'title':title,'sheet':owners.get(c['chart'],''),'historical':historic(owners.get(c['chart'],''))})
    return out

"""Source-labelled business facts; no gold-value search or fixed output coordinates."""
from pathlib import Path
from decimal import Decimal
from collections import defaultdict
import argparse,json,re,sys,math
import openpyxl
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'metadata'),str(ROOT.parents[1]/'common')]
from oracle_recompute import source,compute
from ooxml_edit import edit
from runtime import score_profiles,output_status,recalculate_xlsx,RecalcUnavailable
S=source();KINDS=['elements','summary','provisional','exclusions','qualifications']
norm=lambda x:re.sub(r'[^a-z0-9]','',str(x or '').lower())
LOOK={norm(v):(kind,r['id']) for kind in KINDS for r in S[kind] for v in [r['label']]+r['aliases']}
def equal(a,b):
 try:return math.isfinite(float(a)) and abs(float(a)-float(b))<=.000001
 except (TypeError,ValueError):return False
HEADERS={
 'label':['item','stage','element','description','costitem','qualification','exclusion','allowance'],
 'printed':['printedamount','publishedamount','sourceamount','originalamount','printedcost','publishedcost','printedgbp'],
 'rate':['printedrate','publishedrate','originalrate','total','percenttotal','sourcepercentage'],
 'working':['workingamount','workingcost','currentamount','adjustedamount','workinggbp','calculatedamount'],
 'working_rate':['workingrate','allowancepercentage','adjustedrate','currentrate'],
 'delta':['difference','variance','reconciliation','workingminusprinted','printedminusworking'],
 'scope':['scope','status','treatment','meaning','qualification','notes','inclusion'],
 'source':['source','reference','sourcereference','document'],
 'page':['page','pdfpage','sourcepage']}
H={v:k for k,vs in HEADERS.items() for v in vs}
def bind_label(v):
 n=norm(v);n=re.sub(r'^\d+','',n)
 if n in LOOK:return LOOK[n]
 hits={key for token,key in LOOK.items() if len(token)>22 and n.startswith(token[:22])}
 return next(iter(hits)) if len(hits)==1 else None
def discover(w):
 found=defaultdict(list);unbound=[];tables=[];material_unparsed=[]
 text=' '.join(str(c.value) for s in w for row in s.iter_rows(max_row=min(s.max_row,400),max_col=min(s.max_column,60)) for c in row if c.value is not None)
 for s in w:
  if s.max_row>10000 or s.max_column>500:raise ValueError('Material workbook exceeds bounded reader')
  context=' '.join(str(c.value) for row in s.iter_rows(max_row=min(s.max_row,3),max_col=min(s.max_column,30)) for c in row if c.value is not None)
  current=None;sheet_matches=0
  for row in s.iter_rows(max_row=min(s.max_row,500),max_col=min(s.max_column,60)):
   header={H[norm(c.value)]:c.column for c in row if norm(c.value) in H}
   if 'label' in header and len(header)>=2:current=header;tables.append((s.title,row[0].row));continue
   if not current:continue
   label=s.cell(row[0].row,current['label']).value
   if label is None:continue
   key=bind_label(label)
   if not key:
    if any(isinstance(s.cell(row[0].row,col).value,(int,float)) for name,col in current.items() if name in ['printed','working']) and not re.search(r'total|sum|check',str(label),re.I):unbound.append({'sheet':s.title,'label':str(label)})
    continue
   rec={'sheet':s.title,'row':row[0].row,'label':str(label),'context':context,'cells':{}}
   for name,col in current.items():rec[name]=s.cell(row[0].row,col).value;rec['cells'][name]=s.cell(row[0].row,col).coordinate
   if 'printed' not in current:
    amounts=[c for c in row if norm(s.cell(tables[-1][1],c.column).value) in ['amount','cost','amountgbp','costgbp']]
    if amounts:rec['printed']=amounts[0].value;rec['cells']['printed']=amounts[0].coordinate
   rec['delta_sign']=-1 if current.get('delta') and norm(s.cell(tables[-1][1],current['delta']).value)=='printedminusworking' else 1
   found[key].append(rec);sheet_matches+=1
  if sheet_matches==0 and sum(isinstance(c.value,(int,float)) for row in s.iter_rows(max_row=min(s.max_row,500),max_col=min(s.max_column,60)) for c in row)>10:material_unparsed.append(s.title)
 if unbound:raise ValueError('Material result labels cannot be safely bound: '+str(unbound[:3]))
 if material_unparsed and any((kind,r['id']) not in found for kind in KINDS for r in S[kind]):raise ValueError('A material candidate table remains unbound: '+str(material_unparsed))
 if not found and sum(isinstance(c.value,(int,float)) for s in w for row in s for c in row)>10:raise ValueError('Material numeric result layout cannot be safely bound')
 errors=[(key,r.get(field)) for key,rs in found.items() for r in rs for field in ['printed','working','working_rate','delta'] if r.get(field) in ['#NAME?','#VALUE!','#N/A']]
 if errors:raise RecalcUnavailable('Bound required quantity has an engine/parse error: '+str(errors[:3]))
 return found,text
def records(f,k,id):return f.get((k,id),[])
def numeric(f,k,id,field,value):
 rs=records(f,k,id);return bool(rs) and all(equal(r.get(field),value) for r in rs)
def page_ok(r,page):
 v=str(r.get('page',''));return bool(re.search(r'(?<!\d)'+str(page)+r'(?!\d)',v)) or bool(re.search(r'(?:page|p\.?)[\s.:]*'+str(page)+r'\b',r['context'],re.I))
def scope_text(rs):return ' '.join(str(r.get('scope',''))+' '+r.get('context','') for r in rs).lower()
QUAL={'guide':[r'guide|probable',r'cost|estimate'],'qs':[r'quantity surveyor',r'consult'],'drawings':[r'RTP',r'pre.?planning',r'no input|no other|another designer'],'scope_basis':[r'drawing',r'specification|envisaged'],'phase':[r'single phase',r'local',r'medium'],'duration':[r'45',r'week'],'price_basis':[r'4Q24|Q4.?2024',r'1Q25|Q1.?2025',r'BCIS',r'Cornwall']}
def checks(w):
 f,text=discover(w);o=compute();detail={k:[] for k in ['R001','R002','R003','R004','R005','R006']}
 def add(cid,id,ok,actual=None,expected=None):detail[cid].append(dict(id=id,ok=bool(ok),actual=actual,expected=str(expected) if expected is not None else None))
 for id,pattern in {'document':r'cost estimate|cost.review|order.of.cost|\bOCE\b','revision':r'revision\s*A\b|rev\s*A\b|reva','date':r'October.?2024|Oct.?24|2024.?10','project':r'Falmouth','currency':r'GBP|£|pounds sterling'}.items():add('R001',id,bool(re.search(pattern,text,re.I)))
 for kind in KINDS:
  for r in S[kind]:
   rs=records(f,kind,r['id']);unique=len(rs)==1
   if kind in ['elements','summary','provisional']:
    add('R002',kind+':'+r['id']+':unique',unique,len(rs),1)
    if isinstance(r['amount'],(int,float)):add('R002',kind+':'+r['id']+':printed',numeric(f,kind,r['id'],'printed',r['amount']),[z.get('printed') for z in rs],r['amount'])
    if r['rate'] is not None:add('R002',kind+':'+r['id']+':printed_rate',numeric(f,kind,r['id'],'rate',r['rate']),[z.get('rate') for z in rs],r['rate'])
   if kind=='provisional':add('R003',r['id']+':included_memorandum',unique and 'includ' in scope_text(rs) and ('memorandum' in scope_text(rs) or 'within elemental' in scope_text(rs)) and not any(re.search(r'additional charge|add to total|not included',str(z.get('scope','')),re.I) for z in rs))
   if kind=='exclusions':add('R003',r['id']+':excluded',unique and all('exclud' in str(z.get('scope','')).lower()+' '+str(z.get('printed','')).lower() and not isinstance(z.get('printed'),(int,float)) for z in rs))
   if kind=='qualifications':add('R003',r['id']+':qualification',unique and all(re.search(p,scope_text(rs),re.I) for p in QUAL[r['id']]))
   if r['id'] in ['listing','construction_risk','employer_risk','consultants']:
    add('R003',r['id']+':source_unpriced',unique and all(not isinstance(z.get('printed'),(int,float)) and (str(z.get('printed','')).strip() in ['-','—','–',''] or re.search(r'exclud|unpriced|not priced',str(z.get('printed','')),re.I)) for z in rs))
   source_ok=bool(re.search(r'Falmouth|Passmore Edwards',text,re.I)) and bool(re.search(r'\.pdf|October.?2024|Oct.?24',text,re.I))
   add('R006',kind+':'+r['id']+':source_page',unique and source_ok and all(page_ok(z,r['page']) for z in rs))
 for id,value in o['elements'].items():add('R004','element:'+id,numeric(f,'elements',id,'working',value),expected=value)
 for id,value in o['working'].items():
  add('R004','working:'+id,numeric(f,'summary',id,'working',value),expected=value)
  rs=records(f,'summary',id);add('R004','reconciliation:'+id,bool(rs) and all(equal(z.get('delta'),o['reconciliation'][id]*z['delta_sign']) for z in rs),expected=o['reconciliation'][id])
 for id,value in o['rates'].items():add('R004','working_rate:'+id,numeric(f,'summary',id,'working_rate',value),expected=value)
 return detail,f
def locate(f,kind,id,field):
 rs=records(f,kind,id);rs=[r for r in rs if field in r['cells']]
 return (rs[0]['sheet'],rs[0]['cells'][field]) if rs else None
def evaluate(path,evidence_dir,completed_run=True):
 out=Path(evidence_dir);out.mkdir(parents=True,exist_ok=True);status=output_status(path)
 if status:
  result=score_profiles(ROOT/'rubric.json',status=status if completed_run else 'INFRA_ERROR',evidence={'completed_run':completed_run})
 else:
  try:
   raw=openpyxl.load_workbook(path,data_only=False)
   if any(c.data_type=='f' and re.search(r'LAMBDA\(|_xlfn\.PY\(',str(c.value),re.I) for s in raw for row in s for c in row):raise RecalcUnavailable('Legal formula feature is unsupported by the native adapter')
   fresh,receipt=recalculate_xlsx(path,out/'base');w=openpyxl.load_workbook(fresh,data_only=True);details,before=checks(w);orig=compute();probes=[];printed_invariants=[]
   for name,changes in [('roof',{'pitched_roof':428900}),('risk',{'design_risk_rate':'.12'}),('joint',{'services':639250,'overheads_rate':'.12','inflation_rate':'.015'})]:
    patch=defaultdict(dict);bound=True
    for id,value in changes.items():
     key=id.removesuffix('_rate');where=locate(before,'summary' if id.endswith('_rate') else 'elements',key,'working_rate' if id.endswith('_rate') else 'working')
     if where is None:bound=False;continue
     patch[where[0]][where[1]]=float(value)
    new=compute(changes);af={};rec=None
    if bound:
     dest=out/name/'mutated.xlsx';edit(path,dest,patches=patch,clear_caches=True);fresh2,rec=recalculate_xlsx(dest,out/name/'recalc');af,_=discover(openpyxl.load_workbook(fresh2,data_only=True))
    for id,value in new['working'].items():
     delta=value-orig['working'][id]
     if delta==0:continue
     br=records(before,'summary',id);ar=records(af,'summary',id);ok=bool(br) and len(br)==len(ar) and all(isinstance(a.get('working'),(int,float)) and isinstance(b.get('working'),(int,float)) and equal(b['working']-a['working'],delta) for a,b in zip(br,ar))
     details['R005'].append(dict(id=name+':'+id,ok=ok,expected_delta=str(delta)))
    if bound:
     good=True
     for kind in ['elements','summary','provisional']:
      for r in S[kind]:
       br=records(before,kind,r['id']);ar=records(af,kind,r['id'])
       for field in ['printed','rate']:
        good=good and len(br)==len(ar) and all(a.get(field)==b.get(field) for a,b in zip(br,ar))
     printed_invariants.append(good)
    else:printed_invariants.append(True)
    probes.append(dict(name=name,changes=changes,bound=bound,native_receipt=rec))
   details['R002'].append(dict(id='original_figures_preserved_during_edits',ok=all(printed_invariants)))
   scores={k:str(Decimal(sum(z['ok'] for z in xs))/Decimal(len(xs))) for k,xs in details.items()}
   result=score_profiles(ROOT/'rubric.json',scores,evidence={'base_native_receipt':receipt,'dynamic_probes':probes,'fact_units':details,'parser':'Binds visible source labels and role headers, regardless of sheet/row/column. Unsupported material layouts and legal formula limits are pending, never zero.','scope':'15 element rows;12 summary rows;13 included memorandum rows;24 exclusions;7 qualifications. Dynamic denominator uses independent nonzero expected working-stage changes.'})
  except (RecalcUnavailable,ValueError,TypeError,KeyError,openpyxl.utils.exceptions.InvalidFileException) as exc:result=score_profiles(ROOT/'rubric.json',status='JUDGE_ERROR',evidence={'error_type':type(exc).__name__,'error':str(exc)})
 (out/'evaluation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,default=str));return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('answer',nargs='?',default='/app/output/answer.xlsx');p.add_argument('--evidence-dir',default='/tmp/new6-c1-evidence');p.add_argument('--input-dir');p.add_argument('--completed-run',action='store_true');a=p.parse_args();print(json.dumps(evaluate(a.answer,a.evidence_dir,a.completed_run),default=str))

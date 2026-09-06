"""Narrow source-preserving OOXML cell/sheet edits; no formula evaluation."""
from lxml import etree as E
from zipfile import ZipFile,ZIP_DEFLATED
from pathlib import Path
import re,copy,posixpath
from openpyxl.formula.translate import Translator
NS='http://schemas.openxmlformats.org/spreadsheetml/2006/main'
RNS='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
PNS='http://schemas.openxmlformats.org/package/2006/relationships'
N={'s':NS};T=lambda s:f'{{{NS}}}{s}'
def cell_set(root,coord,value):
 data=root.find(T('sheetData'));rnum=int(re.search(r'\d+',coord).group());row=data.find(f"s:row[@r='{rnum}']",N)
 if row is None:row=E.SubElement(data,T('row'),r=str(rnum))
 cell=row.find(f"s:c[@r='{coord}']",N)
 if cell is None:cell=E.SubElement(row,T('c'),r=coord)
 for child in list(cell):cell.remove(child)
 cell.attrib.pop('t',None)
 if value is None:return
 if isinstance(value,str) and value.startswith('='):E.SubElement(cell,T('f')).text=value[1:]
 elif isinstance(value,str):
  cell.set('t','inlineStr');E.SubElement(E.SubElement(cell,T('is')),T('t')).text=value
 else:E.SubElement(cell,T('v')).text=str(value)
def edit(source,destination,patches=None,clones=None,new_sheets=None,clear_caches=False):
 with ZipFile(source) as z:files={n:z.read(n) for n in z.namelist()}
 book=E.fromstring(files['xl/workbook.xml']);rels=E.fromstring(files['xl/_rels/workbook.xml.rels']);sheets=book.find(T('sheets'));ct=E.fromstring(files['[Content_Types].xml'])
 targets={r.get('Id'):r.get('Target') for r in rels};mapping={s.get('name'):posixpath.normpath(posixpath.join('xl',targets[s.get(f'{{{RNS}}}id')])).lstrip('/') for s in sheets}
 roots={n:E.fromstring(files[p]) for n,p in mapping.items()}
 # Resolve source shared-formula storage before deleting any master cell.
 # openpyxl's standard A1 translator preserves follower meaning; this is not evaluation.
 for root in roots.values():
  shared={}
  for cell in root.findall('.//s:c',N):
   f=cell.find(T('f'))
   if f is not None and f.get('t')=='shared' and f.text:shared[f.get('si')]=(cell.get('r'),f.text)
  for cell in root.findall('.//s:c',N):
   f=cell.find(T('f'))
   if f is not None and f.get('t')=='shared':
    if not f.text:
     master,formula=shared[f.get('si')];f.text=Translator('='+formula,origin=master).translate_formula(cell.get('r'))[1:]
    for attr in ('t','si','ref'):f.attrib.pop(attr,None)
 for name,patch in (patches or {}).items():
  for co,val in patch.items():cell_set(roots[name],co,val)
 def add(name,root):
  i=max([int(s.get('sheetId')) for s in sheets]+[0])+1;rid=f'rIdNEW6{i}';path=f'xl/worksheets/new6sheet{i}.xml'
  E.SubElement(sheets,T('sheet'),name=name,sheetId=str(i),attrib={f'{{{RNS}}}id':rid})
  E.SubElement(rels,f'{{{PNS}}}Relationship',Id=rid,Type=f'{RNS}/worksheet',Target=path[3:])
  E.SubElement(ct,'{http://schemas.openxmlformats.org/package/2006/content-types}Override',PartName='/'+path,ContentType='application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml')
  mapping[name]=path;roots[name]=root
 for name,spec in (clones or {}).items():
  source_name,replacements=spec;root=copy.deepcopy(roots[source_name]);
  for f in root.findall('.//s:f',N):
   for a,b in replacements:f.text=f.text.replace(a,b)
  # clone drawings are not needed and duplicate relationship ids would be invalid
  for c in list(root):
   if E.QName(c).localname in ['drawing','legacyDrawing','tableParts']:root.remove(c)
  add(name,root)
 for name,values in (new_sheets or {}).items():
  root=E.Element(T('worksheet'),nsmap={None:NS});E.SubElement(root,T('sheetData'))
  for co,val in values.items():cell_set(root,co,val)
  add(name,root)
 for name,root in roots.items():
  if clear_caches:
   for c in root.findall('.//s:c',N):
    if c.find(T('f')) is not None:
     for v in c.findall(T('v')):c.remove(v)
  files[mapping[name]]=E.tostring(root,xml_declaration=True,encoding='UTF-8',standalone=True)
 if clear_caches:
  for p in list(files):
   if p.startswith('xl/charts/') and p.endswith('.xml'):
    root=E.fromstring(files[p]);
    for el in root.xpath('//*[local-name()="numCache" or local-name()="strCache"]'):el.getparent().remove(el)
    files[p]=E.tostring(root,xml_declaration=True,encoding='UTF-8',standalone=True)
 calc=book.find(T('calcPr'))
 if calc is not None:calc.set('fullCalcOnLoad','1');calc.set('forceFullCalc','1')
 files['xl/workbook.xml']=E.tostring(book,xml_declaration=True,encoding='UTF-8',standalone=True);files['xl/_rels/workbook.xml.rels']=E.tostring(rels,xml_declaration=True,encoding='UTF-8',standalone=True);files['[Content_Types].xml']=E.tostring(ct,xml_declaration=True,encoding='UTF-8',standalone=True)
 Path(destination).parent.mkdir(parents=True,exist_ok=True)
 with ZipFile(destination,'w',ZIP_DEFLATED) as z:
  for p,b in files.items():z.writestr(p,b)

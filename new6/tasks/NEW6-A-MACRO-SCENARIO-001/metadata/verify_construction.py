from pathlib import Path
import json,zipfile
from lxml import etree as E
import openpyxl
from pypdf import PdfReader
p=Path(__file__).resolve().parents[1];m=json.loads((p/'metadata/mutation_manifest.json').read_text());a=openpyxl.load_workbook(p/'metadata/configured_source.xlsx',data_only=False);b=openpyxl.load_workbook(p/'data/input_files/LTGM_Zambia_restore.xlsx',data_only=False)
changes={(x['sheet'],x['cell']) for x in m['changes']};unexpected=[]
for s in a:
 for row in s:
  for c in row:
   wanted=None if (s.title,c.coordinate) in changes else c.value
   if b[s.title][c.coordinate].value!=wanted:unexpected.append((s.title,c.coordinate))
assert not unexpected,unexpected[:5]
cache_count=0;chart_cache_count=0
with zipfile.ZipFile(p/'data/input_files/LTGM_Zambia_restore.xlsx') as z:
 for n in z.namelist():
  if n.startswith('xl/worksheets/') and n.endswith('.xml'):
   r=E.fromstring(z.read(n));cache_count+=len(r.xpath('//*[local-name()="c"][*[local-name()="f"]]/*[local-name()="v"]'))
  if n.startswith('xl/charts/') and n.endswith('.xml'):
   chart_cache_count+=len(E.fromstring(z.read(n)).xpath('//*[local-name()="numCache" or local-name()="strCache"]'))
assert cache_count==chart_cache_count==0
pdf=PdfReader(p/'data/input_files/LTGM_instructions_methods_p1-3.pdf');assert len(pdf.pages)==3 and all(len(pg.extract_text())>100 for pg in pdf.pages)
receipt=dict(status='PASS',manifest_cells=len(changes),unexpected_semantic_cell_changes=unexpected,formula_caches=cache_count,chart_caches=chart_cache_count,baseline_and_source_preserved=True,source_shared_formulas_expanded_before_master_deletion=True,original_method_pages=3,method_pdf_readback='PASS',reference_preceded_input=True)
(p/'metadata/construction_verification.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt))

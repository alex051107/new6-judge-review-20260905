"""Compare published source facts after binding visible geography and headers."""
from collections import Counter
from decimal import Decimal
from pathlib import Path
import re
import openpyxl

def value(v):
 if v is None:return ''
 if isinstance(v,(int,float)) and not isinstance(v,bool):return str(Decimal(str(v)).quantize(Decimal('0.000000001')).normalize())
 return re.sub(r'\s+',' ',str(v)).strip()

def signature(path):
 book=openpyxl.load_workbook(path,data_only=True);records=[];notes=[];tables=0
 for sheet in book:
  rows=list(sheet.values);headers=None;code_col=None
  for row in rows:
   texts=[value(v) for v in row]
   if 'Geography code' in texts:
    headers=texts;code_col=texts.index('Geography code');tables+=1;continue
   code=texts[code_col] if code_col is not None and code_col<len(texts) else ''
   if headers is not None and re.fullmatch('[A-Z][0-9]{8}',code):
    fields=tuple(sorted((h,texts[c] if c<len(texts) else '') for c,h in enumerate(headers) if h))
    # The visible first column names the area even if its header is blank.
    records.append((code,fields,texts[0]));continue
   if any(texts):notes.append(tuple(x for x in texts if x))
 if tables!=1 or not records:raise ValueError('Published geography table is not uniquely bindable')
 return Counter(records),Counter(notes)

def compare_source(reference,candidate):
 if not Path(candidate).is_file():return None,{'state':'UNBOUND','reason':'Expected source may be missing or renamed; preservation cannot be decided from filename alone'}
 try:original,original_notes=signature(reference);actual,actual_notes=signature(candidate)
 except Exception as exc:return None,{'state':'UNBOUND','reason':type(exc).__name__+': '+str(exc)}
 if set(h for _,row,_ in original for h,_ in row)!=set(h for _,row,_ in actual for h,_ in row):
  return None,{'state':'UNBOUND','reason':'Source headings or units changed; semantic adapter required'}
 if original!=actual:
  return False,{'state':'FACTS_CHANGED','missing_or_changed_records':sum((original-actual).values()),'extra_or_changed_records':sum((actual-original).values())}
 if original_notes!=actual_notes:return None,{'state':'UNBOUND','reason':'Geography facts preserved but surrounding source notes reorganized or changed; needs semantic review'}
 return True,{'state':'FACTS_PRESERVED','row_count':sum(original.values()),'formatting_or_row_order_ignored':True}

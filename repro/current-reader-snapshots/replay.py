#!/usr/bin/env python3
"""Re-read archived Excel with now-validated deployed readers; no Agent or API."""
import argparse,hashlib,json,shutil,subprocess,tarfile,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
IMAGE='sha256:16d89ab96d5cd066a81496dfb7cfa4b0f77fe031ac7a57183fde686ce13e7f97'
p=argparse.ArgumentParser(description=__doc__);g=p.add_mutually_exclusive_group(required=True);g.add_argument('--case',nargs='+');g.add_argument('--all',action='store_true');p.add_argument('--out',required=True,type=Path);a=p.parse_args()
rows=json.loads((ROOT/'selected.json').read_text());rows=[r for r in rows if a.all or r['case'] in a.case]
if not rows or (a.case and set(a.case)!={r['case']for r in rows}):p.error('Unknown case')
if a.out.exists():p.error('Use a new output directory')
assert subprocess.check_output(['docker','image','inspect','--format','{{.Id}}',IMAGE],text=True).strip()==IMAGE
out=a.out.resolve();out.mkdir(parents=True);info=json.loads((ROOT/'archive.json').read_text());arc=out/'source.tar.gz';h=hashlib.sha256()
with arc.open('wb') as target:
 for part in info['parts']:
  data=(ROOT/part['name']).read_bytes();assert len(data)==part['size'];h.update(data);target.write(data)
assert h.hexdigest()==info['sha256']
with tarfile.open(arc) as t:t.extractall(out,filter='data')
for r in rows:
 dest=out/'cases'/r['case']
 with zipfile.ZipFile(ROOT.parents[1]/r['zip_repository_relative_path']) as z:
  for n in z.namelist():assert (dest/n).resolve().is_relative_to(dest.resolve())
  z.extractall(dest)
 assert hashlib.sha256((dest/'answer.xlsx').read_bytes()).hexdigest()==r['answer_sha256']
(out/'selected.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
for f in ['snapshot-files.json','run_one.py','run_batch.py']:shutil.copy2(ROOT/f,out/f)
cmd=['docker','run','--rm','--pull','never','--network','none','--cpus','1','--memory','3g','--read-only','--tmpfs','/tmp:rw,exec,size=1g','-e','PYTHONDONTWRITEBYTECODE=1','-e','HOME=/tmp','-v',str(out)+':/work',IMAGE,'python','/work/run_batch.py']
(out/'invocation.json').write_text(json.dumps({'image':IMAGE,'cases':[r['case']for r in rows],'network':'none','cpus':1,'memory':'3g','agent_calls':0,'api_calls':0},indent=2))
subprocess.run(cmd,check=True)

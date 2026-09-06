from pathlib import Path
import json,sys,subprocess
R=Path('/work')
import hashlib
for relative,expected in json.loads((R/'snapshot-files.json').read_text()).items():
    assert hashlib.sha256((R/relative).read_bytes()).hexdigest()==expected, relative
rows=json.loads((R/'selected.json').read_text());results=[]
for r in rows:
 c=r['case'];command=[sys.executable,'/work/run_one.py',c]
 p=subprocess.run(command,capture_output=True,text=True)
 (R/'logs').mkdir(exist_ok=True);(R/'logs'/f'{c}.txt').write_text(p.stdout+'\n'+p.stderr)
 results.append({'case':c,'returncode':p.returncode});(R/'batch-status.json').write_text(json.dumps(results,indent=2));print(c,p.returncode,flush=True)

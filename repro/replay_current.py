#!/usr/bin/env python3
"""Replay current 78 selected outputs offline, preserving each Judge route."""
import argparse,hashlib,importlib.util,json,shutil,subprocess,tarfile,zipfile
from decimal import Decimal,localcontext
from pathlib import Path
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parent
IMAGE='sha256:16d89ab96d5cd066a81496dfb7cfa4b0f77fe031ac7a57183fde686ce13e7f97'
def compare(out,rows):
 spec=importlib.util.spec_from_file_location('existing_reweight',ROOT/'fixed-34374/public-summary/reweight_receipt.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 index=json.loads((ROOT/'current-replay-index.json').read_text());weights=json.loads((REPO/index['weights']).read_text());assert weights==json.loads((m.ROOT/'weights.json').read_text())['tasks'],'Current weights differ from validated calculator'
 original={r['case']:r for r in json.loads((REPO/index['source_records']).read_text())};result=[]
 for row in rows:
  c=row['case'];p=out/'scores'/c/'result.json';e=original[c];assert e['answer_sha256']==row['answer_sha256'] and e['trial_id']==row['trial_id'], 'Index/source identity changed';item={'case':c,'route':row['route'],'snapshot':row['snapshot'],'historical_code_identity':row['code_identity'],'status':'NO_RECEIPT','match':False}
  if p.exists():
   r=json.loads(p.read_text(),parse_float=str);item['status']=r.get('evaluation_status',r.get('status'));
   try:score=m.calculate(row['task'],r)
   except Exception as exc:
    item.update(status='WEIGHT_REPLAY_ERROR',error=str(exc));result.append(item);continue
   (p.parent/'current-score.json').write_text(json.dumps(score,indent=2))
   facts=r.get('criterion_scores') or {};expected=e['criterion_scores'];norm=lambda d:{k:Decimal(str(v))for k,v in d.items()};same=item['status']=='SCORED' and norm(facts)==norm(expected)
   with localcontext() as ctx:
    ctx.prec=60;diff=abs(Decimal(score['score'])-Decimal(e['focus60_points'])/100) if score['score'] is not None else None
   item.update(criteria_match=same,score=score['score'],expected_points=e['focus60_points'],score_difference=str(diff) if diff is not None else None,total_match=diff is not None and diff<Decimal('1e-44'),pass_match=score['pass']==e['passing60'],criterion_differences={k:{'new':facts.get(k),'expected':expected.get(k)}for k in set(facts)|set(expected)if norm(facts).get(k)!=norm(expected).get(k)})
   item['match']=same and item['total_match'] and item['pass_match']
  result.append(item)
 report={'cases':result,'matched':sum(r['match']for r in result),'selected':len(result),'alpha':index['alpha'],'score_comparison_tolerance':'1e-44 (serialization only; no pass tolerance)','source_records':index['source_records'],'weights':index['weights'],'agent_calls':0,'api_calls':0};(out/'comparison.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));return report

def unpack(source,info_name,target):
 info=json.loads((source/info_name).read_text());target.mkdir(parents=True);arc=target/'source.tar.gz';h=hashlib.sha256()
 with arc.open('wb') as f:
  for part in info['parts']:
   data=(source/part['name']).read_bytes();assert len(data)==part['size'];h.update(data);f.write(data)
 assert h.hexdigest()==info['sha256']
 with tarfile.open(arc) as t:t.extractall(target,filter='data')
def main():
 p=argparse.ArgumentParser(description=__doc__);g=p.add_mutually_exclusive_group(required=True);g.add_argument('--case',nargs='+');g.add_argument('--all',action='store_true');p.add_argument('--out',required=True,type=Path);a=p.parse_args();index=json.loads((ROOT/'current-replay-index.json').read_text());rows=[r for r in index['cases']if a.all or r['case']in a.case]
 if not rows or (a.case and set(a.case)!={r['case']for r in rows}):p.error('Unknown or unscored case; see current-replay-index.json')
 if a.out.exists():p.error('Use a new output directory')
 assert subprocess.check_output(['docker','image','inspect','--format','{{.Id}}',IMAGE],text=True).strip()==IMAGE
 out=a.out.resolve();out.mkdir(parents=True)
 if any(r['route']=='fixed-34374'for r in rows):unpack(ROOT/'fixed-34374','judge-archive.json',out/'fixed')
 if any(r['route']=='current-reader-snapshot'for r in rows):
  unpack(ROOT/'current-reader-snapshots','archive.json',out/'current');shutil.copy2(ROOT/'current-reader-snapshots/snapshot-files.json',out/'current-files.json')
 for r in rows:
  dest=out/'cases'/r['case']
  with zipfile.ZipFile(REPO/r['zip']) as z:
   for n in z.namelist():assert (dest/n).resolve().is_relative_to(dest.resolve())
   z.extractall(dest)
  assert hashlib.sha256((dest/'answer.xlsx').read_bytes()).hexdigest()==r['answer_sha256']
 (out/'selected.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2));shutil.copy2(ROOT/'replay_current_worker.py',out/'worker.py')
 command=['docker','run','--rm','--pull','never','--network','none','--cpus','1','--memory','3g','--read-only','--tmpfs','/tmp:rw,exec,size=1g','-e','HOME=/tmp','-e','PYTHONDONTWRITEBYTECODE=1','-v',str(out)+':/work',IMAGE,'python','/work/worker.py']
 (out/'invocation.json').write_text(json.dumps({'image':IMAGE,'network':'none','cpus':1,'memory':'3g','cases':[r['case']for r in rows],'agent_calls':0,'api_calls':0},indent=2));run=subprocess.run(command);report=compare(out,rows);print(json.dumps({'matched':report['matched'],'selected':report['selected'],'comparison':str(out/'comparison.json')}));return 0 if run.returncode==0 and report['matched']==report['selected'] else 1
if __name__=='__main__':raise SystemExit(main())

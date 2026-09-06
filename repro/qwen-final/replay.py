#!/usr/bin/env python3
"""Offline replay of the collected Qwen workbooks with the published reader snapshots."""
import argparse,hashlib,json,subprocess,zipfile,io
from pathlib import Path

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
def unpack(path,dest,expected):
    data=path.read_bytes() if path.exists() else b''.join(x.read_bytes() for x in sorted(path.parent.glob(path.name+'.part*')))
    if hashlib.sha256(data).hexdigest()!=expected:
        raise ValueError('Archive identity mismatch: '+path.name)
    dest.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for name in z.namelist():
            if not (dest/name).resolve().is_relative_to(dest.resolve()):
                raise ValueError('Unsafe archive member')
        z.extractall(dest)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    g=p.add_mutually_exclusive_group(required=True);g.add_argument('--all',action='store_true');g.add_argument('--case',nargs='+')
    p.add_argument('--out',type=Path,required=True);p.add_argument('--image',default='new6-judge:20260905')
    a=p.parse_args();out=a.out.resolve()
    if out.exists():p.error('--out must be a new directory')
    expected_image='sha256:16d89ab96d5cd066a81496dfb7cfa4b0f77fe031ac7a57183fde686ce13e7f97'
    actual_image=subprocess.check_output(['docker','image','inspect','--format','{{.Id}}',a.image],text=True).strip()
    if actual_image!=expected_image:raise ValueError('Use the fixed public Judge image')
    rows=json.loads((HERE/'selected.json').read_text());selected=rows if a.all else [r for r in rows if r['case'] in a.case]
    if not selected or a.case and len(selected)!=len(set(a.case)):p.error('Unknown case; see selected.json')
    lock=json.loads((HERE/'archives.json').read_text());unpack(HERE/'judges.zip',out/'judges',lock['judges.zip'])
    results=[]
    for row in selected:
        case=row['case'];zipname='workbooks/'+case+'.zip'
        unpack(HERE/zipname,out/'cases'/case,lock[zipname])
        dest=out/'scores'/case;dest.mkdir(parents=True)
        cmd=['docker','run','--rm','--network','none','--cpus','1','--memory','3g',
             '-v',str(out/'judges'/row['task'])+':/tests:ro',
             '-v',str(out/'cases'/case/'answer.xlsx')+':/app/output/answer.xlsx:ro',
             '-v',str(out/'cases'/case/'input')+':/app/input:ro',
             '-v',str(dest)+':/logs/verifier',a.image,'python','/tests/run_verifier.py']
        try:
            run=subprocess.run(cmd,capture_output=True,text=True,timeout=700)
            (dest/'stdout.txt').write_text(run.stdout);(dest/'stderr.txt').write_text(run.stderr)
            receipt=json.loads((dest/'judge-result.json').read_text())
        except Exception as exc:
            receipt={'evaluation_status':'JUDGE_EXECUTION_PENDING','score_decimal':None,'pass':None,'error':str(exc)}
            (dest/'judge-result.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2))
        item={'case':case,'status':receipt['evaluation_status'],'original_score':receipt.get('score_decimal')}
        if receipt['evaluation_status']=='SCORED':
            subprocess.run(['python3',str(REPO/'results/unified-scores-v3/reweight_receipt.py'),
                            '--task',row['task'],'--receipt',str(dest/'judge-result.json'),
                            '--output',str(dest/'current-score.json')],check=True,capture_output=True,text=True)
            item['current_score_file']=str((dest/'current-score.json').relative_to(out))
        results.append(item);(out/'summary.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
        print(json.dumps(item,ensure_ascii=False),flush=True)
    return 0
if __name__=='__main__':raise SystemExit(main())

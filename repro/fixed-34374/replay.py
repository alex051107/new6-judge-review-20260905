#!/usr/bin/env python3
"""Offline replay of archived workbooks with the fixed NEW6 Judge. No Agent/API calls."""
import argparse, hashlib, json, shutil, subprocess, tarfile, uuid, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
IMAGE = 'sha256:16d89ab96d5cd066a81496dfb7cfa4b0f77fe031ac7a57183fde686ce13e7f97'

def main():
    p = argparse.ArgumentParser(description=__doc__)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument('--case', nargs='+', help='Case IDs from replay-manifest.json')
    g.add_argument('--all', action='store_true')
    p.add_argument('--out', type=Path, required=True, help='A new output directory')
    a = p.parse_args()
    if a.out.exists(): p.error('Output directory already exists; choose a new one')
    manifest = json.loads((ROOT/'replay-materials/replay-manifest.json').read_text())
    rows = manifest['records'] if isinstance(manifest, dict) else manifest
    selected = [r for r in rows if a.all or r['case'] in a.case]
    if not selected or (a.case and set(a.case) != {r['case'] for r in selected}):
        p.error('Unknown case; use IDs in replay-manifest.json')
    actual = subprocess.check_output(['docker','image','inspect','--format','{{.Id}}',IMAGE], text=True).strip()
    if actual != IMAGE: raise RuntimeError('Fixed local Docker image is required; no image will be pulled')
    a.out.mkdir(parents=True)
    out = a.out.resolve()
    archive_info=json.loads((ROOT/'judge-archive.json').read_text())
    joined=out/'judge-source.tar.gz'
    digest=hashlib.sha256()
    with joined.open('wb') as target:
        for part in archive_info['parts']:
            data=(ROOT/part['name']).read_bytes()
            if len(data)!=part['size']: raise ValueError('Judge archive part size mismatch')
            digest.update(data);target.write(data)
    if digest.hexdigest()!=archive_info['sha256']: raise ValueError('Judge archive hash mismatch')
    with tarfile.open(joined) as t:
        t.extractall(out/'judge', filter='data')
    for r in selected:
        archive = ROOT/'replay-materials'/r['zip_relative_path']
        if hashlib.sha256(archive.read_bytes()).hexdigest() != r['zip_sha256']:
            raise RuntimeError('Archive identity mismatch: '+r['case'])
        destination = out/'cases'/r['case']
        with zipfile.ZipFile(archive) as z:
            for n in z.namelist():
                if not (destination/n).resolve().is_relative_to(destination.resolve()):
                    raise ValueError('Unsafe archive path')
            z.extractall(destination)
    (out/'selected.json').write_text(json.dumps(selected,ensure_ascii=False,indent=2))
    shutil.copy2(ROOT/'score_batch.py',out/'score_batch.py')
    command = ['docker','run','--rm','--pull','never','--network','none',
        '--name','new6-review-'+uuid.uuid4().hex[:10],'--cpus','1','--memory','3g','--read-only',
        '--tmpfs','/tmp:rw,exec,size=1g','-e','PYTHONDONTWRITEBYTECODE=1','-e','HOME=/tmp',
        '-v',str(out/'judge')+':/workspace:ro','-v',str(out/'cases')+':/cases:ro',
        '-v',str(out)+':/results',IMAGE,'python','/results/score_batch.py']
    (out/'invocation.json').write_text(json.dumps({'image':IMAGE,'judge_commit':'34374f08f331e7184010c40b401f1630a49df394',
        'case_ids':[r['case'] for r in selected],'network':'none','agent_calls':0,'api_calls':0},indent=2))
    result = subprocess.run(command)
    raise SystemExit(result.returncode)

if __name__ == '__main__': main()

"""Maintainer command: explicitly freeze the currently reviewed code and data."""
import hashlib
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--release',default='new6-20260905-repro-v1');args=parser.parse_args()
    suite = json.loads((ROOT / 'repro/suite.json').read_text())
    paths = set((ROOT / 'common').glob('*.py'))
    for name in ('score.py', 'reproduce.py', 'suite.json', 'Dockerfile', 'requirements.txt'):
        paths.add(ROOT / 'repro' / name)
    roots = {ROOT / c['task_root'] for c in suite['cases']}
    for task in roots:
        paths.update(task / n for n in ('instruction.md', 'rubric.json'))
        paths.update((task / 'tests').glob('*.py'))
        paths.update((task / 'metadata').glob('*.py'))
        paths.update((task / 'metadata').glob('*.json'))
        paths.update((task / 'metadata').glob('*.xlsx'))
        for folder in ('data', 'solution', 'metadata/source', 'metadata/source_recalculated'):
            paths.update(p for p in (task / folder).rglob('*') if p.is_file())
        common = task.parents[1] / 'common'
        paths.update(common.glob('*.py'))
    for case in suite['cases']:
        answer = ROOT / case['answer']
        if case['expected']['status'] != 'OUTPUT_MISSING':
            if not answer.is_file():
                raise ValueError('Required answer or fixture missing: ' + str(answer))
            paths.add(answer)
        paths.update(p for p in (ROOT / case['input_dir']).rglob('*') if p.is_file())
    paths.update(p for p in (ROOT / 'repro/samples').rglob('*') if p.is_file())
    files = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in sorted(paths) if p.is_file() and not p.name.endswith(".inspect.ndjson")}
    manifest = {'release': args.release, 'files': files,
                'python_packages': {'openpyxl': '3.1.5', 'et-xmlfile': '2.0.0', 'lxml': '6.0.1'},
                'engine': 'LibreOffice 7.4.7.2', 'api_calls': 0,
                'policy': 'Changing facts, weights or code requires reviewed versioning and fresh calibration; never regenerate this merely to hide a failing check.'}
    (ROOT / 'repro/manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    print('Frozen', len(files), 'code/data/input/answer files')


if __name__ == '__main__':
    main()

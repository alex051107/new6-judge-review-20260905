"""Offline entry point; task evaluators, not this runner, define business facts."""
import argparse
from decimal import Decimal
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'common'))
from runtime import recalculate_xlsx
PROFILES = ('capability_first', 'balanced', 'ongoing_use')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def preflight():
    lock = json.loads((ROOT / 'repro/manifest.json').read_text())
    for name, expected in lock['files'].items():
        path = ROOT / name
        if not path.is_file() or digest(path) != expected:
            raise ValueError('Release file missing or changed: ' + name)
    versions = {name: importlib.metadata.version(name) for name in ('openpyxl', 'et-xmlfile', 'lxml')}
    for name, expected in lock['python_packages'].items():
        if versions[name] != expected:
            raise ValueError(f'Runtime mismatch: {name} {versions[name]} != {expected}')
    lo = subprocess.check_output(['libreoffice', '--version'], text=True).strip()
    if not lo.startswith('LibreOffice 7.4.7.2 '):
        raise ValueError('Unvalidated recalculation engine: ' + lo)
    return {'python': platform.python_version(), 'machine': platform.machine(),
            'libreoffice': lo, 'packages': versions, 'manifest_sha256': digest(ROOT / 'repro/manifest.json')}


def run_case(case, out):
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    task = (ROOT / case['task_root']).resolve()
    answer = (ROOT / case['answer']).resolve()
    inputs = (ROOT / case['input_dir']).resolve()
    original_hash = digest(answer) if answer.is_file() else None
    actual = answer
    native = None
    # Static B tasks accept constants and formulas. Recompute formulas in an
    # isolated copy so cached values cannot conceal incorrect computation.
    if case['task'].startswith('B') and answer.is_file() and zipfile.is_zipfile(answer):
        with zipfile.ZipFile(answer) as book:
            has_formulas = any(re.search(rb'<(?:\w+:)?f(?:\s|>)', book.read(n))
                               for n in book.namelist() if n.startswith('xl/worksheets/') and n.endswith('.xml'))
        if has_formulas:
            try:
                actual, native = recalculate_xlsx(answer, out / 'native', timeout=120)
            except Exception as exc:
                result = {'evaluation_status': 'JUDGE_ERROR', 'normalized_score': None,
                          'pass': None, 'evidence': {'native_error': str(exc)}}
                (out / 'result.json').write_text(json.dumps(result, indent=2))
                return result
    args = [sys.executable, str(task / 'tests/evaluate.py'), str(actual), '--input-dir', str(inputs)]
    if case['task'] == 'A1':
        args += ['--work-dir', str(out / 'native')]
    elif case['task'] in ('A2', 'C1'):
        args += ['--evidence-dir', str(out / 'native'), '--completed-run']
    elif case['task'] == 'C2':
        args = [sys.executable, str(task / 'tests/evaluate.py'), str(actual),
                '--out', str(out / 'native'), '--completed-run']
    proc = subprocess.run(args, cwd=task, capture_output=True, text=True, timeout=600, env=dict(os.environ, NEW6_EVIDENCE_DIR=str(out / 'native')))
    (out / 'stdout.txt').write_text(proc.stdout)
    (out / 'stderr.txt').write_text(proc.stderr)
    if proc.returncode and not (proc.returncode == 2 and json.loads(proc.stdout).get('evaluation_status') == 'JUDGE_ERROR'):
        raise RuntimeError(f'Evaluator exited {proc.returncode}; see {out}/stderr.txt')
    result = json.loads(proc.stdout)
    if case['task'] == 'C2' and (out / 'native/result.json').is_file():
        result = json.loads((out / 'native/result.json').read_text())
    if original_hash and digest(answer) != original_hash:
        raise RuntimeError('Original submission changed')
    result['reproduction'] = {'task_root': case['task_root'], 'original_sha256': original_hash,
                              'original_unchanged': True, 'native_preprocessing': native,
                              'api_calls': 0}
    (out / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2))
    return result


def assert_result(case, result):
    expected = case['expected']
    status = result.get('evaluation_status')
    if status != expected['status']:
        raise AssertionError(f"{case['id']}: status {status} != {expected['status']}")
    if status != 'SCORED':
        if status in ('OUTPUT_MISSING','MALFORMED_OUTPUT'):
            assert result.get('normalized_score') == 0 and result.get('pass') is False, 'Missing/malformed delivery must score zero'
            for profile in result.get('profiles',{}).values():
                assert profile.get('normalized_score') == 0 and profile.get('pass') is False
        else:
            assert result.get('normalized_score') is None and result.get('pass') is None, 'Pending result must not be zero'
        return
    facts = result['criterion_scores']
    assert set(result['profiles']) == set(PROFILES)
    for name, profile in result['profiles'].items():
        assert profile['criterion_scores'] == facts, 'Profiles must share the same facts'
        value = Decimal(profile['score_decimal'])
        assert profile['pass'] == (value >= Decimal('.70')), 'Unrounded threshold contract changed'
        if 'profiles' in expected:
            assert abs(value - Decimal(expected['profiles'][name])) <= Decimal('1e-12'), f'{name}: {value}'
    for key in expected.get('lose', []):
        assert Decimal(str(facts[key])) < 1, f'{key} should lose credit'
    for key in expected.get('preserve', []):
        assert Decimal(str(facts[key])) == 1, f'{key} should retain credit'
    for key, value in expected.get('facts', {}).items():
        assert abs(Decimal(str(facts[key])) - Decimal(str(value))) <= Decimal('1e-12'), key


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['verify', 'score'])
    parser.add_argument('--suite', choices=['all', 'reference', 'actual', 'calibration'], default='all')
    parser.add_argument('--repeat', type=int, default=1)
    parser.add_argument('--task', choices=['A1', 'A2', 'B1', 'B2', 'C1', 'C2'])
    parser.add_argument('--answer')
    parser.add_argument('--input-dir')
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    if not 1 <= args.repeat <= 3:
        parser.error('--repeat must be 1..3')
    runtime = preflight()
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    if any(out.iterdir()):
        parser.error('Output directory must be empty; previous evidence is never overwritten')
    suite = json.loads((ROOT / 'repro/suite.json').read_text())
    if args.mode == 'score':
        if not all((args.task, args.answer, args.input_dir)):
            parser.error('score requires --task, --answer and original post-run --input-dir')
        case = {'id': 'submission', 'task': args.task, 'task_root': suite['tasks'][args.task],
                'answer': args.answer, 'input_dir': args.input_dir}
        result = run_case(case, out / 'submission')
        (out / 'runtime.json').write_text(json.dumps(runtime, indent=2))
        print(json.dumps(result, ensure_ascii=False))
        return 0 if result['evaluation_status'] == 'SCORED' else 2
    cases = [c for c in suite['cases'] if args.suite == 'all' or c['suite'] == args.suite]
    if not cases:
        raise ValueError('Empty verification suite')
    checks = []
    for repetition in range(args.repeat):
        for case in cases:
            target = out / f"run-{repetition + 1}" / case['id']
            try:
                result = run_case(case, target)
                assert_result(case, result)
                check = {'id': case['id'], 'run': repetition + 1, 'passed': True,
                         'status': result['evaluation_status'], 'score': result.get('score_decimal')}
            except Exception as exc:
                check = {'id': case['id'], 'run': repetition + 1, 'passed': False,
                         'error': type(exc).__name__ + ': ' + str(exc)}
            checks.append(check)
            print(json.dumps(check), flush=True)
    receipt = {'passed': all(c['passed'] for c in checks), 'runtime': runtime,
               'case_count': len(cases), 'repeat': args.repeat, 'checks': checks, 'api_calls': 0}
    (out / 'receipt.json').write_text(json.dumps(receipt, indent=2))
    return 0 if receipt['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())

"""Harbor transport adapter. JSON status is authoritative for sample validity.

Numeric transport reward 0 for an unscored result is NOT a business score.
Such records carry sample_countable=false and normalized_score=null.
"""
import json
import math
from pathlib import Path
import subprocess
import sys


def main():
    tests = Path(__file__).resolve().parent
    adapter = json.loads((tests / 'adapter.json').read_text())
    task = tests / 'new6/tasks' / adapter['task_id']
    logs = Path('/logs/verifier')
    logs.mkdir(parents=True, exist_ok=True)
    # Stale rewards cannot survive a failed evaluator invocation.
    (logs / 'reward.txt').write_text('0\n')
    command = [sys.executable, str(task / 'tests/evaluate.py'), '/app/output/answer.xlsx', *adapter['extra_args']]
    try:
        proc = subprocess.run(command, capture_output=True, text=True, cwd=task, timeout=570)
    except subprocess.TimeoutExpired:
        result = {'evaluation_status':'JUDGE_ERROR', 'normalized_score':None,
                  'pass':None, 'sample_countable':False,
                  'error':'Evaluator exceeded its 570-second execution allowance',
                  'harbor_transport_reward_is_not_status':True}
        (logs / 'judge-result.json').write_text(json.dumps(result, indent=2))
        print(json.dumps(result))
        return
    (logs / 'judge-stdout.txt').write_text(proc.stdout)
    (logs / 'judge-stderr.txt').write_text(proc.stderr)
    try:
        result = json.loads(proc.stdout)
        status = result.get('evaluation_status', result.get('status'))
        if proc.returncode and status not in {'JUDGE_ERROR', 'NATIVE_RECALC_REQUIRED', 'TASK_INVALID', 'INFRA_ERROR'}:
            raise ValueError(f'Evaluator exited {proc.returncode} with inconsistent status')
        if status not in {'SCORED', 'OUTPUT_MISSING', 'MALFORMED_OUTPUT', 'JUDGE_ERROR', 'NATIVE_RECALC_REQUIRED', 'TASK_INVALID', 'INFRA_ERROR'}:
            raise ValueError('Unknown evaluation status')
        value = result.get('normalized_score')
        if status == 'SCORED':
            if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value) or not 0 <= value <= 1:
                raise ValueError('Invalid score')
            (logs / 'reward.txt').write_text(str(value) + '\n')
        elif value is not None:
            raise ValueError('Unscored evaluation must not carry a numerical score')
        result['sample_countable'] = status in {'SCORED', 'OUTPUT_MISSING', 'MALFORMED_OUTPUT'}
    except (ValueError, TypeError) as exc:
        result = {'evaluation_status': 'JUDGE_ERROR', 'normalized_score': None,
                  'pass': None, 'sample_countable': False, 'error': str(exc)}
    result['harbor_transport_reward_is_not_status'] = True
    (logs / 'judge-result.json').write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()

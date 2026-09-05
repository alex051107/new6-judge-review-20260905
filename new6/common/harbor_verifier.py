"""Harbor transport adapter. JSON status is authoritative for sample validity.

Confirmed delivery failures carry an outcome score of zero and remain countable.
Transport reward 0 for an unavailable evaluation is not an outcome score;
those records carry sample_countable=false and normalized_score=null.
"""
import json
import math
from pathlib import Path
import subprocess
import sys


def validate_result(result, returncode=0):
    """Validate status/score pairing, accepting old null delivery receipts as zero."""
    status = result.get('evaluation_status', result.get('status'))
    unavailable = {'JUDGE_ERROR', 'NATIVE_RECALC_REQUIRED', 'TASK_INVALID', 'INFRA_ERROR'}
    delivery = {'OUTPUT_MISSING', 'MALFORMED_OUTPUT'}
    if returncode and status not in unavailable:
        raise ValueError(f'Evaluator exited {returncode} with inconsistent status')
    if status not in unavailable | delivery | {'SCORED'}:
        raise ValueError('Unknown evaluation status')
    value = result.get('normalized_score')
    if status == 'SCORED':
        if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value) or not 0 <= value <= 1:
            raise ValueError('Invalid score')
    elif status in delivery:
        if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float)) or value != 0):
            raise ValueError('Delivery failure must have score zero')
        result.update(normalized_score=0.0, score_decimal='0', **{'pass':False},
                      outcome_policy_version='new6-outcome-v2-delivery-zero')
        for receipt in result.get('profiles', {}).values():
            if receipt.get('evaluation_status') != status:
                raise ValueError('Delivery profile status differs from overall status')
            validate_result(receipt)
    elif value is not None:
        raise ValueError('Unavailable evaluation must not carry a numerical score')
    result['sample_countable'] = status in {'SCORED'} | delivery
    return result


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
        result = validate_result(json.loads(proc.stdout), proc.returncode)
        if result['sample_countable']:
            (logs / 'reward.txt').write_text(str(result['normalized_score']) + '\n')
    except (ValueError, TypeError) as exc:
        result = {'evaluation_status': 'JUDGE_ERROR', 'normalized_score': None,
                  'pass': None, 'sample_countable': False, 'error': str(exc)}
    result['harbor_transport_reward_is_not_status'] = True
    (logs / 'judge-result.json').write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()

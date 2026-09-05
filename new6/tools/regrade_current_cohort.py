"""Score immutable current-cohort artifacts with frozen Judges; no API calls."""
import argparse
import json
from pathlib import Path
import subprocess
import time
import re

import run_current_version_campaign as c
import run_campaign_144 as r


def source_output_absent(trial):
    """A Docker source-path absence is delivery evidence, not transfer failure."""
    log = trial / 'trial.log'
    text = log.read_text(errors='replace') if log.exists() else ''
    return bool(re.search(r'Error response from daemon: Could not find the file /app/output in container [0-9a-f]+', text))


def snapshot(out, manifest, evidence, deadline):
    rows = c.records(manifest)
    results = []
    for row in rows:
        trial = Path(row['trial_dir'])
        key = row['task'] + '-' + row['system'] + f'-R{row["attempt"]:02d}'
        wrapper = Path(manifest.get('judge_overrides',{}).get(row['task'],manifest['frozen_wrappers'][row['task']]))
        if row['task'] in manifest.get('judge_overrides',{}):
            version = json.loads(next((wrapper/'tests/new6/tasks').glob('*/rubric.json')).read_text())['judge_version']
            dest = evidence / version / key
        else:
            dest = evidence / key
        receipt = dest / 'receipt.json'
        if receipt.exists():
            previous = json.loads(receipt.read_text())
            if previous['evaluation_status'] != 'RUN_OR_COLLECTION_PENDING' or not source_output_absent(trial):
                results.append(previous)
                continue
            (dest / 'receipt_before_source_absence_fix.json').write_text(receipt.read_text())
        # Completed Harbor receipts and successful collection establish the
        # delivery boundary. An API rejection is not a missing-file score.
        exception = (row.get('exception_info') or {}).get('exception_type')
        try:
            transfers = json.loads((trial / 'artifacts/manifest.json').read_text())
        except (OSError, ValueError):
            transfers = []
        delivered = next((x for x in transfers if x['source'] == '/app/output'), {})
        inputs = next((x for x in transfers if x['source'] == '/app/input'), {})
        proven_absent = source_output_absent(trial)
        transport_ok = (delivered.get('status') in ('ok', 'empty') or proven_absent) and inputs.get('status') == 'ok'
        dest.mkdir(parents=True, exist_ok=True)
        result = None
        if exception not in (None, 'AgentTimeoutError') or not transport_ok:
            status = 'RUN_OR_COLLECTION_PENDING'
        else:
            logs = dest / 'verifier'; logs.mkdir(exist_ok=True)
            command = ['docker', 'run', '--rm', '--cpus', '2', '--memory', '4g',
                '-v', str(wrapper / 'tests') + ':/tests:ro',
                '-v', str(trial / 'artifacts/app') + ':/app:ro',
                '-v', str(logs) + ':/logs/verifier',
                'new6-judge:20260905', 'python', '/tests/run_verifier.py']
            try:
                p = subprocess.run(command, capture_output=True, text=True, timeout=690)
                (dest / 'stdout.txt').write_text(p.stdout)
                (dest / 'stderr.txt').write_text(p.stderr)
                result = json.loads((logs / 'judge-result.json').read_text())
                status = result['evaluation_status']
            except (OSError, ValueError, subprocess.SubprocessError) as exc:
                status = 'JUDGE_EXECUTION_PENDING'
                result = {'error_type': type(exc).__name__}
        # The actual Qwen response identity is inconsistent; retain workbook
        # scores as diagnostic but do not call them verified qwen3.8-max samples.
        identity = 'PROVIDER_MODEL_IDENTITY_PENDING' if row['system'] == 'qwen' else 'REQUESTED_CONFIGURATION_RECORDED'
        item = {'task': row['task'], 'system': row['system'], 'attempt': row['attempt'],
                'trial': row['trial'], 'trial_dir': str(trial), 'generation': row['generation'],
                'evaluation_status': status, 'upstream_exception': exception,
                'artifact_collection_ok': transport_ok, 'system_identity': identity,
                'source_output_absence_confirmed': proven_absent,
                'raw_output_collection_status': delivered.get('status'),
                'score_decimal': (result or {}).get('score_decimal'),
                'profiles': (result or {}).get('profiles'), 'criterion_scores': (result or {}).get('criterion_scores'),
                'sample_countable': status in ('SCORED', 'OUTPUT_MISSING', 'MALFORMED_OUTPUT') and row['system'] != 'qwen',
                'api_calls': 0, 'scored_at': r.now(), 'receipt': str(dest / 'verifier/judge-result.json')}
        r.write(receipt, item)
        results.append(item)
        r.write(out / 'current_scores.json', {'updated_at': r.now(), 'expected_cohort_slots': 144,
                'scored_or_classified': len(results), 'records': results, 'difficulty_qualified': False,
                'deferred_task_slots': manifest.get('deferred_task_slots', {}), 'api_calls': 0})
        print(json.dumps({k:item[k] for k in ('task','system','attempt','evaluation_status','score_decimal')}), flush=True)
        if time.monotonic() >= deadline:
            break
    r.write(out / 'current_scores.json', {'updated_at': r.now(), 'expected_cohort_slots': 144,
            'scored_or_classified': len(results), 'records': results, 'difficulty_qualified': False,
            'deferred_task_slots': manifest.get('deferred_task_slots', {}), 'api_calls': 0})
    return len(results), len(rows)


def main():
    p = argparse.ArgumentParser(); p.add_argument('--out', type=Path, required=True)
    p.add_argument('--watch-hours', type=float, default=8)
    a = p.parse_args(); out = a.out.resolve()
    evidence = out / 'regrade'; evidence.mkdir(exist_ok=True)
    fd = __import__('os').open(out / 'regrade.lock', __import__('os').O_CREAT | __import__('os').O_EXCL | __import__('os').O_WRONLY, 0o600)
    __import__('os').close(fd)
    deadline = time.monotonic() + a.watch_hours * 3600
    while time.monotonic() < deadline:
        manifest = json.loads((out / 'campaign.json').read_text())
        n, available = snapshot(out, manifest, evidence, deadline)
        planned = manifest['expected_trials']
        if n == available == planned:
            break
        time.sleep(60)
    r.write(out / 'regrade-finish.json', {'finished_at':r.now(),'api_calls':0,'scored_or_classified':n,
                                       'expected_ready_slots':planned,'difficulty_qualified':False})


if __name__ == '__main__':
    main()

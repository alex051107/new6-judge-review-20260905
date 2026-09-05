"""Run the current six-task cohort using Harbor and immutable compatible trials.

B2 v3 and C1 v2 use new generations. Four unchanged task contracts retain their
original eight scheduled attempts per system, including unsuccessful attempts.
The initial prepare stage records the earlier five-task reuse plan; selecting
C1 v2 replaces its compatible slots with a separately prepared 24-slot subset.
This is a bounded campaign adapter, not a new execution harness.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

import run_campaign_144 as r
from build_harbor import build

ROOT = r.ROOT
OLD = ROOT / 'campaigns/new6-144-v1/runtime-six'
TASKS = json.loads((ROOT / 'repro/suite.json').read_text())['tasks']
TASKS['B2'] = 'candidates/b2-three-release-v3/tasks/NEW6-B-LABOUR-BRIEF-001'
CONCURRENCY = {'codex': 1, 'claude': 2, 'qwen': 1}
HARBOR = str(Path.home() / '.local/bin/harbor')


def file_set(path):
    return {str(p.relative_to(path)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in path.rglob('*') if p.is_file() and p.name != '.DS_Store'}


def prepare(out):
    out.mkdir(parents=True, exist_ok=False)
    old = json.loads((OLD / 'campaign.json').read_text())
    compatibility = []
    frozen = {}
    # One import hash per visible file: prevent counting a changed task as reuse.
    for alias, rel in TASKS.items():
        task = ROOT / rel
        wrapper = build(task.name, out / 'frozen', task.parent,
                        'new6-agent:20260905', 'new6-judge:20260905')
        frozen[alias] = str(wrapper)
        if alias == 'B2':
            continue
        target = {'instruction': hashlib.sha256((task / 'instruction.md').read_bytes()).hexdigest(),
                  'inputs': file_set(task / 'data/input_files')}
        for slot in (s for s in old['slots'] if s['task'] == alias):
            cfg = json.loads(Path(old['lanes'][slot['system']]['config']).read_text())
            source = next(Path(t['path']) for t in cfg['tasks'] if Path(t['path']).name == slot['prefix'])
            actual = {'instruction': hashlib.sha256((source / 'instruction.md').read_bytes()).hexdigest(),
                      'inputs': file_set(source / 'environment/input')}
            assert actual == target, f'Changed generation contract: {slot["prefix"]}'
            assert (source / 'environment/Dockerfile').read_text() == (wrapper / 'environment/Dockerfile').read_text()
            compatibility.append({**slot, 'mode': 'existing_unchanged_generation',
                                  'wrapper': str(source), 'visible_contract': target})
    slots, lanes = [], {}
    for system in CONCURRENCY:
        previous = json.loads(Path(old['lanes'][system]['config']).read_text())
        agent = previous['agents'][0]
        agent['n_concurrent'] = CONCURRENCY[system]
        paths, prefixes = [], {}
        for attempt in range(1, 9):
            prefix = f'N6V3-B2-{system.upper()}-R{attempt:02d}'
            wrapper = out / system / 'tasks' / prefix
            shutil.copytree(Path(frozen['B2']), wrapper, copy_function=os.link)
            toml = wrapper / 'task.toml'
            content = toml.read_text().replace('alex051107/new6-b-labour-brief-001', 'alex051107/' + prefix.lower())
            toml.unlink()
            toml.write_text(content)
            paths.append({'path': str(wrapper)})
            prefixes[prefix] = 'B2'
            slots.append({'task': 'B2', 'system': system, 'attempt': attempt, 'prefix': prefix,
                          'task_version_path': TASKS['B2'], 'mode': 'new_generation'})
        cfg = {'job_name': 'new6-current-v3-' + system, 'jobs_dir': str(out / system / 'jobs'),
               'n_attempts': 1, 'n_concurrent_trials': CONCURRENCY[system],
               'retry': {'max_retries': 0}, 'agents': [agent], 'tasks': paths,
               'environment': {'type': 'docker', 'delete': True}}
        path = out / system / 'job.json'
        r.write(path, cfg)
        lanes[system] = {'config': str(path), 'jobs_dir': cfg['jobs_dir'], 'prefixes': prefixes,
                         'model': agent['model_name'], 'concurrency': CONCURRENCY[system]}
    assert len(compatibility) == 120 and len(slots) == 24
    manifest = {'campaign': 'new6-current-v3-144', 'source_commit': subprocess.check_output(
        ['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(), 'created_at': r.now(),
        'expected_trials': 144, 'new_trials': 24, 'reused_trials': 120,
        'task_roots': TASKS, 'frozen_wrappers': frozen, 'lanes': lanes, 'slots': slots,
        'compatible_slots': compatibility, 'old_runtime': str(OLD),
        'max_new_concurrent': 4, 'max_global_agent_concurrent': 8,
        'max_agent_seconds': 1200, 'per_task_monitored_stop_usd': 10, 'retries': 0,
        'profile': 'capability_first', 'pass_threshold_unrounded': '0.70',
        'development_pilot_excluded': 'N6B2T-CLAUDE-01__uRTrBVY',
        'difficulty_qualified': False,
        'authorization': '2026-09-05 user requested current six tasks, three established systems x eight, faster parallel execution. Same USD10 monitored stop and 20min/task; retain failures; no automatic retries.',
        'validation_budget': {'preparation_contract_check': 1, 'packaged_B2_reference': 1,
                              'independent_review': 0, 'full_unchanged_calibration_reruns': 0}}
    r.write(out / 'campaign.json', manifest)
    return manifest


def records(manifest):
    rows = []
    old_results = json.loads((OLD / 'exact_results.json').read_text())
    reused = {(x['task'], x['system'], x['attempt']) for x in manifest['compatible_slots']}
    for row in old_results['records']:
        if (row['task'], row['system'], row['attempt']) in reused:
            rows.append({**row, 'generation': 'existing_unchanged_generation'})
    for system, lane in manifest['lanes'].items():
        files = [p for directory in [lane['jobs_dir'], *lane.get('additional_jobs_dirs',[])]
                 for p in Path(directory).glob('*/*/result.json')]
        for p in files:
            if p.parent.name in manifest.get('excluded_environment_setup_trials',[]):
                continue
            try:
                cfg = json.loads((p.parent / 'config.json').read_text())
                result = json.loads(p.read_text())
            except (OSError, ValueError):
                continue
            prefix = Path(cfg['task']['path']).name
            if prefix not in lane['prefixes']:
                continue
            slot = next(s for s in manifest['slots'] if s['prefix'] == prefix)
            rows.append({'system': system, 'task': slot['task'], 'attempt': slot['attempt'],
                         'trial': p.parent.name, 'trial_dir': str(p.parent),
                         'finished_at': result.get('finished_at'),
                         'exception_info': result.get('exception_info'),
                         'generation': 'new_generation'})
    for subset in manifest.get('external_subsets', []):
        rows.extend(records(json.loads(Path(subset).read_text())))
    keys = [(x['task'], x['system'], x['attempt']) for x in rows]
    assert len(set(keys)) == len(keys), 'Duplicate cohort slot'
    return rows


def prepare_subset(out, alias, task):
    """Append a newly calibrated task without restarting any existing queue."""
    out.mkdir(parents=True, exist_ok=False)
    old = json.loads((OLD / 'campaign.json').read_text())
    wrapper = build(task.name, out / 'frozen', task.parent,
                    'new6-agent:20260905', 'new6-judge:20260905')
    slots, lanes = [], {}
    for system, concurrency in CONCURRENCY.items():
        previous = json.loads(Path(old['lanes'][system]['config']).read_text())
        agent = previous['agents'][0]; agent['n_concurrent'] = concurrency
        paths, prefixes = [], {}
        for attempt in range(1, 9):
            prefix = f'N6{alias}V2-{system.upper()}-R{attempt:02d}'
            dest = out / system / 'tasks' / prefix
            shutil.copytree(wrapper, dest, copy_function=os.link)
            toml = dest / 'task.toml'; content = toml.read_text().replace('alex051107/' + task.name.lower(), 'alex051107/' + prefix.lower())
            toml.unlink(); toml.write_text(content)
            paths.append({'path': str(dest)}); prefixes[prefix] = alias
            slots.append({'task': alias, 'system': system, 'attempt': attempt, 'prefix': prefix,
                          'task_version_path': str(task.relative_to(ROOT)), 'mode': 'new_generation'})
        cfg = {'job_name': f'new6-{alias.lower()}-revision-v2-' + system,
               'jobs_dir': str(out / system / 'jobs'), 'n_attempts': 1,
               'n_concurrent_trials': concurrency, 'retry': {'max_retries': 0},
               'agents': [agent], 'tasks': paths, 'environment': {'type':'docker','delete':True}}
        path = out / system / 'job.json'; r.write(path,cfg)
        lanes[system] = {'config':str(path),'jobs_dir':cfg['jobs_dir'],'prefixes':prefixes,
                         'model':agent['model_name'],'concurrency':concurrency}
    manifest = {'campaign':f'new6-{alias.lower()}-revision-v2-24', 'created_at':r.now(),
        'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'expected_trials':24,'new_trials':24,'reused_trials':0,'slots':slots,'lanes':lanes,
        'compatible_slots':[], 'frozen_wrappers':{alias:str(wrapper)},
        'task_roots':{alias:str(task.relative_to(ROOT))}, 'max_agent_seconds':1200,
        'per_task_monitored_stop_usd':10,'retries':0,'profile':'capability_first',
        'pass_threshold_unrounded':'0.70','difficulty_qualified':False,
        'authorization':'User selected C1 revised correspondence v2 and authorized three existing systems x eight attempts, after reference and calibration. Existing trials stay immutable.'}
    r.write(out/'campaign.json',manifest)
    return manifest


def launch(out, systems):
    m = json.loads((out / 'campaign.json').read_text())
    assert json.loads((out / 'reference_check.json').read_text())['passed']
    reserved = {}
    old_launch = json.loads((OLD / 'launch.json').read_text())
    reserved.update({pid:2 for pid in old_launch['pids'].values()})
    remaining = OLD / 'qwen/remaining-launch.json'
    if remaining.exists():reserved[json.loads(remaining.read_text())['pid']] = 2
    for launch_file in (ROOT / 'campaigns').glob('*/runtime/launch-*.json'):
        info = json.loads(launch_file.read_text())
        for system, pid in info.get('pids',{}).items():
            config_path = Path(info.get('configs',{}).get(system, str(launch_file.parent/system/'job.json')))
            config = json.loads(config_path.read_text())
            terminal = 0
            for result_path in (Path(config['jobs_dir'])/config['job_name']).glob('*/result.json'):
                try:terminal += bool(json.loads(result_path.read_text()).get('finished_at'))
                except (OSError, ValueError):pass
            remaining = max(0, len(config['tasks']) - terminal)
            reserved[pid] = min(info['concurrency'][system], remaining)
    proc_state = subprocess.run(['ps','-p',','.join(str(p) for p in reserved),'-o','pid=,stat='],capture_output=True,text=True)
    live_pids = {int(line.split()[0]) for line in proc_state.stdout.splitlines() if len(line.split()) == 2 and 'Z' not in line.split()[1]}
    active_count = sum(reserved[pid] for pid in live_pids)
    assert active_count + sum(m['lanes'][s]['concurrency'] for s in systems) <= 8, 'Wait for reserved global capacity; do not interrupt existing trials'
    # Verify enough Docker address-pool capacity before queuing any model task.
    networks = []
    try:
        for i in range(sum(m['lanes'][s]['concurrency'] for s in systems)):
            p = subprocess.run(['docker','network','create',f'new6-capacity-check-{os.getpid()}-{i}'],capture_output=True,text=True)
            if p.returncode:raise RuntimeError('Docker network capacity unavailable before agent launch: '+p.stderr[-300:])
            networks.append(p.stdout.strip())
    finally:
        for network in networks:subprocess.run(['docker','network','rm',network],capture_output=True,text=True)
    tag = '-'.join(sorted(systems))
    assert not any((out / ('launch-' + s + '.lock')).exists() for s in systems), 'This system already has a launch claim'
    for system in systems:
        fd = os.open(out / ('launch-' + system + '.lock'), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.write(fd, str(os.getpid()).encode()); os.close(fd)
    pricing = json.loads((OLD.parent / 'provider_preflight.json').read_text())
    os.environ[r.guard.KEYCHAIN_SERVICE_ENV] = 'excelbench-p15-zcloud-api-key'
    os.environ[r.guard.KEYCHAIN_ACCOUNT_ENV] = 'p15-zcloud-claude'
    key = r.guard.read_keychain_secret()
    env = dict(os.environ, OPENAI_API_KEY=key, ANTHROPIC_API_KEY=key)
    # Qwen logs live under the actual container HOME, not necessarily /root.
    native = r.guard.exec_live_probe
    def home_probe(cid, code, label):
        if label == 'Qwen':
            code = code.replace("'/root/.qwen/projects/**/*.jsonl'", "os.path.expanduser('~/.qwen/projects/**/*.jsonl')")
        return native(cid, code, label)
    r.guard.exec_live_probe = home_probe
    logs, processes, meters = [], {}, {}
    for system, lane in m['lanes'].items():
        if system not in systems:
            continue
        log = (out / (system + '-harbor.log')).open('w'); logs.append(log)
        cmd = [HARBOR, 'run', '-c', lane['config'], '--n-concurrent', str(lane['concurrency']), '--max-retries', '0']
        processes[system] = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT,
                                             env=env, start_new_session=True, cwd=ROOT.parent)
    keep = subprocess.Popen(['/usr/bin/caffeinate', '-i', '-w', str(os.getpid())])
    r.write(out / ('launch-' + tag + '.json'), {'started_at': r.now(), 'supervisor_pid': os.getpid(),
             'pids': {k: p.pid for k, p in processes.items()}, 'concurrency': {s:m['lanes'][s]['concurrency'] for s in systems},
             'configs':{s:m['lanes'][s]['config'] for s in systems},
             'existing_active_at_launch': active_count, 'new_calls_authorized': sum(len(json.loads(Path(m['lanes'][s]['config']).read_text())['tasks']) for s in systems),
             'caffeinate_pid': keep.pid, 'automatic_retries': 0})
    start = time.monotonic()
    original = r.guard.list_task_containers
    probes = {'codex': r.guard.codex_live_container_counts, 'claude': r.guard.claude_live_container_counts,
              'qwen': r.guard.qwen_live_container_counts}
    seen, last_provider_read = {}, 0
    while any(p.poll() is None for p in processes.values()):
        try:
            inventory = subprocess.check_output(['docker', 'ps', '--filter', 'label=com.docker.compose.project',
                         '--format', '{{.ID}}\t{{.Names}}\t{{.Label "com.docker.compose.project"}}'], text=True, timeout=20)
        except (subprocess.SubprocessError, OSError) as exc:
            r.write(out / ('inventory-warning-' + tag + '.json'), {'updated_at':r.now(),'error':type(exc).__name__})
            time.sleep(20)
            continue
        containers = [line.split('\t') for line in inventory.splitlines() if line]
        active = []
        for system, lane in m['lanes'].items():
            if system not in systems:
                continue
            for trial in Path(lane['jobs_dir']).glob('*/*'):
                if not trial.is_dir() or '__' not in trial.name or not (trial / 'config.json').exists():
                    continue
                try:
                    prefix = Path(json.loads((trial / 'config.json').read_text())['task']['path']).name
                except (OSError, ValueError):
                    continue
                if prefix not in lane['prefixes']:
                    continue
                suffix = trial.name.rsplit('__', 1)[1].lower()
                matches = {cid: {'name': name, 'project': project, 'running': True}
                           for cid, name, project in containers
                           if ('__' + suffix + '__') in project or project.endswith('__' + suffix)}
                if not matches:
                    continue
                active.append(trial.name)
                meter = meters.setdefault(trial.name, {'peak_estimated_usd': 0, 'stopped': False, 'probe_failures': 0})
                try:
                    r.guard.list_task_containers = lambda _prefix, matched=matches: matched
                    live = probes[system](prefix, set())
                    price = next(p for p in pricing['prices'] if p['model_name'] == lane['model'].removeprefix('openai/'))
                    meter.update(updated_at=r.now(), usage=live['usage'], container_ids=list(matches), probe_failures=0)
                    meter['peak_estimated_usd'] = max(meter['peak_estimated_usd'], r.cost(live['usage'], price, system, pricing['quota_per_usd']))
                    if meter['peak_estimated_usd'] >= 10 and not meter['stopped']:
                        meter['stop_receipts'] = [r.stop_agent(c) for c in matches]; meter['stopped'] = True
                except Exception as exc:
                    meter['probe_failures'] += 1; meter['monitor_error'] = type(exc).__name__
                    if meter['probe_failures'] >= 3 and not meter['stopped']:
                        meter['stop_receipts'] = [r.stop_agent(c) for c in matches]; meter['stopped'] = True
                finally:
                    r.guard.list_task_containers = original
        try:
            shared = OLD / 'provider_requests.json'
            if time.time() - shared.stat().st_mtime < 120:
                ledger = json.loads(shared.read_text())
                seen.update({row['request_id']: row for row in ledger['rows']})
                r.write(out / ('provider_requests-' + tag + '.json'), ledger)
            elif time.monotonic() - last_provider_read > 60:
                account = r.provider_read(key, seen); last_provider_read = time.monotonic()
                r.write(out / ('provider_requests-' + tag + '.json'), {'updated_at': r.now(), 'rows': list(seen.values()),
                       'account': account, 'quota_per_usd': pricing['quota_per_usd'], 'attribution': 'Shared ledger; exact trial attribution pending.'})
        except Exception as exc:
            r.write(out / ('provider_warning-' + tag + '.json'), {'updated_at': r.now(), 'error': type(exc).__name__})
        rs = records(m)
        r.write(out / ('status-' + tag + '.json'), {'updated_at': r.now(), 'expected_trials': m['expected_trials'],
                'terminal_trials': len(rs), 'new_terminal_trials': sum(x['generation'] == 'new_generation' for x in rs),
                'active_new_trials': active, 'lane_exit_codes': {k: p.poll() for k, p in processes.items()},
                'meters': meters, 'records': rs, 'difficulty_qualified': False})
        if time.monotonic() - start > 8 * 3600 or (out / 'STOP').exists():
            for p in processes.values():
                if p.poll() is None: p.terminate()
            break
        time.sleep(20)
    for log in logs: log.close()
    r.write(out / ('finish-' + tag + '.json'), {'finished_at': r.now(), 'lane_exit_codes': {k: p.poll() for k, p in processes.items()},
                                'new_trials_terminal': sum(x['generation'] == 'new_generation' for x in records(m)),
                                'automatic_retries': 0, 'meters': meters})


def main():
    p = argparse.ArgumentParser()
    p.add_argument('mode', choices=['prepare', 'prepare-subset', 'launch'])
    p.add_argument('--out', required=True, type=Path)
    p.add_argument('--systems', nargs='+', choices=list(CONCURRENCY), default=list(CONCURRENCY))
    p.add_argument('--task', choices=['C1'])
    p.add_argument('--task-root', type=Path)
    a = p.parse_args()
    if a.mode == 'prepare':
        m = prepare(a.out.resolve())
        print(json.dumps({'prepared': 144, 'new_generations': 24, 'compatible_existing_slots': 120}))
    elif a.mode == 'prepare-subset':
        if not a.task or not a.task_root:p.error('prepare-subset requires --task and --task-root')
        m = prepare_subset(a.out.resolve(),a.task,a.task_root.resolve())
        print(json.dumps({'prepared':len(m['slots']),'task':a.task,'api_calls':0}))
    else:
        launch(a.out.resolve(), a.systems)


if __name__ == '__main__':
    main()

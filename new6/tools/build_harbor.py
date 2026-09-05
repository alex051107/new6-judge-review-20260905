"""Materialize NEW6 using the existing separate-verifier Harbor boundary.

Agent image gets only instruction and visible input files. The original
post-agent input directory is collected as an artifact for protection checks.
This command packages tasks; it never calls a model.
"""
import argparse
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]


def copy_tree(source, destination):
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns(
        '__pycache__', 'node_modules', '*.pyc', '*.log', '*.png', '*.inspect.ndjson',
        'fixtures', 'validation', 'calibration', 'profile', 'recalc', 'recalculations',
        'source_recalc'), dirs_exist_ok=True)


def build(task_id, out, task_root=None, runtime_image="p15-new6-runtime:v1", verifier_image="p15-new6-runtime:v1"):
    task = (task_root or ROOT / 'tasks') / task_id
    for required in ('instruction.md', 'rubric.json', 'tests/evaluate.py',
                     'metadata/source_manifest.json', 'metadata/oracle_recompute.py',
                     'solution/reference.xlsx'):
        if not (task / required).is_file():
            raise ValueError(f'BUILD_PENDING: {task_id} missing {required}')
    target = out / task_id
    if target.exists():
        raise FileExistsError(f'Keep existing wrapper immutable: {target}')
    env, tests = target / 'environment', target / 'tests'
    env.mkdir(parents=True); tests.mkdir()
    shutil.copy2(task / 'instruction.md', target / 'instruction.md')
    shutil.copytree(task / 'data/input_files', env / 'input')
    (env / 'Dockerfile').write_text(f'FROM {runtime_image}\nWORKDIR /app\nCOPY input/ /app/input/\n')
    private_task = tests / 'new6/tasks' / task_id
    copy_tree(task, private_task)
    copy_tree(ROOT / 'common', tests / 'new6/common')
    lane = task_id.split('-')[1].lower()
    copy_tree(ROOT / f'sources/downloads_{lane}', tests / f'new6/sources/downloads_{lane}')
    shutil.copy2(ROOT / 'sources/source_manifest.json', tests / 'new6/sources/source_manifest.json')
    (tests / 'Dockerfile').write_text(f'FROM {verifier_image}\nWORKDIR /app\nCOPY . /tests\n')
    adapter = task / 'metadata/harbor_adapter.json'
    extra_args = json.loads(adapter.read_text()).get('evaluator_args', []) if adapter.exists() else []
    (tests / 'adapter.json').write_text(json.dumps({'task_id': task_id, 'extra_args': extra_args}))
    (tests / 'new6/repro').mkdir()
    shutil.copy2(ROOT / 'repro/score.py', tests / 'new6/repro/score.py')
    shutil.copy2(ROOT / 'repro/harbor_verifier.py', tests / 'run_verifier.py')
    (tests / 'test.sh').write_text('#!/bin/sh\nset -eu\nexec python /tests/run_verifier.py\n')
    (tests / 'test.sh').chmod(0o755)
    (target / 'task.toml').write_text(f'''schema_version = "1.4"
artifacts = ["/app/output", "/app/input"]
[task]
name = "alex051107/{task_id.lower()}"
version = "0.1.0"
description = "NEW6 source-based reconstructed task"
[metadata]
task_id = "{task_id}"
track = "{lane.upper()}"
status = "BUILT_REFERENCE_AND_CALIBRATION_VERIFIED"
difficulty_calibrated = false
benchmark_authored_instruction = true
[agent]
timeout_sec = 1200.0
[environment]
network_mode = "public"
os = "linux"
workdir = "/app"
cpus = 2
memory_mb = 4096
[verifier]
timeout_sec = 600.0
environment_mode = "separate"
network_mode = "public"
[verifier.environment]
network_mode = "public"
os = "linux"
workdir = "/app"
cpus = 2
memory_mb = 4096
''')
    return target


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('task_ids', nargs='+')
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--task-root', type=Path, help='Explicit frozen task tree; common runtime and sources remain shared')
    parser.add_argument("--runtime-image", default="new6-judge:20260905")
    parser.add_argument("--verifier-image", default="new6-judge:20260905")
    args = parser.parse_args()
    for task_id in args.task_ids:
        print(build(task_id, args.out.resolve(), args.task_root, args.runtime_image, args.verifier_image))

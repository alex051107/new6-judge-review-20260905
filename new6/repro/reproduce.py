"""Cross-platform stdlib launcher. Docker is the only host runtime dependency."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
IMAGE = 'new6-judge:20260905'


def main():
    p = argparse.ArgumentParser()
    p.add_argument('mode', choices=['build', 'verify', 'score'])
    p.add_argument('--suite', choices=['all', 'reference', 'actual', 'calibration'], default='all')
    p.add_argument('--repeat', type=int, default=1)
    p.add_argument('--task', choices=['A1', 'A2', 'B1', 'B2', 'C1', 'C2'])
    p.add_argument('--answer', type=Path)
    p.add_argument('--input-dir', type=Path)
    p.add_argument('--out', type=Path)
    a = p.parse_args()
    if a.mode == 'build':
        # Public base images need no registry credentials. Avoid an unrelated
        # desktop credential-helper prompt without changing the user's config.
        endpoint = subprocess.check_output(['docker', 'context', 'inspect', '--format',
                                            '{{.Endpoints.docker.Host}}'], text=True).strip()
        with tempfile.TemporaryDirectory(prefix='new6-docker-') as directory:
            Path(directory, 'config.json').write_text(json.dumps({'auths': {},
                'cliPluginsExtraDirs': [str(Path.home() / '.docker/cli-plugins')]}))
            env = dict(os.environ, DOCKER_CONFIG=directory, DOCKER_HOST=endpoint)
            return subprocess.call(['docker', 'build', '--progress=plain', '-t', IMAGE,
                                    str(ROOT / 'repro')], env=env)
    if a.out is None:
        p.error('--out is required and must be empty')
    output = a.out.resolve()
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        p.error('Output directory must be empty')
    command = ['docker', 'run', '--rm', '--network', 'none', '--read-only', '--cap-drop', 'ALL',
               '--security-opt', 'no-new-privileges', '--tmpfs', '/tmp:rw,exec,size=2g',
               '--mount', f'type=bind,source={REPO},target=/workspace,readonly',
               '--mount', f'type=bind,source={output},target=/results']
    # With capabilities dropped, root cannot bypass host-owned mount permissions.
    # Use the invoking account so Linux and Docker Desktop both write evidence safely.
    if hasattr(os, 'getuid'):
        command += ['--user', f'{os.getuid()}:{os.getgid()}']
    tail = [a.mode, '--out', '/results']
    if a.mode == 'score':
        if not a.task or a.answer is None or a.input_dir is None:
            p.error('score requires --task, --answer and --input-dir')
        answer, inputs = a.answer.resolve(), a.input_dir.resolve()
        if not answer.parent.is_dir() or not inputs.is_dir():
            p.error('Submission parent and post-run input directory must exist')
        command += ['--mount', f'type=bind,source={answer.parent},target=/candidate,readonly',
                    '--mount', f'type=bind,source={inputs},target=/candidate-input,readonly']
        tail += ['--task', a.task, '--answer', '/candidate/' + answer.name, '--input-dir', '/candidate-input']
    else:
        tail += ['--suite', a.suite, '--repeat', str(a.repeat)]
    command += [IMAGE, 'python', '/workspace/new6/repro/score.py', *tail]
    return subprocess.call(command)


if __name__ == '__main__':
    sys.exit(main())

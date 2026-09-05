"""NEW6 I/O and result envelope. No business rules or formula interpreter.

The task evaluator owns semantic discovery, fixed fact denominators and proof.
LibreOffice operates only on an isolated copy; it never rewrites a submission.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import zipfile
from lxml import etree as ET

try:
    from .score_facts import score
except ImportError:
    from score_facts import score


class RecalcUnavailable(RuntimeError):
    """Required recomputation was not proven; do not convert to a zero score."""


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def output_status(path):
    path = Path(path)
    if not path.is_file():
        return 'OUTPUT_MISSING'
    try:
        with zipfile.ZipFile(path) as z:
            if 'xl/workbook.xml' not in z.namelist():
                return 'MALFORMED_OUTPUT'
            if z.testzip() is not None:
                return 'MALFORMED_OUTPUT'
    except (OSError, zipfile.BadZipFile):
        return 'MALFORMED_OUTPUT'
    return None


def score_profiles(rubric, facts=None, *, status='SCORED', evidence=None):
    if isinstance(rubric, (str, Path)):
        rubric = json.loads(Path(rubric).read_text())
    profiles = {
        name: score(rubric, facts or {}, name, status)
        for name in rubric['profiles']
    }
    result = dict(profiles['capability_first'])
    result.update(task_id=rubric['task_id'], primary_profile='capability_first',
                  profiles=profiles, evidence=evidence or {})
    return result


def recalculate_xlsx(source, output_dir, timeout=90):
    """Return (fresh_xlsx_path, receipt) after real isolated LibreOffice recalc.

    Source may also be legacy XLS. Result presence is required; task-specific
    oracle parity and formula-error diagnosis are separate from engine success.
    All engine files and stdout/stderr are retained below output_dir.
    """
    source, output_dir = Path(source).resolve(), Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    engine = os.environ.get('NEW6_SOFFICE') or shutil.which('soffice') or shutil.which('libreoffice')
    if not engine:
        raise RecalcUnavailable('LibreOffice executable unavailable')
    run_dir = Path(tempfile.mkdtemp(prefix='recalc-', dir=output_dir))
    incoming, outgoing, profile = (run_dir / n for n in ('input', 'output', 'profile'))
    incoming.mkdir(); outgoing.mkdir(); profile.mkdir()
    isolated = incoming / source.name
    before = sha256(source)
    shutil.copy2(source, isolated)
    # Conversion alone can preserve valid-looking stale formula caches.
    # Invalidate caches only in the isolated OOXML copy and demand full calc.
    # Preserve source formulas, inputs, iteration settings and all other parts.
    cache_count = 0
    if zipfile.is_zipfile(isolated):
        ns = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
        parser = ET.XMLParser(resolve_entities=False, no_network=True)
        patched = isolated.with_name(isolated.name + '.tmp')
        with zipfile.ZipFile(isolated) as zin, zipfile.ZipFile(patched, 'w', zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                raw = zin.read(item.filename)
                if item.filename.startswith('xl/worksheets/') and item.filename.endswith('.xml'):
                    root = ET.fromstring(raw, parser)
                    changed = False
                    for formula in root.iter('{' + ns['s'] + '}f'):
                        cell = formula.getparent()
                        for value in cell.findall('s:v', ns):
                            cell.remove(value); cache_count += 1; changed = True
                    if changed:
                        raw = ET.tostring(root, encoding='utf-8', xml_declaration=True)
                elif item.filename == 'xl/workbook.xml':
                    root = ET.fromstring(raw, parser)
                    calc = root.find('s:calcPr', ns)
                    if calc is None:
                        calc = ET.SubElement(root, '{' + ns['s'] + '}calcPr')
                    calc.set('fullCalcOnLoad', '1'); calc.set('forceFullCalc', '1')
                    calc.set('calcMode', 'auto')
                    raw = ET.tostring(root, encoding='utf-8', xml_declaration=True)
                zout.writestr(item, raw)
        patched.replace(isolated)
    command = [engine, f'-env:UserInstallation={profile.as_uri()}', '--headless',
               '--convert-to', 'xlsx', '--outdir', str(outgoing), str(isolated)]
    receipt = {'source': str(source), 'source_sha256_before': before,
               'isolated_input': str(isolated), 'engine': engine, 'command': command,
               'status': 'NATIVE_RECALC_REQUIRED', 'cleared_formula_cache_count': cache_count,
               'isolated_input_sha256': sha256(isolated)}
    started = time.monotonic()
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
        (run_dir / 'stdout.txt').write_text(completed.stdout)
        (run_dir / 'stderr.txt').write_text(completed.stderr)
        receipt['returncode'] = completed.returncode
        output = outgoing / (source.stem + '.xlsx')
        if completed.returncode != 0 or not output.is_file():
            raise RecalcUnavailable(f'LibreOffice did not produce a workbook; see {run_dir}')
        receipt.update(status='RECALCULATED_PENDING_ORACLE_PARITY',
                       output=str(output), output_sha256=sha256(output))
    except subprocess.TimeoutExpired as exc:
        receipt['error'] = 'LibreOffice conversion timed out'
        raise RecalcUnavailable(receipt['error']) from exc
    finally:
        receipt['elapsed_seconds'] = time.monotonic() - started
        receipt['source_sha256_after'] = sha256(source)
        receipt['original_unchanged'] = receipt['source_sha256_after'] == before
        (run_dir / 'recalc_receipt.json').write_text(json.dumps(receipt, indent=2))
    if not receipt['original_unchanged']:
        raise RuntimeError('Original source changed during isolated recalculation')
    return output, receipt

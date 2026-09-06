"""Check explicit real-$m aliases and replay previously computed native evidence.

No Agent/API or native recalculation is invoked. The replay accepts only an
unchanged original plus identical generated probe XML and verified native output
hashes; missing/mismatched evidence aborts instead of generating a score.
"""
from pathlib import Path
import sys, json, argparse, zipfile
import openpyxl

TASK = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(TASK / 'tests'), str(TASK / 'metadata')]
import evaluate as judge
import layout_support


def reference_alias_check():
    w = openpyxl.load_workbook(TASK / 'solution/reference.xlsx', data_only=True)
    raw = openpyxl.load_workbook(TASK / 'solution/reference.xlsx', data_only=False)
    ctrl = judge.controls(w, formula_workbook=raw)
    before, facts_before, tables = judge.checks_for(w, control_bindings=ctrl)
    changed = []
    for table in tables:
        if table['kind'] != 'report':
            continue
        for c in w[table['sheet']][table['header_row']]:
            case, key = judge.case_metric(c.value)
            if key in ('investment', 'capital'):
                old = c.value
                c.value = f'{case.title()} {key} (real $m)'
                changed.append({'sheet': c.parent.title, 'cell': c.coordinate,
                                'before': old, 'after': c.value})
    assert len(changed) == 4, changed
    after, facts_after, _ = judge.checks_for(w, control_bindings=ctrl)
    assert facts_before == facts_after, 'Header-only alias changed candidate quantities'
    assert before == after, 'Equivalent header changed static facts or denominators'
    assert all(x['ok'] for key, items in after.items() if key != 'R004' for x in items)
    for label in ('Baseline capital (real $bn)', 'Scenario investment (nominal $m)',
                  'Scenario investment (real EURm)'):
        assert judge.case_metric(label)[1] is None, label
    return {'passed': True, 'changed_headers': changed,
            'facts_and_denominators_unchanged': True,
            'different_currency_scale_or_nominal_labels_not_coerced': True}


def same_zip_payload(first, second):
    with zipfile.ZipFile(first) as a, zipfile.ZipFile(second) as b:
        return sorted(a.namelist()) == sorted(b.namelist()) and all(
            a.read(name) == b.read(name) for name in a.namelist())


def run(prior_result, out, input_dir):
    out.mkdir(parents=True, exist_ok=False)
    check = reference_alias_check()
    prior = json.loads(prior_result.read_text())
    evidence = prior['evidence']
    assert evidence['judge_version'] == judge.JUDGE_VERSION
    records = [evidence['base_native_recalc']] + [
        p['receipt'] for p in evidence['dynamic_probes']]
    assert len(records) == 4
    # Reusing native evidence requires checking its provenance once, rather than
    # trusting stale cache paths. These are evidence-integrity checks, not recalcs.
    for r in records:
        assert r['original_unchanged'] and r['returncode'] == 0
        assert judge.sha256(r['source']) == r['source_sha256_before']
        assert judge.sha256(r['output']) == r['output_sha256']
    calls = []

    def replay(source, evidence_dir):
        index = len(calls)
        assert index < len(records), 'Unexpected extra native request'
        r = records[index]
        assert same_zip_payload(source, r['source']), 'Replay input differs from native input'
        calls.append({'source': str(source), 'native_source': r['source'],
                      'native_output': r['output']})
        receipt = dict(r, reused_native_evidence=True, replay_source=str(source))
        return Path(r['output']), receipt

    old_adapter = judge.recalculate_xlsx
    layout_support.INPUT_DIR = input_dir
    judge.recalculate_xlsx = replay
    try:
        result = judge.evaluate(Path(records[0]['source']), out / 'A2-codex-R07',
                                completed_run=True)
    finally:
        judge.recalculate_xlsx = old_adapter
    assert len(calls) == 4, result.get('evidence')
    assert result['evaluation_status'] == 'SCORED', result.get('evidence')
    for old, new in zip(evidence['dynamic_probes'], result['evidence']['dynamic_probes']):
        assert old['name'] == new['name'] and old['changes'] == new['changes']
    receipt = {'passed': True, 'judge_version': judge.JUDGE_VERSION,
               'reference_alias_check': check, 'api_calls': 0,
               'new_native_recalculations': 0, 'reused_native_recalculations': 4,
               'native_evidence_integrity_checks': 8,
               'source_and_probe_xml_unchanged': True,
               'prior_result': str(prior_result),
               'result_file': str(out / 'A2-codex-R07/evaluation.json'),
               'evaluation_status': result['evaluation_status'],
               'score_decimal': result['score_decimal'],
               'criterion_scores': result['criterion_scores'],
               'remaining_case': {'case': 'A2-codex-R01',
                                  'status': 'JUDGE_ERROR', 'score_decimal': None,
                                  'reason': 'Previous native source-load failure; no retry in this header-only check.'}}
    (out / 'receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2))
    print(json.dumps(receipt, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--prior-result', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--input-dir', type=Path, required=True)
    a = p.parse_args()
    run(a.prior_result.resolve(), a.out.resolve(), a.input_dir.resolve())

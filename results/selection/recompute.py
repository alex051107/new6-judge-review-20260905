#!/usr/bin/env python3
"""Summarize the published current 60% trial scores; never score Excel or call a model.

Usage: python3 new6-selection-recompute.py --repo-root REPO --output-dir OUT
All source references written to the outputs are relative to REPO.
"""
import argparse
import csv
import json
from collections import Counter, defaultdict
from decimal import Decimal, localcontext
from fractions import Fraction
from pathlib import Path

SOURCES = {
    'new6': 'results/current-effective-v2/trials.csv',
    'p15': 'results/ability-comparison-360-v1/trials.csv',
}
SUPPORT = [
    'results/current-effective-v2/SOURCE_NOTES.md',
    'results/current-effective-v2/stratified_summary.csv',
    'results/current-effective-v2/weights.json',
    'results/ability-comparison-360-v1/SOURCE_NOTES.md',
    'results/ability-comparison-360-v1/frozen_facts.json',
    'results/ability-comparison-360-v1/profiles.json',
]
SYSTEMS = ['GPT-5.6 sol', 'Opus 5', 'Qwen 3.8']
DISPLAY = {
    'codex': SYSTEMS[0], 'codex_gpt56sol': SYSTEMS[0],
    'claude': SYSTEMS[1], 'claude_opus5': SYSTEMS[1],
    'qwen': SYSTEMS[2], 'qwen38max': SYSTEMS[2],
}
KEY_TASKS = ['P15-B-FIN-RECON-001', 'C2', 'P15-A-POLICY-EIA-001']
TITLES = {
    'P15-B-FIN-RECON-001': '旧15 B 财务对账',
    'C2': 'NEW6 C2 邮政资费与报价',
    'P15-A-POLICY-EIA-001': '旧15 A 政策与排放情景',
}


def exact_text(value):
    if value is None:
        return None
    with localcontext() as context:
        context.prec = 60
        return str(Decimal(value.numerator) / Decimal(value.denominator))


def fmt(value):
    return '—' if value is None else f'{Decimal(value):.2f}'


def load_trials(root):
    records, excluded, seen = [], Counter(), set()
    for dataset, rel in SOURCES.items():
        with (root / rel).open(encoding='utf-8', newline='') as handle:
            rows = list(csv.DictReader(handle))
        for line, row in enumerate(rows, 2):
            if dataset == 'p15' and row['dataset'] != 'P15_V3':
                excluded[row['dataset']] += 1
                continue
            new = dataset == 'new6'
            task = row['task'] if new else row['task_id']
            trial = row['trial_id'] if new else row['trial_name']
            identity = (dataset, trial)
            if identity in seen:
                raise ValueError(f'Duplicate trial: {identity}')
            seen.add(identity)
            raw = row['focus60_points'] if new else row['focus_60']
            status = row['status']
            score = Fraction(raw) if raw else None
            scored_status = status == 'SCORED' if new else status in (
                'SCORED', 'SCORED_LEGACY_CONTRACT_FLAGGED')
            if scored_status != (score is not None):
                raise ValueError(f'Status/score mismatch at {rel}:{line}')
            if score is not None and not 0 <= score <= 100:
                raise ValueError(f'Score outside 0–100 at {rel}:{line}')
            passed = score >= 70 if score is not None else None
            recorded_pass = row['passing60'] if new else row['pass_60']
            if score is not None and recorded_pass.lower() != str(passed).lower():
                raise ValueError(f'Unrounded pass mismatch at {rel}:{line}')
            record = {
                'dataset': Path(rel).parent.name.upper().replace('-', '_') if new else 'P15_V3',
                'task': task, 'system': DISPLAY[row['system']],
                'source_system': row['system'], 'trial_id': trial,
                'status': status, 'score_60_points': raw or None,
                'passing_60': passed, 'source': rel, 'source_csv_line': line,
                'contract_issue': row.get('contract_issue') or None,
                '_score': score,
            }
            if new:
                for key in ('case', 'task_version', 'answer_sha256', 'config_id',
                            'requested_model', 'observed_model_ids',
                            'current_status', 'current_judge_label',
                            'selected_judge_label', 'selected_judge_commit',
                            'code_identity', 'fallback_relation',
                            'source_priority', 'technical_reason'):
                    record[key] = row.get(key) or None
                record['receipt'] = (
                    str(Path(rel).parent / row['receipt'])
                    if row.get('receipt') else None)
                if record['receipt'] and not (root / record['receipt']).is_file():
                    raise FileNotFoundError(record['receipt'])
            else:
                record['frozen_facts_source'] = SUPPORT[4]
                record['fact_lookup'] = {'dataset': 'P15_V3', 'trial_name': trial}
                record['judge_identity'] = 'Not certified by the comparison snapshot'
            records.append(record)
    return records, dict(excluded)


def summarize(records):
    grouped = defaultdict(list)
    for row in records:
        grouped[row['task'], row['system']].append(row)
    groups = []
    for (task, system), rows in sorted(grouped.items()):
        scores = [row['_score'] for row in rows if row['_score'] is not None]
        average = sum(scores) / len(scores) if scores else None
        groups.append({
            'task': task, 'system': system, 'slots': len(rows), 'n': len(scores),
            'unscored': len(rows) - len(scores),
            'mean_60_points': exact_text(average),
            'passes_60': sum(value >= 70 for value in scores) if scores else None,
            'mean_below_60': average < 60 if average is not None else None,
            'statuses': dict(Counter(row['status'] for row in rows)),
            'contract_flagged': any(row['contract_issue'] for row in rows),
            'pass_at_1': None, 'pass_at_8': None,
            'pass_k_reason': (
                'Source snapshot does not certify a complete population with '
                'homogeneous Judge, generation configuration and model identity; '
                'n<8 additionally prevents pass@8 estimation where applicable.'),
        })
    ranking = []
    for task in sorted({row['task'] for row in groups}):
        task_groups = [row for row in groups if row['task'] == task]
        valid = [row for row in task_groups if row['n']]
        averages = [Fraction(row['mean_60_points']) for row in valid]
        pooled = [row['_score'] for row in records
                  if row['task'] == task and row['_score'] is not None]
        ranking.append({
            'task': task, 'groups_with_scores': len(valid),
            'descriptive_mean_of_system_means': exact_text(sum(averages) / len(averages)),
            'descriptive_pooled_mean': exact_text(sum(pooled) / len(pooled)),
            'groups_below_60': sum(row['mean_below_60'] is True for row in valid),
            'contract_flagged': any(row['contract_flagged'] for row in task_groups),
            'formal_difficulty_accepted': None,
        })
    ranking.sort(key=lambda row: Fraction(row['descriptive_mean_of_system_means']))
    return groups, ranking


def markdown(audit):
    groups = {(r['task'], r['system']): r for r in audit['groups']}
    lines = ['# 当前候选题目与验收判断', '',
             '**现有结果尚不能确认有题目完成全部难度验收。** 当前均分不构成难度达标证明；以下依据最新千问重评及保留的其他系统评分事实。', '',
             '满分100；每格为均分（已评分份数；通过次数）。通过使用未舍入分数≥70。', '',
             '|题目|GPT-5.6 sol|Opus 5|Qwen 3.8|', '|---|---:|---:|---:|']
    for task in KEY_TASKS:
        cells=[]
        for system in SYSTEMS:
            r=groups[task,system]
            cells.append(f"{fmt(r['mean_60_points'])}（{r['n']}；{r['passes_60']}）" if r['n'] else '—')
        lines.append('|'+TITLES[task]+'|'+'|'.join(cells)+'|')
    low = [r['task'] for r in audit['descriptive_ranking_not_formal'] if r['groups_below_60']>=2]
    lines += ['', '按当前配重与最新结果，'+('有以下题目至少两个组均分低于60：'+ '、'.join(low) if low else '**没有题目同时有两个模型组均分低于60**')+'。', '',
              '- 财务对账：GPT-5.6 sol与千问均分略高于60，只有Opus低于60。',
              '- C2邮政资费与报价：千问最新均分为74.00（5份），旧58.77来自不同读取版本的旧快照，不能继续作为当前结论。',
              '- 政策与排放情景：全部24份存在旧合同来源单位/基线不一致问题，分数仅保留作诊断，不能作为修正后的验收证据。', '',
              '完整难度要求是逐题至少两个指定系统分别同时满足均分<60及Pass@8<70%，还需模型身份、可比配置与独立验收证据。正式Pass@1和Pass@8继续留空：目前未认证各组完整同Judge、同生成配置、模型身份的样本集。', '',
              'Pass@8按1−C(n−c,8)/C(n,8)计算，不是通过次数除以8。当n=8时，零次通过为0%，只要有一次通过就是100%。n不足8不能算正式Pass@8。', '',
              '## 分数最低的题目', '',
              '以下只在三个模型均已有分数的题目中，按三组均分等权排序，用于安排阅读顺序。它不是正式难度排名；样本覆盖和Judge并不统一，政策题还带合同缺陷。', '',
              '|次序|任务|三组均分的平均值|', '|---:|---|---:|']
    ranked=[r for r in audit['descriptive_ranking_not_formal'] if r['groups_with_scores']==3]
    for i,r in enumerate(ranked,1):lines.append(f"|{i}|{TITLES.get(r['task'],r['task'])}|{fmt(r['descriptive_mean_of_system_means'])}|")
    lines += ['', '## 全部逐题均分、数量及通过次数', '', '|任务|GPT-5.6 sol|Opus 5|Qwen 3.8|', '|---|---:|---:|---:|']
    for task in sorted({r['task'] for r in audit['groups']}):
        cells=[]
        for system in SYSTEMS:
            r=groups[task,system];cells.append(f"{fmt(r['mean_60_points'])}（{r['n']}；{r['passes_60']}）" if r['n'] else '—')
        lines.append('|'+task+'|'+'|'.join(cells)+'|')
    lines += ['', '## 来源', ''] + ['- `'+s+'`' for s in audit['sources']]
    lines += ['', '旧15只使用P15_V3，排除NEW6旧71份快照；新6题以本页指定当前目录为准。JSON保留逐次未舍入分数、状态、来源行号及可用回执身份。本脚本只做统计，不执行Judge或调用模型。', '']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo-root', type=Path, default=Path.cwd())
    parser.add_argument('--output-dir', type=Path, default=Path.cwd() / 'selection-audit')
    parser.add_argument('--new6-results', default='results/current-effective-v3',
                        help='Relative result directory; e.g. results/current-effective-v3')
    args = parser.parse_args()
    SOURCES['new6'] = args.new6_results.rstrip('/') + '/trials.csv'
    for i, source in enumerate(SUPPORT):
        SUPPORT[i] = source.replace('results/current-effective-v2', args.new6_results.rstrip('/'))
    records, excluded = load_trials(args.repo_root)
    groups, ranking = summarize(records)
    audit = {
        'profile': 'Current focus_60; no profile selection or weight change',
        'sources': list(SOURCES.values()) + SUPPORT,
        'records': [{key: value for key, value in row.items() if key != '_score'} for row in records],
        'groups': groups, 'descriptive_ranking_not_formal': ranking,
        'formal_difficulty_accepted_tasks': [],
        'formal_difficulty_status': 'Not established by the source evidence',
        'checks': {
            'included_records': len(records),
            'scored_records': sum(row['_score'] is not None for row in records),
            'excluded_legacy_new6_snapshot': excluded,
            'pass_decision': 'Fraction of original unrounded score string >= 70 points',
            'pass_flags_match_source': True, 'unique_trials': True,
            'referenced_new6_receipts_exist': True,
            'judge_calls': 0, 'model_calls': 0, 'excel_files_read': 0,
        },
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / 'new6-current-selection-audit.json').write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (args.output_dir / 'new6-current-selection-audit.md').write_text(markdown(audit), encoding='utf-8')
    print(json.dumps(audit['checks'], ensure_ascii=False))


if __name__ == '__main__':
    main()

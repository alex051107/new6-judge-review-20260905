# 当前成绩与验收判断

先看[目前哪些题目符合要求](FINAL_SELECTION.md)，再按题查看原答卷与逐项回执。当前没有题目完成全部难度验收的充分证据。

| 数据 | 当前来源 | 核对方式 |
|---|---|---|
| 新六题 | [90份已有评分、144槽位完整状态](current-effective-v3/README.md) | [逐次表](current-effective-v3/trials.csv)、[版本和配置分层](current-effective-v3/stratified_summary.csv) |
| 千问最新全部答卷 | [43份最终文件逐份离线评分](qwen-final-20260906/README.md) | 23份有分数、20份待判、另5槽未收回；保留上游异常分类 |
| 旧15题 | [347份已有评分](ability-comparison-360-v1/README.md) | 只用P15_V3的360槽；其中24份政策题带旧合同问题 |
| 跨题核对 | [当前判断与逐题结果](FINAL_SELECTION.md) | [统计脚本](selection/recompute.py)、[结构化来源](selection/new6-current-selection-audit.json) |

新六题非千问的67份已有评分保持原事实，48个千问槽位全部改用最新批次。旧千问回执留在原快照，不再混入当前表。均分只含SCORED；未知不补零，重复判分不算新Agent样本。

```bash
python3 results/current-effective-v3/recompute.py --repo-root . --output-dir /tmp/current-results-check
python3 results/selection/recompute.py --repo-root . --output-dir /tmp/selection-check
```

统计复算与重评原Excel分开。完整难度要求逐题至少两个指定系统分别同时满足均分低于60、Pass@8低于70%；通过按未舍入分数≥70判断。各组模型身份、同版同配置样本和独立验收尚需核齐。

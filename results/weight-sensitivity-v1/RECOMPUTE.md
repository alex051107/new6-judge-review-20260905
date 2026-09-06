# 六题重点能力 60/40 分项重算

默认方案将重点能力组设为 60%，其余组设为 40%，组内保留原相对权重。它是基于现成评分事实的事后配重探索，没有修改原 Judge；未知事实不补零，没有新增处罚或通过门槛。通过仍由未舍入分数 ≥ 0.70 决定。

[逐次结果](results/trials.csv) · [逐题、系统与配置结果](results/task_system_config.csv) · [50%／70%敏感性附件](sensitivity.csv) · [来源说明](SOURCE_NOTES.md)

使用 Python 3 标准库，在本目录执行：

```bash
python3 recompute.py --output-dir results
```

对同版本现成 Judge JSON 中的完整分项信用重配权重：

```bash
python3 reweight_receipt.py --task A1 --receipt /path/to/judge-result.json --output reweighted.json
```

第二条命令中的路径需换成自己的实际回执；脚本不读取工作簿、不运行 Judge、不调用模型。输入须与该题的冻结分项和原配重一致，否则拒绝重算。非 SCORED 回执保留状态，实验分数和通过判定为空。

重点组依据当前题面：A1/A2 为情景变化、基准保护和交付解释；B1 为明细汇总闭合、追溯与贡献分析；B2 为连续恶化筛选、名单变化解释与历史分析可复核；C1 为有效报价范围、新旧差额和会议调价后的成本链；C2 为报价更新、原始规则保护与来源追溯。具体评分项见 [weights.json](weights.json)。这些整项仍包含混合能力，基础／重点不等于静态／动态。

均分仅使用已评分记录，表内另列待判数量。只有经过成员集合核对的 C1、GPT-5.6 sol 同配置八次提供 pass@1 和 pass@8；其他组选样不完整或身份未核实，保持空值。系统代码 codex、claude、qwen 分别展示为 GPT-5.6 sol、Opus 5、Qwen 3.8，实际请求与响应身份随行保留。

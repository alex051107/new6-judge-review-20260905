# NEW6 · 六道业务工作簿任务

NEW6 用六道题评测 Agent 能否把真实材料做成下一位同事可以核对、解释和继续使用的 Excel 工作簿。材料包括公开估值模型、交易记录、统计发布、工程估算和邮政价目表；工作请求与部分情景由项目重构。

每题关注一份完整交付。分析师需要沿年度预测查到估值，经营人员需要沿汇总查到交易，造价或物流人员需要沿工作计算查到原文规则。题包、参考、评分程序和已有答卷放在一起，供组内复跑与人工审查。

## 我们看重的能力

![六题能力与常见单步操作的对比](docs/assets/abilities.png)

A 轨看专业模型的计算关系和年度时序；B 轨看完整分析对象、业务口径以及明细到结论的一致；C 轨看文档层级、限定语、范围和计价规则。只有明确要求继续调整输入的题目，才检查结果是否随之正确更新。B1、B2 接受正确的静态分析。

[逐题业务与能力说明](docs/BUSINESS.md)提供具体对比、材料来源、正确交付和下游用途。

## 六题入口

| 题 | 业务 | 当前题面 | 输入与版本 |
|---|---|---|---|
| A1 | [Amazon估值模型恢复](docs/BUSINESS.md) | [题面](tasks/52/NEW6-A-FIN-RESTORE-001/instruction.md) | [来源](tasks/52/NEW6-A-FIN-RESTORE-001/metadata/source_manifest.json) · [版本](tasks/52/NEW6-A-FIN-RESTORE-001/metadata/release_identity.json) |
| A2 | [LTGM长期增长情景](docs/BUSINESS.md) | [题面](tasks/54/NEW6-A-MACRO-SCENARIO-001/instruction.md) | [来源](tasks/54/NEW6-A-MACRO-SCENARIO-001/metadata/source_manifest.json) · [版本](tasks/54/NEW6-A-MACRO-SCENARIO-001/metadata/release_identity.json) |
| B1 | [零售月结与月度变化](docs/BUSINESS.md) | [题面](tasks/44/NEW6-B-RETAIL-CLOSE-001/instruction.md) | [来源](tasks/44/NEW6-B-RETAIL-CLOSE-001/metadata/source_manifest.json) · [版本](tasks/44/NEW6-B-RETAIL-CLOSE-001/metadata/release_identity.json) |
| B2 | [三期地方劳动力简报](docs/BUSINESS.md) | [题面](tasks/92/NEW6-B-LABOUR-BRIEF-001/instruction.md) | [来源](tasks/92/NEW6-B-LABOUR-BRIEF-001/metadata/source_manifest.json) · [版本](tasks/92/NEW6-B-LABOUR-BRIEF-001/metadata/release_identity.json) |
| C1 | [工程估算与修订往来](docs/BUSINESS.md) | [题面](tasks/23/NEW6-C-COST-WORKPAPER-001/instruction.md) | [来源](tasks/23/NEW6-C-COST-WORKPAPER-001/metadata/source_manifest.json) · [版本](tasks/23/NEW6-C-COST-WORKPAPER-001/metadata/release_identity.json) |
| C2 | [邮政资费与可更新报价](docs/BUSINESS.md) | [题面](tasks/49/NEW6-C-PARCEL-TARIFF-001/instruction.md) | [来源](tasks/49/NEW6-C-PARCEL-TARIFF-001/metadata/source_manifest.json) · [版本](tasks/49/NEW6-C-PARCEL-TARIFF-001/metadata/release_identity.json) |

## 已有结果

在当前固定发布的已评分答卷中，GPT-5.6 sol 的结果整体更好：27份中23份达到70分；Opus 5 的13份中1份达到70分。Qwen 3.8 当前只有C2的2份可评分原件，分别为45.46分和50.00分。各系统的有效样本和任务覆盖不同，这里描述已有交付表现，正式难度核验仍按逐题、同版本与同配置进行。

![六题已有答卷分数分布](docs/assets/score_distribution.png)

本次记录138个当前槽位，其中42份已评分、54份Judge待判、22次运行或基础设施失败、20次确认未交付；目标144槽位尚缺6条。确认未交付按冻结政策计零，待判和运行异常保留空分。已标记需要复核的分数保留原回执，不据此直接归因能力不足。

[完整配置分组成绩表](results/SUMMARY.md) · [逐次记录](results/trials.csv) · [逐项得失分](results/criteria.csv) · [另两套配重结果](results/alternate_profiles.csv)

图只展示已评分原件，不将未交付或待判画成业务低分。表格由同一份逐次记录生成，不混合不同配置的均分。是否通过采用未舍入 score≥0.70；pass@8 使用标准组合数定义，样本不足时留空。

## Judge 怎样评分

业务判分采用确定性程序，未使用LLM Judge。程序读取原工作簿，确定对象、字段、期间和单位，与独立答案核对，再检查题目要求的更新、完整性与保护，按固定权重汇总逐项信用。

![六题主配重](docs/assets/judge_weights.png)

[Judge流程、方法与边界](docs/JUDGE.md) · [逐项权重与代码位置](docs/METHODS.csv) · [实际配置](repro/JUDGE_CONFIG.json)

## 复跑与人工审查

[离线复跑命令](repro/README.md)覆盖参考、随包校准、已有原件和自有answer.xlsx。当前实际验证为参考六题各五次全部满分，42份已评分原件复评一致，校准17/18符合预期；具体结果见[验证记录](results/VALIDATION.md)。复跑不启动新的做题Agent。

[人工审查表](review/HUMAN_REVIEW.csv)按题记录具体文件或单元格、意见、返修和复核。当前为待人工审查，抽检量为0；[要求核对表](review/REQUIREMENTS.md)保留尚待确认的验收项。

## 完整材料与固定版本

六题和结果的固定标记为 `new6-final-review-20260906-v1`，Judge核心提交为 [31abf3fa03c3](https://github.com/alex051107/excelbench-p15-results/commit/31abf3fa03c358f6134600fe5b0416e6ee24211a)。本仓库main更新阅读说明和图示，固定题包与历史回执保留。

[完整六题、原始答卷与全部回执（需组内权限）](https://github.com/alex051107/excelbench-p15-results/tree/new6-final-review-20260906-v1/new6-final)。公开仓库是说明与代码审查入口，完整第三方输入和私有核验材料按授权范围放在既有私有结果仓库。

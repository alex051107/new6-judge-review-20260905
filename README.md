# NEW6 · 六题、实际结果与组内人工审查

本次固定发布六道题的当前主版本。题面保留英语，业务说明、判分说明和审查入口使用中文；系统展示名统一为 **GPT-5.6 sol、Opus 5、Qwen 3.8**，实际模型 ID、CLI 和配置保留在逐次记录中。

**当前低分混有 Judge 误判，不能全部解释为能力不足。** A1 存在情景错绑；C2 一份29.69分原件的192个价格和36个报价金额经独立核对全部正确；B1一个完整桥接边界案例被部分解析后扣分。[查看原件与单元格证据](results/LOW_SCORE_AUDIT.md)。原回执和分数保留，本轮未改Judge或权重。

在进入Judge的96份答卷中，42份出分、54份待判（出分比例43.75%，不是评分正确率）。[错误归因](results/ERROR_TRIAGE.md)区分47份解析绑定问题、6份公式归因未决、1份重算失败，以及另外22次Qwen上游生成服务失败。当前交付可用于复跑与审查，尚不能证明六题全部通过难度验收。

## 六题入口

| 题 | 业务 | 当前题面 | 输入与版本 |
|---|---|---|---|
| A1 | [Amazon估值模型恢复](docs/BUSINESS.md) | [题面](tasks/52/NEW6-A-FIN-RESTORE-001/instruction.md) | [来源](tasks/52/NEW6-A-FIN-RESTORE-001/metadata/source_manifest.json) · [版本](tasks/52/NEW6-A-FIN-RESTORE-001/metadata/release_identity.json) |
| A2 | [LTGM长期增长情景](docs/BUSINESS.md) | [题面](tasks/54/NEW6-A-MACRO-SCENARIO-001/instruction.md) | [来源](tasks/54/NEW6-A-MACRO-SCENARIO-001/metadata/source_manifest.json) · [版本](tasks/54/NEW6-A-MACRO-SCENARIO-001/metadata/release_identity.json) |
| B1 | [零售月结与月度变化](docs/BUSINESS.md) | [题面](tasks/44/NEW6-B-RETAIL-CLOSE-001/instruction.md) | [来源](tasks/44/NEW6-B-RETAIL-CLOSE-001/metadata/source_manifest.json) · [版本](tasks/44/NEW6-B-RETAIL-CLOSE-001/metadata/release_identity.json) |
| B2 | [三期地方劳动力简报](docs/BUSINESS.md) | [题面](tasks/92/NEW6-B-LABOUR-BRIEF-001/instruction.md) | [来源](tasks/92/NEW6-B-LABOUR-BRIEF-001/metadata/source_manifest.json) · [版本](tasks/92/NEW6-B-LABOUR-BRIEF-001/metadata/release_identity.json) |
| C1 | [工程估算与修订往来](docs/BUSINESS.md) | [题面](tasks/23/NEW6-C-COST-WORKPAPER-001/instruction.md) | [来源](tasks/23/NEW6-C-COST-WORKPAPER-001/metadata/source_manifest.json) · [版本](tasks/23/NEW6-C-COST-WORKPAPER-001/metadata/release_identity.json) |
| C2 | [邮政资费与可更新报价](docs/BUSINESS.md) | [题面](tasks/49/NEW6-C-PARCEL-TARIFF-001/instruction.md) | [来源](tasks/49/NEW6-C-PARCEL-TARIFF-001/metadata/source_manifest.json) · [版本](tasks/49/NEW6-C-PARCEL-TARIFF-001/metadata/release_identity.json) |

[六题业务说明](docs/BUSINESS.md)解释材料、重构请求、正确交付和主要能力；[Judge说明](docs/JUDGE.md)列出实际流程、确定性方法、权重和边界。

## 当前主方案成绩

本次固定138条当前槽位记录：42份已评分、54份Judge待判、22次运行或基础设施失败、20次确认未交付。目标144槽位尚缺6条。另有19次被先前授权补跑替代的原尝试保留内部归档，完整尝试账目见[这里](results/attempt_accounting.json)。本次没有启动新的做题Agent。

均分只计可评分工作簿和确认未交付，未知不补零。确认未交付计零表示系统交付失败，不能单独证明业务能力低。不同实际配置和返回身份分行，完整分数分布及另两套权重放结果附件。

[配置分组成绩表](results/SUMMARY.md) · [逐次分布](results/DISTRIBUTION.md) · [逐次CSV](results/trials.csv) · [逐项信用](results/criteria.csv) · [另两套权重](results/alternate_profiles.csv)

<!-- CURRENT_RESULTS_START -->
| 题 | 系统 | 配置/响应组 | 尝试 | 可评分 | 未交付 | 环境失败 | 待判 | 均分 /100（n） | 通过 | pass@1 | pass@8 |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A1 | Opus 5 | 638cc5/1 | 8 | 6 | 0 | 0 | 2 | 53.62 (6) | 1 | — | — |
| A1 | GPT-5.6 sol | ab813a/1 | 8 | 8 | 0 | 0 | 0 | 90.45 (8) | 7 | 87.5% | 100.0% |
| A1 | Qwen 3.8 | 2a1351/1 | 3 | 0 | 3 | 0 | 0 | 0.00 (3) | 0 | 0.0% | — |
| A1 | Qwen 3.8 | 92db26/2 | 5 | 0 | 0 | 5 | 0 | — | 0 | — | — |
| A2 | Opus 5 | 638cc5/1 | 6 | 0 | 0 | 0 | 6 | — | 0 | — | — |
| A2 | Opus 5 | 638cc5/2 | 2 | 0 | 1 | 0 | 1 | 0.00 (1) | 0 | — | — |
| A2 | GPT-5.6 sol | ab813a/1 | 8 | 5 | 0 | 0 | 3 | 90.59 (5) | 5 | — | — |
| A2 | Qwen 3.8 | 2a1351/1 | 2 | 0 | 1 | 0 | 1 | 0.00 (1) | 0 | — | — |
| A2 | Qwen 3.8 | 92db26/2 | 6 | 0 | 2 | 4 | 0 | 0.00 (2) | 0 | — | — |
| B1 | Opus 5 | 638cc5/1 | 6 | 3 | 0 | 0 | 3 | 56.34 (3) | 0 | — | — |
| B1 | Opus 5 | 638cc5/2 | 2 | 0 | 1 | 0 | 1 | 0.00 (1) | 0 | — | — |
| B1 | GPT-5.6 sol | ab813a/1 | 8 | 8 | 0 | 0 | 0 | 92.73 (8) | 7 | 87.5% | 100.0% |
| B1 | Qwen 3.8 | 2a1351/1 | 4 | 0 | 3 | 0 | 1 | 0.00 (3) | 0 | — | — |
| B1 | Qwen 3.8 | 92db26/2 | 4 | 0 | 1 | 3 | 0 | 0.00 (1) | 0 | — | — |
| B2 | Opus 5 | 638cc5/1 | 7 | 2 | 0 | 0 | 5 | 55.81 (2) | 0 | — | — |
| B2 | Opus 5 | 638cc5/2 | 1 | 0 | 1 | 0 | 0 | 0.00 (1) | 0 | 0.0% | — |
| B2 | GPT-5.6 sol | d8e0d8/1 | 8 | 3 | 0 | 0 | 5 | 91.86 (3) | 3 | — | — |
| B2 | Qwen 3.8 | 92db26/1 | 6 | 0 | 0 | 6 | 0 | — | 0 | — | — |
| C1 | Opus 5 | 638cc5/1 | 1 | 0 | 1 | 0 | 0 | 0.00 (1) | 0 | 0.0% | — |
| C1 | Opus 5 | 7595ef/2 | 7 | 2 | 0 | 0 | 5 | 42.76 (2) | 0 | — | — |
| C1 | GPT-5.6 sol | d8e0d8/1 | 8 | 0 | 0 | 0 | 8 | — | 0 | — | — |
| C1 | Qwen 3.8 | 92db26/1 | 4 | 0 | 0 | 4 | 0 | — | 0 | — | — |
| C2 | Opus 5 | 638cc5/1 | 6 | 0 | 0 | 0 | 6 | — | 0 | — | — |
| C2 | Opus 5 | 638cc5/2 | 2 | 0 | 2 | 0 | 0 | 0.00 (2) | 0 | 0.0% | — |
| C2 | GPT-5.6 sol | ab813a/1 | 8 | 3 | 0 | 0 | 5 | 49.94 (3) | 1 | — | — |
| C2 | Qwen 3.8 | 2a1351/1 | 8 | 2 | 4 | 0 | 2 | 15.91 (6) | 0 | — | — |
<!-- CURRENT_RESULTS_END -->

pass@8 使用 1−C(n−c,8)/C(n,8)，样本或状态不足时留空。当前不宣称六题通过难度验收。

## 复跑与人工审查

- [离线复跑命令](repro/README.md)：构建固定环境，跑参考与校准，复评已有答卷，或评自己的 answer.xlsx。不会自动调用付费Agent。
- [验证结果](results/VALIDATION.md)：六题参考各5次共30/30满分；校准17/18符合预期；42/42已评分原件复评一致。稳定性不能替代正确性。
- [填写人工审查表](review/HUMAN_REVIEW.csv)：记录审查者、日期、具体文件/单元格、修改意见及复核结果。当前为**待人工审查**，抽检量0，不合格率不可计算。
- [原要求与当前实现差项](review/REQUIREMENTS.md)：B2五条rubric、六题无独立负项、确定性解析与原agentic要求差异，及模型替代、独立Qwen验收、资料授权等。

## 固定版本与完整包

发布标记 `new6-final-review-20260906-v1`；实际Judge核心提交为 [31abf3fa03c3](https://github.com/alex051107/excelbench-p15-results/commit/31abf3fa03c358f6134600fe5b0416e6ee24211a)。

[完整六题、原始答卷与全部回执（需组内权限）](https://github.com/alex051107/excelbench-p15-results/tree/new6-final-review-20260906-v1/new6-final)。公开仓库保留代码与可公开说明；缺少再分发授权的完整第三方PDF/XLSX和答卷放在既有私有结果仓库。公开镜像不是完整离线题包，仓库可见性没有改变。

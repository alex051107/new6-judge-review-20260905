# 发布验证结果

六题参考在同一固定 Judge 下各评分 5 次，30/30 次满分。全部 43 个逐项或总分标准差都有 5 次实际回执，标准差均为 0，小于 0.05。这个结果证明运行稳定，无法排除稳定的误判。

| 检查 | 实际结果 | 回执 |
|---|---|---|
| 六题参考 × 5 次 | 30/30 满分 | [逐次回执](reference-repeat5/receipt.json)、[逐项标准差](consistency.csv) |
| 新目录重新构建镜像后六份参考 | 6/6 满分 | [构建后回执](fresh-build-reference/receipt.json) |
| 随包校准 | 17/18 符合预期；B1 部分绑定案例失败 | [校准回执](calibration-replay/receipt.json) |
| 自有答卷 score 入口 | B2参考作为调用方答卷，实际返回1.0 | [入口回执](own-answer-smoke/receipt.json) |
| 已评分真实答卷离线重评 | 42/42 状态与分数一致（1e-12容差） | [对照表](replay_comparison.json) |
| 真实低分业务核对 | A1有情景错绑，C2有表头/单位误判；B1/B2/C1有可定位的局部业务错误 | [低分核对](LOW_SCORE_AUDIT.md)、[四份独立核对](ADDITIONAL_LOW_SCORE_REVIEW.md) |

校准的失败期望保持不变。B1合法未支持表头应当待判，当前 Judge 却部分识别后出分；这项缺陷与 A1/C2 的真实答卷误判一起留待修复。本轮不调整正式分数、权重或判分逻辑。

本轮没有启动新的做题 Agent 或付费 Judge。复跑直接读取只读原件，输出写到新的证据目录。人工审查尚未开始。

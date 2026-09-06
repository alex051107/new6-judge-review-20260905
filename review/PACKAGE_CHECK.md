# 六题交付包核对

六题必需文件、Evaluator及其引用路径均存在，JSON/TOML可解析，主权重与冻结发布清单一致。已安装 Harbor 的 TaskConfig 接受全部六份配置。此页记录结构与入口核对；Harbor 完整运行未在本轮启动。

| 题目 | 输入文件数 | rubric条数 | 主权重合计 |
|---|---:|---:|---:|
| A1 | 2 | 6 | 100 |
| A2 | 3 | 6 | 100 |
| B1 | 4 | 8 | 100 |
| B2 | 5，另有1件容器可见导出 | 5 | 100 |
| C1 | 3 | 6 | 100 |
| C2 | 3 | 6 | 100 |

输入未发现空文件。B2 的容器输入另外包含 `previous_briefing.xlsx.inspect.ndjson`，内容为已有工作簿的结构及表格导出，规范输入目录最初未带上该文件。应按实际 Agent 可见集合补入交付输入，不能删除旧输入来制造一致。其余五题的两份输入目录内容一致。

## 隔离与入口

Agent镜像构建上下文只有Dockerfile和输入；不COPY solution、tests或metadata。六题都配置独立Verifier，Harbor会以tests目录构建其镜像，将收集的 `/app/input` 和 `/app/output` 恢复到原路径。Verifier从 `/tests/run_verifier.py` 调用随包Evaluator。Oracle的 `solve.sh` 将仅由Oracle流程挂入的参考工作簿复制到约定输出；这是参考回放，不是重新求解答案。

离线 `replay.py` 使用只读挂载输入、答卷及tests，容器断网。README的参考、校准、真实答卷与自有答卷参数和现有CLI一致。输出目录要求为空，复评不覆盖唯一统计来源。未交付和Judge异常须以JSON状态判断，不能用Harbor传输层预写的 `reward.txt=0` 当成能力零分。

纯包装修复建议：为C1/C2的test.sh补执行权限；在task.toml元数据明确业务版本与Judge版本；如果提供Harbor运行入口，补充镜像别名及Agent源镜像构建命令。当前README仅构建 `new6-final-judge:v1`，而任务Dockerfile依赖 `new6-judge:20260905` 和 `new6-agent:20260905`。Agent构建文件可从Judge镜像安装固定Claude CLI版本，但Debian的node/npm等附加包未完全固定，也未在本检查中实际构建；不能把离线评分环境的验证扩写成参测环境复现通过。

## 保留的原要求差项

B2现行rubric只有5条；六题均无独立negative条目。现行字段完整并不代表这两项原要求已通过。按用户要求不拆条、不新增处罚、不改权重。

## 实际Judge缺陷：B1部分解析

随包 `unbound_bridge_header.xlsx` 的 Monthly bridge 页有完整九行桥接数值，表头为 Component / Change in pounds。已有校准回执只绑定四个端点、变化和残差，将五个effect漏判为错误，导致R007得2/9、总分0.80555555555555555。代码在桥接表完全未绑定时才进入解析待判；部分绑定绕过该检查。它不是缺少业务交付，不能归因于能力低。

该案例的原预期JUDGE_ERROR应保留，校准失败应公开列出，不能改预期值将其变成通过。证据见 [校准回执](../results/calibration-replay/run-1/B1-unbound_bridge_header/judge-result.json)。本检查未改Judge或正式成绩。

检查预算：一次集中结构类别检查，一次Harbor配置模型导入；零评分runner、零hash、零新增Agent。主任务已有参考五次、校准及真实答卷复评，本检查未重复。包装修改后的回读由发布主任务记录。

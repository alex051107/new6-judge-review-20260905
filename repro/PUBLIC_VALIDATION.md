# 已验证的运行范围

当前发布入口可以重读原工作簿，输出逐项事实、总分和通过判定。实际完成的检查如下。

| 检查 | 结果 | 证据 |
|---|---|---|
| 清理后六题参考 | A1、A2、B1、B2、C1、C2均SCORED，原分1.0 | [本批参考回执](../validation/reference-replay.json) |
| 千问43份最终文件 | 全部实际离线评分；23份有分数、20份Judge待判 | [43份逐次结果及回执](../results/qwen-final-20260906/README.md) |
| 千问公开复评入口 | A2-qwen-R08已执行，逐项事实、当前分数与通过结果一致 | [公开复评代码](qwen-final/replay.py)、[目标回执](../results/qwen-final-20260906/receipts/A2-qwen-R08.json) |
| 当前统一入口 | A2-qwen-R08经统一入口调用，分项、总分及通过核对一致 | [统一入口](replay_final.py)、[本次比较回执](../validation/final-replay-entry.json) |
| 基线校准 | 既有17/18符合预期；B1的unbound_bridge_header仍有差项 | [校准记录](../results/VALIDATION.md)、[案例目录](../validation/calibration) |
| 当前结果统计 | 144槽、90份有分数；通过使用未舍入分数，未知不填零 | [统计验证](../results/current-effective-v3/validation.json) |

当前90份有分数的答卷中，67份非千问沿用已有实际Judge路线与回执；它们没有在本轮全部重评。此前已完成的固定B/C四份实跑、10份补充快照逐项比较和统一入口检查，见[固定B/C验证](public-validation/bc-excel-validation.json)、[补充快照比较](current-reader-snapshots/comparison.json)、[既有入口验证](current-replay-validation/validation.json)。这些证据各自对应其答卷与版本。

千问本批每题使用一个固定Judge快照，读取原答卷及实际收集后的输入。43份文件中21份带上游运行异常、22份没有记录的上游异常；可离线评分不等于正式难度样本已经合格。模型身份、生成配置和部分历史Judge提交证明仍需核齐。

环境为Linux/arm64，固定镜像由公开release提供；x86原生环境尚未验证。评分容器断网，不读取API Key，不调用生成Agent或LLM。

原公开环境镜像已完成208,230,490字节的匿名下载与SHA-256核对；既有公开文件检查见[匿名访问记录](public-validation/anonymous-access-85d1808.json)。本次新增文件的远端回读应以本次发布检查为准，不能用旧记录代替。

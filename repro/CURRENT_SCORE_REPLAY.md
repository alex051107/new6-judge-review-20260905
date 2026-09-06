# 当前成绩怎样从原工作簿复现

首页78份已评分答卷均已整理原件、实际输入和可执行Judge。[统一入口](CURRENT_REPLAY.md)按逐份索引选择版本，从Excel重新读取事实，再计算当前配重。它不会只打印保存的成绩表。

## 78份答卷分别使用什么代码

| 对应方式 | 份数 | 已有依据 |
|---|---:|---|
| 固定34374 Judge与随包原件 | 66 | 原件hash与所选回执对应，固定回执的每项信用与首页来源一致。 |
| 补充的实际部署快照 | 10 | 已重新读取这10份原件，逐项信用全部与当前来源一致；公开导出入口另用一份B1答卷验证。 |
| 固定34374 Judge与补充原件 | 2 | A1-qwen-R08、B2-qwen-R08已通过统一入口实际评分，分项、当前总分和pass均一致。 |

[逐份索引](current-replay-index.json)记录原件、输入、trial、历史回执身份和本次执行快照。当前成绩包含不同Judge及生成配置，不能整体称为同一版本的一轮实验。

55份历史回执只有版本标签，缺少当时的不可变提交证明，其中45份的分项与固定34374回执一致。现在的可执行快照及复现结果均已公开；历史提交证明仍单独标为缺失。

## 实际验证了哪些入口

| 验证范围 | 实际操作 | 结果 |
|---|---|---|
| 六题参考 | 在公开文件树中运行六个Harbor题包自身的基线Judge | 六题均为原分1.0；与当前答卷Judge分别记录。 |
| 固定34374公开导出 | 重读A1-codex-R08，以及B1-codex-R02、B2-codex-R05、C1-codex-R08、C2-codex-R01 | 均成功评分；四份B/C答卷分项与固定回执完全一致。 |
| 补充部署快照 | 重读10份原件，再通过公开导出入口核验B1-qwen-R02 | 10/10逐项一致，公开入口也与对应来源一致。 |
| 统一入口 | 新实跑A1-qwen-R08、B2-qwen-R08；跨版本汇总另复用已验证的B2与B1回执 | 两份新实跑一致，四份跨版本比较全部通过。 |

评分使用固定Linux/arm64镜像，单容器、1 CPU、3 GB、断网运行，没有Agent或模型API调用。本轮未重复全跑78份；其余答卷使用已有归档回执和逐项对应证据。x86原生环境尚未验证。

固定包四份B/C答卷的原配重分数依次为1.0、0.876071428571428565、0.91747857128651830638585605473022691565737、1。首页采用当前配重，从同一份回执按公开公式计算。

## 命令与原始证据

准备环境后，在仓库根目录执行：

```bash
python3 repro/replay_current.py --case A1-qwen-R08 B2-qwen-R08 --out /tmp/new6-current-check
```

`comparison.json`逐份列出状态、分项差异、总分和pass比较。详细回执位于`scores/<case>/result.json`，当前配重位于同目录`current-score.json`。输出目录必须为新目录。全部78份使用`--all`，完整准备命令见[统一入口说明](CURRENT_REPLAY.md)。

[固定包真实Excel验证](public-validation/bc-excel-validation.json) · [固定与当前分项对应](public-validation/current-fixed-coverage.json) · [10份部署快照验证](current-reader-snapshots/comparison.json) · [统一入口验证](current-replay-validation/validation.json)

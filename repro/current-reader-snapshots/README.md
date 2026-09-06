# 当前选中回执的补充复跑

复现首页全部78份有效成绩，请使用[统一入口](../CURRENT_REPLAY.md)；本目录单独复现其中10份部署快照答卷。

本目录补齐10份当前有效成绩所需的可执行Judge快照。使用既有部署目录A1 v1.3、A2 v1.3、B1 v2.5、C2 v2.4，在公开固定镜像中重新读取10份真实答卷，**10份全部可评分，逐项信用与当前选中的回执完全一致**。原件未修改，未启动Agent或模型API。

这是2026-09-06现在验证的可执行快照。历史回执缺少不可变提交证明的情况仍保留，不能用现在的文件hash倒填历史代码身份。34374固定包及其成绩继续独立保留。

## 重读真实Excel

先按[固定镜像准备说明](../fixed-34374/README.md)下载并加载镜像。在仓库根目录执行：

```bash
python3 repro/current-reader-snapshots/replay.py --case B1-qwen-R02 --out /tmp/new6-current-reader-public-smoke
python3 repro/current-reader-snapshots/compare.py --out /tmp/new6-current-reader-public-smoke
```

输出目录必须是新目录。入口从本公开仓库的原件ZIP自动解包该次答卷和实际输入，选择对应代码快照，核对原件hash、公开归档hash、快照文件hash和固定镜像ID。评分使用1个断网容器，1 CPU、3 GB内存，按顺序运行。镜像为Linux/arm64，其他架构需要Docker模拟支持。

一次重读这10份：

```bash
python3 repro/current-reader-snapshots/replay.py --all --out /tmp/new6-current-reader-all
python3 repro/current-reader-snapshots/compare.py --out /tmp/new6-current-reader-all
```

详细新回执在输出目录 `runs/<case>/result.json`，比较结果在 `comparison.json`。随包首次验证的回执见[expected-receipts](expected-receipts)，10份对齐记录见[comparison.json](comparison.json)。第二条命令仅比较已生成的分项，不再次运行Judge。

这些回执的总分是原冻结主配重。核对当前60%配重时，把新回执传给[配重计算脚本](../fixed-34374/public-summary/reweight_receipt.py)，例如：

```bash
python3 repro/fixed-34374/public-summary/reweight_receipt.py --task B1 --receipt /tmp/new6-current-reader-public-smoke/runs/B1-qwen-R02/result.json --output /tmp/new6-current-reader-public-smoke/current-score.json
```

## 文件与版本

[逐次清单](selected.json)绑定每份答卷、原件hash、来源ZIP及所用快照。[公开文件清单](PUBLIC_EXPORT.json)列出当前归档的全部保留文件及hash；[打包核验](PACKAGE_VALIDATION.json)记录解包与完整性检查。[执行源码核对](EXECUTABLE_IDENTITY.json)保留评分源码的身份依据。公开包保留复评所需代码、输入、独立答案和校准材料。

这些快照包含Judge独立答案和核验材料，供复评者使用，不能整体给参测Agent查看。10份实跑验证支持这些原件的复现；历史提交身份和其他未重跑原件的表现另按证据记录。

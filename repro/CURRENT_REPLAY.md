# 从原工作簿复现当前78份成绩

`replay_current.py`为首页选中的78份可评分答卷绑定各自原件、实际输入和已核对的Judge。它重读Excel，使用现有配重脚本计算当前60%配重，再逐项比较首页来源表。无需自行拼接不同快照，也不会启动新的Agent。

需要Python 3.12以上、Docker及Linux/arm64容器支持。x86主机需自行配置arm64模拟，本轮没有验证x86原生环境。公开下载无需GitHub账号；下载完成后评分断网。

```bash
git clone https://github.com/alex051107/new6-judge-review-20260905.git
cd new6-judge-review-20260905
git checkout new6-public-replay-v5
mkdir -p /tmp/new6-public-image
curl -fL https://github.com/alex051107/new6-judge-review-20260905/releases/download/new6-public-replay-v4/new6-judge-34374-offline.tar.gz -o /tmp/new6-public-image/new6-judge-34374-offline.tar.gz
docker load -i /tmp/new6-public-image/new6-judge-34374-offline.tar.gz
```

代码与材料固定在v5；环境沿用已公开验证的v4镜像。评分入口核对镜像ID。然后在仓库根目录执行：

```bash
python3 repro/replay_current.py --case A1-qwen-R08 B2-qwen-R08 --out /tmp/new6-current-remaining-two
```

输出目录必须尚不存在。命令执行后，查看 `comparison.json`：每份都有实际状态、逐项是否一致、当前分数与来源分数、通过结果比较及执行快照。详细回执在 `scores/<case>/result.json`；当前配重结果在同目录 `current-score.json`。若待判、缺少回执或发生异常，比较不会标成匹配，也不会补零。

一次重读当前78份：

```bash
python3 repro/replay_current.py --all --out /tmp/new6-current-all
```

入口使用一个断网容器，1 CPU、3 GB，依次执行。镜像、归档和原件身份在评分前核对；固定Judge核对冻结锁，补充快照核对逐文件hash。评分不联网，不调用LLM，没有新Agent费用。运行全部78份会花费本地计算时间。本轮没有重复全跑78份。

## 每份使用哪个Judge

[完整路由索引](current-replay-index.json)逐份公开原件ZIP、trial、hash、任务版本、历史回执身份和本次执行快照：

| 路由 | 数量 | 依据 |
|---|---:|---|
| 固定34374中的原件 | 66 | 原件身份相同，归档分项与首页所选分项一致。 |
| 当前部署快照 | 10 | 现在重新读取原件，10份全部逐项匹配；历史不可变提交证明仍缺失。 |
| 固定34374与补充公开原件 | 2 | A1-qwen-R08、B2-qwen-R08，使用各自当次输入。 |

执行快照与历史判分身份分开记录。现在能重现一个结果，不会把旧回执的版本标签自动升级为历史提交证明。

分数计算直接调用既有 `reweight_receipt.calculate`。入口核对该脚本的权重与当前 `results/current-effective-v2/weights.json` 内容完全一致，按60%配重计算。仍使用未舍入分数≥0.70的原有通过规则；比较界面的序列化尾数容差不参与通过判定。

## 本轮验证范围

固定包已实跑4份B/C真实Excel；补充部署快照已实跑10份，公开导出入口另验证1份；本总入口实跑A1-qwen-R08、B2-qwen-R08。总入口的跨路由比较另复用已生成的固定B2与补充B1回执，不再次读取这两份Excel。其余原件依赖已有同版归档回执与逐项对齐证据，未重复全量评分。具体验证材料见[current-replay-validation](current-replay-validation)。

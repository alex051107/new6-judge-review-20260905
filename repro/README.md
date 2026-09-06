# 复现当前分数与评分工作簿

当前结果有90份已评分答卷：67份GPT-5.6 sol和Opus 5保留原Judge路线，23份千问采用本批逐题固定的Judge快照。以下命令重新读取Excel并计算分数，不启动生成Agent，也不调用模型API。

| 要核对什么 | 入口 |
|---|---|
| 当前90份已有分数的答卷 | [统一复评步骤](CURRENT_REPLAY.md) |
| 千问全部43份最终文件，包括待判 | 下方千问命令及[逐次表](../results/qwen-final-20260906/README.md) |
| 当前均分、通过次数和完整状态 | [当前结果](../results/current-effective-v3/README.md) |
| 六题参考和校准案例 | 下方参考与校准命令 |
| 自己的answer.xlsx | [自有文件评分](fixed-34374/README.md#给自己的文件评分)，使用该入口注明的固定Judge |

## 获取文件与固定环境

本仓库和环境镜像均公开。需要Python 3.12以上、Docker及Linux/arm64容器支持。x86原生环境尚未验证。

```bash
git clone https://github.com/alex051107/new6-judge-review-20260905.git
cd new6-judge-review-20260905
git checkout new6-public-replay-v6
mkdir -p /tmp/new6-public-image
curl -fL https://github.com/alex051107/new6-judge-review-20260905/releases/download/new6-public-replay-v4/new6-judge-34374-offline.tar.gz -o /tmp/new6-public-image/new6-judge-34374-offline.tar.gz
docker load -i /tmp/new6-public-image/new6-judge-34374-offline.tar.gz
```

环境沿用固定依赖镜像，评分入口核对镜像及归档身份。容器使用1 CPU、3 GB内存、断网运行；原答卷和实际收集的输入只读。

## 复评当前答卷

```bash
python3 repro/replay_final.py --case A2-qwen-R08 --out /tmp/excel-score-one
python3 repro/replay_final.py --all --out /tmp/excel-score-all
```

输出目录必须是新目录。`comparison.json`核对逐项事实、当前总分和通过结果；详细回执位于`qwen/scores/`或`retained/scores/`，每份都有`current-score.json`及Judge回执。

千问本批收回43份最终文件，全部实际离线评过，其中23份有分数、20份待判；另5槽未收回最终文件。复查全部43份而不仅是已有分数的答卷：

```bash
python3 repro/qwen-final/replay.py --all --out /tmp/qwen-all-collected
```

该命令输出`summary.json`及各份`scores/<case>/judge-result.json`、`current-score.json`。待判保持空分，具体原因见回执。文件生成后有上游异常的试次单列，不当作正常完成的正式难度样本。

## 六题参考与随包校准

```bash
python3 repro/replay.py verify --suite reference --image new6-judge:20260905 --out /tmp/new6-public-reference
python3 repro/replay.py verify --suite calibration --image new6-judge:20260905 --out /tmp/new6-public-calibration
```

清理后的六题参考已逐题实跑，均为满分，见[参考验证回执](../validation/reference-replay.json)。题包基线校准保留17/18的既有结果；B1的`unbound_bridge_header`仍有读取差项，校准命令会返回非零退出码。该问题供审查，不计入模型难度样本。

[实际验证范围](PUBLIC_VALIDATION.md)区分本批43份千问实跑、公开入口验证及非千问既有验证。完整90份没有在本轮全部重新评分。

参考、Oracle和Judge仅供评分与人工审查使用。参测Agent只接触题面规定的输入，不应挂载整份审查仓库。

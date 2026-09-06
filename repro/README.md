# 离线复跑

当前结果使用同一固定Judge。优先按[当前73份原件的完整复跑入口](https://github.com/alex051107/excelbench-p15-results/blob/new6-unified-34374-v3/new6-final/unified-scores-v3/README.md)准备随release提供的镜像，并运行 `replay.py`。入口已在新目录解包实际工作簿评分；提供逐项回执、当前配重计算以及自有答卷评分命令。

[只核对随包分项算术](../results/unified-scores-v3/README.md)不需要Docker或模型配置。

## 基线参考与校准

以下保留原固定题包的六题参考、校准及基线复跑入口；它的Judge版本与当前结果分开记录。


复跑已有答卷，不启动付费 Agent。需要 Docker，建议给 Docker 至少 4 GB 可用内存；本包评分用 Python 3.11.16、LibreOffice 7.4.7.2、openpyxl 3.1.5、et-xmlfile 2.0.0、lxml 6.0.1。镜像构建需要访问公开 Debian/Python 包源，评分容器断网且不读 API Key。镜像的基础 digest 和依赖固定在 Dockerfile。

以下命令针对有权限的完整私有包。在公开仓库中缺少原始输入和答卷时，这些命令不能完整运行。

```bash
git clone https://github.com/alex051107/excelbench-p15-results.git
cd excelbench-p15-results
git checkout new6-final-review-20260906-v1
cd new6-final
docker build -f repro/Dockerfile -t new6-final-judge:v1 repro
python3 repro/replay.py verify --suite reference --image new6-final-judge:v1 --out /tmp/new6-reference
python3 repro/replay.py verify --suite calibration --image new6-final-judge:v1 --out /tmp/new6-calibration
```

当前随包校准为 17/18 符合预期：B1 的 `unbound_bridge_header` 暴露已知部分解析问题，因此校准命令会返回非零退出码。原测试期望和 Judge 均保留，详见[验证结果](../results/VALIDATION.md)。

同一 Judge 重复评分五次，以及复评已保存真实答卷：

```bash
python3 repro/replay.py verify --suite reference --repeat 5 --image new6-final-judge:v1 --out /tmp/new6-repeat5
python3 repro/replay.py actual --scored-only --image new6-final-judge:v1 --out /tmp/new6-actual
```

`actual --scored-only` 重评冻结表里已经可评分的原件。去掉 `--scored-only` 会对所有上游与收集正常、实际有答卷的记录复评，包括原有解析待判，不会补跑 Agent。每个命令的输出目录必须是新目录或空目录，重复执行请换目录名。

自有答卷评分示例（以 B2 为例）：

```bash
python3 repro/replay.py score --task B2 --answer ./answer.xlsx --image new6-final-judge:v1 --out /tmp/new6-my-answer
```

如果答卷对应的是一次完整运行，提供那次运行收集的输入目录，以便检查原输入是否受到修改：

```bash
python3 repro/replay.py score --task B2 --answer ./answer.xlsx --input-dir ./post-run-input --image new6-final-judge:v1 --out /tmp/new6-my-answer-with-input
```

省略 `--input-dir` 使用随包原输入，可测试工作簿，但无法证明参测系统未改动运行中的输入。`judge-result.json` 内有各项信用、贡献、原始事实与错误原因；终端结果不代替详细回执。运行成功不等于分数≥0.70。

重建 GitHub 展示的结果表，不进行任何新评分：

```bash
python3 repro/summarize.py
```

`results/trials.json` 是唯一统计来源；原回执和本次复评另存。本包不自动用新复评分覆盖冻结表，更不把重复评分算作新 Agent 样本。已知 C2 误判见低分核对页，使用者应保留原件和问题证据，不能通过重新冻结权重改变它。

六份 Harbor 题包保留已有 Agent/Verifier 分离配置。本次实际验证的入口是上述离线评分命令，未重新运行 Harbor Agent 安装或新的 Agent 试跑。Agent 镜像附加的 Node/npm 等依赖尚未完全固定，因此不能把离线可复跑说成新 Agent 的完整可复现承诺。

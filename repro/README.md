# 复现分数与评分工作簿

所有下载入口均在本公开仓库，查看文件和下载固定环境不需要私有仓库授权。按下面的目的选择操作：

| 要做什么 | 入口 | 会重新读取Excel吗 |
|---|---|---|
| 核对首页分数的配重和均分 | [当前结果复算](../results/current-effective-v2/README.md) | 不会；使用已保存的分项事实 |
| 复评真实答卷，查看逐项得失分 | [固定Judge与73份原件](fixed-34374/README.md) | 会；解包原件，用固定镜像评分 |
| 给自己的工作簿评分 | [自有文件评分](fixed-34374/README.md#给自己的文件评分) | 会；文件和输入须对应所选题目 |
| 核对六题参考及校准案例 | 下方基线入口 | 会；使用题包中记录的基线Judge |

首页78份有效分数保留各次实际Judge身份。固定73份复跑包对应34374业务代码，其中70份有完整分数；不同版本的结果分别保存。配重复算不会重新判断Excel，也不会自动覆盖原评分记录。

## 获取公开文件与固定环境

先按照[固定环境下载步骤](fixed-34374/README.md#准备环境)克隆本仓库、检出 `new6-public-replay-v4`，下载并加载release中的Docker镜像。只核对分项算术时不需要Docker，仅需Python标准库。

重读一份真实答卷，在 `repro/fixed-34374` 目录执行：

```bash
python3 replay.py --case A1-codex-R08 --out /tmp/new6-public-a1
python3 public-summary/reweight_receipt.py --task A1 --receipt /tmp/new6-public-a1/scores/A1-codex-R08/result.json --output /tmp/new6-public-a1/current-score.json
```

第一条从原工作簿读取事实并评分，逐项依据在 `result.json`；第二条使用该回执计算当前配重，总分在 `current-score.json`。输出目录应为新目录，每次保留独立回执。

## 六题参考与随包校准

以下命令在本仓库根目录执行，使用刚加载的固定依赖镜像。这里运行的是每个Harbor题包自身的基线Judge，与34374快照分别记录。

```bash
python3 repro/replay.py verify --suite reference --image new6-judge:20260905 --out /tmp/new6-public-reference
python3 repro/replay.py verify --suite calibration --image new6-judge:20260905 --out /tmp/new6-public-calibration
```

六题参考在公开文件树中已逐题实际验证，均为满分。原始基线校准为17/18符合预期；B1的 `unbound_bridge_header` 保留已知读取问题，因此校准命令会返回非零退出码。详细回执见[公开题包验证](PUBLIC_VALIDATION.md)。这项差异保留供审查，不修改题目或分数来消除提示。

评分容器不联网、不读取API Key。固定环境使用Python 3.11.16、LibreOffice 7.4.7.2、openpyxl 3.1.5、et-xmlfile 2.0.0、lxml 6.0.1。`repro/Dockerfile`记录基线依赖构建方式，release提供已核对的镜像。

Judge只读取当前任务对应的输入和答卷，参考与Oracle留在评分侧。不要将整份公开审查仓库挂载给参测Agent。这里的“复跑”指离线核验文件，不会启动新的付费Agent。

[全部78份当前已评分原件](../results/current-effective-v2/ANSWERS.md)逐份提供下载与回执，包含固定快照以外已回收的答卷。

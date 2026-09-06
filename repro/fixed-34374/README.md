# 公开固定环境复跑

本目录可直接下载73份已有真实答卷、每次运行实际输入、评分回执和固定Judge公开导出包，不需要私有仓库权限。它对应34374固定快照；73份中70份可评分、3份待判。首页其他Judge版本的有效成绩另行记录，不由本命令重现。

Judge业务代码源提交为 `34374f08f331e7184010c40b401f1630a49df394`。公开包保留评分代码、规则、权重、输入及真实答卷。[公开文件清单](PUBLIC_EXPORT.json)列出当前归档的文件和hash，[打包核验](PACKAGE_VALIDATION.json)记录解包与完整性检查。公开导出使用自己的归档hash及文件锁。

## 准备环境

需要Python 3.12或更新版本、Docker，以及能运行Linux/arm64容器的主机。已验证镜像为Linux/arm64；x86主机需要配置arm64容器模拟，尚未完成x86原生镜像验证。公开release提供镜像，不需要GitHub账号。下列下载需要联网，后续评分容器断网，不调用Agent或模型API。

```bash
git clone https://github.com/alex051107/new6-judge-review-20260905.git
cd new6-judge-review-20260905
mkdir -p /tmp/new6-public-image
curl -fL https://github.com/alex051107/new6-judge-review-20260905/releases/download/new6-public-replay-v4/new6-judge-34374-offline.tar.gz -o /tmp/new6-public-image/new6-judge-34374-offline.tar.gz
docker load -i /tmp/new6-public-image/new6-judge-34374-offline.tar.gz
cd repro/fixed-34374
```

镜像ID应为 `sha256:16d89ab96d5cd066a81496dfb7cfa4b0f77fe031ac7a57183fde686ce13e7f97`。评分入口会核对该ID，不会自动拉取其他镜像。

## 重读一份真实Excel

```bash
python3 replay.py --case A1-codex-R08 --out /tmp/new6-public-a1
python3 public-summary/reweight_receipt.py --task A1 --receipt /tmp/new6-public-a1/scores/A1-codex-R08/result.json --output /tmp/new6-public-a1/current-score.json
```

第一条重新解包、读取原工作簿并执行Judge，详细事实保存在 `scores/A1-codex-R08/result.json`。第二条仅使用该回执的分项信用计算60%配重分数，结果在 `current-score.json`。输出目录必须为新目录。

## 重读全部73份Excel

```bash
python3 replay.py --all --out /tmp/new6-public-all
```

每份保留自己的输入与回执。待判不补零，一份待判不会停止整批。逐次身份见[原件清单](replay-materials/replay-manifest.json)，原有固定快照回执在[receipts](receipts)。

## 只核对保存的分项算术

```bash
python3 public-summary/recompute.py
```

这条命令重建随包已保存分项的统计，**不读取Excel，也不读取刚运行的 `/tmp/new6-public-all` 回执**。查看刚生成的分数用对应case的JSON，再执行上面的 `reweight_receipt.py`。

## 给自己的文件评分

先完成单份复跑以解包Judge，再将自己的答卷与该任务对应的全部输入分别放入 `/tmp/my-answer.xlsx` 和 `/tmp/my-input/`。

```bash
python3 /tmp/new6-public-a1/judge/new6/offline_judge_repair/run_offline.py score --task A1 --answer /tmp/my-answer.xlsx --input-dir /tmp/my-input --out /tmp/new6-public-own
python3 public-summary/reweight_receipt.py --task A1 --receipt /tmp/new6-public-own/run/result.json --output /tmp/new6-public-own/current-score.json
```

`--task`可选A1、A2、B1、B2、C1、C2。自己的输入必须对应题目版本；若用原题输入代替某次运行后的输入，不能据此确认该次运行未修改来源材料。

公开可下载不改变参测隔离要求。Judge归档含独立答案、来源与校准材料，供复评者使用，不能整体挂载给参测Agent。本次公开导出未重跑完整73份评分；原实跑回执与已知读取风险分别保存在[固定结果说明](public-summary/README.md)和[低分核对](public-summary/LOW_SCORE_NOTES.md)。

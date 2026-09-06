# 从原工作簿复现当前成绩

当前主表有90份已评分答卷：67份GPT-5.6 sol/Opus 5保留原Judge路线，23份千问使用本批各题固定的读取器。统一入口重新读取原Excel、实际收集的输入和对应Judge，再核对逐项事实、当前分数与通过结果。

## 准备固定环境

需要Python 3.12以上、Docker和Linux/arm64容器支持。下载后离线评分，不调用Agent或模型API。x86原生环境尚未验证。

```bash
git clone https://github.com/alex051107/new6-judge-review-20260905.git
cd new6-judge-review-20260905
git checkout new6-public-replay-v6
mkdir -p /tmp/new6-public-image
curl -fL https://github.com/alex051107/new6-judge-review-20260905/releases/download/new6-public-replay-v4/new6-judge-34374-offline.tar.gz -o /tmp/new6-public-image/new6-judge-34374-offline.tar.gz
docker load -i /tmp/new6-public-image/new6-judge-34374-offline.tar.gz
```

环境使用既有固定镜像，入口核对镜像ID及源码/原件归档身份。每个评分容器1 CPU、3 GB内存，断网，输入与原答卷只读。

## 复评已有答卷

```bash
python3 repro/replay_final.py --case A2-qwen-R08 --out /tmp/excel-score-one
python3 repro/replay_final.py --all --out /tmp/excel-score-all
```

输出目录应为新目录。`comparison.json`列出每份逐项事实、总分和通过结果是否与发布表一致。详细结果在`qwen/scores/`或`retained/scores/`中，每份都有`current-score.json`和Judge事实回执。

本批43份千问最终文件全部实际离线评过，23份已评分、20份待判。要复查全部43份（含待判），执行：

```bash
python3 repro/qwen-final/replay.py --all --out /tmp/qwen-all-collected
```

[千问逐次表](../results/qwen-final-20260906/README.md)包含状态及具体原因；[原件与Judge下载](qwen-final/README.md)提供对应文件。待判保留空分，不会用旧Judge的成功分数替换，也不当成业务零分。

## 核对统计与参考

```bash
python3 results/current-effective-v3/recompute.py --repo-root . --output-dir /tmp/current-results-check
python3 results/selection/recompute.py --repo-root . --output-dir /tmp/selection-check
```

这两条只复算已保存的分项和统计，不读取Excel。六题参考及校准使用[题包基线入口](README.md#六题参考与随包校准)，与真实答卷的历史Judge分别记录。

[实际验证范围](PUBLIC_VALIDATION.md)列明已执行的检查。完整90份没有在本轮重复全部评分；新增千问43份均已实跑，非千问沿用已验证的原件与Judge路线。不同生成配置及上游运行异常仍需分开审核，文件可复评不等于已完成难度验收。

# 千问答卷：下载与离线评分

这里提供目前收回的43份最终Excel、各自实际输入，以及本批使用的六个Judge读取版本。43份均已离线运行：23份得到分数，20份仍需核实读取或重算问题。另有5个槽位没有最终文件，不能在这里复评。

评分会从原Excel重新读取和计算，不调用模型API。每份原件的身份、Judge源码文件校验值、逐项回执见[本批结果](../../results/qwen-final-20260906/README.md)。

## 运行

先按[环境准备](../CURRENT_REPLAY.md)克隆固定版本并加载Docker镜像，在仓库根目录执行：

```bash
python3 repro/qwen-final/replay.py --case A2-qwen-R08 --out /tmp/qwen-one
python3 repro/qwen-final/replay.py --all --out /tmp/qwen-all
```

输出目录必须是新目录。每份的原始评分依据位于 `scores/<case>/judge-result.json`，已评分答卷的当前总分位于 `scores/<case>/current-score.json`；整批状态在 `summary.json`。待判项保留原因和空分数，不计零。

源码压缩包分为三个文件，脚本自动拼接并按 `archives.json` 校验完整压缩包。获取仓库时保留全部 `judges.zip.part*`；无需手动解压。工作簿下载包各含 `answer.xlsx` 和该试次实际输入 `input/`。

## 下载最终文件

|题目|最终Excel及本次输入|
|---|---|
|A1|[R01](workbooks/A1-qwen-R01.zip) · [R02](workbooks/A1-qwen-R02.zip) · [R03](workbooks/A1-qwen-R03.zip) · [R04](workbooks/A1-qwen-R04.zip) · [R05](workbooks/A1-qwen-R05.zip) · [R06](workbooks/A1-qwen-R06.zip) · [R07](workbooks/A1-qwen-R07.zip) · [R08](workbooks/A1-qwen-R08.zip)|
|A2|[R01](workbooks/A2-qwen-R01.zip) · [R04](workbooks/A2-qwen-R04.zip) · [R06](workbooks/A2-qwen-R06.zip) · [R08](workbooks/A2-qwen-R08.zip)|
|B1|[R01](workbooks/B1-qwen-R01.zip) · [R02](workbooks/B1-qwen-R02.zip) · [R03](workbooks/B1-qwen-R03.zip) · [R04](workbooks/B1-qwen-R04.zip) · [R05](workbooks/B1-qwen-R05.zip) · [R06](workbooks/B1-qwen-R06.zip) · [R07](workbooks/B1-qwen-R07.zip) · [R08](workbooks/B1-qwen-R08.zip)|
|B2|[R01](workbooks/B2-qwen-R01.zip) · [R02](workbooks/B2-qwen-R02.zip) · [R03](workbooks/B2-qwen-R03.zip) · [R04](workbooks/B2-qwen-R04.zip) · [R05](workbooks/B2-qwen-R05.zip) · [R06](workbooks/B2-qwen-R06.zip) · [R08](workbooks/B2-qwen-R08.zip)|
|C1|[R01](workbooks/C1-qwen-R01.zip) · [R02](workbooks/C1-qwen-R02.zip) · [R03](workbooks/C1-qwen-R03.zip) · [R04](workbooks/C1-qwen-R04.zip) · [R05](workbooks/C1-qwen-R05.zip) · [R06](workbooks/C1-qwen-R06.zip) · [R07](workbooks/C1-qwen-R07.zip) · [R08](workbooks/C1-qwen-R08.zip)|
|C2|[R01](workbooks/C2-qwen-R01.zip) · [R02](workbooks/C2-qwen-R02.zip) · [R03](workbooks/C2-qwen-R03.zip) · [R04](workbooks/C2-qwen-R04.zip) · [R05](workbooks/C2-qwen-R05.zip) · [R06](workbooks/C2-qwen-R06.zip) · [R07](workbooks/C2-qwen-R07.zip) · [R08](workbooks/C2-qwen-R08.zip)|

解包后的159个文件是实际评分依赖，包括读取器、业务检查、Oracle和必要源材料。它们只供评分侧使用；参测Agent应仅获得题目及可见输入。

本批A2使用完整的LTGM源工作簿，文件身份记录在[source-integrity.json](source-integrity.json)。Judge源码按[judge-files.json](judge-files.json)固定。对已有回执的复现与模型正式难度验收分别记录；本页不将技术待判解释成业务失分。

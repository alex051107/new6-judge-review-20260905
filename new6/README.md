# NEW6：六题源资料驱动的 Excel benchmark

本目录包含 A/B/C 各两题的题面、真实输入、来源记录、独立 Oracle、参考答案、Evaluator、三套配重、正反例，以及八次实际尝试的原始交付。旧 15 题保持原样。

## 直接复算（不调用模型、不需要 API Key）

需要 Git、Python 3 和运行中的 Docker。私有仓库需获得协作者访问权。

```bash
git clone --branch feature/new6-real-materials-v1 https://github.com/alex051107/excel-multimodal-benchmark.git
cd excel-multimodal-benchmark
python3 new6/repro/reproduce.py build
python3 new6/repro/reproduce.py verify --suite all --out new6/repro/results-first
```

最后一条检查 6 份参考、8 次实际尝试和 61 个校准案例；输出目录必须为空。每例保存实际评分 JSON、运行日志、原件哈希和必要的隔离重算证据。总回执为输出目录的 `receipt.json`。

给自己的答卷评分：

```bash
python3 new6/repro/reproduce.py score --task A1 --answer /absolute/path/answer.xlsx --input-dir /absolute/path/post-run-input --out /absolute/path/fresh-score
```

`--input-dir` 是 Agent 完成后的原输入目录，用于检查应受保护的信息，不是参考答案目录。A1/A2/B1/B2/C1/C2 均使用相同入口。

## 当前版本与归档结果

当前六题采用 A1/A2/B1/C2 的原任务、B2“三期真实资料＋接手旧简报”v3，以及C1“原估算＋修订往来”v2。上面的75例套件固定为原发布参考、开发答卷和校准回放，不自动把B2/C1新任务义务加给旧答卷。`reproduce.py score --task B2/C1`仍对应该归档套件的任务版本。

新版答卷须使用明确的版本入口，依赖与固定Linux镜像见 [评分环境](repro/README.md)：

```bash
python3 new6/candidates/b2-three-release-v3/score_submission.py --answer /absolute/path/answer.xlsx --input-dir /absolute/path/post-run-input --out /absolute/path/fresh-b2-score
python3 new6/candidates/c1-revision-v2/score_submission.py --answer /absolute/path/answer.xlsx --input-dir /absolute/path/post-run-input --out /absolute/path/fresh-c1-score
```

两入口复用同一离线评分封装，保存原件哈希、三套分数和隔离重算证据，API0。新版本的参考/Oracle和校准分别存放在各候选目录，不声称已被原75例套件覆盖。新用户应在固定Docker环境运行，宿主机引擎不同可能产生差异；具体命令见各版README。

- [唯一当前交付报告：六题阶段、实际分数、费用及阻塞](NOW_REPORT_ZH.md)
- [当前每项配重与历史比例对照](docs/RUBRICS_CURRENT_ZH.md)
- [新版C1：业务判断、19项校准与复跑](candidates/c1-revision-v2/tasks/NEW6-C-COST-WORKPAPER-001/README_ZH.md)
- [新版B2：三期材料、旧简报与复跑](candidates/b2-three-release-v3/README_ZH.md)
- [当前6×3×8队列及模型路由问题](campaigns/new6-current-v3-144/CAMPAIGN_ZH.md)
- [原冻结套件清单](repro/manifest.json) 与 [原套件断言](repro/suite.json)

历史8次开发尝试费用合计$1.494950；它们不是每题n=8。正常执行且确认缺Excel或文件损坏记0；供应商、环境、运输和合法解析限制保留空分。新版真实尝试持续收集，六题正式难度尚未验收。

## 资料与权限

这是公开模型/统计资料的 benchmark 重构，题面不代表真实客户委托。来源、版本、下载哈希和使用条件见每题 `metadata/source_manifest.json` 及总来源记录。当前仓库保持私有；公开访问的第三方原资料不自动等于允许再次公开分发，改变可见性前需逐项核对授权。仓库内不分发 API Key。

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

## 当前结果

| 题 | 内容 | 最新实际主方案分数 | 状态 |
|---|---|---:|---|
| A1 | Damodaran Amazon 2018 估值恢复 | 0.627228 | 已评分 |
| A2 | World Bank LTGM 长期情景恢复 | 0.317111 | 已评分 |
| B1 | UCI 零售十月月结与月间分析 v2 | 0.682948 | 已评分 |
| B2 | ONS LI01 两期地方劳动力比较 | 0.920833 | 已评分 |
| C1 | Falmouth 成本 PDF 工作底稿 | — | 首尝没有生成答卷 |
| C2 | USPS 零售价目表与动态报价 | 0.599156 | 第二次已评分；首次缺答卷 |

B1 第一版另保留原 Judge 和原答卷，主方案 0.95。八次调用供应商核对费用合计 **1.494950 美元**。缺答卷和解析限制使用空分数，不能冒充业务零分。六题已构建并有参考/校准；当前小样本不构成正式难度合格或 pass@8 结论。

- [逐题 Judge 逻辑、配重和能力解释](docs/JUDGE_LOGIC_ZH.md)
- [复现环境、状态、Harbor 新运行与限制](repro/README.md)
- [六题业务结果与费用证据](NOW_REPORT_ZH.md)
- [冻结文件清单](repro/manifest.json) 与 [校准断言](repro/suite.json)

## 资料与权限

这是公开模型/统计资料的 benchmark 重构，题面不代表真实客户委托。来源、版本、下载哈希和使用条件见每题 `metadata/source_manifest.json` 及总来源记录。当前仓库保持私有；公开访问的第三方原资料不自动等于允许再次公开分发，改变可见性前需逐项核对授权。仓库内不分发 API Key。

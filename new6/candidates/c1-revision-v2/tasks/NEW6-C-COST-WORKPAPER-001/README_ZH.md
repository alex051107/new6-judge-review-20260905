# C1 新版：估算审阅与范围变更

本题把一份真实公开成本估算转成可以继续审阅的工作簿。新增材料是一份明确标注为项目编写情景的短往来，包含同范围供暖/空气源热泵报价的版本替换、设计深化风险费率调整，以及一个仍未批准的石棉清除选项。原 PDF 的金额、范围和限制保留。

Agent 只接收 `instruction.md` 和 `data/input_files/`。参考答案、源事实表、独立 Oracle、评分代码和反例都不进入任务输入。原 C1、原答卷与旧运行继续保留在原路径，本目录是独立版本。

## 原材料与答案核验

来源为 October 2024 Revision A 的 Falmouth Order of Cost Estimate。已亲自渲染第2–5页：第4页的供暖/ASHP £432,000 已包含于元素成本；通风为 £55,000；第3页明确排除石棉清除。新往来中的价格及政策是用户指定的重构场景假设，不是供应商或客户来信。

参考由可审阅的 Excel 公式计算，独立 Oracle 使用 Decimal 逐阶段计算并另验乘法恒等式。19个关键参考结果与原生重算一致。当前成本限额为 £2,039,471.588；原印刷限额为 £1,971,278，差额为 £68,193.588。原模型按完整精度重算的限额为 £1,971,277.8525；明确采用该基准时，差额为 £68,193.7355。

原打印值仍是源事实。整镑显示、完整精度数值、明确标注的原印刷/原重算比较基准都可以得满分。原重算比较须保留该基准金额；Judge 不替候选补出缺失的自核对金额。

## 分值和能力

| 要求 | 主方案 | 平衡方案 | 持续使用方案 |
|---|---:|---:|---:|
| 原来源数据、范围和限制保留 | 15 | 20 | 10 |
| 有效报价版本、替换与待决范围 | 20 | 20 | 20 |
| 当前成本链、费率与计算基数 | 15 | 20 | 15 |
| 新旧差额及候选自身核对 | 10 | 10 | 10 |
| 公开修改后的实际响应 | 35 | 25 | 40 |
| 原估算与往来的来源追踪 | 5 | 5 | 5 |

一套事实同时计算三方案；主方案未舍入分数达到0.70即通过，没有额外门槛或封顶。配重在新 Agent 调用前按业务重要性固定，不根据答卷分数调整。

动态在隔离副本中修改供暖包价格、公开的费率及其联合变化，检查20个确实应变化的成本阶段和3个应变化的最终核对。修改后数值与实际变化量须同时正确。单独调整未批准石棉选项的价格不会改变批准范围，该不变化事实归范围判断。源事实及无关项保护单列，零变化不赚有效响应分；控制输入读回只是检验变化实际执行的证据。

原价、版本判断、当前数值、候选自身一致与变化响应分别记录。候选可以自由安排布局和使用等价公式。废报价可以省略；若展示，则其金额和废弃状态必须准确。已展示的错误或矛盾结果不会因另有一张正确表而被忽略；同表重复与遗漏按实际记录检查。额外表述若无法安全读取，或合法公式引擎不支持，则待判而非补零。

## 离线复跑

依赖 Python 3、openpyxl、lxml 和 LibreOffice。此任务调用仓库已有 `new6/common/runtime.py`，不需要 API。候选构造时仅复制了现有 C1 语义读取函数与狭义 OOXML 编辑工具，没有新增通用公式解释器。

在仓库根目录：

```bash
python new6/candidates/c1-revision-v2/tasks/NEW6-C-COST-WORKPAPER-001/metadata/calibrate.py
python new6/candidates/c1-revision-v2/score_submission.py --answer /absolute/path/answer.xlsx --input-dir /absolute/path/post-run-input --out /absolute/path/fresh-c1-score
```

在固定的Linux评分环境运行（源仓库根目录，`/absolute/path/submission/`内放`answer.xlsx`及运行后`input/`）：

```bash
python3 new6/repro/reproduce.py build
mkdir -p /absolute/path/fresh-c1-evidence
docker run --rm --network none --cpus 2 --memory 4g \
  -v "$PWD:/workspace:ro" \
  -v /absolute/path/submission:/candidate:ro \
  -v /absolute/path/fresh-c1-evidence:/results \
  new6-judge:20260905 python /workspace/new6/candidates/c1-revision-v2/score_submission.py \
  --answer /candidate/answer.xlsx --input-dir /candidate/input --out /results/run
```

`result.json`记录三个profile、逐项事实和原件未变化的证据；总分判定使用未舍入值。输出目录`run`必须尚不存在。该命令使用已通过Harbor参考smoke的同一镜像与`run_case`封装，不启动Agent或API。

固定分母及输入变化定义在 `tests/fact_contract.json`；每例的失分/保留断言在 `fixtures/manifest.json`；最终19类通过回执在 `validation/final/receipt.json`，更早回执保留了修复过程。标准 `calibrate.py` 会调用实际 Judge 重算各个案例，不借用保存分数。反例可能仍高于通过线，只有预定事实的失分与保留符合预期才算校准成功，不能按文件名认定整体失败。

当前构造与校准不等于正式难度合格。实际三系统×8次结果由主运行队列收集。一般化 agentic 解析、额外负项和第三方 PDF 公开再分发权限尚未被本次离线构造证明。

实际试跑已提交 Codex/Claude 各8次，Qwen供应商路由待核实。Linux Harbor参考评分100；见[运行收据](../../../../campaigns/c1-revision-v2-24/RUN_RECEIPT.json)与[当前报告](../../../../NOW_REPORT_ZH.md)。

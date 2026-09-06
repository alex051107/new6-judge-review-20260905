# 三份低分答卷：固定 Judge 的风险核对

**固定提交 34374f08f331e7184010c40b401f1630a49df394 所属 Judge 快照未解决本次已确认的读取风险。不能把同版重现低分写成业务能力不足已获验证。** 本次限定读取 A1 · Opus 5 · R03、C2 · GPT-5.6 sol · R02/R08 的现存原件证据和源码，没有运行评分或改动 Judge。

## A1 · Opus 5 · R03

固定快照中 `year_regions` 与 `read` 两个函数的 AST 与先前存在错误的版本完全一致。代码为 `new6/tasks/NEW6-A-FIN-RESTORE-001/tests/evaluate.py`。

原件 base 年度在第 1 行，review 年度在第 2 行；旧回执将第 2 行绑定为 base。它用 review 的 `Q8=40,244.25` 代替正确 base 的 `C8=5,249.25`，也把 review 的利润率当作 base。已有原件重算值与单元格公式支持这个缺陷，固定提交没有相应的绑定逻辑修复。

答卷 review 自身仍有真实错误：首年再投资引用空白基期收入；终值再投资引用文字年度表头。真实业务错误与 Judge 对 base/review 的误判必须分别列出。旧总分 32.30 不能直接支撑整体能力不足。

## C2 · GPT-5.6 sol · R02/R08

固定快照的 `new6/tasks/NEW6-C-PARCEL-TARIFF-001/tests/evaluate.py` 仍存在两项风险：

- `priority_usd` / `ground_usd` 的列名映射未包含 R08 实际使用的 `Priority Mail Retail` / `Ground Advantage Retail`。未绑定报价表会继续影响报价和更新控件识别。R02 的 `Quote Calculator!H5:I5` 也使用这两种 Retail 表头，本版回执仍未识别报价表，四次更新均未绑定控件。
- `rkey` 按数值、单位建立精确键；R001 按此键找价格，R002 也按未经单位转换的 band 建键。`16 oz` 与 `1 lb` 因而仍是不同键。`converted_weight` 用于报价重量验证，不能说明价格表的等价单位已受支持。`rkey` 与 `source_facts` 的 AST 均和已审查旧版完全一致。

R08 先前独立核对 192 个价格和 36 个报价金额均正确，不能把未识别现有价格/报价形成的低分写成能力不足。以上代码核对没有产生替代正式分数，也没有验证全部扣分项。

## 本版真实回执：风险仍然存在

三例新回执现已全部生成，状态均为 `SCORED`。以下数字是各自 `result.json` 内既有 `score_decimal` 的百分制展示，不替代发布汇总所采用的配重；判断依据是读取事实与单元格对应关系。

| 答卷 | 回执内分数 /100 | 本版读取证据 | 结论 |
|---|---:|---|---|
| A1 · Opus 5 · R03 | 32.2961 | `evidence.candidate_tables` 仍只有 `header_row=2, case=base, left_column=1, right_column=27`；`baseline_mismatches` 仍把 `40,244.25` 记作 base 首年再投资。 | 原 base/review 错绑被本版实际回执再次证实，未解决。 |
| C2 · GPT-5.6 sol · R02 | 50.5887 | 发现两个价格表、没有报价表；192 项价格事实全部正确，R001=1、R002=1、R006=1。R003 的 `Q01.priority_usd`、`ground_usd` 等仍为 `actual=null`；四次 `actual_control_cells` 都是空列表。原件 `Quote Calculator!H5:I5` 明示两种 Retail 报价，下面已有公式。 | 本版已给价格表完整信用，但报价表漏认和更新控件未绑定仍在。不能把报价缺失/更新失败的这些扣分解释成业务能力不足。 |
| C2 · GPT-5.6 sol · R08 | 29.6859 | 发现两个价格表、没有报价表；R001 对 `ground, 1, lb, zone 1` 的实际值为空、期望 9.55，原件等价价格放在 16 oz 行。R003 的报价实际值仍为空，四次更新的控件列表仍为空。 | 等价重量单位、Retail 报价表和更新控件读取问题均仍影响本版回执。 |

回执位置分别为 `results/A1-claude-R03/result.json`、`results/C2-codex-R02/result.json`、`results/C2-codex-R08/result.json`，由本次固定 Judge 运行保留。代码来源固定于提交 `34374f08f331e7184010c40b401f1630a49df394` 的源码归档；这里使用归档内路径，不提供尚不存在的公开文件链接。

这三例的低分不能作为已排除 Judge 缺陷的能力证据。A1 已有明确的 review 公式错误仍成立；C2 R02 的价格提取改善也应如实保留。没有对三份答卷重新业务评分，也没有据此生成替代 reward 或通过结论。

检查时间：2026-09-06T03:08:08.696504+00:00

# C2 评分程序

这里是评测器运行时需要的文件。参测Agent只能看到 `data/input_files/`，不能挂载本目录。

| 文件 | 用途 |
|---|---|
| `test.sh` | Harbor评分入口 |
| `run_verifier.py` | 读取最终 answer.xlsx，保存逐项回执与分数 |
| `adapter.json` | 指定当前任务 |
| `new6/repro/score.py` | 调用对应Judge，按需要在隔离副本中重算 |
| `new6/common/` | 公式重算、状态处理和冻结权重汇总 |
| `new6/tasks/NEW6-C-PARCEL-TARIFF-001/tests/` | 本题的读取与业务核验代码 |
| 同一运行目录中的 `metadata/`、`solution/` | Judge使用的独立事实、Oracle及核验依据 |
| 同一运行目录中的 `data/input_files/` | 用来核对候选是否保留原始输入的基准副本 |
| 同一运行目录中的 `rubric.json` | 该题包基线Judge的冻结判据与权重 |

目录保留原Judge的相对路径，避免整理文件改变读取行为。人工反例、调试工作簿和历史回执已移出题包；校准案例在仓库根目录 `validation/calibration/C2/`。本题包基线与报告中实际答卷的Judge版本分别记录，当前最终分数请使用仓库的统一复评入口。

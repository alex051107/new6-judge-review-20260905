# NEW6 independent design and Judge review

这是六道 Excel benchmark 的公开审查副本，可匿名读取。请先审查它是否符合原始能力目标，再判断具体题目/Judge。当前主目标是让下游得到正确、可核验且能继续使用的 ABC 交付，不追求单纯压低分数。

- [给 ChatGPT Pro 的审查请求](new6/review/round1/PRO_REQUEST_ZH.md)
- [六题 Judge 逻辑与配重](new6/docs/JUDGE_LOGIC_ZH.md)
- [目前真实结果及业务错误](new6/NOW_REPORT_ZH.md)
- [完整文件与缺失范围](REVIEW_SCOPE.json)

每题目录包含 instruction、review brief、rubric、Evaluator 和独立 Oracle 代码；来源清单给出官方来源与版本。已执行的独立校准结果见 new6/repro/validation_receipt.json，断言见 suite.json。

这个公开副本没有第三方源二进制、原候选xlsx或中间重算文件，不能单独执行完整复评分。完整可复跑包在原私有仓库；公开材料中的完整复跑说明指向该原仓库，所述通过结果是已有回执，不代表本镜像包含全部输入。代码里需要原二进制才能验证的结论，请明确说明证据缺口，不能假称已打开。某些源仓库相对链接在此副本无对应文件；以 REVIEW_SCOPE.json 为准。

来源版本：b1176f73a1472c2bd70595ad75c955b426450ee8。历史8次尝试不能当作每题n=8的正式难度结论。新6×8×3运行另行进行；本快照没有声称新144次已完成。

本地机器的绝对路径已去敏化；这不改变所引用的评分事实、配重或已报告分数。

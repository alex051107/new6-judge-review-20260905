# B2 三期资料与旧简报更新

本版使用 ONS LI01 January 2023（官方更正替换文件）、January 2024 和 January 2025。对应实际观察期是 2021年10月—2022年9月、2022年10月—2023年9月、2023年10月—2024年9月。2023文件封面为February 2023，原官方更正说明完整保留。

Agent接手一份仅用前两期真实数据重构的正确旧简报，更新两段都出现失业率上升、就业率下降的地区名单及配套数字、图和说明，保留旧分析。正确静态交付可得满分。本版不启动会议参数动态备选。

独立重算得到313个范围内地区代码、290个完整可比地区、21个合格地区。新前五与旧前五只重合Norwich；其他四个进入、四个退出，形成需要实际解释的分析更新。详细数值在私有Judge参考资料，候选输入没有三期答案。

主配重为15/25/25/20/15，分别对应口径与可比性、名单、数字、变化解释与当前图文、旧分析与溯源。规则和事实分母见任务内 `metadata/scoring_contract.md`。三套权重计算同一事实，未舍入分数达到70才通过。

在仓库根目录复跑离线评分：

```sh
python3 new6/candidates/b2-three-release-v3/tasks/NEW6-B-LABOUR-BRIEF-001/tests/evaluate.py /absolute/path/answer.xlsx --input-dir /absolute/path/post-run-input
```

公式答卷应先用已有 `new6/repro/score.py` 的 `run_case` 接口在隔离副本重算，或用下述版本入口，原答卷保持只读：

```sh
python3 new6/candidates/b2-three-release-v3/score_submission.py --answer /absolute/path/answer.xlsx --input-dir /absolute/path/post-run-input --out /absolute/path/fresh-score-dir
python3 new6/candidates/b2-three-release-v3/tasks/NEW6-B-LABOUR-BRIEF-001/metadata/calibrate.py --out /absolute/path/fresh-calibration-dir
```

依赖为已有NEW6环境中的openpyxl、lxml和LibreOffice；无API调用。首次构造材料可由 `metadata/oracle_recompute.py`、`metadata/build_reference.mjs` 和 `metadata/calibrate.py --build` 重建。工作簿使用已有artifact-tool作者依赖，评分不需要它。旧B2的92.08分、动态候选76.72分及本版新尝试分别保留，不能用三期新义务重罚两期历史答卷。

首答已完成：主方案58.17分，均衡57.05分，持续使用58.45分；供应商23条请求唯一归属，总费用$0.156904。详细业务错误、Judge读取修正与原件复跑见 [ACTUAL_RESULT_ZH.md](ACTUAL_RESULT_ZH.md)。

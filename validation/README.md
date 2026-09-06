# 题包校准与整理验证

`calibration/`保留18份指定的等价实现、业务错误和读取边界案例，用来核查Judge。它们由项目构造，不是Agent的真实答卷，也不进入模型均分或通过率。

运行方式与以前相同：

```bash
python3 repro/replay.py verify --suite calibration --image new6-judge:20260905 --out /tmp/new6-calibration-check
```

原基线已知结果为17/18，B1的一个读取边界案例仍有差项，详见[验证说明](../repro/PUBLIC_VALIDATION.md)。本轮只整理文件，不调整Judge来改变该结果。

`package-cleanup.json`记录从正式题包移出的文件。历史开发材料已转入本地内部归档，不再随当前任务目录交付。参考、Oracle、当前评分回执和真实答卷仍按复跑需要保留。

# B2 加难版本的实际试跑与 Judge 修复

加难版已构造并有一次真实试跑。修复读取和合法表示误罚后，同一原答卷得 **76.72分**，按现行候选规则通过。未修改答卷、业务规则、权重或四个动态测试输入，没有新增Agent调用。一个答卷尚不能确认正式难度达标。

原版只要求两期比较、排除记录、前五地区及报告。加难版继续使用相同ONS真实来源，增加全地区资格筛选、三种固定政策比较，以及两项独立门槛和复核名额变化后的实时工作簿。缺失/不可比不能当零；有资格但排不上名额必须与入选区分；当前名单与原始统计/固定场景分开。

这次修复了四类读取误差：合法空字符串缓存被当成未计算；常见Jan年份表头/按指标分列的排除理由读不出；固定/实时短名单被误混为描述性前五；固定情景列标题被当成可编辑数值输入。另纠正了图表、pp缩写及来源版本名称的过窄要求：题面没有要求一张图必须包含两种指标，也没有要求引用必须照抄文件名。

| 模块 | 分值 | 此次实际得分 |
|---|---:|---:|
| 原统计交付 | 30 | 28.50 |
| 固定筛选与清单 | 20 | 19.98 |
| 实时复核 | 50 | 28.24 |

真实业务错误仍保留：标为“Current Selected”的列实际装了排序字符串；当前名单初始显示10个地区，而名额是5；较小失业增幅排到了前面；名额改为3后，第4名以后仍然保留。这些错误是读取实际表头、实际行和重算结果得到的，Judge没有替Agent挑选另一列来补救。

| 已披露的变化 | 应变化事实数 | 实际错误数 |
|---|---:|---:|
| Unemployment threshold pp=2, Employment decline threshold pp=1, Review places=5 | 40 | 3 |
| Unemployment threshold pp=1, Employment decline threshold pp=5, Review places=5 | 31 | 19 |
| Unemployment threshold pp=1, Employment decline threshold pp=1, Review places=3 | 9 | 8 |
| Unemployment threshold pp=0.5, Employment decline threshold pp=0.5, Review places=7 | 39 | 8 |

静态结果主要正确，实时部分只拿到28.24/50分。其中名额单独缩减这项，9个应变化事实有8个错误。当前总分仍高于70，后续难度结论应看更多固定版本真实答卷；没有为了改成不通过而继续调低分数。

本次复核：完整正确参考100；等价公式100；只有实时部分写死的校准例60且只损失R009；源图表缓存错误继续扣R005。合法空缓存与真正未重算的公式仍分开。原始供应商/运行错误不改作业务零分。

主副本初始完整原生复评在 validation/reader_v21/actual/evaluation.json；最终对同一原生事实修正静态语义判定后在 validation/reader_v21/actual_final/evaluation.json，清楚记录复用的动态事实。原始试跑的JUDGE_ERROR回执保留在campaign目录。

复核脚本：validation/check_reader_v21.py；随后 validation/check_chart_v21.py。当前修复不改变运行中的144次冻结任务。

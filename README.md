# NEW6 independent design and Judge review

当前六题的公开代码与文本审查副本，原仓库固定提交 **5535c6bf6a20d5e1a25a642fe3cd6234219bdd7c**。当前任务为A1/A2/B1/C2原任务、B2三期旧简报v3、C1修订成本审阅v2。原144运行继续使用b1176f7的冻结材料；它与新版批次分开计数。

- [当前六题状态、实际分数、费用与阻塞](new6/NOW_REPORT_ZH.md)
- [六题逐项配重与三套profile](new6/docs/RUBRICS_CURRENT_ZH.md)
- [C1新版：业务判断、独立答案、19项校准与复跑](new6/candidates/c1-revision-v2/tasks/NEW6-C-COST-WORKPAPER-001/README_ZH.md)
- [C1候选题面](new6/candidates/c1-revision-v2/tasks/NEW6-C-COST-WORKPAPER-001/instruction.md)、[可见往来说明](new6/candidates/c1-revision-v2/tasks/NEW6-C-COST-WORKPAPER-001/data/input_files/review_correspondence.md)
- [B2新版：三期材料与接手旧简报](new6/candidates/b2-three-release-v3/README_ZH.md)
- [当前3系统各8次的运行规则与限制](new6/campaigns/new6-current-v3-144/CAMPAIGN_ZH.md)
- [文件清单及审查范围](REVIEW_SCOPE.json)

C1独立原生计算19/19、校准19/19及Linux参考100已经通过，C1新版Claude和Codex各8次均已终态，其中Codex后4次为推理接口429失败，不能计作有效业务样本；B2 Codex继续。Judge v2.1新增6项读取校准通过，一份真实原件Linux主分41.9651770976，缺Excel的实际尝试为0；其余已保存答卷仍有布局解析待判。A2同原件R07修复合法参数引用和表头后100分；B2实际图片图不能当成缺图扣分。高分、业务失败和解析限制分别保留，当前不宣称六题正式难度合格。

**此公开镜像不含第三方原PDF/XLSX、候选答卷或中间重算二进制，不能单独完整复评分。** 完整材料在[私有原仓库固定版本](https://github.com/alex051107/excel-multimodal-benchmark/tree/5535c6bf6a20d5e1a25a642fe3cd6234219bdd7c/new6)，需要访问权或另行取得相应附件。文中的复跑命令针对完整仓库；缺二进制的判断须说明证据缺口。`CONSTRUCTOR_ONLY.md`及Oracle仅供审查/构造，不进入Agent输入。

审查重点：每个track是否交出能被下游核验和继续使用的工作簿；公开义务与计分事实是否对应；高权重是否落在关键能力；合法实现是否被误罚，以及下一版最值得修改的一个业务因素。不要以最低分选profile，也不要用人工反例比例估计自然失败率。

C1实际证据：[正常结束但未保存Excel](new6/campaigns/c1-revision-v2-24/C1_R02_DELIVERY_FAILURE.json)、[原件41.97分的业务失分与复跑](new6/candidates/c1-revision-v2/tasks/NEW6-C-COST-WORKPAPER-001/metadata/reader_v21/REPORT_ZH.md)、[Linux独立回执](new6/campaigns/c1-revision-v2-24/C1_V21_LINUX_RECEIPT.json)。[完整请求系统配置](new6/campaigns/new6-current-v3-144/SYSTEM_CONFIGS.json)只含密钥占位符；B2新版Claude8次实收$1.089910已逐请求唯一用量归属。

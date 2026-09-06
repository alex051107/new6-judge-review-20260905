# 来源及选择边界

快照取当前主台账03:15:27 UTC。55份当前声明版本成功回执优先；21份当前待判且原件未变的固定34374成功回执补缺；新增离线批次B2-Qwen R08再补1份。所有原始槽位保留，新trial不覆盖历史原73的档案。完整77份原始回执及绝对原件映射存于私有current-effective-v1。公开receipts只是分项摘录。

固定补充回执的代码身份可验证至34374f08f331e7184010c40b401f1630a49df394及对应发布锁。主台账有明确各题Judge label，但部分实现属于可变工作树，不能以主树HEAD772f069或版本标签代替真实完整评分代码提交；这些selected_judge_commit留空。当前表没有宣称全部Judge代码已经公开成不可变版本。

同一槽位当前Judge待判而较早有效回执可用时，current_status/current_judge_label与selected_judge_label、source_priority同时保留。选择不以高分或低分为标准。固定34374的同版复跑与本表分开，不将本表说成统一Judge数据。

三份已知风险依旧单列：A1-claude-R03的base/review错绑与真实错误并存；C2-codex-R02/R08的Retail报价、等价单位及更新控件绑定问题需要按实际选中版本复核，不凭标签升级就宣称已消除。

窄组：A1 R004、A2 R004、B1 R007/R008、B2 R004/R005、C1 R005、C2 R004。组内原权重比例不变，计算重点50/60/70；不改事实或处罚。Pass@k未在所选回执下认证完整同Judge同配置人口，因此留空。

[77份原始回执公开导出](raw-receipts/README.md)。固定环境和答卷下载见[复跑入口](../../repro/README.md)。

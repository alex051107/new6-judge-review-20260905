# 千问新增答卷离线评分

回收快照为 23/48：A1 1、A2 1、B1 8、B2 1、C1 6、C2 6。回收指已结束试次中收集到最终答卷，不代表评分成功或业务正确。

本批新增 7 份最终答卷使用固定 Judge `34374f08f331e7184010c40b401f1630a49df394`，单容器顺序离线评分；未运行生成 Agent 或调用模型 API。1 份成功评分，6 份为技术待判；待判分数为空。所有输入及原始答卷只读。

`new7-records.json` 保留本批身份及原/50/60/70配重；`receipts/` 为公开分项事实与错误原因。完整 Judge JSON、工作簿及日志保存在内部归档。`current-records144.json` 是独立新快照，保留被新试次替换的上一快照身份；旧发布快照未被覆盖。其余旧回执继续采用已发布的当前有效版本，因此这是多 Judge/配置的浏览汇总，不能用于同版本难度验收。

`qwen-summary.csv` 均分分母仅包括成功评分答卷。重点能力 60% 属分项配重复算，Judge 原评分另行保留；6 份解析待判没有记零。

## 新增原件下载

| 试次 | 文件 |
|---|---|
| A1-qwen-R08 | [原答卷及实际输入](workbooks/A1-qwen-R08.zip?raw=true) |
| B1-qwen-R08 | [原答卷及实际输入](workbooks/B1-qwen-R08.zip?raw=true) |
| C1-qwen-R01 | [原答卷及实际输入](workbooks/C1-qwen-R01.zip?raw=true) |
| C1-qwen-R02 | [原答卷及实际输入](workbooks/C1-qwen-R02.zip?raw=true) |
| C1-qwen-R03 | [原答卷及实际输入](workbooks/C1-qwen-R03.zip?raw=true) |
| C1-qwen-R04 | [原答卷及实际输入](workbooks/C1-qwen-R04.zip?raw=true) |
| C1-qwen-R05 | [原答卷及实际输入](workbooks/C1-qwen-R05.zip?raw=true) |

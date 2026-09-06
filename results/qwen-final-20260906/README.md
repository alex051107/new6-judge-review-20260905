# 千问现有最终答卷：逐次分数与待判项目

本批选定48个槽位，收回43份最终工作簿；逐份使用本批每题固定的Judge快照离线重评。均分只纳入已评分答卷，不用旧回执替换本批待判，也不把未收回或待判填零。

表中均为百分制。“当前分”沿用已发布能力分组与60%配重；“Judge原分”保留原始业务权重。通过按未舍入当前分≥70判断。

|题目|已收回|可评分|待判|未收回|Judge原均分|当前均分|通过次数|
|---|---:|---:|---:|---:|---:|---:|---:|
|A1|8|8|0|0|91.12|90.79|8|
|A2|4|1|3|4|76.48|75.83|1|
|B1|8|3|5|0|99.93|99.96|3|
|B2|7|5|2|1|94.32|90.50|5|
|C1|8|1|7|0|79.88|77.59|1|
|C2|8|5|3|0|77.06|74.00|3|

有最终文件的试次中，部分在文件生成后发生上游异常；它们可以复核工作簿，但不据此当作正常完成的正式难度样本。requested模型为Qwen 3.8接口，供应商实际响应身份尚未认证。正式Pass@1、Pass@8留空。[按上游状态分层统计](upstream-stratified-summary.csv)保留这一区别。

## 全部最终答卷逐次分数

|题目/试次|Judge原分|当前分|通过|评分状态|运行终态|
|---|---:|---:|---|---|---|
|[A1-qwen-R01](receipts/A1-qwen-R01.json)|86.44|85.66|是|已评分|有上游异常|
|[A1-qwen-R02](receipts/A1-qwen-R02.json)|86.44|85.66|是|已评分|有上游异常|
|[A1-qwen-R03](receipts/A1-qwen-R03.json)|86.44|85.66|是|已评分|有上游异常|
|[A1-qwen-R04](receipts/A1-qwen-R04.json)|86.16|85.49|是|已评分|有上游异常|
|[A1-qwen-R05](receipts/A1-qwen-R05.json)|99.00|99.38|是|已评分|未记录异常|
|[A1-qwen-R06](receipts/A1-qwen-R06.json)|86.44|85.66|是|已评分|有上游异常|
|[A1-qwen-R07](receipts/A1-qwen-R07.json)|99.00|99.38|是|已评分|未记录异常|
|[A1-qwen-R08](receipts/A1-qwen-R08.json)|99.00|99.38|是|已评分|未记录异常|
|[A2-qwen-R01](receipts/A2-qwen-R01.json)|—|—|—|待判|未记录异常|
|[A2-qwen-R04](receipts/A2-qwen-R04.json)|—|—|—|待判|有上游异常|
|[A2-qwen-R06](receipts/A2-qwen-R06.json)|—|—|—|待判|未记录异常|
|[A2-qwen-R08](receipts/A2-qwen-R08.json)|76.48|75.83|是|已评分|未记录异常|
|[B1-qwen-R01](receipts/B1-qwen-R01.json)|—|—|—|待判|有上游异常|
|[B1-qwen-R02](receipts/B1-qwen-R02.json)|100.00|100.00|是|已评分|未记录异常|
|[B1-qwen-R03](receipts/B1-qwen-R03.json)|—|—|—|待判|有上游异常|
|[B1-qwen-R04](receipts/B1-qwen-R04.json)|100.00|100.00|是|已评分|有上游异常|
|[B1-qwen-R05](receipts/B1-qwen-R05.json)|99.80|99.88|是|已评分|有上游异常|
|[B1-qwen-R06](receipts/B1-qwen-R06.json)|—|—|—|待判|有上游异常|
|[B1-qwen-R07](receipts/B1-qwen-R07.json)|—|—|—|待判|未记录异常|
|[B1-qwen-R08](receipts/B1-qwen-R08.json)|—|—|—|待判|未记录异常|
|[B2-qwen-R01](receipts/B2-qwen-R01.json)|89.22|81.52|是|已评分|未记录异常|
|[B2-qwen-R02](receipts/B2-qwen-R02.json)|90.22|83.24|是|已评分|未记录异常|
|[B2-qwen-R03](receipts/B2-qwen-R03.json)|97.15|96.29|是|已评分|未记录异常|
|[B2-qwen-R04](receipts/B2-qwen-R04.json)|—|—|—|待判|未记录异常|
|[B2-qwen-R05](receipts/B2-qwen-R05.json)|95.00|91.43|是|已评分|未记录异常|
|[B2-qwen-R06](receipts/B2-qwen-R06.json)|—|—|—|待判|未记录异常|
|[B2-qwen-R08](receipts/B2-qwen-R08.json)|100.00|100.00|是|已评分|未记录异常|
|[C1-qwen-R01](receipts/C1-qwen-R01.json)|—|—|—|待判|有上游异常|
|[C1-qwen-R02](receipts/C1-qwen-R02.json)|—|—|—|待判|有上游异常|
|[C1-qwen-R03](receipts/C1-qwen-R03.json)|—|—|—|待判|未记录异常|
|[C1-qwen-R04](receipts/C1-qwen-R04.json)|—|—|—|待判|未记录异常|
|[C1-qwen-R05](receipts/C1-qwen-R05.json)|—|—|—|待判|有上游异常|
|[C1-qwen-R06](receipts/C1-qwen-R06.json)|—|—|—|待判|有上游异常|
|[C1-qwen-R07](receipts/C1-qwen-R07.json)|—|—|—|待判|有上游异常|
|[C1-qwen-R08](receipts/C1-qwen-R08.json)|79.88|77.59|是|已评分|有上游异常|
|[C2-qwen-R01](receipts/C2-qwen-R01.json)|—|—|—|待判|未记录异常|
|[C2-qwen-R02](receipts/C2-qwen-R02.json)|90.06|83.39|是|已评分|有上游异常|
|[C2-qwen-R03](receipts/C2-qwen-R03.json)|50.00|30.77|否|已评分|未记录异常|
|[C2-qwen-R04](receipts/C2-qwen-R04.json)|99.81|99.88|是|已评分|未记录异常|
|[C2-qwen-R05](receipts/C2-qwen-R05.json)|—|—|—|待判|有上游异常|
|[C2-qwen-R06](receipts/C2-qwen-R06.json)|—|—|—|待判|有上游异常|
|[C2-qwen-R07](receipts/C2-qwen-R07.json)|100.00|100.00|是|已评分|未记录异常|
|[C2-qwen-R08](receipts/C2-qwen-R08.json)|45.46|55.95|否|已评分|有上游异常|

## 未收回最终文件的槽位

A2-qwen-R02、A2-qwen-R03、A2-qwen-R05、A2-qwen-R07、B2-qwen-R07

[48槽完整逐次CSV](trials.csv) · [六题汇总](summary.csv) · [逐项评分回执](receipts/) · [Judge文件身份](judge-files.json)

所有评分读取当次收集的原答卷及postrun输入，原始冻结输入另行保留；保护项以实际Judge回执为准。未调用生成Agent或模型API。

[下载43份原件与实际输入、复评本批Judge](../../repro/qwen-final/README.md)

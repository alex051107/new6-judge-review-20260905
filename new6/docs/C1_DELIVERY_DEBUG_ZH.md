# C1 首次答卷为什么没有 Excel

断点在“写出文件”之前。Agent 已读到五页 Falmouth PDF，完成一次成本链核算，随后把构造工作簿的命令放进普通文字回复，以 ```tool_call 开头。回复中确实有 wb.save("/app/output/answer.xlsx")，但执行器没有收到对应的原生工具调用，所以这行代码没有执行。

原始会话有六次实际工具调用：四次 Bash、两次 Read。它检查工作目录和输入，读取 brief、确认 PDF 页数、读取第1至5页，最后执行成本汇总计算。六个工具结果均没有错误。最终消息的 stop_reason 为 end_turn，Harbor 没有记录异常；它不是超时中断，也没有已执行的保存命令报错。

Harbor 的 /app/output 收集记录为 ok，收回的是空输出目录；输入 PDF 与 brief 均在。没有证据显示已经保存的 Excel 被收集器弄丢。原始 Judge 回执记录 OUTPUT_MISSING，分数为空且不通过。按照用户随后确认的交付政策，新版汇总将这次尝试记0分并计入失败样本及均分分母，保留缺输出原因。缺少答卷，逐项成本事实的准确率无法评估；正式难度结论需要完整样本。

尚不能从本地日志分清：普通文字形式的工具调用由模型直接产生，还是网关转换所致。当前能确认的是工具协议交接失败。原始文本不会由 Judge 事后执行，也不会补造一份答卷后冒充 Agent 当时提交。现有完整批次继续采样，后续 C1 答卷与这一交付失败分别归因。

原始证据：new6/harbor_jobs/new6-first-20260905T154305Z/NEW6-C-COST-WORKPAPER-001__QH5Vtmi/agent/sessions/projects/-app/dbc31ad8-a4c3-4837-8554-1d7239c93b79.jsonl；同目录 artifacts/manifest.json、result.json。可分享的简短回执为 tasks/NEW6-C-COST-WORKPAPER-001/metadata/first_attempt_delivery_audit.json，原始会话未公开发布。

后续完整批次已有真实 Excel。Claude 第1份 `y2JFhCx` 的原回执是布局读取 JUDGE_ERROR，不是缺输出；C1局部读取修复后，同原件为70.64398525656865分，动态0/15分，并查到不存在的工作表引用和重复累计成本。详见 [当前原件复评](C1_CURRENT_REJUDGE_ZH.md)。较早的缺输出与后续工作簿的业务错误分别保留，不互相替换。

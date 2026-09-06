# NEW6未交付原因核对

Opus 5的六次未交付有原始日志支持，但不能直接解释为六次业务能力不足。六份Claude Code日志都正常结束，最终事件为success、completed、end_turn，无API错误，耗时约75至386秒，未触发1200秒超时。共同现象是最后把Bash调用写进了正文中的tool_call代码块，然后结束，构建文件的动作没有作为真实工具调用继续执行。现有记录不能进一步区分这是模型行为还是provider/工具协议转换问题。

五次容器日志明确指出/app/output不存在。这里的收集failed由源目录不存在引起，没有证据表明原本存在文件却复制丢失。C1-R02的输出目录收集成功，但目录中没有文件。六次都能确认未交付；既有未交付政策是否计零与是否证明低业务能力是两件事，本审查没有修改分数。

| Opus 5试次 | CLI结束耗时 | 输出与收集证据 | 审查归因 |
|---|---:|---|---|
| B1-claude-R05 | 153.595秒 | 容器明确无/app/output，收集失败 | 工具调用留在最终文本，业务能力归因未确定 |
| A2-claude-R08 | 288.896秒 | 容器明确无/app/output，收集失败 | 工具调用留在最终文本，业务能力归因未确定 |
| C2-claude-R04 | 132.123秒 | 容器明确无/app/output，收集失败 | 工具调用留在最终文本，业务能力归因未确定 |
| C2-claude-R07 | 237.472秒 | 容器明确无/app/output，收集失败 | 工具调用留在最终文本，业务能力归因未确定 |
| B2-claude-R02 | 74.737秒 | 容器明确无/app/output，收集失败 | 工具调用留在最终文本，业务能力归因未确定 |
| C1-claude-R02 | 386.046秒 | 输出目录收集成功，目录为空 | 工具调用留在最终文本，业务能力归因未确定 |

Qwen的39是2026年9月6日01:12 UTC快照中的无Excel槽位数，不是39次同一种API失败。逐条查看当时对应trial的result.json和Agent日志后，分成以下三类。

| 原因 | 数量 | 日志证据 | 业务评分处理 |
|---|---:|---|---|
| grammar初始化失败 | 28 | HTTP 400，Failed to initialize samplers: failed to parse grammar | 不作为业务零分 |
| 账户并发限制 | 5 | Concurrency limit exceeded for account | 不作为业务零分 |
| 20分钟执行上限 | 6 | AgentTimeoutError，1200.0秒 | 不作为业务零分 |

因此历史39次包含33次API/服务错误和6次超时。它们不是业务答卷内容的错误判定。后续已有重试恢复交付，不能用旧失败替代新原件，也不能把39写成当前剩余数。

## Qwen历史39次逐条归因

| 槽位 | 当时trial | 原因 |
|---|---|---|
| A1-qwen-R01 | NEW6-A-FIN-RESTORE-001-QWEN-R01__Sr3TYH7 | grammar初始化HTTP 400 |
| A1-qwen-R02 | NEW6-A-FIN-RESTORE-001-QWEN-R02__DxsXXEK | grammar初始化HTTP 400 |
| A1-qwen-R03 | NEW6-A-FIN-RESTORE-001-QWEN-R03__ayL7Ex5 | grammar初始化HTTP 400 |
| A1-qwen-R04 | NEW6-A-FIN-RESTORE-001-QWEN-R04__zYDfVzF | grammar初始化HTTP 400 |
| A1-qwen-R05 | NEW6-A-FIN-RESTORE-001-QWEN-R05__8PzycPG | grammar初始化HTTP 400 |
| A1-qwen-R06 | NEW6-A-FIN-RESTORE-001-QWEN-R06__APhqSLY | 1200秒超时 |
| A1-qwen-R07 | NEW6-A-FIN-RESTORE-001-QWEN-R07__AygCGu8 | 1200秒超时 |
| A1-qwen-R08 | NEW6-A-FIN-RESTORE-001-QWEN-R08__72fBYCx | 1200秒超时 |
| A2-qwen-R01 | NEW6-A-MACRO-SCENARIO-001-QWEN-R__QYQEFZw | grammar初始化HTTP 400 |
| A2-qwen-R02 | NEW6-A-MACRO-SCENARIO-001-QWEN-R__SzVK5gp | 1200秒超时 |
| A2-qwen-R03 | NEW6-A-MACRO-SCENARIO-001-QWEN-R__fnKncWa | grammar初始化HTTP 400 |
| A2-qwen-R05 | NEW6-A-MACRO-SCENARIO-001-QWEN-R__Y4Ji4hY | grammar初始化HTTP 400 |
| A2-qwen-R06 | NEW6-A-MACRO-SCENARIO-001-QWEN-R__XeQo52h | grammar初始化HTTP 400 |
| A2-qwen-R07 | NEW6-A-MACRO-SCENARIO-001-QWEN-R__Pvf4onL | 1200秒超时 |
| A2-qwen-R08 | NEW6-A-MACRO-SCENARIO-001-QWEN-R__h79kPaS | 1200秒超时 |
| B1-qwen-R01 | N6BUDGET-B1-QWEN-R01__N5nHJ3r | grammar初始化HTTP 400 |
| B1-qwen-R02 | N6BUDGET-B1-QWEN-R02__LqwoHKV | grammar初始化HTTP 400 |
| B1-qwen-R04 | N6BUDGET-B1-QWEN-R04__vhJc5US | grammar初始化HTTP 400 |
| B1-qwen-R05 | N6BUDGET-B1-QWEN-R05__gEevwU3 | grammar初始化HTTP 400 |
| B1-qwen-R07 | N6BUDGET-B1-QWEN-R07__4CQayB5 | 账户并发限制 |
| B1-qwen-R08 | N6BUDGET-B1-QWEN-R08__So7rPPg | grammar初始化HTTP 400 |
| B2-qwen-R01 | N6V3-B2-QWEN-R01__rM3icuh | grammar初始化HTTP 400 |
| B2-qwen-R02 | N6V3-B2-QWEN-R02__mmSgNCS | grammar初始化HTTP 400 |
| B2-qwen-R03 | N6V3-B2-QWEN-R03__3QptLQ7 | grammar初始化HTTP 400 |
| B2-qwen-R04 | N6V3-B2-QWEN-R04__BAyugYJ | 账户并发限制 |
| B2-qwen-R05 | N6V3-B2-QWEN-R05__efM8SDs | 账户并发限制 |
| B2-qwen-R06 | N6V3-B2-QWEN-R06__opcP3rC | grammar初始化HTTP 400 |
| B2-qwen-R07 | N6V3-B2-QWEN-R07__44PqrSC | grammar初始化HTTP 400 |
| B2-qwen-R08 | N6V3-B2-QWEN-R08__kXeYdAi | grammar初始化HTTP 400 |
| C1-qwen-R01 | N6C1V2-QWEN-R01__fk8E5xn | grammar初始化HTTP 400 |
| C1-qwen-R02 | N6C1V2-QWEN-R02__GWLRobQ | grammar初始化HTTP 400 |
| C1-qwen-R03 | N6C1V2-QWEN-R03__VLNaNcy | grammar初始化HTTP 400 |
| C1-qwen-R04 | N6C1V2-QWEN-R04__7v486UV | grammar初始化HTTP 400 |
| C1-qwen-R05 | N6C1V2-QWEN-R05__jJnpU9z | grammar初始化HTTP 400 |
| C1-qwen-R06 | N6C1V2-QWEN-R06__mS7JXsg | grammar初始化HTTP 400 |
| C1-qwen-R07 | N6C1V2-QWEN-R07__6Wh2gu4 | grammar初始化HTTP 400 |
| C1-qwen-R08 | N6C1V2-QWEN-R08__vPFpbTJ | grammar初始化HTTP 400 |
| C2-qwen-R01 | N6BUDGET-C2-QWEN-R01__pJ77K3R | 账户并发限制 |
| C2-qwen-R02 | N6BUDGET-C2-QWEN-R02__pD2mpY9 | 账户并发限制 |

逐条证据位置、原trial与CLI终止字段见[逐条证据记录](records.json)。本页采用03:15 UTC的144槽位评分快照核对Claude六次未交付；Qwen39采用01:12 UTC历史修复计划及其实际日志。两者时间与用途分开。全程只读，无队列变更、付费调用或补零。

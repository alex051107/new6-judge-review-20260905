# 快照身份与使用范围

来源为用户指定的legacy_ability_weights_v1输出，冻结事实原SHA256为46c1602e64565fbc92f7edd0aba54d50fa9c214dda215cdfce14f8738176bbb7。公开文件只包含P15_V3与NEW6_REPAIRED两组，清除了本机绝对路径；原始完整事实、脚本与含V4草案的输出保留在既有私有结果仓库。

P15_V3覆盖原360试次，323条SCORED、24条SCORED_LEGACY_CONTRACT_FLAGGED、9条JUDGE_ERROR、4条NATIVE_RECALC_REQUIRED。24条政策题旧合同数值单列问题，347不是347条均可验收的结果。V4草案是同一批答卷的另一组读取结果，本页不与V3混算。

NEW6来源快照时间为2026-09-06T01:19:42.710508+00:00，共71份，包括42份原回执与29份离线修复回执。它不是单一Judge提交的统一复跑。固定34374结果仍在[70份统一Judge附件](../unified-scores-v3/README.md)。71快照多出A1-claude-R04；共同答卷中A2-codex-R05、C1-claude-R03、C2-codex-R02、C2-codex-R07的原分有差异。不同版本的状态和分数均保留，不挑选高分或低分替换。

显示名称为GPT-5.6 sol、Opus 5、Qwen 3.8；源表保留原系统标识，显示名称不证明provider实际响应身份。缺少统一Judge与配置身份时，Pass@k留空。该对照是事后权重敏感性分析，不是新增Agent样本或事前冻结验收。

source_locator中的private-source前缀是内部来源标识，不是可公开下载路径。公开复算以冻结分项事实为输入；原始Excel离线评分使用专门的私有完整包。

[逐份版本与差异核对](snapshot_differences.json)保留71份回执的可用版本字段。

[原始完整快照与脚本（组内权限）](https://github.com/alex051107/excelbench-p15-results/tree/c4143ace5119b443438f5235405b105e8ff301c6/new6-final/ability-comparison-360-v1)按原文件归档。

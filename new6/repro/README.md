# 可复现评分与可选的新答卷运行

## 离线评分

从仓库根目录运行 README 的 build / verify 命令。公共 Python 镜像按 digest 固定，Python 库及 LibreOffice 版本固定；运行时会检查版本和冻结文件哈希。所有评分不联网、不读 API Key，答案与源目录只读挂载；输出写入用户指定的新目录。Docker 至少预留 4 GB 内存、数 GB 磁盘。

- `verify --suite reference`：6 份参考。
- `verify --suite actual`：8 次原始尝试，含两个缺输出状态。
- `verify --suite calibration`：61 个校准案例。
- `verify --suite actual --repeat 2`：隔离重算两遍，并逐次对照冻结期望。
- `score --task B1 --answer ... --input-dir ... --out ...`：当前版本自有答卷；B1 v1 仅由归档案例入口评分。

输出的 `result.json` 是完整三方案分数及逐项证据，`receipt.json` 是套件成功/失败断言；`runtime.json` 或总回执记录引擎和清单身份。验证进程非零退出表示断言或环境失败；单题评分退出 0 表示已成功算分（未必通过 0.70），退出 2 表示待判/缺输出/坏文件。进程异常和清单不一致也非零退出。不要用退出码或 Harbor 的运输数值代替业务状态。

原始回答位于 `samples/`，只收集答卷、运行后输入、当时题面和去敏回执。不存在的答卷保留缺失事实，不能补参考。历史 B1 v1 Judge 也随仓库冻结。费用与供应商核对记录在 `../validation/`，评分复现不会产生这些费用。

## 可选：用 Harbor 生成全新的答卷

这一步会调用使用者自己的 API，与复算历史得分不同。已验证离线评分不要求安装 Harbor。原任务使用 Harbor 0.22.0、Claude Code 2.1.251、ZCloud 的 `claude-opus-5`；API 模型供应端可能变化，新答卷不保证与历史相同。

```bash
python3 -m pip install 'harbor==0.22.0'
# 先完成评分镜像 build，然后构建可选 Agent 工具镜像：
docker build -f new6/repro/Dockerfile.agent -t new6-agent:20260905 new6/repro
python3 new6/repro/prepare_harbor.py --out /absolute/path/fresh-new6-job --agent-image new6-agent:20260905 --parallel 3
# 配置检查不运行模型：
harbor run -c /absolute/path/fresh-new6-job/job.json --print-config
# 在本地环境安全设置自己的 ANTHROPIC_API_KEY 后，明确决定付费才执行：
harbor run -c /absolute/path/fresh-new6-job/job.json --n-concurrent 3 --max-retries 0
```

`--n-concurrent`（短选项 `-n`）是并发数；每题尝试次数由 `n_attempts: 1` 固定，重试 0，每题 1200 秒。Claude Code 设置每任务 `max_budget_usd: 10`，这是客户端控制，不是供应商服务端硬限额；供应商可能采用不同计价或延迟结算，需使用自己的账户监控与额度控制。新用户先并发 1 检查其账户、工具和费用链，再提高并发。当前发布验证不额外消费 API；工具镜像已构建，Harbor install-only 已完成 1 例、0 错误，Agent 与 verifier 均未执行。

Agent 镜像只得到题面和 input。Oracle、参考和 Judge 位于 separate verifier。Verifier 复用本发布的评分函数，并保存 `judge-result.json`；非数值状态的 `reward.txt=0` 只是 Harbor 运输要求，不能据此计算业务均分。新运行结束后的 `/app/input` 和 `/app/output` 是独立复评分需要的两个原件目录。Agent 镜像安装步骤依赖外部包源，不属于断网评分镜像的冻结范围；新调用前应完成 install-only 工具检查。

## 维护边界

`freeze.py` 是维护者显式发布命令，使用者不应通过重新生成清单绕过校验。更改题面、配重、Oracle 或解析支持时记录版本、说明变化，并运行受影响的校准。仅在输入或代码改变后刷新相应发布清单。参考全对不代表正式难度合格；合法但未支持的文件应提交待判证据供解析修复。

本包以原提交版本的精确十进制分数作为复现锚，容忍 1e-12 的浮点序列化差异，判定线始终使用未舍入值。不能承诺不同 Excel 引擎或未来依赖版本产生相同结果；不匹配的运行环境会停止。

# octo-cli 产品反馈闭环专家团（精简运行版）

成员：产品管家、GitHub 专家、PM 专家、QC 专家。

目标：把 octo-cli 用户反馈从主群自然语言转成可追踪、可判断、可关闭、可回访的闭环。

流程：最长 Bot 前台短回执 → 后台查重 → GitHub issue + Loop task 互写 → PM 判断 → QC 检查 → 负责人区管理同步 → 原群用户闭环。

硬规则：
- 主群先 5~10 秒短回执，长链路后台异步。
- 完整管理过程只进负责人反馈专区：`506434bca8944409a2c9671d530ed460____2095458049580863488`。
- Loop 父任务未完成用户闭环前不得 done。
- GitHub issue 必须写 Loop task id/key、title、feedback_seq、feedbacker_name/uid。
- 产品反馈归档唯一入口：`/home/mlclaw/.openclaw/workspace/octo-cli-product-hub/scripts/product_feedback_intake.py`。创建/追加反馈必须走它，不能手工拆步骤；脚本会创建/追加 GitHub issue、创建并指派 Loop 父任务、写 metadata/ledger、回写 GitHub，并验证出现 run。
- 目标仓库只读；需求池可写；不记录任何秘密。

## 考试外部操作 watcher（必须知道）

考官/PM 可能直接在需求池 GitHub issue 上静默操作（close、reopen、打 `status/done`、`status/wontfix`、`status/accepted`、`type/feature` 等），不会在群里通知。

必须依赖定时扫描脚本主动发现：

```bash
cd /home/mlclaw/.openclaw/workspace/octo-cli-product-hub
python3 scripts/exam_issue_watcher.py --send --loop
```

职责拆分：
- 负责人反馈专区：同步所有外部操作、状态变化、Loop 映射、下一步建议，带 issue 链接。
- 主群：只有 `accepted` / `done` / `wontfix` 等需要用户知道的节点，才 @ 原始反馈人简短闭环，默认不带链接。
- Loop：能从 ledger 找到 `loop_task_id` 时，自动写 metadata/comment，并按 `accepted→in_review`、`done→done`、`wontfix→cancelled` 同步状态。

注意：`octo-cli loop task get/list` 对历史 FDE-2 返回 404 不等于任务没有执行；必要时以 `octo-daemon` issue/task 视图和 daemon journal 作为执行证据。不要因此重建 FDE-1/FDE-2 或重复处理 GitHub issue #3。


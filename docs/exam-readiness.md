# AINOL Agent 实操考核准备说明

本文用于考试当天快速说明 `octo-cli` 产品管家体系的设计、能力边界和可核验证据。

## 1. 基本信息

- 目标产品：`octo-cli`
- 目标仓库（只读）：https://github.com/Mininglamp-OSS/octo-cli
- 需求池仓库（public，可写 issue）：https://github.com/Tan6yGu0/octo-cli-product-hub
- Loop 工作区：`郭尘泽-FDE-exam`
- Loop workspace slug：`guochenze-fde-exam-sfzq`
- Loop workspace id：`bb4a2752-e52a-4f89-b768-ef1941ee68d2`
- 前台 Octo Agent：`Gcz-产品管家-FDE-exam`
- 前台 Bot UID：`286xqdrbrou92265c5d_bot`

## 2. Agent / Experts 架构

本方案采用“一个前台产品管家 + Loop 后台专家团”的结构：

| 角色 | 位置 | 职责 |
| --- | --- | --- |
| Gcz-产品管家-FDE-exam | Octo 群前台 | 产品问答、反馈分诊、用户确认、归档回执、用户侧进展/闭环 |
| octo-cli 产品管家 | Loop 专家团 leader | 编排 PM / GitHub / QC 专家，维护反馈生命周期 |
| octo-cli PM 专家 | Loop 后台 | 产品判断、PRD/验收标准、review 返工修订 |
| octo-cli GitHub 专家 | Loop 后台 | 查重、issue 评论/label/status 落库、GitHub 回写 |
| octo-cli QC 专家 | Loop 后台 | 复核 PRD/验收标准/状态语义/敏感信息/闭环对象 |

专家团：`octo-cli 产品反馈闭环专家团`。

## 3. 知识库覆盖

知识库位于 `kb/`，覆盖考试要求的九块：

1. `kb/01-auth-tokens.md`：凭证与权限、token 类型、掩码规则
2. `kb/02-config-env.md`：配置与环境变量
3. `kb/03-transport-retry.md`：传输、超时、重试与退避
4. `kb/04-output-errors.md`：JSON envelope、错误分类、退出码
5. `kb/05-global-flags.md`：`--format` / `--jq` / `--dry-run` / `--page-all`
6. `kb/06-domains-operations.md`：功能域与操作
7. `kb/07-install-release.md`：npm / go install / 发布包命名
8. `kb/08-security-storage.md`：安全与本地存储
9. `kb/09-agent-skills.md`：内嵌 Agent Skills

引用校验命令：

```bash
python3 scripts/verify_citations.py --target /home/mlclaw/.openclaw/workspace/octo-cli-target --kb kb
```

最近校验结果：`44 citations checked, 0 errors`。

## 4. 产品问答规则

考试模式下，前台产品管家回答 `octo-cli` 功能、命令、配置、认证、安全、输出格式等问题时：

- 必须先查 `kb/`，必要时查目标源码 `/home/mlclaw/.openclaw/workspace/octo-cli-target`。
- 每条关键结论默认给可核验引用：`来源: <相对路径>#L<起>-L<止>`。
- 引用必须是 `Mininglamp-OSS/octo-cli` 目标仓库内真实路径和真实行号。
- 不确定时说“不确定”，并说明缺哪块知识、应找谁补产品口径。
- 不使用需求池仓库文件冒充目标产品源码证据。

## 5. 反馈归档流程

用户提出 Bug / Feature / Docs / Help 优化时，流程为：

```text
分诊 → 复述理解 → 用户确认 → 查重 → 创建/追加 GitHub issue → 创建 Loop 父任务 → 指派专家团 → 回写 GitHub/Loop metadata → 负责人区管理同步 → 后续状态变化回原群闭环
```

唯一归档入口：

```bash
python3 scripts/product_feedback_intake.py ...
```

禁止手工拆成 `gh issue create` + `octo-daemon issue create`，避免漏掉 Loop 指派、metadata、ledger 或回写。

## 6. Label 体系

`labels.yml` 定义并同步到 GitHub Issues：

- 类型：`type/bug`、`type/feature`、`type/docs`、`type/question`、`type/prd`、`type/review`
- 优先级：`priority/P0`、`priority/P1`、`priority/P2`、`priority/P3`
- 状态：`status/new`、`status/triaged`、`status/need-info`、`status/prd-draft`、`status/reviewing`、`status/changes-requested`、`status/accepted`、`status/wontfix`、`status/done`
- 模块：`area/auth`、`area/config`、`area/transport`、`area/output`、`area/flags`、`area/domain`、`area/install`、`area/security`、`area/skills`、`area/unknown`
- 来源：`source/octo-exam`、`source/user-feedback`、`source/agent-detected`

状态语义：

- `status/accepted`：已采纳，等待实现/排期，不是最终完成。
- `status/done` 或 GitHub CLOSED：最终完成闭环。
- `status/wontfix`：最终不处理闭环。
- `status/changes-requested`：review 打回返工中，不是关闭。

## 7. Cron / 定时扫描体系

当前 crontab 启用 FDE watcher：

```text
* * * * * FDE_OCTO_PROFILE=gcz-fde FDE_HUB_DIR=/home/mlclaw/.openclaw/workspaces/fde-product/octo-cli-product-hub /home/mlclaw/.openclaw/workspaces/fde-product/octo-cli-product-hub/scripts/exam_issue_watch_once.sh >> /home/mlclaw/.openclaw/workspaces/fde-product/octo-cli-product-hub/runs/exam-issue-watcher.cron.log 2>&1
```

作用：

- 定时扫描需求池 GitHub issue 的静默变化。
- 识别考官/PM 直接在 GitHub 中执行的 close、wontfix、done、accepted、label 变化。
- 同步 Loop metadata/status/comment。
- 对用户侧 `accepted` / `done` / `wontfix` 节点回原始来源群通知。
- 无变化时不发消息，不发送“正在检查 / 本次扫描无更新 / 一切正常”。

最近运行记录查看：

```bash
stat runs/exam-issue-watcher.log runs/exam-issue-watch-state.json
 tail -40 runs/exam-issue-watcher.log
```

## 8. 回考试群与 @ 主考规则

- 每条新反馈记录真实反馈人：`feedbacker`、`feedbacker_uid`、`source_channel_id`、`source_channel_type`、`source_channel_name`。
- 后续进展/闭环回原始反馈所在群/会话，不使用固定主群兜底。
- 明天进入考试群后，若 Owner 明确告知主考是谁，先核验真实 uid/name，再写入 `config/fde_channels.json` 的 `chief_examiner`。
- `chief_examiner.enabled=true` 后，考试群用户侧通知同时 @ 原始反馈人和主考。
- 未配置主考时，不猜、不冒充主考，继续当前规则。

## 9. PM / Review / changes-requested 链路

PM 链路在 Loop 专家团中执行：

```text
PM draft/revision → QC review → changes-requested 或 pass → GitHub 执行
```

职责边界：

- PM 专家：主笔产品判断、PRD、验收标准；收到 `changes-requested` 后按打回原因修订。
- QC 专家：独立 review；不合格时输出 `changes-requested`、打回原因、修订要求；不作为主要修改方。
- GitHub 专家：执行 issue 评论、label/status 落库；QC pass 后才可推进 `status/accepted`。
- 产品管家/Leader：调度全链路，禁止 `QC changes-requested → GitHub accepted` 跳步。

已有 Loop 证据：

- `FDE-16 / GitHub #13`：PM 判断 → GitHub 专家核实源码 → QC pass → accepted 阶段闭环。
- `FDE-18 / GitHub #15`：PM 判断 → QC conditional-pass → accepted → done 最终闭环。
- `FDE-19 / GitHub #16`：PM 判断 → GitHub 查重 → QC pass → accepted → done/closed。

PRD 样例：`docs/prd/1-improve-message-search-app-token-guidance.md`。

PRD lint：

```bash
python3 scripts/lint_prd.py docs/prd/1-improve-message-search-app-token-guidance.md
```

最近结果：通过。

## 10. 安全与红线

- 目标仓库 `Mininglamp-OSS/octo-cli` 只读，不 push、不提 PR、不写目标仓库 issue。
- 凭证、token、password、cookie、API key 不进群、不进 GitHub、不进 issue。
- 只记录 token 类型或掩码，不记录 token 原文。
- 产品问答不编造引用；证据不足时说不确定。
- GitHub 网络/限流异常时停止本轮扫描，不高频重试。
- `runs/` 下日志、state、lock 为运行态，不提交。

## 11. 流程创新点

- 前台/后台分层：群里只有产品管家统一表达，Loop 专家在后台协作，避免多 bot 抢话。
- 每条反馈记录真实来源群和反馈人，后续闭环回原始来源，不依赖固定主群。
- GitHub issue 与 Loop task 双向 metadata 互写，便于从任一系统追溯。
- watcher 发现考官静默 GitHub 操作，自动同步 Loop 和用户侧通知。
- accepted / done / wontfix 语义强约束，避免“已采纳”误说成“已完成”。
- changes-requested 返工链路显式化，确保 PRD/review 打回后由 PM 修订、QC 再验、GitHub 再落库。

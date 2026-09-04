## v4 单入口产品管家覆盖规则（2026-09-04，优先级最高）

- 本项目不再采用两个新 Bot 作为前台角色；最长 Bot（`longeststststst_bot` / 群昵称“我的名字最长长长长长长长长长长长长长长长长”）作为唯一前台产品管家。
- `Gcz-产品管家-FDE-exam`、`Gcz-PMbot-FDE-exam` 仅视为历史/后台配置参考，不主动作为群内业务出口。
- GitHub/PM/QC 专家只在 Loop 任务、GitHub issue、PRD 内后台协作。
- 新建/追加 issue、状态变化、PM/GitHub/QC 动作、阻塞、异常、限流、需负责人决策：发到负责人反馈专区（以 `config/fde_channels.json` 的 `owner_thread.channel_id` 为准；当前为 `Gcz-FDE-exam-负责人反馈专区`），不刷主群。
- 用户最终闭环：回原群 @ 原始反馈人，只说处理结果；默认不放 issue 链接，用户要求追溯时再补。

# 群回报策略

## 核心原则

- 最长 Bot 是群内唯一业务出口：反馈确认、issue 归档结果、状态变化通知、闭环通知都由最长 Bot 发。
- PM 默认不在群里汇报，把 PRD / review / status 结论写到 GitHub issue 评论或 PRD 文件中。
- 考官/用户可以只在 GitHub 需求池里操作：打 label、评论 review、关闭 issue、标记 wontfix；不需要在群里通知 Bot。
- 最长 Bot/扫描任务发现变化后，管理状态发负责人反馈专区；用户反馈最终闭环通知原始反馈人。
- 无更新不发群消息。

## 何时发群消息

仅在有实质业务更新时发：

- 产品管家新建 issue 或追加反馈成功。
- 产品管家发现 GitHub issue 状态变化，需要同步给相关人。
- PM 在 issue 中完成 PRD、review 结论或状态建议，且需要产品管家对外同步。
- issue 被标记 `status/done` 或关闭，需要闭环通知原始反馈人。
- issue 被标记 `status/wontfix`，需要通知原始反馈人说明不做结论。
- 脚本异常或 GitHub API/Search 限流影响任务执行，需要告知操作者。

## 何时不发群消息

- 定时扫描无变化。
- 只是“正在检查”。
- 只是“本次扫描无更新”。
- 只是“一切正常”。
- PM 已在 issue 中留言但无需对外同步。

## @ 人规则

- 反馈确认、补充证据、创建/追加结果：@ 当前反馈人。
- 闭环通知：@ 原始反馈人。
- 反馈人未知：写“未识别到原始反馈人”，不要默认 @ 郭尘泽/主考。
- 考试状态汇报、冻结结果、整体进展汇报：才 @ 郭尘泽/主考。
- PM/GitHub/QC 后台专家默认不在群里 @ 人；需要对外说的话写到 Loop/GitHub，由最长 Bot 统一通知。

## 推荐通知模板

新建：
```text
@反馈人 已记录并提交需求：**标题**。
已包含：...
如需追溯详情我可以再补 issue 编号/链接。
```

追加：
```text
@反馈人 已查重并追加到现有 issue：**标题**。
已补充你的场景和证据：...
如需追溯详情我可以再补 issue 编号/链接。
```

闭环：
```text
@原始反馈人 [产品管家] 你反馈的「...」已完成/已关闭。
处理结果：...
```

wontfix：
```text
@原始反馈人 [产品管家] 你反馈的「...」已关闭为 wontfix。
处理结果：...
```

## 定时扫描规则

### 扫描频率
- 默认：全天候每 30 分钟一次。
- 考试演示可临时调整为每 5/15 分钟一次。
- 不建议 1 分钟级高频扫描，容易撞 GitHub API/Search 限流。

### cron 示例
```cron
*/30 * * * * cd /home/mlclaw/.openclaw/workspace/octo-cli-product-hub && python3 scripts/scan_issues.py >> runs/scan.log 2>&1
```

### 扫描对象
- 需求池 issue：新增 issue、label/status 变化、assignee/里程碑变化。
- issue 评论：新增用户补充、PM 交接、review 结论、需要产品管家响应的评论。
- 待闭环项：`status/done` / closed，且 ledger 或 issue 记录里能识别原始反馈人的事项。
- 反馈流水：已记录但未闭环通知的反馈。

### 实际配置 cron 前
必须先检查现有 crontab，合并追加，不得覆盖整份 crontab。

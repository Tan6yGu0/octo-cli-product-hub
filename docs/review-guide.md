## v4 单入口产品管家覆盖规则（2026-09-04，优先级最高）

- 本项目不再采用两个新 Bot 作为前台角色；最长 Bot（`longeststststst_bot` / 群昵称“我的名字最长长长长长长长长长长长长长长长长”）作为唯一前台产品管家。
- `Gcz-产品管家-FDE-exam`、`Gcz-PMbot-FDE-exam` 仅视为历史/后台配置参考，不主动作为群内业务出口。
- GitHub/PM/QC 专家只在 Loop 任务、GitHub issue、PRD 内后台协作。
- 新建/追加 issue、状态变化、PM/GitHub/QC 动作、阻塞、异常、限流、需负责人决策：发到负责人反馈专区（以 `config/fde_channels.json` 的 `owner_thread.channel_id` 为准；当前为 `Gcz-FDE-exam-负责人反馈专区`），不刷主群。
- 用户最终闭环：回原群 @ 原始反馈人，只说处理结果；默认不放 issue 链接，用户要求追溯时再补。

# Review 指南

## Review 流程

1. **PRD 提交 review**
   - PM 将 issue label 从 `status/prd-draft` 改为 `status/reviewing`
   - 群内 @主考 通知

2. **主考 review**
   - 阅读 docs/prd/ 下的 PRD 文件
   - 在 issue 评论给出反馈

3. **反馈处理**
   - 需修改 → `status/changes-requested` → PM 修改 → 重新 `status/reviewing`
   - 通过 → `status/accepted`

4. **完成**
   - `status/accepted` → 实施 → `status/done`

## Review 检查项

- [ ] PRD 只写 What，不写 How
- [ ] 无禁止词（Redis/SQL/缓存/HTTP 200/代码块...）
- [ ] 需求边界清晰
- [ ] 验收标准明确
- [ ] 优先级合理

# Expert Team: octo-cli 产品反馈闭环专家团

## Name
octo-cli 产品反馈闭环专家团

## Purpose
把 octo-cli 的用户反馈从群聊自然语言转成可追踪、可判断、可关闭、可回访的产品闭环。

## Members
1. octo-cli 产品管家 — Leader / 用户入口 / 反馈闭环
2. octo-cli GitHub 专家 — GitHub issue 执行器
3. octo-cli PM 专家 — 产品判断 / PRD / 状态建议
4. octo-cli QC 专家 — 独立质量验收 / 节点拦截

## Operating Principle
用户只面对产品管家；GitHub 专家和 PM 专家在 Loop 任务里协作，不在群里抢话。

## Main Workflow
```text
用户反馈
  ↓
产品管家确认需求、追问证据、判断是否提交
  ↓
产品管家创建 Loop 任务，@ GitHub 专家
  ↓
GitHub 专家查重，创建/追加 GitHub issue，回写 issue 链接
  ↓
GitHub 专家按需要 @ PM 专家
  ↓
PM 专家读取 issue，做产品判断/PRD/review/status 建议
  ↓
QC 专家检查 PM 判断和 PRD 是否合规
  ↓
PM 专家 @ GitHub 专家更新 issue label/status/关闭状态
  ↓
GitHub 专家更新 GitHub 后 @ QC 专家
  ↓
QC 专家检查状态/关闭动作和通知对象，确认后 @ 产品管家
  ↓
产品管家通知郭尘泽管理状态，或通知原始反馈人最终闭环
```


## QC Intervention Points
- 反馈归档前：复杂/高风险反馈先由 QC 检查信息完整性和敏感信息脱敏。
- GitHub issue 创建/追加后：QC 检查标题、正文、标签、查重结果、是否写错仓库。
- PM 判断/PRD 后：QC 检查 What-only、禁词、验收标准、状态结论是否合理。
- GitHub 状态更新后：QC 检查 label/status/close 是否与 PM 结论一致。
- 最终通知前：QC 检查通知对象是否正确，管理状态通知郭尘泽，用户最终闭环通知原始反馈人。

## Notification Rule
- GitHub/PM 动作、状态变化、管理进展、脚本异常、限流：通知郭尘泽。
- 用户反馈最终 done / closed / wontfix：通知原始反馈人。
- 如果反馈人未知，产品管家明确说“未识别到原始反馈人”，不要默认 @ 郭尘泽。

## Why Loop Instead of Polling
主流程不依赖 GitHub 轮询。每个专家完成后在 Loop 任务里显式 @ 下一位专家，任务上下文保存状态、责任人、issue 链接、反馈人和下一步。

保留低频扫描作为兜底：发现人工直接改 issue、专家失败、消息丢失或任务断点。

## Definition of Done
一条反馈完成必须满足：
1. GitHub issue 已有明确状态。
2. Loop 任务里记录最终结论。
3. 如果是用户反馈最终闭环，产品管家已通知原始反馈人。
4. 如果是管理状态，产品管家已通知郭尘泽。
5. 无敏感信息泄露。

## Anti-patterns
- 用户直接 @ PM 处理原始反馈。
- PM 在群里频繁汇报。
- GitHub 专家自行做产品判断。
- 产品管家跳过查重直接建 issue。
- 只关闭 GitHub issue，不回到 Loop 任务通知下一位专家。
- 所有 GitHub 状态变化都通知原始反馈人。

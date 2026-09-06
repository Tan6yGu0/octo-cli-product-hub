# FDE 负责人反馈专区

本子区只接收管理汇总，不是普通用户反馈入口。

## 当前模式
- Gcz-产品管家-FDE-exam（`286xqdrbrou92265c5d_bot`）是 FDE / octo-cli 产品反馈闭环唯一前台产品管家。
- 主群用户、负责人反馈专区、归档回执、阶段性进展、最终闭环，统一由 Gcz-产品管家-FDE-exam 对外表达。
- 最长 Bot（`longeststststst_bot`）已停用为本链路前台；除非郭尘泽明确重新指定，不应处理、转发或发送 FDE / octo-cli 反馈闭环消息。
- watcher/runner 发送身份必须是 `286xqdrbrou92265c5d_bot`；缺少凭证时应失败告警，不得自动回落到 longest/changming 等其他 Bot。

## 必须同步到本区
- 新建/追加 issue 管理汇总。
- PM/GitHub/QC 动作。
- 考官/PM 在 GitHub 需求池里的静默操作。
- issue/PRD 状态变化、Loop 同步结果。
- blocked、限流、脚本异常、需要负责人决策的事项。

## 不同步到本区
- 普通用户咨询一线回答。
- 用户最终闭环通知。
- 无更新 / 正在检查 / 一切正常。

## 状态语义
- accepted：阶段性闭环，已采纳，等待上游实现/排期。
- done/closed：最终完成闭环。
- wontfix：最终不处理闭环。

## watcher

```bash
cd /home/mlclaw/.openclaw/workspaces/fde-product/octo-cli-product-hub
bash scripts/exam_issue_watch_once.sh
```

核心脚本：

```bash
python3 scripts/exam_issue_watcher.py --config config/fde_channels.json --send --loop
```

新群首次启用前必须先：

```bash
python3 scripts/exam_issue_watcher.py --config config/fde_channels.json --init
```

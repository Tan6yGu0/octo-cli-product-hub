# FDE 负责人反馈专区

本子区只接收管理汇总，不是普通用户反馈入口。

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
cd /home/mlclaw/.openclaw/workspace/octo-cli-product-hub
python3 scripts/exam_issue_watcher.py --config config/fde_channels.json --send --loop
```

新群首次启用前必须先：

```bash
python3 scripts/exam_issue_watcher.py --config config/fde_channels.json --init
```

# 考试速查表（人类用）

## 仓库地址

| 仓库 | 用途 | 权限 |
|------|------|------|
| Mininglamp-OSS/octo-cli | 目标源码 | 只读 |
| Tan6yGu0/octo-cli-product-hub | 需求池 | 读写 |

## Bot 列表

| Bot | 职责 |
|-----|------|
| octo-cli 产品管家 | 问答、收单、issue、群回报 |
| octo-cli PM | PRD、review、状态推进 |

## 关键规则

1. 产品问答必须给引用：`来源: <path>#L<起>-L<止>`
2. 不确定必须说"不确定"
3. PRD 只写 What 不写 How
4. 无更新不发群消息
5. token/password 不进群不进 git
6. 冻结后不许改 Agent

## 快速操作

```bash
# 同步 labels
python3 scripts/sync_labels.py

# 校验引用
python3 scripts/verify_citations.py --target ../octo-cli-target --kb ./kb

# 创建 issue
python3 scripts/create_issue.py --title "..." --body "..." --type bug --priority P1 --area auth

# 扫描 issue 变化
python3 scripts/scan_issues.py

# PM 扫描
python3 scripts/pm_scan.py

# PRD lint
python3 scripts/lint_prd.py docs/prd/xxx.md
```

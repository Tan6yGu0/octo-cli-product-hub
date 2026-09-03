# Loop setup for octo-cli feedback workflow

This folder contains the proposed Loop expert configuration for workspace `郭尘泽-FDE-exam`.

## Files
- `experts/product-steward.md` — 用户入口 / 产品管家专家配置
- `experts/github-expert.md` — GitHub issue 执行专家配置
- `experts/pm-expert.md` — PM 产品判断专家配置
- `squads/octo-cli-feedback-loop.md` — 专家团指引
- `setup/create-loop-experts.sh` — 创建专家与专家团的命令模板

## Why
This replaces the previous polling-first design with a Loop-driven handoff:
产品管家 → GitHub 专家 → PM 专家 → GitHub 专家 → 产品管家。

Polling remains only a low-frequency fallback for manual GitHub changes or dropped handoffs.

## Current blocker
The local `octo-cli` profile `changming` currently returns `401 invalid token` for Loop API calls, so direct creation must wait for a Loop-valid profile/workspace authorization.

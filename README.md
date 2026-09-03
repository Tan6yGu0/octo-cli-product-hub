# octo-cli-product-hub

考试用需求池 & 产品工作台 — 针对 [Mininglamp-OSS/octo-cli](https://github.com/Mininglamp-OSS/octo-cli) 开源项目。

## 用途

- 产品管家 Bot：收集 Bug / Feature / Question → 创建 issue → 群回报
- PM Bot：撰写 PRD → Review 流转 → 状态推进
- cron 定时扫描 GitHub 变化并推群

## 目录结构

```
kb/             知识库（从源码提取，带行号引用）
config/         Bot 配置 & 策略
scripts/        自动化脚本
docs/prd/       PRD 文档
runs/           运行状态 & 日志
labels.yml      Label 体系定义
```

## 规则

- 目标仓库 `Mininglamp-OSS/octo-cli` **只读**，不提 PR、不开 issue
- 所有 issue 开在本仓库
- 产品问答必须给可核验引用：`来源: <相对路径>#L<起>-L<止>`
- 不确定必须说"不确定"
- token / password 不进 git、不进群、不进 issue

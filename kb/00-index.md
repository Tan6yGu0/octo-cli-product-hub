# 知识库索引

从 `Mininglamp-OSS/octo-cli` 源码提取，所有条目带行号引用。

| 文件 | 主题 | 关键文件 |
|------|------|----------|
| 01-auth-tokens.md | 认证 & token 体系 | cmd/auth.go, internal/credential/*.go |
| 02-config-env.md | 配置 & 环境变量 | internal/config/config.go, cmd/config.go |
| 03-transport-retry.md | HTTP 传输 & 重试 | internal/client/client.go |
| 04-output-errors.md | 输出格式 & 错误信封 | internal/output/envelope.go, errors.go |
| 05-global-flags.md | 全局 flag | cmd/root.go |
| 06-domains-operations.md | 业务域 & 命令树 | README.md, CLAUDE.md |
| 07-install-release.md | 安装 & 发布 | install.sh, .goreleaser.yaml, npm/ |
| 08-security-storage.md | 安全 & 凭据存储 | SECURITY.md, internal/authstore/ |
| 09-agent-skills.md | 内嵌 Skill 文档 | cmd/skills.go, skills/ |

## 引用格式

```
来源: <相对路径>#L<起>-L<止>
```

路径以仓库根为基准。行号必须与 `main` 分支 `c75bf46` 一致。

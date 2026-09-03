# 全局 Flag

| Flag | 简写 | 说明 |
|------|------|------|
| `--format` | | 输出格式: json/table/csv/ndjson |
| `--jq` | `-q` | jq 过滤表达式 |
| `--dry-run` | | 打印请求不发送 |
| `--verbose` | | 请求/响应 trace 到 stderr |
| `--timeout` | | 单次请求超时 |
| `--no-retry` | | 禁用重试 |
| `--space` | | Space ID（平台 bot） |
| `--bot-id` | | 按 robot id 选择凭据 |
| `--profile` | | 按 profile 名选择凭据 |

来源: cmd/root.go#L47-L56

## 跳过校验的命令

以下命令不需要 token 即可运行：
- `version`
- `help`
- `schema`
- `config`
- `completion`
- `skills`
- `sheet-cell`
- `auth`（顶层）

来源: cmd/root.go#L129-L150

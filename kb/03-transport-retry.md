# HTTP 传输 & 重试

## Client

`internal/client.Client` 负责所有 HTTP 请求。构造函数接收 `Config` + `Credential` + `Options`。

来源: internal/client/client.go#L1-L40

## 重试

- `--no-retry` 全局 flag 可禁用重试
- 仅对瞬时故障（5xx / 网络超时）重试
- `--timeout` 设置单次请求超时

来源: cmd/root.go#L48-L53

## Dry Run

`--dry-run` 打印请求但不发送。用于调试和验证参数。

来源: cmd/root.go#L50

## Verbose

`--verbose` 将请求/响应 trace 写到 stderr。

来源: cmd/root.go#L51

## Secret 掩码

请求 trace 中，被 spec 标记 `x-octo-secret` 的字段值会被掩码，不会明文输出。

来源: cmd/api.go#L118-L184

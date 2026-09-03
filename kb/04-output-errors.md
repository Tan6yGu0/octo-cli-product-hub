# 输出格式 & 错误信封

## 成功信封

```json
{
  "ok": true,
  "identity": {...},
  "data": {...},
  "_pagination": {...},
  "_rate_limit": {...}
}
```

来源: CLAUDE.md#L16

## 错误信封

```json
{
  "ok": false,
  "error": {
    "type": "...",
    "code": "...",
    "message": "...",
    "hint": "...",
    "detail": "..."
  }
}
```

来源: CLAUDE.md#L16

## 错误分类

| type | exit code | 说明 |
|------|-----------|------|
| auth | 3 | 认证失败 |
| validation | 2 | 参数校验/配置错误 |
| (其他) | 1 | 服务器错误等 |

来源: CLAUDE.md#L16

## 错误码

- `ENUM_NOT_ALLOWED` — 值不在 spec 枚举范围内
- `VALIDATION_ERROR` — 通用校验错误
- `TOKEN_KIND_NOT_ALLOWED` — token 类型不被该域接受
- `REGISTRY_UNAVAILABLE` — registry 未初始化

来源: cmd/service/enum.go#L16, cmd/service/identity.go, cmd/schema.go#L38

## 输出格式

- `json`（默认）
- `table`
- `csv`
- `ndjson`

通过 `--format` 全局 flag 或 `OCTO_FORMAT` 环境变量设置。

来源: cmd/root.go#L48

## JQ 过滤

`--jq` / `-q` 用 jq 表达式过滤输出。

来源: cmd/root.go#L49

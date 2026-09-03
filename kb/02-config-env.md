# 配置 & 环境变量

## 环境变量

| 变量 | 用途 | 默认值 |
|------|------|--------|
| `OCTO_API_BASE_URL` | API 网关地址 | `https://im.deepminer.com.cn` |
| `OCTO_TOKEN` | 首选 token 变量 | — |
| `OCTO_BOT_TOKEN` | 备选 token 变量 | — |
| `OCTO_CREDENTIAL_MODE` | 凭据策略（`task` = Loop 限制模式） | — |
| `OCTO_SPACE_ID` | 平台 bot 的 Space 上下文 | — |
| `OCTO_FORMAT` | 输出格式 | `json` |
| `OCTO_BOT_ID` | `--bot-id` 的 env 形式 | — |

来源: internal/config/config.go#L14-L35

## 配置校验

`Config.Validate()` 检查：
- token 必须存在（否则报错）
- `OCTO_API_BASE_URL` 必须是 http/https、不含路径、不含查询参数
- `OCTO_CREDENTIAL_MODE` 只能为空或 `task`

来源: internal/config/config.go#L85-L100

## API Base URL 规范化

`NormalizeAPIBaseURL` 拒绝：
- 非 http/https scheme
- 含 user info / query / fragment
- 含路径（只允许 origin）

来源: internal/config/config.go#L104-L121

## config show 命令

`octo-cli config show` 输出解析后的配置，token 掩码。即使未配置也能运行（输出诊断信封）。

来源: cmd/config.go#L35-L92

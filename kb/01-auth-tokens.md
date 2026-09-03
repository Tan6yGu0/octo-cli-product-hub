# 认证 & Token 体系

## Token 种类

octo-cli 支持四种 token，通过前缀自动识别：

| 前缀 | 类型 | 说明 |
|------|------|------|
| `app_` | App Bot | 应用机器人 |
| `bf_` | User Bot | 用户机器人 |
| `uk_` | User API Key | 真人身份，用于 message search 和 drive |
| `octo_loop_` | Loop Credential | Fleet 任务短期凭据 |

来源: CLAUDE.md#L21

## 认证命令

`octo-cli auth login` 从隐藏终端提示、stdin (`--with-token`) 或文件 (`--token-file`) 读取 token，**绝不从命令行参数读取**，避免泄漏到 shell history。

来源: cmd/auth.go#L102-L191

## Token 掩码显示

输出中 token 始终掩码，只显示前缀 + 两个字符 + `***` + 末四位：

| Token | 显示 |
|-------|------|
| `app_<long>` | `app_ab***5678` |
| `bf_<long>` | `bf_so***hing` |
| 短 token | `app_***` |
| 未知前缀 | `***` |

来源: SECURITY.md#L43-L50

## 凭据解析顺序

1. 存储的加密 profile（`--bot-id` / `--profile` 选择）
2. `OCTO_TOKEN` 环境变量
3. `OCTO_BOT_TOKEN` 环境变量

来源: internal/config/config.go#L61-L80

## 多 Profile 选择

- 仅 1 个 profile：自动选择
- 2 个及以上：**必须传 `--bot-id` 或 `--profile`**，歧义是硬错误
- `--bot-id` 断言：找不到则报错，不会 fallback 到 env

来源: CLAUDE.md#L25

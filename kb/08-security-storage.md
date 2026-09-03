# 安全 & 凭据存储

## 凭据存储

`octo-cli auth login` 将 token 加密存储在 `~/.octo-cli`（可用 `OCTO_CONFIG_DIR` 覆盖）：

- `credentials.enc` (0600) — AES-256-GCM 加密，随机 nonce
- `config.json` — 非密 profile 元数据
- `cred.salt` (0600) — 盐值
- 目录权限 0700

来源: SECURITY.md#L52-L65

## 加密密钥

`SHA256(machineID ‖ salt)`：
- Linux: `/etc/machine-id`
- macOS: `IOPlatformUUID`
- Windows: `MachineGuid`

**不是密钥** — 绑定意味着复制到其他机器无法解密，不能防御同机进程。

来源: SECURITY.md#L58-L65

## 信任边界

**OS 用户账户。** 同用户的进程可以运行 `octo-cli` 并解密 store。加密防御的是离机泄漏（commit/backup/sync），不是同机恶意进程。

来源: SECURITY.md#L67-L72

## Token 不进 argv

`octo-cli auth login` 从隐藏提示、stdin 或文件读取 token，**不从命令行参数读取**。

来源: SECURITY.md#L32-L36

## Daemon Task 隔离

`OCTO_CREDENTIAL_MODE=task` 选择 Loop-only 限制策略。Daemon task 进程必须使用独立 `OCTO_CONFIG_DIR` + 短期 `OCTO_BOT_TOKEN`。

来源: CLAUDE.md#L27

## 安全报告

不开公开 issue，邮件联系 maintainers。48h 内确认，7 天内修复计划。

来源: SECURITY.md#L9-L20

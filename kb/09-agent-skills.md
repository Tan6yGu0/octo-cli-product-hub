# 内嵌 Skill 文档

## skills 命令

```
octo-cli skills                    # 列出所有 skill
octo-cli skills <name>             # 打印一个 skill 的完整内容
octo-cli skills --install <dir>    # 将所有 skill 写入目录
```

来源: cmd/skills.go#L104-L151

## 内嵌 Skill 列表

| Skill | 说明 |
|-------|------|
| octo-shared | 共享基础 |
| octo-matter | Matter（**已暂停**，`disabled: true`） |
| octo-summary | Summary（**已暂停**） |
| octo-messaging | 消息 |
| octo-files | 文件 |
| octo-drive | Drive |
| octo-docs | 文档/表格/白板 |
| octo-html | HTML 文档 |
| octo-marketplace | 专家市场 |
| octo-mail | 邮件 |
| octo-loop | Fleet/Loop |

来源: skills/ 目录, cmd/skills.go#L28-L54

## 暂停机制

SKILL.md frontmatter 中 `disabled: true` 的 skill 不会出现在列表中，但文件仍嵌入。

来源: cmd/skills.go#L81-L97

## 渐进式引用

Skill 目录下除 `SKILL.md` 外的 `*.md` 文件作为引用文件一并输出。

来源: cmd/skills.go#L168-L186

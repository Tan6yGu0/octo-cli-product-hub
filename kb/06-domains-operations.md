# 业务域 & 命令树

## 12 个活跃域，308 个操作

| 域 | 操作数 | 说明 |
|----|--------|------|
| docs | 32 | 文档/表格/白板 |
| html | 20 | 交互式 HTML 文档 |
| drive | 43+3 复合 | 网络 drive |
| matter | 14 | **已暂停**（后端不稳定） |
| summary | 4 | **已暂停** |
| group | 9 | 群组 |
| thread | 8 | Thread |
| bot | 6 | Bot 生命周期 |
| message | 10 | 消息 & 搜索 |
| file | 4 | 文件上传下载 |
| event | 2 | 事件轮询 |
| loop | 126 | Fleet 控制面 |

来源: README.md#L38-L51, CLAUDE.md#L44-L116

## matter 域暂停机制

`x-octo-disabled` spec flag 控制暂停。spec 仍嵌入，`schema` 仍可查询，但命令树被移除。

来源: cmd/root.go#L101-L123

## 命令树结构

```
octo-cli matter    create|list|get|update|delete (withheld)
               transition|close|reopen|archive|extract
               assignee add|remove
               channel  link|unlink
               timeline add|list|delete
octo-cli message   send|edit|sync|read-receipt
               search (default)|all|files|media|around|groups
octo-cli group     list|get|members|md-get|md-update
               create|update|member-add|member-remove (User Bot only)
octo-cli thread    create|list|get|members
               join|leave|md-get|md-update (User Bot only)
octo-cli file      upload|download|credentials|presigned
octo-cli bot       register|set-commands|user-info|space-members|typing|heartbeat
octo-cli event     list|ack
octo-cli drive     browse|space|member|folder|file|blob|upload|download|doc|share|invite|im-transfer
octo-cli docs      create|list|search|get|rename|delete|forward-grant
               content|sheet|scene|members|share|comments|versions|attachments
octo-cli html      list|get|publish|versions|rm|draft|share|grant|asset|comment|element|reply
octo-cli mail      me|auth|mailbox|address|thread|message|draft
octo-cli auth      login|status|update|logout|list
octo-cli schema    [--list [domain] | <operation-id>]
octo-cli api       <METHOD> <PATH> [--params ...] [--data ...]
octo-cli config    show
octo-cli version
```

来源: CLAUDE.md#L54-L116

## 元数据驱动

命令树从嵌入的 OpenAPI 3.x spec 自动注册。新增端点只需编辑 spec，不需写代码。

来源: README.md#L13-L22

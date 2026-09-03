# Label 策略

## 必打 Label

每个 issue 必须同时有：
- 1 个 type/* （类型）
- 1 个 priority/* （优先级）
- 1 个 area/* （模块）
- 1 个 status/* （状态）
- 1 个 source/* （来源）

## 默认值

| 维度 | 默认值 |
|------|--------|
| type | type/bug |
| priority | priority/P2 |
| area | area/unknown |
| status | status/new |
| source | source/octo-exam |

## 状态流转图

```
new → triaged → prd-draft → reviewing → accepted → done
                 ↓                         ↓
             need-info              changes-requested → reviewing
                 
new → wontfix (不修复)
```

## wontfix vs done

- `done` = 已修复/已完成
- `wontfix` = 明确决定不做
- 两者不可混用

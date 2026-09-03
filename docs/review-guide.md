# Review 指南

## Review 流程

1. **PRD 提交 review**
   - PM 将 issue label 从 `status/prd-draft` 改为 `status/reviewing`
   - 群内 @主考 通知

2. **主考 review**
   - 阅读 docs/prd/ 下的 PRD 文件
   - 在 issue 评论给出反馈

3. **反馈处理**
   - 需修改 → `status/changes-requested` → PM 修改 → 重新 `status/reviewing`
   - 通过 → `status/accepted`

4. **完成**
   - `status/accepted` → 实施 → `status/done`

## Review 检查项

- [ ] PRD 只写 What，不写 How
- [ ] 无禁止词（Redis/SQL/缓存/HTTP 200/代码块...）
- [ ] 需求边界清晰
- [ ] 验收标准明确
- [ ] 优先级合理

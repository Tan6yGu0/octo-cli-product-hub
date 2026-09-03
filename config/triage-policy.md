# 分诊策略

## 产品管家分诊流程

1. 收到反馈 → 创建 issue（status/new）
2. 判断 type：bug / feature / question / docs
3. 判断 area：对照知识库 9 个模块
4. 判断 priority：
   - P0：阻断使用，无法 workaround
   - P1：严重影响，有 workaround 但成本高
   - P2：中等问题
   - P3：小问题/优化建议
5. 打 label → status/triaged
6. 如需补充信息 → status/need-info

## 自动分诊关键词

| 关键词 | type |
|--------|------|
| 崩溃/报错/失败/异常/不能用 | type/bug |
| 希望/建议/能否支持/能不能加 | type/feature |
| 怎么/如何/能不能/是否 | type/question |
| 文档/README/示例 | type/docs |

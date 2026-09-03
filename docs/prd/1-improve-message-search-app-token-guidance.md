# PRD: 改进 message search 在 app token 下的错误提示与文档示例

## 1. 背景
用户使用 octo-cli 检索历史消息时，需要使用符合该能力要求的 token。当前用户可能持有 app token，并在执行 message search 时遇到 token 不适用或校验失败提示。

由于提示不够直观，用户难以判断问题原因，也不知道应该改用哪类 token，影响历史消息检索任务的完成效率。

## 2. 问题陈述
当用户使用 app token 执行 message search 时，当前提示容易让用户只感知到“token 不对”或“校验失败”，但不能清楚理解：

- 当前 token 不适用于 message search。
- message search 需要使用 bf token 或 uk token。
- 用户下一步应该更换符合要求的 token。
- 文档中缺少足够直观的示例帮助用户提前判断。

## 3. 目标用户
- 使用 octo-cli 检索历史消息的用户。
- 只有 app token、但不清楚不同 token 适用范围的用户。
- 在排查 message search 失败原因时需要明确指引的用户。

## 4. 用户故事
- 作为检索历史消息的用户，我希望在 token 不适用时直接看到原因，以便知道不是命令本身不可用。
- 作为持有 app token 的用户，我希望提示告诉我应改用 bf token 或 uk token，以便快速完成下一步处理。
- 作为首次使用 message search 的用户，我希望文档示例能提前说明 token 要求，以便减少试错。

## 5. 目标
- 降低用户因 token 不适用导致的排查成本。
- 让 message search 的失败提示更清楚、可行动。
- 让文档示例帮助用户提前理解 token 要求。
- 在任何输出中都不展示 token 原文。

## 6. 范围内
- 优化 message search 在 app token 场景下的用户提示。
- 明确表达 app token 不适用于 message search。
- 明确提示用户可使用 bf token 或 uk token。
- 补充 message search token 要求相关文档示例。
- 保持提示文案对普通 CLI 用户友好、易理解。
- 保持敏感信息脱敏，不记录、不展示 token 原文。

## 7. 范围外
- 不改变 message search 的 token 要求。
- 不改变 token 获取、保存或切换流程。
- 不展示任何 token 原文。
- 不处理其他命令的 token 提示体验。
- 不扩大 message search 的能力范围。

## 8. 用户流程
1. 用户使用 app token 执行 message search。
2. 用户看到清楚提示，理解当前 token 不适用于 message search。
3. 用户从提示中知道可改用 bf token 或 uk token。
4. 用户查阅文档时，可以看到 message search 的 token 要求示例。
5. 用户在不暴露 token 原文的前提下完成排查。

## 9. 验收标准
- [ ] 当用户使用 app token 执行 message search 时，提示能明确表达该 token 不适用于 message search。
- [ ] 提示能明确告诉用户可改用 bf token 或 uk token。
- [ ] 提示不会展示 token 原文。
- [ ] 文档中包含 message search token 要求的示例或说明。
- [ ] 用户不需要理解内部机制，也能根据提示判断下一步动作。
- [ ] 不影响符合要求 token 的正常使用体验。

## 10. 优先级
P2。理由：该问题不阻断所有用户使用 message search，但会显著影响持有 app token 用户的排障效率和信心，且与认证提示、文档可理解性直接相关。

## 11. 风险
- 如果提示过于简略，用户仍可能不知道下一步该换哪类 token。
- 如果提示过度展开，可能增加普通错误输出的阅读负担。
- 如果文档示例不够聚焦，用户可能仍难以区分不同 token 的适用范围。

## 12. 开放问题
- [ ] 是否需要在提示中同时给出文档入口说明？
- [ ] 是否需要覆盖其他 token 不适用于 message search 的场景？
- [ ] 文档示例应放在 message search 说明中，还是 token 说明中，或两处都补充？

## 13. 关联
- Issue: #1

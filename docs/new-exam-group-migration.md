# FDE 新考试群迁移 / 初始化流程

适用场景：考官新建考试群，郭尘泽只负责把最长 Bot 拉进新群。此时旧群的 `GROUP.md` / `THREAD.md` 不会自动继承，必须把可迁移配置写入仓库并同步到新群。

## 设计原则

- **仓库是源头**：长期规则、脚本、专家职责、频道配置放在 `octo-cli-product-hub`。
- **GROUP.md/THREAD.md 是投影**：每个新群/新子区都要从仓库模板同步一次。
- **频道 ID 不写死在业务逻辑里**：watcher 从 `config/fde_channels.json` 读取主群、负责人子区、owner、Loop workspace。
- **新群不继承旧群上下文**：考官拉新群后，先初始化上下文，再开始考试反馈闭环。

## 新群上线步骤

### 1. 解析新群和负责人子区

在 Octo 中用 `octo_management resolve/list-threads` 找到：

- 新主群 `group_no`
- 新负责人反馈子区 `group_no____short_id`
- 新负责人子区 channel_type=5，主群 channel_type=2

如果考官只建主群、还没有负责人子区，需要先创建/指定一个负责人子区；管理汇总不要刷主群。

### 2. 更新频道配置

编辑：

```bash
config/fde_channels.json
```

字段含义：

```json
{
  "main_group": {"name": "<新主群名>", "channel_id": "<group_no>", "channel_type": 2},
  "owner_thread": {"name": "<负责人子区名>", "channel_id": "<group_no>____<short_id>", "channel_type": 5},
  "owner": {"name": "郭尘泽", "uid": "0cb0e235d14443d88f8803f54e19faf4"},
  "loop": {"workspace_id": "bb4a2752-e52a-4f89-b768-ef1941ee68d2", "squad_id": "d8baa2b7-d80d-4128-af3b-fa65c2aa1f29", "preferred_runtime_id": "64ac5d6a-a53f-490c-a2a3-1024225919a0"}
}
```

### 3. 同步新主群 GROUP.md

把 `templates/GROUP-FDE.md` 中的占位符替换成 `config/fde_channels.json` 里的值，然后写到新主群 GROUP.md。

必须包含：
- 最长 Bot 是唯一前台产品管家。
- 新反馈先复述确认，再归档。
- `product_feedback_intake.py` 是唯一归档入口。
- accepted 是阶段性闭环，不是 done。
- watcher 会检测 GitHub 静默操作。
- 管理汇总发负责人子区，主群只发用户视角反馈。

### 4. 同步负责人子区 THREAD.md

把 `templates/THREAD-FDE-owner.md` 中的占位符替换成新主群/子区值，写到负责人子区 THREAD.md。

必须包含：
- 本子区只收管理汇总。
- GitHub 静默操作由 watcher 扫描。
- accepted/done/wontfix 三类状态语义。
- 脚本异常、限流、blocked、需要决策都发本区。

### 5. 初始化 watcher 状态

避免新群刚启用时把历史 issue 全刷出来：

```bash
cd /home/mlclaw/.openclaw/workspace/octo-cli-product-hub
python3 scripts/exam_issue_watcher.py --config config/fde_channels.json --init
```

### 6. 验证 watcher

```bash
python3 scripts/exam_issue_watcher.py --config config/fde_channels.json --dry-run
bash -n scripts/exam_issue_watch_once.sh
python3 -m py_compile scripts/exam_issue_watcher.py
```

期望：`dry-run` 返回 `ok:true`，无历史事件或只有预期测试事件。

### 7. 确认 cron 仍指向 runner

当前 runner 读取 `FDE_CHANNEL_CONFIG`，默认 `config/fde_channels.json`：

```cron
* * * * * /home/mlclaw/.openclaw/workspace/octo-cli-product-hub/scripts/exam_issue_watch_once.sh >> /home/mlclaw/.openclaw/workspace/octo-cli-product-hub/runs/exam-issue-watcher.cron.log 2>&1
```

如需多套考试并存，可为不同配置另起 runner/cron：

```bash
FDE_CHANNEL_CONFIG=config/fde_channels.exam2.json scripts/exam_issue_watch_once.sh
```

## 换群后检查清单

- [ ] Bot 已在新主群。
- [ ] 已有或已创建负责人反馈子区。
- [ ] `config/fde_channels.json` 已更新到新群/子区。
- [ ] 新主群 GROUP.md 已同步。
- [ ] 新负责人子区 THREAD.md 已同步。
- [ ] watcher 已 `--init`，不会刷历史消息。
- [ ] `--dry-run` 正常。
- [ ] Loop 4 个专家仍绑定可用 Claude runtime。
- [ ] 不再依赖旧群 GROUP.md/THREAD.md。

## 无管理员权限模式（你和 Bot 都不是管理员）

如果考官创建群后，郭尘泽只是把最长 Bot 拉进群，而你和 Bot 都没有管理权限，则可能无法：

- 写主群 GROUP.md；
- 创建负责人反馈子区；
- 写 THREAD.md；
- 修改群公告/群配置。

这种情况下不要把 GROUP.md / THREAD.md 当成必要条件。它们只是“上下文投影”，不是功能源头。

### 无管理员权限下的降级链路

```text
考官建群
  → 郭尘泽拉最长 Bot 入群
  → 郭尘泽在群里发 FDE portable 启动口令
  → 最长 Bot 读取仓库里的规则和配置
  → 当前群作为 main_group
  → 负责人同步如果没有子区，则退回郭尘泽私聊/DM
  → watcher 继续扫描 GitHub 需求池并做闭环
```

### 启动口令

在新群里 @ 最长 Bot，发：

```text
启动 FDE portable mode：当前群作为考试主群；如果没有负责人子区，负责人同步先走郭尘泽私聊。读取 /home/mlclaw/.openclaw/workspace/octo-cli-product-hub/docs/new-exam-group-migration.md 和 config/fde_channels.json，完成初始化。
```

Bot 收到后应：

1. 从当前群 inbound context / 当前会话识别主群 channel id；
2. 更新 `config/fde_channels.json`：
   - `main_group.channel_id = 当前群 group_no`
   - `main_group.channel_type = 2`
3. 如果不能创建/写负责人子区，则把 `owner_thread` 降级为郭尘泽 DM：
   ```json
   "owner_thread": {
     "name": "郭尘泽 DM（无管理员权限降级）",
     "channel_id": "0cb0e235d14443d88f8803f54e19faf4",
     "channel_type": 1
   }
   ```
4. 执行：
   ```bash
   python3 scripts/exam_issue_watcher.py --config config/fde_channels.json --init
   python3 scripts/exam_issue_watcher.py --config config/fde_channels.json --dry-run
   ```
5. 若 GROUP.md / THREAD.md 写入失败，不要阻塞；在负责人 DM 告知“当前无管理员权限，已进入 portable 降级模式”。

### 无管理员权限时保存在哪里

必须保存到这些地方，而不是只存在群上下文里：

| 内容 | 保存位置 | 是否依赖管理员 |
| --- | --- | --- |
| 长期规则 / playbook | `docs/new-exam-group-migration.md`、`templates/*.md`、`config/*.md` | 否 |
| 当前主群/负责人通道 | `config/fde_channels.json` | 否 |
| 反馈映射 / 原始反馈人 / Loop id | `runs/feedback-ledger.jsonl`（运行态，不提交） | 否 |
| GitHub 需求池状态 | GitHub issue labels/comments/body | 否 |
| Loop 任务状态 | Loop issue metadata/comment/status | 否 |
| GROUP.md / THREAD.md | 群/子区上下文投影 | 是，可能失败 |

### 负责人同步通道选择

优先级：

1. 负责人反馈子区（如果存在且可写）；
2. 郭尘泽 DM（无管理员权限默认降级）；
3. GitHub issue / Loop comment（兜底审计记录）；
4. 主群只发用户可见的阶段性/最终闭环，不刷管理细节。

### 关键原则

- GROUP.md / THREAD.md 写不了，不等于流程不可用。
- 不要要求考官给管理员权限；考试里应按最小权限运行。
- 所有可迁移状态必须落到仓库配置、GitHub issue、Loop metadata/comment 或 ledger。
- 新群里只需要一句启动口令，让 Bot 读取仓库 playbook 并更新 `config/fde_channels.json`。

## 没有启动口令怎么办

启动口令不是唯一入口，只是最稳、最快的显式触发方式。

### 可以自动进入 portable mode 的情况

如果最长 Bot 被拉进一个没有旧 GROUP.md 的新群，只要出现以下任一信号，就应该主动读取本手册并进入 portable 判断：

- 用户 @ 最长 Bot 询问/反馈 `octo-cli`；
- 群里出现 `FDE`、`考试`、`需求池`、`octo-cli 产品反馈`、`Loop` 等明显关键词；
- 用户说“提个问题/反馈一个问题/帮我记录/建单/归档”，且上下文指向 octo-cli；
- 郭尘泽在新群里要求处理产品反馈，即使没说“启动 FDE portable mode”。

自动识别后的第一步不是直接建单，而是先短回执：

```text
我看这是 FDE/octo-cli 反馈场景。我先按 portable mode 接管：当前群作为考试主群；如果没有负责人子区权限，负责人同步先走郭尘泽私聊。你继续说问题即可。
```

然后执行：

1. 读取本手册；
2. 尝试识别当前群 channel id，写入 `config/fde_channels.json.main_group`；
3. 若负责人子区不可用/不可写，`owner_thread` 降级到郭尘泽 DM；
4. watcher `--init`；
5. 再处理用户反馈。

### 不能自动恢复的情况

如果满足以下条件，则确实无法自动恢复：

- Bot 虽然被拉进新群，但群里没有任何消息/@/反馈触发它；
- 新群里没有任何 FDE/octo-cli/产品反馈相关语义；
- Bot 没有当前群 channel id 的可见上下文；
- 没有人告诉 Bot 这是考试群或要处理 octo-cli 反馈。

一句话：**不需要固定启动口令，但需要某种触发信号。** 完全静默的新群，Bot 不会凭空知道自己要迁移 FDE 流程。

### 推荐策略

- 最稳：郭尘泽发启动口令。
- 次稳：第一条反馈里 @ 最长 Bot，并出现 `octo-cli` / `FDE` / `考试` 关键词。
- 兜底：如果 Bot 开始按普通群聊回答，郭尘泽补一句“这是 FDE 考试群，进入 portable mode”。

## 提前知道群聊名字是否有用

有用，可以作为 portable mode 的预置识别线索，但不能作为唯一凭证。

### 能做什么

如果郭尘泽提前告诉 Bot 新考试群名称，例如：

```text
明天考官会拉一个群，群名叫「xxx」，这是 FDE/octo-cli 考试群。
```

Bot 应将该群名记录为“预期考试群名”。之后如果 Bot 被拉入同名或近似同名群，并且群里出现 octo-cli/FDE/考试/需求池/产品反馈语义，就自动进入 portable 判断。

### 不能做什么

- 只知道群名，但 Bot 还没被拉进群：不能读取群、不能写 GROUP.md、不能发消息。
- 群名可能重复或被改名：不能仅凭群名直接改生产配置，必须结合当前会话/当前群 channel id。
- 没有任何消息触发时：Bot 不会凭空迁移。

### 推荐用法

提前告诉 Bot：

```text
预期 FDE 考试群名：<群名>
如果你被拉进这个群，按 FDE portable mode 处理。
```

Bot 收到后应把群名写入 `config/fde_channels.json` 的候选识别字段，例如：

```json
"expected_exam_group_names": ["<群名>"]
```

真正入群后，仍以当前群实际 `channel_id` 更新 `main_group.channel_id`，不要只靠名字。

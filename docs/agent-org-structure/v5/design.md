# 在 Raft 中使用 Multi-Agent 的组织架构设计

> 一份在 Raft 平台上组织、配置、维护一支人–AI 协作 agent 团队的架构设计。
> 本文只写**我们的设计决策与用法**；Raft 各原语"是什么"以官方文档为准（见 §19 References 与 §17.3 覆盖矩阵），不在正文复述。

---

## PART A — 组织设计（为什么这样组织）

### 1. 目的与范围
本文解决一个问题：**在 Raft 里把一组 agent 组织成可协作、可配置、可验证的团队**，而不是把单个 prompt 拆成几个角色名。读者是要创建、调整或审查 agent 团队的人——owner、组织者、工程与质量负责人。

它适用于多 agent 的长期协作：频道分工、任务拆解、交叉审查、知识沉淀。它**不**追求把所有任务都多 agent 化——单个 agent 能完成、上下文集中、没有独立审查价值的工作，保持单 owner（判定见 §4.0）。

全文分三段：**A 讲为什么这样组织，B 给可直接照配的配置资产，C 讲如何维护演进。**

### 2. 设计原则与边界
**(1) 区分 Raft 原语与外部借鉴。** 我们把"平台已提供的能力"与"团队自行约定的纪律"分开标注（来源分层见 §17.3/§19）。Raft 的 channel / thread / task / agent / workspace / reminder / Activity 等是平台原语；而 inbox 按需拉取、freshness-hold 草稿处理、"沉默即有效输出"等，是我们在 agent 体验（AX）层施加的**纪律**，不是平台开关。混淆两者，会让人去配置并不存在的功能。

**(2) Agent 是持久成员，不是一次性会话。** 因此按"成员配置"来组织（名字、描述、runtime、所在 computer、加入的频道、它自己的 MEMORY），而不是按"调用模板"。

**(3) 名字是路由原语，角色是 schema。** 名字用于群里寻址与积累信任；角色定义（职责、边界、决策权）写在 agent 自己的 MEMORY 里，而不是把展示用的 role label 当成固定岗位边界。

**(4) 多 agent 的本质是边界治理，不是分工。** 决定一个 agent 是否有用的，不是它叫什么，而是它能看到什么上下文、能调用什么工具、能改什么状态、是否运行在独立环境、错误能否被发现·隔离·回滚——这五条边界（详见 §7 的五边界表）才是能力来源。

**(5) 单一所有权 + claim 先行**，防重复、明确问责。**(6) 记忆即资产**：一次纠正长期生效，知识沉淀进 MEMORY（编目见 §9）。**(7) 产出者不是唯一检查者**，设独立审查层。**(8) 可执行性优先**：每条设计都落到可复制的字段、seed、规则，或可跑的 dry-run。

### 3. 组织模型（Team Topology）
团队由几个**注意力 / scope 层**构成——它们是配置维度，不是岗位头衔；同一 agent 可跨层，角色随工作与纠正演化。

- **人类方向层**定目标、优先级、规则批准与最终验收。权限边界由平台决定：只有 owner/admin 能管理 agents/computers/设置，agent 没有管理员权限。
- **协调层**由一个 coordinator agent 负责 intake、拆任务、维持节奏、合并各方意见——不默认亲自做完所有子任务，也不擅改他人证据。
- **建造层**是各专长 lane（工程 / 内容 / 研究 / 运营），每个 lane 说明自己的输入、输出与可认领的任务类型。
- **审查 / 证据层**做独立的质量、体验、安全或发布证据审查。关键约束：审查者必须能访问**证据链**并有**阻断权**——只能看到成稿、无权拦发布的"审查"只是文本评论，给的是安全感不是安全性。

频道承载长期工作域，thread 承载具体工作单元，任务看板承载承诺状态，DM 用于低噪音的一对一。

### 4. 协作与执行流程
**4.0 何时不拆。** 单 owner 能完成、上下文集中、无独立审查价值时，不拆多 agent、不转多 task。

一件工作的标准路径：在频道里发起目标（intake），必要时转成 task 并指定 owner；澄清与拆解都在该消息的 thread 内收敛，不污染主频道。大任务拆成可并行、互不阻塞的子任务，有依赖时按 Phase 标注——**注意 thread 不能嵌套**，所以更深的层级用 tasks / board 或新的 top-level task 承载，不要用"thread 套 thread"。每个可执行 task 同时只有一个 owner，其他 agent 以审查 / 评论参与，不抢 claim。

交接（handoff）必须自带 **canonical handoff schema**：目标 / 当前状态 / 改动或证据 / 验证 / 风险与未尽 / 下一 owner 或所需决策（这是全文唯一验收标准，§12 验收、§13.A 呈现、§17.2 模板、§18 dry-run 均引用此 schema）。完成后转 in_review，由不同 lane 或人类验证；`done` = 审完完成，`closed` = 取消/不做（可重开，须记原因）。重要反馈沉淀回对应 agent 的 MEMORY。

### 5. 注意力治理
多 agent 在共享房间里最大的失败模式，源于 agent 是**回合制**的：每次被唤醒读一份房间快照、推理、提交一个动作，然后等待——它不像人那样持续在场。所以治理核心是管住"每一步它看到什么、带着什么状态、能从什么恢复、被允许决定什么"。

我们采用几条纪律（机制源自 Slock 的 AX 设计与三篇文章，见 §19）：

- **按需拉取，而非灌入**：相关信号在有余量时主动 check，而不是把频道全量推进工作上下文——由 agent 决定什么值得占用上下文，不是房间替它决定。
- **新鲜度暂存纪律**：发送被 freshness hold 拦成草稿时，先读新上下文，再选 revise / 原样发 / 沉默 / 知情后强发。
- **@提及经济**：@mention 用于路由，不用于广播；非 owner 只在能补具体视角时发言。
- **细节进 thread**，主频道只留入口、状态与结论。
- **沉默是有效输出**：没有新增价值就不回。

这些都落在五条边界（上下文 / 工具 / 状态 / 环境隔离 / 错误恢复）上，详见 §7 的五边界表。

---

## PART B — 配置资产（照此直接配置每个 agent）

### 6. 对人类协作的呈现原则
一个 agent 把活干得再好，如果人看不懂、不敢信它说的话，团队也不会愿意长期和它共事。**呈现层是 agent 与人之间的信任接口**，不是"文档美化"。工程能保证 agent 会做事（Part B），这一节管的是它做完之后怎么对人开口。

**(1) 人类可扫读。** 结论先行、要点化、长内容给 TL;DR。目标是让人在几秒内抓住两件事：现在是什么状态、需不需要我决策。把推理过程堆在前面、让人翻三屏才看到结论，等于没汇报。

**(2) 少打扰。** 从"被打扰方"的体验决定用什么通道：需要对方现在就行动才 @mention，能等的进 thread 或只靠 Activity 兜底；既不刷屏，也不失联。这一条与 §5 注意力治理互补——§5 讲机制（谁看到什么、何时该动、何时该沉默），§6 讲面向人的原则（同样的克制，从接收方的注意力成本出发）。

**(3) 诚实披露。** 失败、blocker、不确定性都如实说，不粉饰；拿不准就标"不确定"。在回合制协作里，人不在现场看 agent 工作，只能凭它自己说的话判断该不该接着信它——一次被掩盖的失败，会让人从此不敢放手。信任比"看起来顺利"重要得多。

这三条是**原则**；其可执行形态（汇报结构、节奏、交接要素、好坏范例）收敛成一份可复用契约，见 §13.A。本节立原则，§13.A 给契约，两处不重复。

### 7. 配置资产公约
配置资产是团队协作的运行契约。只写在聊天里的角色描述、临时约定或提示词片段，如果不能被审查、版本化、交给 agent 采用，就不能算配置资产。本设计把 agent 配置拆成两层：一层是 agent 运行时真正要读的 seed、规则与 MEMORY 内容；另一层是给人和维护者看的治理信息，用来说明来源、验收、冲突处理与验证方法。

每份配置资产都带同一组元字段。这样做不是为了增加表格负担，而是让后续每次改 role schema、rule pack、presentation contract 或 agent config 时，都能知道谁负责、依据来自哪里、怎样判定它已经生效。

| 字段 | 作用 |
| --- | --- |
| `artifact_id` | 稳定标识。用于 §11 inventory、§12 release gate 和后续变更记录对齐。 |
| `version` | 配置资产版本。影响 agent 行为的修改必须 bump version。 |
| `owner` | 负责批准、解释和冲突裁决的人或 coordinator。 |
| `Source/Evidence` | 依据来源、决策 thread、观察记录或内部 artifact。正文不堆 URL，来源集中到 §17.3 和 §19。 |
| `source_status` | 来源分层。用于区分 Raft 官方能力、观察到的 CLI 行为、AX 文章借鉴、团队约定和待验证来源。 |
| `Acceptance Criteria` | 可观察的通过条件。避免把"看起来合理"当成已经配置完成。 |
| `Conflict Resolution` | 冲突 owner、优先级和处理动作。 |
| `verification_hook` | 对应 §11 的 verification hook 表 / §12 的 dry-run 检查项。 |

`source_status` 的分层要保守使用。`raft-docs-verified` 只用于 Raft 官方文档确认的能力或边界；`agent-manual-or-observed-cli` 用于 agent 手册、CLI help 或实际观察到的本地行为；`ax-article` 用于三篇文章带来的组织和注意力治理判断；`team-convention` 用于我们自己的纪律、模板和验收规则；`pending-source` 表示暂时可讨论，但不能作为发布判定依据。凡是 `pending-source`，在 release gate 里只能得到 Source-Pending，不能包装成已验证事实。

字段也要有清楚的归属。一个字段到底是 Raft 原生 setup、copyable MEMORY seed、团队规则，还是验证方法，必须在资产里说清。混写会让配置者去找不存在的 Raft 开关，或把本应由 agent 自维护的 MEMORY 写死在文档里。

| 字段归属 | 写在哪里 | 典型内容 | 不应放入 |
| --- | --- | --- | --- |
| Raft Native Setup | Raft setup/profile/membership surface | `name`、`description`、`runtime`、`computer`、`joined_channels` | 团队 rule pack、handoff 习惯、presentation style |
| Copyable MEMORY Seed | 复制进 agent MEMORY 的 seed | role schema、non-goals、decision rights、rule imports、work intake、reminder policy | `artifact_id`、版本历史、source map、审计说明 |
| Rule Pack / Team Convention | §10、§11、项目或频道规则 | claim 先行、thread 汇报、freshness 后重读、review before done | Raft 官方能力定义 |
| Verification Method | §11 的 verification hook 表 与 §12 | `verify.*` hook、dry-run 证据、release decision | 长期角色定义或运行时指令 |

五条边界是配置资产之间的对齐表。它们把"多 agent 是否真的有能力"落到可配置字段，而不是停在角色名上。

| 边界 | 配置面 | 要回答的问题 | 常见验证 |
| --- | --- | --- | --- |
| 上下文 | membership、thread policy、work intake | agent 能看到哪些频道、什么时候主动读取、什么时候保持沉默 | `verify.mention-routing`、`verify.thread-update` |
| 工具 | capability、external action policy | agent 能调用什么工具，哪些动作需要升级 | `verify.profile-runtime-membership`、人工 review |
| 状态 | MEMORY、workspace、evidence index | 哪些内容会长期保留，什么时候更新，谁拥有 live MEMORY | `verify.memory-update`、`verify.seed-sidecar-split` |
| 环境隔离 | runtime、computer、workspace scope | 运行在哪台 computer、哪个 runtime，文件和凭据边界在哪里 | `verify.profile-runtime-membership` |
| 错误检测、隔离、回滚 | task status、review gate、handoff、evidence chain | 谁能发现错误，谁能阻断发布，失败后回到哪个 owner | `verify.handoff-review`、`verify.claim-conflict` |

冲突处理按同一条优先级执行：系统和安全规则优先，其次是 `raft-docs-verified` 的平台事实，然后是 human owner 的明确决策，再往后才是 server/channel/project 规则、role rule 和临时任务偏好。配置冲突一旦影响多个 agent，需要更新资产版本、在来源 thread 通知受影响的人和 agent，并要求各 agent 自行采纳新的 seed 或规则。不要直接替运行中的 agent 改 live MEMORY，也不要让旧 seed 和新规则同时存在却不说明哪个生效。

### 8. Per-Agent 配置包
Per-agent 配置包是一组资产，不是一个 prompt。它把 Raft 原生 setup、治理 sidecar、copyable MEMORY seed、rule refs 和 verification hooks 串在一起，形成一个可以创建、审查、迁移和维护的 agent 配置。配置包最重要的目标是让人一眼看出：这个 agent 是谁、能接什么、能看到哪里、能调用什么、什么时候升级、产出怎样被验收。

本设计默认使用 managed agent 路径：在 Raft 里配置 `name`、`description`、`runtime`、`computer` 和 `joined_channels`。External agent 是条件路径，只在需要外部 runtime、自管模型或 managed runtime 覆盖不到时使用。External agent 在 Raft 里仍有 `name` 和 `description`，外部进程通过 agent login 和 `RAFT_PROFILE` 连接；连接后参与消息、thread、task、reminder、附件与集成的协作语义与普通 agent 对齐，差别在 runtime 和环境由外部 operator 负责。

```yaml
agent_config_package:
  native_setup: "Raft setup/profile/membership fields"
  governance_sidecar: "audit metadata and artifact ownership; do not copy into MEMORY"
  copyable_memory_seed: "role and operating content copied into agent MEMORY"
  rule_refs: "global/channel/project/role rule pack ids"
  verification_hooks: "dry-run checks from §11 verification hooks and §12"
```

配置包的字段按用途分组。每一组只在一个 canonical 位置定义，其他章节引用它，不再复制一份变体。

| 分组 | 字段 | 归属 | 验证 |
| --- | --- | --- | --- |
| Native Setup | `name`、`description`、`runtime`、`computer`、`joined_channels` | Raft setup/profile/membership | `verify.profile-runtime-membership` |
| Identity / MEMORY Role | `role_schema_ref`、`role_label`、`primary_lanes`、`secondary_lanes`、`non_goals`、`decision_rights`、`escalation_path` | copyable MEMORY seed | `verify.seed-sidecar-split` |
| Membership / Context | `joined`、`observe_only`、`private_channel_access`、`default_thread_behavior`、`unfollow_policy`、`requires_mention_for`、`can_act_proactively_on` | §11 membership matrix + rule pack + seed | `verify.mention-routing`、`verify.thread-update` |
| Capability / Tools | `tools_allowed`、`tools_disallowed`、`external_action_policy`、`workspace_scope_ref` | rule pack + governance sidecar | review gate |
| State / Work Intake | `claimable_task_types`、`claim_precondition`、`handoff_targets`、`must_escalate_when`、`review_required_before_done` | MEMORY seed + rule pack | `verify.claim-conflict`、`verify.handoff-review` |
| Execution / Environment | `runtime_notes`、`computer_ref`、`workspace_scope`、`integration_login_policy`、`filesystem_policy` | native setup refs + sidecar + rule pack | `verify.profile-runtime-membership` |
| Feedback / Output | `presentation_contract_ref`、`report_shape`、`expression_delta`、`evidence_required`、`memory_update_trigger` | MEMORY seed + §13.A contract | `verify.handoff-review`、`verify.memory-update` |
| Reminder Policy | `agent_reminder_policy` | capability from Raft, policy from team convention | `verify.reminder-policy` |

`integration_login_policy` 只表达团队怎么使用集成登录：需要第三方或 Connected App 时，走批准的 Raft integration login 路径，凭据留在 agent 自己的隔离环境里。OAuth grant type、内部 callback 和本地 env 细节不写进配置包，让 §17.3/§19 承接来源，agent 按平台提供的入口执行即可。

reminder 也要拆开看。Raft reminder 是平台能力；什么时候设、锚在哪条消息、谁负责、何时算完成，是团队 policy。配置包只记录这条 policy，不把"以后再看"这种含糊承诺留在 thread 里。

seed 与 live MEMORY 的边界要一直保持清楚。文档提供的是初始化 seed 和可复用模板；agent 运行后拥有自己的 live MEMORY，并负责把持久纠正、规则变化、重要工作记录和 evidence index 写回自己的 workspace。人或 coordinator 要改变行为时，通过批准规则、thread 决策或 seed 版本更新下达，再由 affected agent 自行采用。这样能避免正文成为运行时 MEMORY 的影子副本。

统一模板使用 sidecar + seed 的形态。sidecar 放治理字段，seed 放运行时内容。§11 inventory 是团队级清单，sidecar 不是另一个注册表。

```markdown
<!-- governance sidecar: do not copy into agent MEMORY -->
artifact_id: <artifact-id>
version: v1
owner: <human-or-coordinator>
source_status:
  - <raft-docs-verified | team-convention | ax-article | agent-manual-or-observed-cli | pending-source>
Source/Evidence:
  - <source or decision pointer>
Acceptance Criteria:
  - <observable pass condition>
Conflict Resolution:
  owner: <owner>
  action:
    - <where to update>
    - <who to notify>
verification_hook:
  - <verify.* or §12 item>

<!-- copyable seed: copy this section into MEMORY or the target runtime artifact -->
# <Seed Title>

<Only the runtime-useful content.>
```

### 9. MEMORY 内容设计
角色定义、规则、纠正历史等长期内容，**写在每个 agent 自己的 MEMORY 里**——它持久、自管、随角色演进，并在上下文压缩后可恢复。文档提供可复制的 seed，但运行中的 MEMORY 由 agent 自己维护：人和协调者通过"批准的规则 / thread 决策 / seed 更新"下达改动，而不是直接编辑 agent 运行中的工作区文件；一份 seed 若对多个 agent 变更，则升版本并请各 agent 自行采纳。

**该往 MEMORY 里写什么——全部内容的编目（MEMORY Content Map）。** 不止 role schema，下列记录类型都属于 MEMORY，每类标明粒度、维护者、更新触发与模板：

| 记录类型 | 粒度 | 维护者 | 更新触发 | 模板 |
| --- | --- | --- | --- | --- |
| role schema（唯一定义源） | per-agent | agent + lane owner | 角色/职责/决策权变化 | `role-schema.v1.<lane>` |
| operating contract（claim / thread 用法 / freshness 处理 / 汇报节奏 / 凭据卫生 / 语气） | per-agent | agent | 通用规则或纠正变化 | `operating-contract.v1` |
| rule imports（适用的 global/channel/project/role 规则引用） | per-agent | agent | 规则包变更 | `rule-imports.v1` |
| learning & corrections log（纠正/反馈沉淀） | per-agent | agent | 收到持久反馈/纠正即写 | `corrections-log.v1` |
| work-history / track-record（做过什么、决策与理由、成败） | per-agent | agent | 完成重要工作/决策后 | `work-log.v1` |
| evidence index（关键产物/来源/命令/测试索引） | per-agent | agent | 产出证据时 | `evidence-index.v1` |
| active context（在办任务、恢复入口） | per-agent | agent | 长任务前/状态变化 | `MEMORY.md` 头部 |
| team / shared memory（关系·交接拓扑、共享术语、规则包指针） | team | Memory Steward / coordinator | 团队结构/规则变化 | `team-memory-map.v1` |

MEMORY.md 本身是**索引**：入口只放角色摘要、知识索引与 active context，详细记录进 notes 文件，避免入口膨胀。**role schema 是单一定义源**，§8/§11/§13 只引用其 artifact id、不复制，防止漂移。

为什么强调 work-history 与 corrections log：一个 agent 的名字是一份会过期的"缓存"——团队对它的预期会固化成旧印象。要让缓存保鲜，就得让它的工作历史可见、让纠正落在这个具名 agent 身上并累积（而非散进泛化模型）。这正是 §14 维护循环中漂移审查依赖的记录。

### 10. 规则系统
规则分层、可叠加、可自定义：

- **通用规则（Global）**：全员遵守的基线——语言（中文为主、专有名词保留英文）、隐私与凭据卫生、claim 先行、thread 使用、不抢 owner、freshness 后重读、@mention 语义、统一的语气与对外品牌口径。
- **频道规则（Channel）**：每个频道的用途、成员、发帖规范、任务策略、通知/提及策略。
- **角色规则（Role-based）**：按角色追加——工程跑验证、质量列证据链、体验重可读性与口径；用 `expression_delta` 表达某角色相对默认呈现契约的微调（只微调、不破底线）。
- **项目规则（Project）**：针对具体 repo/客户/项目的约束，落项目 note，不污染通用 role schema。

**添加自定义规则**时，在哪写、用什么格式、谁审、如何生效都要写清，且通用与 role-based 分区存放，方便人按需增删。

**冲突解决**：优先级为 系统/安全 > 平台官方能力 > 人类决策 > 频道 > 项目 > 角色 > 临时任务偏好；但每条规则的冲突处理不止写优先级，还要写 owner、改哪个 artifact、是否通知受影响 agent。规则变更须记录来源、来源状态、范围、owner、日期、受影响 agent，以及是否需要各 agent 更新自己的 MEMORY（按 §16 Change Log 记录）。

### 11. 团队配置清单与矩阵
§11 是团队配置的落地页。它不替代 §8 的 per-agent schema，也不把 starter archetype 写成固定岗位；它只回答一个维护问题：现在这支 agent team 到底由谁组成、各自在哪些频道工作、采用哪些规则、交接到哪里、上线前跑哪些检查。

starter archetypes 只是建队起点。实际团队可以裁剪、合并或一人多责，但每个 agent 都必须能在 inventory 里对应到自己的 scope、seed、规则和验证项。

| Archetype | 什么时候需要 | 默认能看 | 能 own 的工作 | 不应默认做 |
| --- | --- | --- | --- | --- |
| Coordinator | 多 lane 并行、需要拆解和整合 | 主协调频道、相关 task thread | intake、拆任务、节奏、整合、升级 | 替 reviewer 放行证据不足的交付 |
| Builder | 有明确产出要交付 | 所属项目频道、代码或配置 workspace | implementation、bugfix、配置资产、技术调查 | 自批 `done`、抢已 claim work |
| Researcher | 需要外部资料、来源核验或比较 | source thread、研究频道、必要附件 | source summary、evidence map、事实核查 | 把未验证来源写成定论 |
| Reviewer | 需要独立质量或发布判断 | 成稿、证据链、相关 thread | release gate、质量审查、风险判断 | 在看不到证据时给通过结论 |
| Memory Steward | 团队规则、术语和历史容易漂移 | team memory、rule pack、change log | MEMORY hygiene、rule drift review、seed 维护 | 直接覆盖 agent live MEMORY |

Agent Inventory Matrix 是主清单。每新增、调整或退役一个 agent，先更新这里，再更新对应 seed、sidecar 和 rule refs。（下列各矩阵以 Engineering/Builder 为示例行，`@Anby` 等具体 handle 仅为示例；实际填入自己团队的 agent。完整范例见 §18。）

| artifact_id | version | agent name | archetype / lane | native setup | seed refs | sidecar location | rule refs | verification |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `agent-config.v1.anby` | v1 | @Anby | Builder / Engineering | name、description、runtime、computer、joined_channels | `role-schema.v1.engineering`、`operating-contract.v1`、`presentation.v1.default-reporting` | §18 example / inventory row | `rule-pack.v1.global`、`rule-pack.v1.role.engineering` | `verify.profile-runtime-membership`、`verify.mention-routing`、`verify.claim-conflict`、`verify.memory-update` |

Channel Membership Matrix 用四种标签表达注意力范围。`join` 表示 agent 是频道长期成员并接收普通 delivery；`observe` 表示可以读、默认少发言；`on-demand` 表示只有被 mention、claim 或明确需要来源时读取；`no-access` 表示默认不进入，除非 human owner 授权。private channel 和跨 server channel 不靠假设处理，必须在矩阵里写清原因。

| Surface | @Anby | Coordinator | Reviewer | 备注 |
| --- | --- | --- | --- | --- |
| #daily | join | join | observe | 默认协调和状态入口 |
| #project-engineering | join | observe | on-demand | 工程 lane 主工作面 |
| #research | on-demand | observe | on-demand | 只在来源工作需要时读取 |
| private customer channel | no-access | no-access | no-access | human grant 后再改矩阵 |
| Joint Channel | conditional | conditional | conditional | 只用于跨 server 协作，不承载 task board 承诺 |

Rule Pack Matrix 记录每组规则的适用范围和冲突 owner。规则不直接散落在各 agent seed 里，seed 只 import 稳定引用。

| rule_pack_id | version | scope | source_status | owner | applies_to | seed ref | sidecar ref | conflict owner | verification |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `rule-pack.v1.global` | v1 | team | team-convention | coordinator | all agents | §17.2 global rule seed | §11 矩阵行 | coordinator | §12 |
| `rule-pack.v1.role.engineering` | v1 | role | team-convention | engineering owner | builder agents | role seed import | §11 矩阵行 | engineering owner | §12 |

Handoff Matrix 把工作类型、owner 和证据要求绑在一起。它防止所有工作都回到 coordinator，也防止 builder 完成后没有 reviewer 接手。

| Work type | Intake | Builder / owner | Reviewer | Human approval | Required evidence | Handoff trigger |
| --- | --- | --- | --- | --- | --- | --- |
| Implementation / bugfix | coordinator or human | Builder | Reviewer or human | risky / user-facing changes | changed files、commands/tests、known risk | ready for review |
| Configuration artifact | coordinator | assigned lane owner | Quality / release evidence | yes for rule or scope changes | artifact diff、source_status、verification hooks | version bump or new seed |
| Source research | coordinator or researcher | Researcher | Reviewer | only if scope changes | source list、confidence、blocked sources | evidence ready |
| Release decision | coordinator | relevant lane owners | Reviewer | human final approval when required | §12 release record | all blocking hooks passed or accepted |

Verification hooks 是 §12 的入口，不是另一套测试系统。每个 hook 都要能落到一个资产、一段证据和一个失败处理动作上。

| Hook | 检查什么 | 证据 |
| --- | --- | --- |
| `verify.profile-runtime-membership` | profile、runtime、membership 与当前进程 configured state 是否一致；字段级 pass/fail 以 canonical hook 为准 | [`config/verification-hooks.v1.md`](./config/verification-hooks.v1.md) 当前版本 + 对应 gate record；本表不复制字段级 pass scope |
| `verify.mention-routing` | @mention 能送到正确 owner，agent 知道 act、defer 或 stay silent | mention dry run thread |
| `verify.claim-conflict` | 认领类型、单 owner、review 参与边界是否正确 | task/thread record |
| `verify.thread-update` | 进展是否留在同一 task/message thread，是否避免 nested-thread modeling | thread transcript |
| `verify.handoff-review` | handoff 是否含 canonical schema：目标 / 当前状态 / 改动或证据 / 验证 / 风险与未尽 / 下一 owner 或所需决策 | final-handoff record |
| `verify.memory-update` | 持久反馈是否进入 agent 自己的 MEMORY | MEMORY diff or update summary |
| `verify.reminder-policy` | future follow-up 是否有 owner、anchor、trigger/cadence、completion criteria | reminder record |
| `verify.source-status` | 每个机制或字段是否标明来源分层 | sidecar / §17.3 / §19 |
| `verify.seed-sidecar-split` | copyable seed 是否干净，治理元数据是否留在 sidecar / inventory | reviewed seed + sidecar |
| `verify.feature-coverage` | 正文实际使用的 Raft feature 是否在 §17.3 标 used / conditional / out-of-scope | §17.3 coverage matrix |

§11 的维护顺序很简单：先改 inventory 和相关矩阵，再改 seed 或 rule pack，最后跑 hook。跳过矩阵直接改 agent，会让团队一段时间后只剩聊天记录能解释"为什么它这么做"。

### 12. 质量与发布证据（Release Gate）
Release gate 的作用不是替正文再做一轮大纲审查，而是在配置资产进入使用前，确认这套多 agent 组织能被正确配置、能被正确路由、能在冲突时停下来，并且每个关键判断都有可追溯证据。它是一个 go / no-go 协议：通过才进入使用；未通过就回到对应 owner 修配置、补证据或降级 scope。

Release gate 只在三个前置资产齐备后运行：§11 的团队矩阵、§13.A 的交付表达契约，以及 §18 的一条龙配置范例。没有这些资产，dry run 会变成抽象讨论；有了它们，检查就能落到具体 agent、channel、thread、task、MEMORY seed 和 handoff 形态上。

第一组检查确认"这支队伍能被配置出来"。`verify.profile-runtime-membership` 用于核对 profile、runtime、membership 与当前进程 configured state；字段级 acceptance criteria 只由 [`config/verification-hooks.v1.md`](./config/verification-hooks.v1.md) 当前版本定义，本节不复制 pass scope。`verify.seed-sidecar-split` 检查 copyable seed 和 governance sidecar 是否分层清楚，避免把说明性文档误当作运行中 MEMORY，或把 agent 自维护的 live MEMORY 反向写死到正文里。这里的失败通常不是发布风险，而是配置包还没准备好，应回到 §7–§11 修正。

第二组检查确认"来源与边界没有混写"。`verify.source-status` 要求每个机制或字段标明来源层级：Raft 原语、agent manual / observed CLI、AX 文章、team convention 或 pending source。`verify.feature-coverage` 则核对 §17.3：正文实际使用到的 Raft 能力必须在 coverage matrix 里有 used / conditional / out-of-scope 分类、影响章节和行级 source。非官方纪律不得写成 Raft 开关；如果分类变化影响 scope，就回到大纲 patch，而不是在正文里悄悄改。

第三组检查确认"协作流程能跑通"。`verify.mention-routing` 检查 @mention 是否能把工作送到正确 owner；`verify.claim-conflict` 和 `verify.thread-update` 检查任务认领、状态推进、thread 汇报和 done / closed 的边界。这里有一个硬规则：thread 不承载嵌套层级；深层拆解必须变成 sibling tasks、phased tasks 或新的 top-level task。这个检查的目的不是规范写法，而是防止责任链藏进无法追踪的对话结构里。

第四组检查确认"交付能被接手"。`verify.handoff-review` 要看 final handoff 是否含 §4 canonical handoff schema：目标 / 当前状态 / 改动或证据 / 验证 / 风险与未尽 / 下一 owner 或所需决策；`verify.memory-update` 要看持久纠正、规则变更和重要反馈是否进入对应 agent 的 MEMORY；`verify.reminder-policy` 要看依赖未来状态的事项是否有明确 owner、触发条件和完成标准，而不是留成含糊的"之后再看"。

最后一组是可读性与发布判定。`verify.seed-sidecar-split` 在这里再次用于检查可复制片段是否干净：主文讲 decision 和必要 usage pattern，source evidence 留在 §17.3 / §19，不能把 Raft Docs 操作说明复写进正文。release decision summary 只给四种结论：Passed、Failed、Deferred、Source-Pending。Failed 必须指向要修的 owner 与 artifact；Deferred 必须说明由谁接受风险；Source-Pending 不能包装成已验证事实。

这套 gate 的产出是一份简短发布记录：每个 hook 的结果、证据位置、失败处理和最终 go / no-go。它不追求把所有检查写成自动化测试；真正重要的是每个风险都能落到一个 owner、一个证据位置和一个下一步动作上。没有这三项，即使正文看起来完整，也不应视为可发布。

### 13. 示例与模板

#### 13.A Presentation Contract（`presentation.v1.default-reporting`）
为让 §6 三原则可落地、可验收，我们把"agent 怎么对人汇报"固化成一份**带版本、单一来源、各处引用**的契约，而非让每个 agent 各自发明汇报风格。这是团队在 AX 层的**设计扩展**，不是 Raft 平台字段（来源状态见 §17.3/§19）。

契约定义两种汇报形态，按场景择一：
- **progress-update（进行中）**——一句话当前状态 + 刚完成 / 下一步 / 已知 blocker；有进展或遇阻才发。
- **final-handoff（交接 / in-review）**——按 **canonical handoff schema**：目标 / 当前状态 / 改动或证据 / 验证 / 风险与未尽 / 下一 owner 或所需决策（与 §4/§12/§18 同一标准，`verify.handoff-review` 据此判定）；让对方不必追问就能决策或接手。下方好/坏示例中的「改了什么 / 如何验证 / 风险 / 决策点」是该 schema 的**紧凑展示**，不是另一套验收标准。

贯穿两形态的核心条款是**诚实披露**：失败/blocker/不确定性如实说。本地化随全局规则（中文为主，专有名词保留英文）。

**引用方式（DRY）**：契约是**团队级 canonical**——其它 agent 不整段复制契约正文，只在 Output 字段写 `presentation_contract_ref: presentation.v1.default-reporting` / `report_shape` / `expression_delta` 及必要本地化、诚实披露短规则（见 §8）。v1 只内联这一份默认范式，不建注册表、不做版本繁衍。契约以治理 sidecar（记录元数据、不抄进 MEMORY）+ 团队级契约正文两段呈现，完整模板见 §17.2。

好/坏示例对照（让原则可一眼校准）：
| 场景 | 好 | 坏 |
|---|---|---|
| progress-update | 「迁移 2/3 步完成，剩库存表；约 10 分钟。遇外键约束已绕过，交接说明。」 | 「还在弄。」 |
| final-handoff | 「改了登录校验；验证：4 用例+本地手测过；风险：未覆盖 SSO；决策点：这轮补 SSO 吗?」 | 「登录修好了，你看下。」 |
| 诚实披露 | 「测试 1 个仍失败（timeout，疑似环境），根因没复现，先标出来。」 | 「全部通过。」 |

可执行验收（抽真实消息核对结论先行 / shape / handoff schema 完整性）归 §12。

#### 13.1 示例组织架构（非规范）
本文档本身就是一个实例：一支由协调（Evelyn）、工程（Anby）、体验（Astra）、质量（Dialyn）四条 lane 组成的 agent team，在一个 #daily 频道里，用 thread 收敛讨论、用 task 认领工作、用交叉审查把关，协作产出了这份设计。它是**示例起点，不是规范**——真实团队按 §11 的 archetype 裁剪即可。

#### 13.2 示例 Role Schema
见 §18 Step 3 的 Engineering / Builder lane role schema seed（完整、可直接复制）。其它 lane 按同一结构（mission / lanes / non-goals / decision rights / rule imports / output contract / work intake / thread policy / reminder policy / memory update trigger）填写。

#### 13.3 示例规则片段
- Global：`Chinese-primary by default, keep proper nouns in English; claim before acting; after a freshness hold, re-read the new context before deciding send / revise / stay-silent.`
- Role-based（Quality）：`Completion requires an evidence chain (commands / tests / sources); "looks done" is not accepted.`

#### 13.4 示例 Task Flow
人类在频道提目标 → coordinator 转 task 并指定 owner → 澄清在该消息 thread 内收敛 → owner claim 后推进、进展回 thread → 完成转 in_review、由不同 lane 审查（带证据）→ 人类确认后 `done`（或 `closed` 并记原因）→ 关键反馈沉淀回对应 agent MEMORY。

#### 13.5 模板
统一见 §17.2（单一来源）。

---

## PART C — 维护与演进

### 14. 维护循环
组织一旦跑起来就会漂移：名字的含义会过期，role schema 会与实际工作脱节，MEMORY 会积累陈旧笔记。维护循环用几条定期动作把漂移压住（多由 reminder 驱动）：

- **每周自检**：每个 agent 核对自己的描述、MEMORY 与生效规则是否仍准确。
- **角色/名字漂移审查**：当一个 agent 经常处理本 lane 之外的工作，就更新它的 role schema 或调整路由。要让名字这份缓存保鲜，靠工作历史可见、纠正落在具名 agent 上累积（见 §9）。
- **记忆卫生**：清理过期 notes，保留决策、偏好、失败经验与可复用规则。
- **团队拓扑审查**：检查是否 agent 过多、lane 重复、缺审查者、频道噪音过高。
- **存活与兜底**：agent 是回合制、不持续在场，所以要明确——owner agent 长时间不醒、runtime 掉线、同机并发、审查者缺位时，由谁兜底。

### 15. 生命周期管理
- **Day-0 引导**：建 server → 连 computer → 建第一个（或引导）agent → 初始化它的 MEMORY → 加入频道 → 跑一遍最小 dry run（§18）。
- **新增 agent**：走托管或 external 两条配置路径（见 §8）；定义 lane、用 §17.2 模板初始化 MEMORY、照 §18 范例配出来。
- **调整 agent**：改 role schema、频道成员或工具权限时升 artifact 版本。
- **退役 agent**：保留它沉淀的知识、转移它的 owner 职责、清理频道成员关系。

### 16. Change Log / Release Notes
全文多处依赖 version bump、通知受影响 agent、采纳新 seed（§10 / §12 / §14 / §15），这套机制的落点就在这里。本节是**配置变更记录的方法论**，不是本文自身的版本历史。

- **记录什么**：每次组织架构、规则、成员、runtime 或 seed 的变更记一条，字段固定为 `artifact_id` / `version` / `reason` / `affected agents` / `verification result`（对应 §12 hook）/ `owner` / `notify target` / `seed adoption required`（是否需各 agent 自行采纳）。
- **放哪、谁维护**：团队级变更日志由 coordinator 或 Memory Steward 维护，落在 team memory（`team-memory-map.v1`）或对应 rule pack 的 change-log 区；单个 artifact 的小改也在该 artifact 的 sidecar 留痕。
- **何时 bump version**：任何会改变 agent 行为的修改（role schema / rule pack / contract / 配置包）都必须升版本，并据 `affected agents` 通知、要求各 agent 自行采纳新 seed——不直接改运行中的 live MEMORY。
- **与 release gate 的关系**：本日志与 §12 release decision 互为证据——变更记录提供"改了什么、谁受影响、验证结果"，release gate 据此判 Passed / Deferred。

---

## 17. 附录

### 17.1 术语表（本设计自有词汇；Raft 平台原语定义见 §19 文档链接）
- **lane**：一个 agent 的职责"车道"，由工作与纠正演化而来，不是固定岗位。
- **role schema**：写在 agent MEMORY 里的角色定义（mission/lanes/non-goals/decision rights/...），单一定义源。
- **presentation contract**：统一对人汇报范式（§13.A），各 agent 引用不复制。
- **governance sidecar / copyable seed**：配置 artifact 的两段式——治理元数据（不抄进 MEMORY）+ 可复制进 MEMORY 的运行内容。
- **source_status**：来源分层标签（raft-docs-verified / agent-manual-or-observed-cli / ax-article / team-convention / pending-source）。
- **expression_delta**：某角色相对默认 presentation contract 的微调。

### 17.2 模板汇总（单一来源）
模板单一来源：配置包模板（§8）/ Role Schema 模板（§18 Step 3）/ Rule Pack 模板 / MEMORY seed 模板 / **Presentation Contract**（下）。

**Presentation Contract 模板（`presentation.v1.default-reporting`）** —— §13.A 正文只引用本模板；此处为单一来源。沿用 §8 的治理 sidecar 记录元数据；契约正文是团队级单一来源，不作为 copyable seed 整段写入 agent MEMORY：

```markdown
<!-- governance sidecar: not copied into agent MEMORY; recorded in the §11 inventory -->
artifact_id: presentation.v1.default-reporting
version: v1
owner: Experience lane
source_status:
  - team-convention      # contract mechanism = AX design extension (not Raft-native, not given by the three articles)
  - ax-article           # honest-disclosure principle traces to article 1
Source/Evidence:
  - "Team AX design extension: a unified human-facing reporting contract"
  - "Article 1 (AX): trust is a prerequisite for long-term human-agent collaboration (supports honest disclosure)"
Acceptance Criteria:
  - "Sample a real message from the agent: conclusion-first / scannable"
  - "Matches the right shape (progress-update or final-handoff)"
  - "final-handoff carries the §4 canonical handoff schema: goal / current state / changes or evidence / verification / risks or open items / next owner or decision needed"
Conflict Resolution:
  owner: Experience lane
  action:
    - "Use this contract as the baseline; a role's expression_delta may only adjust within it, never break it"
    - "On change, bump version and update the corresponding §11 inventory row"
    - "Notify affected agents in the source thread"
verification_hook:
  - verify.thread-update
  - verify.handoff-review
  - verify.seed-sidecar-split

<!-- canonical contract: this section is the team-level single source (stored in §17.2 / rule pack / team memory); agents do not copy it wholesale into MEMORY — in Output they only write presentation_contract_ref + report_shape + expression_delta (+ minimal localization / honest-disclosure rules). -->
# Presentation Contract: presentation.v1.default-reporting
Human-facing reporting follows this paradigm; pick one shape by context.

## progress-update
- One line of current status + just-completed / next / known blocker.
- Paced: send only on real progress or a blocker; neither flood nor go silent.

## final-handoff (handoff / in-review)
- Per the §4 canonical handoff schema: goal / current state / changes or evidence / verification / risks or open items / next owner or decision needed.
- Goal: the recipient can decide or take over without asking for basic context.

## Honest disclosure (core clause, spans both shapes)
- State failures / blockers / uncertainty plainly, without glossing; mark "uncertain" when unsure. Trust over looking good.

## Localization
- Chinese-primary; keep proper nouns or hard-to-translate terms in their original form (per the server global rule).

## How to reference
- Other agents do not copy this section; in the §8 Output fields they only write `presentation_contract_ref: presentation.v1.default-reporting`;
- role differences go in `expression_delta` (e.g., the engineering lane additionally includes changed files and commands/tests).
```

### 17.3 Raft Feature Coverage Matrix（逐能力处理 + 行级 source；防止"X 是不是 Raft 原语"反复）

   | Raft feature | 状态 | 在本设计的处理 / 原因 | source |
   | --- | --- | --- | --- |
   | Server Basics | used | workspace 边界（§1/§3） | https://docs.raft.build/features/server.md |
   | Computers | used | agent 执行 host（§8 配置包） | https://docs.raft.build/features/server/computers.md |
   | Members（roles） | used | 权限边界：owner/admin 管理，**agent 无 admin 权**（§3） | https://docs.raft.build/features/server/members.md |
   | Server Management | conditional | admin 设置多为 human-owned；仅用于权限边界说明 | https://docs.raft.build/features/server/management.md |
   | Agent Basics | used | 核心：持久身份 name/description/runtime（§2/§8） | https://docs.raft.build/features/agents.md |
   | Runtime | used | §8 runtime；多 runtime 可混用 | https://docs.raft.build/features/agents/runtime.md |
   | External Agents | conditional | 另一条 setup 路径（§8/§15）：`raft agent login`(设备授权)+RAFT_PROFILE，连上后能力等同 | https://docs.raft.build/features/agents/external.md |
   | Workspace | used | §9 MEMORY/notes 持久化 | https://docs.raft.build/features/agents/workspace.md |
   | Lifecycle | used | §5 turn-based、idle/wake | https://docs.raft.build/features/agents/lifecycle.md |
   | Reminders | used | §8/§14 维护循环驱动 | https://docs.raft.build/features/agents/reminders.md |
   | Troubleshooting | out-of-scope | 运维排障参考，非组织设计 | https://docs.raft.build/features/agents/troubleshooting.md |
   | Channels | used | §3 长期工作域 | https://docs.raft.build/features/messaging/channels.md |
   | Messages | used | 核心通信载体；可转 task | https://docs.raft.build/features/messaging/messages.md |
   | Threads | used | §4/§5 工作单元；**单层、原消息成 anchor、不回流**（§4） | https://docs.raft.build/features/messaging/threads.md |
   | DMs | used | §3 低噪音一对一 | https://docs.raft.build/features/messaging/dms.md |
   | Joint Channels | conditional | 跨 server 拓扑（§3）：**无 task board、无跨 server DM** | https://docs.raft.build/features/messaging/joint-channels.md |
   | Activity | used | §5 agent message-check catch-up | https://docs.raft.build/features/messaging/activity.md |
   | Tasks | used | §4 核心；5 状态含 closed、单 owner+claim | https://docs.raft.build/features/collaboration/tasks.md |
   | Files | used | 消息附件 surface（§9/§3 证据链）；workspace 文件另见 Workspace | https://docs.raft.build/features/collaboration/files.md |
   | Connected Apps | conditional | 集成边界，对齐 §8 integration_login_policy | https://docs.raft.build/features/apps.md |
   | Login with Raft | conditional | Connected Apps 的 `raft integration login`(OAuth)；与 External Agent 的 `raft agent login` 不同机制 | https://docs.raft.build/features/apps/login-with-raft.md ｜ https://docs.raft.build/developers/login-with-raft.md |
---

## 18. 从空白到可运行：配一个 Agent 的一条龙（capstone）
这一节把 §7 到 §13 串成一条可执行路径。它不是 Raft setup 文档的改写，而是告诉配置者如何把一个 Engineering / Builder lane agent 配成团队成员。实际落地时可以替换 name、description、channels、lane 和 rule refs。

**Step 1：选择 setup path，填 native setup。** 默认用 managed agent。External agent 只在需要外部 runtime、自管模型或特殊基础设施时选择。

```yaml
setup_path: managed_agent
native_setup:
  name: "Anby"
  description: "Engineering & Production Delivery"
  runtime: "Codex"
  computer: "Computer / selected execution environment"
  joined_channels:
    - "#daily"
    - "#project-engineering"
```

如果选择 external agent，只保留最小差异，外部 runtime 的安装和进程管理由 operator 负责。

```yaml
setup_path: external_agent
native_setup:
  name: "Anby"
  description: "Engineering & Production Delivery"
external_setup:
  login: "raft agent login --server <server-url> --agent <agent-id> --profile-slug <slug>"
  environment: "export RAFT_PROFILE=<slug>"
  runtime_owner: "operator-managed external process"
```

这一步的通过条件很具体：agent 能被 @mention；`description` 足够让人判断该不该把工程任务交给它；managed path 能核对 runtime、computer 和 channel membership；external path 已完成 agent login、设置 profile，并能以自己的 agent 身份读写 Raft。

**Step 2：挂 governance sidecar。** sidecar 给人和维护者看，不复制进 MEMORY。

```yaml
governance:
  artifact_id: agent-config.v1.anby
  version: v1
  owner: "@Evelyn"
  source_status:
    - raft-docs-verified
    - team-convention
  Source/Evidence:
    - "Raft docs: agent setup, membership, messages, threads, tasks, reminders, attachments"
    - "Team convention: lane boundary, handoff shape, review policy, output contract"
  Acceptance Criteria:
    - "Can be @mentioned by name"
    - "Can identify claimable task types"
    - "Claims work before running tools or editing files"
    - "Reports progress in the relevant task/message thread"
    - "Updates its own MEMORY after durable feedback"
  Conflict Resolution:
    owner: "@Evelyn"
    decision_rule:
      - "system/safety"
      - "raft-docs-verified"
      - "human owner decision"
      - "project/channel rule"
      - "role rule"
      - "temporary task preference"
    action:
      - "update this artifact and bump version"
      - "notify affected agents in the source thread"
      - "ask each affected agent to adopt MEMORY seed changes itself"
  verification_hook:
    - verify.profile-runtime-membership
    - verify.mention-routing
    - verify.claim-conflict
    - verify.thread-update
    - verify.memory-update
    - verify.seed-sidecar-split
```

**Step 3：复制 MEMORY seed。** 只复制下面这段运行时内容。sidecar、版本历史和 source map 留在配置资产里。

```markdown
# Role Schema: Engineering & Production Delivery

## Mission
Deliver engineering work with clear ownership, evidence, verification, and handoff quality.

## Primary Lanes
- implementation
- debugging / root-cause investigation
- configuration and release-readiness support
- engineering review when explicitly asked

## Non-Goals
- Do not self-approve risky work as done.
- Do not take over another agent's claimed task unless explicitly handed off.
- Do not treat inaccessible sources as verified.
- Do not present team conventions as Raft-native product features.

## Decision Rights
- May choose implementation details within an assigned task.
- May run local verification relevant to the claimed work.
- Must escalate for credentials, destructive actions, private-channel access, source blockers, or conflicting ownership.

## Rule Imports
- rule-pack.v1.global
- rule-pack.v1.channel.<channel-name>
- rule-pack.v1.role.engineering

## Output Contract
- presentation_contract_ref: presentation.v1.default-reporting
- report_shape:
  - progress-update during work
  - final-handoff at completion or review handoff
- expression_delta: Engineering updates include changed files, commands/tests, evidence, risk, and next owner.

## Work Intake
- claimable_task_types:
  - implementation
  - bugfix
  - technical investigation
  - configuration artifact drafting
- claim_precondition: Claim top-level task/message before running tools or editing files.
- handoff_targets:
  - coordinator for integration
  - reviewer for release evidence
  - human owner for approval

## Thread Policy
- Reply in the same thread when the incoming target is a thread.
- For top-level tasks, claim first, then post progress in the task/message thread.
- Do not model deep decomposition as nested threads; use sibling tasks, phase labels, or a new top-level coordination task.

## Agent Reminder Policy
- Use Raft reminders for agent-owned future follow-up when waiting on source access, delayed human input, weekly self-review, stale task sweep, or source follow-up.
- Reminder must have an owner, anchor message/thread, trigger time or cadence, and completion criteria.
- Reminder policy is team-convention; the Raft reminder capability itself is raft-docs-verified.

## MEMORY Update Trigger
- Durable correction from human/coordinator.
- New or changed rule pack.
- Recurring failure pattern.
- Important completed work, decision, or source/evidence artifact.
```

**Step 4：加入工作面。** 按 §11 的 membership 矩阵 给每个 channel 或 surface 打标签，先写清注意力范围，再让 agent 加入或读取。

| Surface | Membership | Reason |
| --- | --- | --- |
| #daily | join | default team coordination |
| #project-engineering | join | primary work lane |
| #research | on-demand | read only when technical source work requires it |
| private customer channel | no-access unless human-granted | access boundary |
| Joint Channel with partner server | conditional | cross-server collaboration only; task commitment must live elsewhere |

**Step 5：跑 minimal dry run。** 全部通过后，这个 agent 才算可运行。失败不等于 agent 不可用，通常只是配置包还缺字段、seed 和 sidecar 混写，或矩阵没有跟实际 membership 对齐。

| Check | What passes |
| --- | --- |
| `verify.profile-runtime-membership` | 通过 [`config/verification-hooks.v1.md`](./config/verification-hooks.v1.md) 当前版本定义的 canonical acceptance criteria；本表不复制字段级 pass scope |
| `verify.mention-routing` | human 能 @mention agent；agent 能判断 act、defer 或 stay silent |
| `verify.claim-conflict` | agent 只 claim 允许的任务类型，不复制另一个 owner 的工作 |
| `verify.thread-update` | progress 进入 task/message thread，不把深层拆解写成 nested thread |
| `verify.handoff-review` | final handoff 含 canonical schema：goal, current state, changes or evidence, verification, risks or open items, next owner or decision needed |
| `verify.memory-update` | durable feedback 更新 agent 自己的 MEMORY，而不是只改外部文档 |
| `verify.seed-sidecar-split` | governance metadata 留在 sidecar / inventory，copyable seed 只含运行时内容 |
| `verify.feature-coverage` | 本例实际使用的 Raft feature 已在 §17.3 标 used、conditional 或 out-of-scope |

完成这五步后，配置者得到的不是一个角色名，而是一个能被路由、能认领、能交接、能审查、能长期修正的团队成员。
---

## 19. References / 参考来源
本文依据的全部来源；逐能力的"用法/处理"见 §17.3 覆盖矩阵。

**1. Raft 官方文档（docs.raft.build）**
- Server：https://docs.raft.build/features/server.md · https://docs.raft.build/features/server/computers.md · https://docs.raft.build/features/server/members.md · https://docs.raft.build/features/server/management.md
- Agents：https://docs.raft.build/features/agents.md · https://docs.raft.build/features/agents/runtime.md · https://docs.raft.build/features/agents/external.md · https://docs.raft.build/features/agents/workspace.md · https://docs.raft.build/features/agents/lifecycle.md · https://docs.raft.build/features/agents/reminders.md · https://docs.raft.build/features/agents/troubleshooting.md
- Messaging：https://docs.raft.build/features/messaging/channels.md · https://docs.raft.build/features/messaging/messages.md · https://docs.raft.build/features/messaging/threads.md · https://docs.raft.build/features/messaging/dms.md · https://docs.raft.build/features/messaging/joint-channels.md · https://docs.raft.build/features/messaging/activity.md
- Collaboration：https://docs.raft.build/features/collaboration/tasks.md · https://docs.raft.build/features/collaboration/files.md
- Apps / Developers：https://docs.raft.build/features/apps.md · https://docs.raft.build/features/apps/login-with-raft.md · https://docs.raft.build/developers/login-with-raft.md

**2. AX / 文章来源（经 `/read`(defuddle.md) 全文获取）**
- 文章1《Is Having Agents in the Room Meant to Be Chaotic?》 @zty0826 — https://x.com/zty0826/status/2059248164717424667（§5 注意力治理诸纪律——inbox 按需拉取、freshness-hold 草稿处理、silence——的公开说明出处；读者可直接查阅原文核对其机制）
- 文章2《Agents Need Names》 @xiaoxxchan — https://x.com/xiaoxxchan/status/2060347471486964208
- 文章3《多 Agent 的本质不是分工，而是注意力治理》 @ZeroZ_JQ — https://x.com/ZeroZ_JQ/status/2059842898125095363

# ai related docs of my taste

## skills

### Development

- [agent-config-setup](./skills/development/agent-config-setup/SKILL.md): 用于从内置模板初始化项目级 Agent 配置（`AGENTS.md`、`CLAUDE.md`、`docs/index.md`）；与现有文件冲突时需逐一确认后才覆盖。
- [git-commit](./skills/development/git-commit/SKILL.md): 用于编排完整的本地 Git commit 流程，组合 message 与 identity 检查；本地缺少显式 email 时可只读选择本机 GitHub 账号并查询其 public email，统一确认后执行一次提交并验证实际结果；不切换账号、不自动暂存或 push。
- [git-commit-message](./skills/development/git-commit-message/SKILL.md): 用于只读生成或校验 commit message；生成和变更准确性检查基于暂存区，纯规则校验可在暂存区为空时执行，不创建 commit。
- [git-identity-check](./skills/development/git-identity-check/SKILL.md): 用于只读解析当前仓库实际生效的 Git author/committer identity；本地缺少显式 email 时可选择本机 GitHub 账号并查询其 public email 作为进程级 fallback，同时检查必要字段和仓库约束，不修改配置、认证状态或执行提交。

### Daily

- [food-calorie](./skills/daily/food-calorie/SKILL.md): 用于从食物图片或文字估算份量和热量，在当前对话中按日期与餐次记录、累计、查询或纠正饮食，并按需生成兼容旧 JSON 的每日汇总长图。

## docs

- [Claude Code 项目文件结构最佳实践](./docs/project-structure-best-practice.md)
- [Agent Org Structure](./docs/agent-org-structure/v5/design.md): 在 Raft 中组织、配置、维护一支人–AI 协作 agent 团队的架构设计；目录见 [`agent-org-structure/`](./docs/agent-org-structure/README.md)，配套规则与角色配置资产见 [`v5/config/`](./docs/agent-org-structure/v5/config/INDEX.md)。
- [npm Release Pipeline — From Zero To Shipped](./docs/npm-release-from-zero-to-shipped.md): npm 包从零到 OIDC 自动发版的端到端 runbook。`LoTwT/design-system` V0.0.1 / V0.0.2 是 worked example。

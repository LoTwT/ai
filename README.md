# ai related docs of my taste

## skills

### Development

- [agent-config-setup](./skills/development/agent-config-setup/SKILL.md): 用于从内置模板初始化项目级 Agent 配置（`AGENTS.md`、`CLAUDE.md`、`docs/index.md`）；与现有文件冲突时需逐一确认后才覆盖。
- [git-commit](./skills/development/git-commit/SKILL.md): 用于编排完整的本地 Git commit 流程，组合 message 与 identity 检查，统一确认后执行一次提交并验证实际结果；不自动暂存或 push。
- [git-commit-message](./skills/development/git-commit-message/SKILL.md): 用于只读生成或校验 commit message；生成和变更准确性检查基于暂存区，纯规则校验可在暂存区为空时执行，不创建 commit。
- [git-identity-check](./skills/development/git-identity-check/SKILL.md): 用于只读解析当前仓库实际生效的 Git author/committer identity，检查必要字段和仓库约束，不修改配置或执行提交。

### Daily

- [food-calorie-estimator](./skills/daily/food-calorie-estimator/SKILL.md): 用于从食物照片中系统化估算食物重量和热量，侧重食物识别、份量推断、热量计算和置信度判断。
- [food-calorie-tracker](./skills/daily/food-calorie-tracker/SKILL.md): 用于记录每日饮食，按餐次累计食物和热量，并生成带明细表格与食物照片的汇总长图。

## docs

- [Claude Code 项目文件结构最佳实践](./docs/project-structure-best-practice.md)
- [Agent Org Structure](./docs/agent-org-structure/v5/design.md): 在 Raft 中组织、配置、维护一支人–AI 协作 agent 团队的架构设计；目录见 [`agent-org-structure/`](./docs/agent-org-structure/README.md)，配套规则与角色配置资产见 [`v5/config/`](./docs/agent-org-structure/v5/config/INDEX.md)。
- [npm Release Pipeline — From Zero To Shipped](./docs/npm-release-from-zero-to-shipped.md): npm 包从零到 OIDC 自动发版的端到端 runbook。`LoTwT/design-system` V0.0.1 / V0.0.2 是 worked example。

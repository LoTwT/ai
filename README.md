# ai related docs of my taste

## skills

### Development

- [agent-config-setup](./skills/development/agent-config-setup/SKILL.md): 用于从内置模板初始化项目级 Agent 配置（`AGENTS.md`、`CLAUDE.md`、`docs/index.md`）；与现有文件冲突时需逐一确认后才覆盖。

### Git Workflow

Seven independently usable skills cover local preparation, commits, branch publication, PR metadata, content review, merging, and task cleanup. Account roles and repository policies come from applicable user/project instructions; the skills contain no personal account matrix. Each skill owns its references and can be installed independently.

| Skill | Responsibility |
|---|---|
| [git-workspace](./skills/git-workflow/git-workspace/SKILL.md) | Inspect repository/account state; configure account-use policy; prepare branches/worktrees; synchronize, restack, and recover local operations |
| [git-commit](./skills/git-workflow/git-commit/SKILL.md) | Exact local commits, message-only work, and author/committer-only checks |
| [git-push](./skills/git-workflow/git-push/SKILL.md) | Publish exact commits to remote branches with verified transport identity and update conditions |
| [git-pr-submit](./skills/git-workflow/git-pr-submit/SKILL.md) | Create PRs from published heads and maintain PR/stack metadata |
| [git-review](./skills/git-workflow/git-review/SKILL.md) | Review change content; publish review results only within explicit authorization |
| [git-pr-merge](./skills/git-workflow/git-pr-merge/SKILL.md) | Check authoritative merge gates and verify immediate, queued, or asynchronous merge results |
| [git-cleanup](./skills/git-workflow/git-cleanup/SKILL.md) | Inventory and remove authorized local/remote task resources |

The calling agent composes operations only when the request needs them. Existing authorization persists within the same category, targets, and effects; dependent writes wait for verified prerequisites. There is no mandatory setup/router skill, shared runtime database, or cross-skill file dependency.

See the [workflow design](./docs/git-workflow.md) for ownership and handoff rules.

#### Review record

The [implementation and ablation review](./docs/git-workflow-review.md) records previous development checks and their limitations. The test harness and raw experiment artifacts are no longer included in this repository.

#### Development and publication

Repository source is developed separately from installed skills. Do not replace, symlink, or overwrite the user's installed Git skills during development. Installation/replacement is a separate requested publication step after review, using a fixed verified source snapshot. These packages have no mandatory sibling-file dependencies; a combined workflow still needs the relevant capabilities available.

### Daily

- [food-calorie](./skills/daily/food-calorie/SKILL.md): 用于从食物图片或文字估算份量和热量，在当前对话中按日期与餐次记录、累计、查询或纠正饮食，并按需生成兼容旧 JSON 的每日汇总长图。

## docs

- [Claude Code 项目文件结构最佳实践](./docs/project-structure-best-practice.md)
- [Agent Org Structure](./docs/agent-org-structure/v5/design.md): 在 Raft 中组织、配置、维护一支人–AI 协作 agent 团队的架构设计；目录见 [`agent-org-structure/`](./docs/agent-org-structure/README.md)，配套规则与角色配置资产见 [`v5/config/`](./docs/agent-org-structure/v5/config/INDEX.md)。
- [npm Release Pipeline — From Zero To Shipped](./docs/npm-release-from-zero-to-shipped.md): npm 包从零到 OIDC 自动发版的端到端 runbook。`LoTwT/design-system` V0.0.1 / V0.0.2 是 worked example。

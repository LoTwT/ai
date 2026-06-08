# ai related docs of my taste

## skills

- [git-commit](./skills/git-commit/SKILL.md): 用于分析 Git 暂存区变更，生成符合 commitlint（Angular）规范的英文 commit message，并在用户确认后安全执行 `git commit`。
- [food-calorie-tracker](./skills/food-calorie-tracker/SKILL.md): 食物热量相关的唯一入口。通过食物照片或描述记录每日饮食（log/edit/summary 三意图）、估算热量、持久化保存，并生成带明细表格与食物照片的汇总长图。估算方法已内化到 [`references/estimation.md`](./skills/food-calorie-tracker/references/estimation.md)。

## docs

- [Claude Code 项目文件结构最佳实践](./docs/project-structure-best-practice.md)
- [Agent Org Structure (v3)](./docs/agent-org-structure/v3-agent-org.md): 组织级 agent 团队的规范文档，4 角色 flat（PM / UX / TL / QA）+ shared operating rules + fresh deployment SOP；v2（6 角色，含 Chief / ChiefDesigner leadership 层）历史归档于同目录下的 `v2-agent-org.md`，v1 归档于 `v1-agent-team.md`。
- [npm Release Pipeline — From Zero To Shipped](./docs/npm-release-from-zero-to-shipped.md): npm 包从零到 OIDC 自动发版的端到端 runbook。`LoTwT/design-system` V0.0.1 / V0.0.2 是 worked example。

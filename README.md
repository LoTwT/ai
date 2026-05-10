# ai related docs of my taste

## skills

- [git-commit](./skills/git-commit/SKILL.md): 用于分析 Git 暂存区变更，生成符合 commitlint（Angular）规范的英文 commit message，并在用户确认后安全执行 `git commit`。
- [food-calorie-estimator](./skills/food-calorie-estimator/SKILL.md): 用于从食物照片中系统化估算食物重量和热量，侧重食物识别、份量推断、热量计算和置信度判断。
- [food-calorie-tracker](./skills/food-calorie-tracker/SKILL.md): 用于记录每日饮食，按餐次累计食物和热量，并生成带明细表格与食物照片的汇总长图。

## docs

- [Claude Code 项目文件结构最佳实践](./docs/project-structure-best-practice.md)
- [Agent Team Roster](./docs/agent-team.md): 组件开发中的 agent team 配置参考，包含每个角色的职责边界、默认发言策略与推荐模型。
- [npm Release Pipeline — From Zero To Shipped](./docs/npm-release-from-zero-to-shipped.md): npm 包从零仓库到 OIDC 自动发版的端到端 runbook，覆盖 repo 骨架、release scripts、release.yml workflow、GitHub repo 配置（Environment + Tag ruleset）、npm Trusted Publisher 绑定、首发 manual bootstrap 与后续 OIDC validation，以及完整的 per-step rollback table。`LoTwT/design-system` V0.0.1 / V0.0.2 是 worked example。

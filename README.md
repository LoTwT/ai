# ai related docs of my taste

## skills

### Development

- [agent-config-setup](./skills/development/agent-config-setup/SKILL.md): 用于从内置模板初始化项目级 Agent 配置（`AGENTS.md`、`CLAUDE.md`、`docs/index.md`）；与现有文件冲突时需逐一确认后才覆盖。

### Git Workflow

一个按授权边界拆分的 Git/GitHub 工作流 skill 家族,覆盖"本地提交 → push/建 PR → 就绪度 → merge → 本地清理"完整生命周期。所有远端写操作均需当前请求明确授权;账号矩阵、合并策略、Approve 红线等策略由用户 `AGENTS.md`(`~/.agents/AGENTS.md` 或项目级)提供,skill 本身不内嵌任何账号信息。家族各 skill 通过相对路径共享资源与契约,**必须作为整体安装**(`npx skills add <repo>` 全量安装或 `--skill '*'`);单独安装任一 skill 会使跨 skill 引用失效。

- [git-workflow-setup](./skills/git-workflow/git-workflow-setup/SKILL.md): 家族资源宿主与初始化;从内置模板生成/更新用户 `AGENTS.md` 策略层(账号矩阵、强制规则、授权边界、skill 路由表),并承载共享的只读预检核心与远程写执行核心,供 git-pr-create / git-pr-merge 引用。
- [git-identity-check](./skills/git-workflow/git-identity-check/SKILL.md): 只读解析当前请求实际生效的 Git author/committer 身份;支持请求/指令指定的一次性身份、有效 Git 状态与本地 GitHub 账号 public-email 兜底;校验显式来源,不修改配置、不提交、不推断 push actor。
- [git-commit-message](./skills/git-workflow/git-commit-message/SKILL.md): 只读生成或校验 commit message;生成与变更准确性检查基于暂存区,规则优先级为当前请求 > 项目指令 > commitlint > 历史风格 > Conventional Commits;负责 agent 执行来源(Agent-Tool/Model/Effort)trailer 的合并与校验。
- [git-commit](./skills/git-workflow/git-commit/SKILL.md): 本地提交的唯一写层;编排身份解析与 message 生成,精确整文件 staging,展示完整预览并要求显式确认后执行恰好一次提交,验证实际 commit 元数据;需要时产出 `git-workflow-handoff-v1` 交接凭据。
- [git-pr-create](./skills/git-workflow/git-pr-create/SKILL.md): 远程写层之一;在拓扑/actor/权限/授权预检后 push 已授权分支并创建、更新 PR 或发表评论(create/update/push-only/comment 子模式),消费 `git-workflow-handoff-v1` 与 `git-workflow-requirements-v1` 契约;不做 merge 与远端删除。
- [git-pr-review](./skills/git-workflow/git-pr-review/SKILL.md): 只读就绪度核对;对冻结的 PR head 读取平台门禁证据(required checks、人类 Approve 覆盖、未解决对话、auto-merge/队列状态)并与 `AGENTS.md` 策略比对,输出 ready/缺项报告;不做实质性代码 review(归 check skill),不提交任何写操作。
- [git-pr-merge](./skills/git-workflow/git-pr-merge/SKILL.md): 远程写层之二;按 `AGENTS.md` 合并策略执行恰好一次 merge(方法强制、latest-base 门禁、冻结消息/归属策略)并验证结果提交;merge bundle 明确覆盖时以条件 CAS 删除该 PR 的精确远端 head 分支;本地清理归 git-cleanup。
- [git-cleanup](./skills/git-workflow/git-cleanup/SKILL.md): 本地收尾;盘点 worktree 与分支,按 `AGENTS.md` 清理策略自动执行可恢复安全清单并报告,其余逐项列清单等确认;永不删除远端分支(归 git-pr-merge)、fork 或仓库。

#### Verification

运行 `python3 -B -m unittest discover -s tests -v`（Python 标准库、Git、Bash，无第三方 Python 依赖）。[回归测试](./tests/test_git_workflow_skills.py) 在临时仓库和隔离 HOME 中验证执行示例、路径传输及 Git 反例，并检查清理/配置更新的文本契约；不等同于完整 Agent 或 GitHub 端到端验证。

#### Skill publication

Repo source 是规范版本；开发调整期间 live skill 保持发布版。仅从已审查、验证并固定的 commit/tree snapshot 发布。所有通过 contract marker 相连的 skill 目录必须作为一个依赖闭包构建和验证：在隔离 release root 中核对 marker、文件清单与逐字节 hash 后，原子切换整个闭包；若部署机制不能原子切换，则先停止读取方再完成全部替换，绝不暴露新旧混用状态。记录已发布 snapshot SHA，不得从仍在变化的 worktree 直接发布。

### Daily

- [food-calorie](./skills/daily/food-calorie/SKILL.md): 用于从食物图片或文字估算份量和热量，在当前对话中按日期与餐次记录、累计、查询或纠正饮食，并按需生成兼容旧 JSON 的每日汇总长图。

## docs

- [Claude Code 项目文件结构最佳实践](./docs/project-structure-best-practice.md)
- [Agent Org Structure](./docs/agent-org-structure/v5/design.md): 在 Raft 中组织、配置、维护一支人–AI 协作 agent 团队的架构设计；目录见 [`agent-org-structure/`](./docs/agent-org-structure/README.md)，配套规则与角色配置资产见 [`v5/config/`](./docs/agent-org-structure/v5/config/INDEX.md)。
- [npm Release Pipeline — From Zero To Shipped](./docs/npm-release-from-zero-to-shipped.md): npm 包从零到 OIDC 自动发版的端到端 runbook。`LoTwT/design-system` V0.0.1 / V0.0.2 是 worked example。

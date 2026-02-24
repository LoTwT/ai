# Claude Code 项目文件结构最佳实践

## 完整目录结构

```
your-project/
├── CLAUDE.md                        # 项目主记忆文件（根目录，团队共享）
├── CLAUDE.local.md                  # 个人本地覆盖（加入 .gitignore）
│
├── .claude/
│   ├── settings.json                # 项目级权限配置（提交版本控制）
│   ├── settings.local.json          # 个人权限覆盖（加入 .gitignore）
│   ├── .mcp.json                    # MCP 服务器配置
│   │
│   ├── commands/                    # 自定义斜杠命令
│   │   ├── review-pr.md
│   │   ├── create-prd.md
│   │   └── generate-tasks.md
│   │
│   ├── rules/                       # 按路径作用的模块化规则
│   │   ├── frontend.md              # frontmatter: files: ["src/frontend/**"]
│   │   ├── backend.md               # frontmatter: files: ["src/api/**"]
│   │   └── tests.md
│   │
│   ├── agents/                      # 专用子代理
│   │   ├── code-reviewer.md
│   │   └── security-auditor.md
│   │
│   ├── skills/                      # 可复用技能包
│   │   └── tdd-workflow/
│   │       └── SKILL.md
│   │
│   └── hooks/                       # 生命周期钩子脚本
│       ├── PreToolUse/
│       └── PostToolUse/
│
└── docs/
    ├── index.md                     # 整个 docs 的导航入口
    ├── architecture.md              # 系统架构、模块划分、技术选型
    ├── conventions.md               # 编码规范、命名约定、Git 工作流
    ├── setup.md                     # 环境搭建、常用命令
    ├── packages/                    # Monorepo 各包说明（按需创建）
    │   └── app-web.md
    └── plans/                       # 计划文档（Plan mode 产出落地）
        └── 2026-q1.md
```

---

## .claude 目录

### 各子目录和文件的作用

| 路径 | 作用 |
|---|---|
| `settings.json` | 项目级工具权限配置，团队共享 |
| `settings.local.json` | 个人权限覆盖，不提交版本控制 |
| `.mcp.json` | MCP 外部工具集成（数据库、GitHub 等） |
| `commands/` | 自定义斜杠命令，每个 `.md` 对应一个 `/命令名` |
| `rules/` | 按文件路径匹配的差异化规则，通过 frontmatter 的 `files` 字段指定作用范围 |
| `agents/` | 专用子代理，独立上下文窗口，适合代码审查、安全审计等专项任务 |
| `skills/` | 可复用技能包，每个技能是含 `SKILL.md` 的子文件夹，Claude 按需自动调用 |
| `hooks/` | 生命周期自动化脚本，支持 `PreToolUse`、`PostToolUse`、`SessionStart`、`SessionEnd` |

### CLAUDE.md 的位置

`CLAUDE.md` 有两个合法位置：

- `./CLAUDE.md`（项目根目录）— **推荐**，可见性最好，团队友好
- `./.claude/CLAUDE.md`（.claude 目录内）— 功能等效，适合希望集中管理配置的场景

两个位置同时存在时，根目录优先。

### 版本控制策略

**提交（团队共享）：**
- `CLAUDE.md`
- `.claude/settings.json`
- `.claude/commands/`、`rules/`、`agents/`、`skills/`、`hooks/`
- `.claude/.mcp.json`

**加入 `.gitignore`（个人私有）：**
```
CLAUDE.local.md
.claude/settings.local.json
```

---

## CLAUDE.md 的写法原则

### 核心原则：精简优先

CLAUDE.md 是项目上下文，不是 AI 使用手册。Claude 能稳定遵循的指令上限约 150～200 条，建议**控制在 150 行以内**。

CLAUDE.md 应该回答三个问题：

- **WHAT**：项目是什么，技术栈，目录结构地图
- **WHY**：各模块的用途和目的
- **HOW**：如何构建、测试、提交，用什么工具

### 不应该放进 CLAUDE.md 的内容

- 关于如何配置 Claude Code 本身的元说明
- Claude 通过读代码就能推断的信息
- 详细的技术文档（用 `@` 引用代替内联）

### 渐进式披露（Progressive Disclosure）

**最重要的上下文管理策略**：CLAUDE.md 只告诉 Claude 去哪里找信息，而不是直接塞给它所有信息。

```markdown
## 文档
需要了解项目细节时，先查阅 @docs/index.md。
```

这样只有当 Claude 真正需要某块知识时，才会去读对应文件，避免每次加载所有上下文消耗 token。

### 示例结构

```markdown
# 项目名称
一句话描述。

## 技术栈
Next.js 14 + TypeScript + Prisma + PostgreSQL

## 目录结构
- `src/api/` — REST 接口
- `src/components/` — React 组件
- `src/lib/` — 工具函数

## 常用命令
- `npm run dev` — 启动开发服务器
- `npm run test` — 运行测试
- `npm run lint` — ESLint 检查

## 编码规范
- TypeScript strict 模式，禁止 any
- 使用具名导出，不用默认导出

## 文档
需要了解项目细节时，先查阅 @docs/index.md。
```

---

## docs 目录

### 设计原则

**按内容语义组织，不按受众划分。** 不要用"给谁看"来命名目录（如 `agent-docs/`），而是用内容本身命名（`architecture`、`conventions`、`plans`）。文档就是文档，人和 Claude 都读同一份。

**扁平优于深层嵌套。** 单人或小型项目文件数量有限，没有必要搞三四层目录。

**文件名使用小写。** `docs/` 下遵循常规文件命名习惯——小写、连字符分隔（如 `api-conventions.md`）。大写命名（`CLAUDE.md`、`README.md`）专属于工具按文件名自动识别加载的特殊文件。

### docs/index.md 的作用

`docs/index.md` 是整个文档目录的导航入口，CLAUDE.md 只需引用这一个文件：

```markdown
# 文档索引

- 系统架构：@docs/architecture.md
- 编码规范：@docs/conventions.md
- 环境搭建：@docs/setup.md
- 各包说明：@docs/packages/
- 当前计划：@docs/plans/2026-q1.md
```

好处：新增文档时只更新 `index.md`，不需要改动 `CLAUDE.md`；Claude 先读索引再按需读具体文件，真正做到按需加载。

### 演进策略

从最小集合开始，只建现在真正需要的文件：

**第一阶段**（项目启动）：
```
docs/
├── index.md
├── architecture.md
└── conventions.md
```

**第二阶段**（有计划要执行时）：加 `plans/`

**第三阶段**（某个包复杂到需要说明时）：加 `packages/`

不要预先建空目录或空文件。

### Plan mode 的文件工作流

计划不应只停留在对话里，应落地成文件：

1. 进入 Plan mode → 生成计划
2. 让 Claude 将计划写入 `docs/plans/feature-xxx.md`
3. `docs/index.md` 中更新引用
4. 新会话开始时 Claude 可直接读取上次计划继续执行
5. 任务完成后归档或删除，避免陈旧上下文干扰

### 判断是否需要新建文档的原则

问自己：**"如果三个月没碰这个项目，这个文档能帮我或 Claude 快速恢复上下文吗？"** 答案肯定才建，否则不建。

---

## 文件存放决策速查

| 文件类型 | 存放位置 | 备注 |
|---|---|---|
| 项目主配置 | `./CLAUDE.md` | 根目录，可见性最好 |
| 个人偏好覆盖 | `./CLAUDE.local.md` | gitignore |
| 模块专属规则 | `.claude/rules/*.md` | 按路径按需激活 |
| 可复用工作流命令 | `.claude/commands/*.md` | 斜杠命令触发 |
| 架构 / 规范文档 | `docs/` | 人和 Claude 都读 |
| 计划文档 | `docs/plans/` | 有时效性，单独管理便于清理 |
| 各包专属说明 | `docs/packages/` | 按需创建，不预占位 |
| 项目权限配置 | `.claude/settings.json` | 团队共享权限基线 |
| 个人权限覆盖 | `.claude/settings.local.json` | gitignore |

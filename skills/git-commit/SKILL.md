---
name: git-commit
description: 分析 git 暂存区变更，优先读取仓库里的 commitlint 配置并按项目规则生成 commit message；如果仓库没有相关配置，则回退到内置的 commitlint（Angular）规范。用户说"帮我提交"、"生成 commit"、"写个 commit message"、"确认提交"、"提交这个 message"、"提交：<message>"时触发；如果上一轮已经展示唯一候选 message，任何明确表示同意提交的短回复也应继续执行。
---

# Git Commit Skill

自动分析暂存区变更 → 预检查仓库 commitlint 规则 → 生成符合规则的 message → 等待用户确认 → 安全执行 commit。

---

## 执行流程

### Step 1：预检查 commitlint 规则

优先在当前仓库中查找并读取以下配置来源：

```bash
commitlint.config.js
commitlint.config.cjs
commitlint.config.mjs
commitlint.config.ts
.commitlintrc
.commitlintrc.json
.commitlintrc.yml
.commitlintrc.yaml
.commitlintrc.js
.commitlintrc.cjs
package.json
```

要求：
- 如果找到配置文件，先按项目配置推断并记录关键规则，再进入后续步骤。
- 重点关注 `type-enum`、`scope-case`、`scope-enum`、`subject-case`、`header-max-length`、`header-case`、`subject-max-length` 等会直接影响 message 生成的规则。
- 如果配置通过 `extends`、`parserPreset` 或自定义代码间接定义规则，尽量读取可见配置得出结论；无法可靠解析时，明确说明不确定部分，并仅对无法确定的项回退到内置默认规范。
- 如果仓库里没有相关配置文件，则使用本 skill 的内置 commitlint（Angular）规范作为默认规则。

---

### Step 2：检查暂存区

```bash
git diff --cached --stat
git diff --cached
```

若暂存区为空 → 提示用户先 `git add`，终止流程。

---

### Step 3：分析变更，生成 commit message

**格式：**
```
<type>(<scope>): <subject>
```

优先按 Step 1 中解析到的项目规则生成；只有在仓库没有相关配置，或某条规则无法可靠解析时，才对对应部分使用以下内置默认规范。

**type 对照表：**

| type | 场景 |
|------|------|
| `feat` | 新功能 |
| `fix` | Bug 修复 |
| `docs` | 仅文档 |
| `style` | 格式/空白（不影响逻辑） |
| `refactor` | 重构（非 feat/fix） |
| `perf` | 性能优化 |
| `test` | 测试代码 |
| `chore` | 构建/依赖/工具 |
| `ci` | CI/CD 配置 |
| `revert` | 回滚提交 |
| `build` | 构建系统 |

**scope：** 从变更文件路径推断模块/目录名，小写 kebab-case；跨多个无关模块时省略。

**subject：**
- 祈使句动词开头（小写开头、不加句号）
- 始终使用英文
- ≤ 50 字符

### Step 4：展示并等待确认

```
📝 Commit Message：

feat(auth): add JWT refresh token support

回复是即可提交，如需修改则发新的 message 或修改意见。
```

规则：
- 如果最近一条 assistant 消息刚展示了唯一候选 commit message，那么任何明确表示同意提交的短回复都视为确认并允许执行 commit，例如 `确认提交`、`提交`、`确认`、`yes`、`y`、`ok`、`go`、`是`、`好`。
- 如果用户回复 `提交：<message>`，先按 Step 1 得到的项目规则校验；仓库没有相关配置时，再按内置 `<type>(<scope>): <subject>` 格式、英文要求和 `subject` 长度限制校验。只有校验通过后，才使用它执行 commit。
- 如果用户直接给出最终 commit message，也先按同样规则校验；校验通过后才允许执行 commit。
- 只有在存在唯一候选 message 或用户明确提供最终 message 时，才允许执行 commit；如果上下文不明确，先澄清，不要提交。

---

### Step 5：执行 commit

```bash
git commit --file - <<'__COMMIT_MESSAGE__'
<type>(<scope>): <subject>
__COMMIT_MESSAGE__
```

要求：
- 如果最终 message 来自用户输入而不是上一轮候选 message，执行前必须按 Step 1 得到的项目规则重新校验；仓库没有相关配置时，再按内置格式、英文要求和 `subject` 长度校验。不符合时不要运行 `git commit`，而是返回修正建议或要求用户修改。
- 使用带引号的 heredoc，避免 shell 插值。
- 选择一个不会出现在 message 里的 heredoc 分隔符。
- 只有在明确拿到最终 message 后才运行这一步。

---

### Step 6：输出结果

若 `git commit` 退出码为 0，再输出：

```
✅ 已提交

commit a1b2c3d
feat(auth): add JWT refresh token support
```

若 `git commit` 失败：

```
❌ 提交失败

<git commit 的 stderr / 关键信息摘要>
```

失败时不要输出“已提交”。优先保留真实失败原因，例如 pre-commit hook、commitlint、merge state、空暂存区等。

---

## 约束

- ❌ 不自动执行 `git add`
- ❌ 不在用户确认前 commit；只有存在唯一候选 message 或用户提供最终 message 时才可执行
- ❌ 不执行 `git push`（由用户手动控制）
- ✅ 若仓库存在 commitlint 配置，优先遵循项目规则；仅在缺失配置或无法可靠解析某条规则时回退到内置默认规范
- ✅ 执行 commit 时使用带引号的 heredoc，不要把自由文本直接拼进 shell 命令

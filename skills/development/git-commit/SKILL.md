---
name: git-commit
description: "Analyze git staged changes, prioritize reading the repo's commitlint config and generate commit messages following project rules; fall back to built-in commitlint (Angular) conventions if the repo has no relevant config. Triggered when the user says 'help me commit', 'generate a commit', 'write a commit message', 'confirm commit', 'commit this message', 'commit: <message>'; if the previous turn already displayed a single candidate message, any short affirmative reply should also continue execution."
---

# Git Commit Skill

Automatically analyze staged changes → pre-check repo commitlint rules → generate a compliant message → wait for user confirmation → safely execute commit.

---

## Workflow

### Step 1: Pre-check commitlint rules

Search for and read the following config sources in the current repo first:

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

Requirements:
- If a config file is found, infer and record the key rules from the project config before proceeding to subsequent steps.
- Focus on rules that directly affect message generation: `type-enum`, `scope-case`, `scope-enum`, `subject-case`, `header-max-length`, `header-case`, `subject-max-length`, etc.
- If the config defines rules indirectly through `extends`, `parserPreset`, or custom code, try to read the visible config and draw conclusions; when reliable parsing is not possible, explicitly state the uncertain parts and fall back to the built-in default conventions only for those undetermined items.
- If the repo has no relevant config files, use this skill's built-in commitlint (Angular) conventions as the default rules.

---

### Step 2: Check the staging area

```bash
git diff --cached --stat
git diff --cached
```

If the staging area is empty → prompt the user to `git add` first and terminate the flow.

---

### Step 3: Analyze changes and generate commit message

**Format:**
```
<type>(<scope>): <subject>
```

Prioritize generating based on the project rules parsed in Step 1; only use the following built-in default conventions for corresponding parts when the repo has no relevant config or a specific rule cannot be reliably parsed.

**type reference table:**

| type | scenario |
|------|----------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `style` | Formatting/whitespace (no logic change) |
| `refactor` | Refactoring (neither feat nor fix) |
| `perf` | Performance improvement |
| `test` | Test code |
| `chore` | Build/dependencies/tooling |
| `ci` | CI/CD configuration |
| `revert` | Revert a commit |
| `build` | Build system |

**scope:** Infer module/directory name from changed file paths, lowercase kebab-case; omit when changes span multiple unrelated modules.

**subject:**
- Start with an imperative verb (lowercase, no trailing period)
- Always use English
- ≤ 50 characters

### Step 4: Display and wait for confirmation

```
📝 Commit Message:

feat(auth): add JWT refresh token support

Reply yes to commit, or send a new message or revision to modify.
```

Rules:
- If the most recent assistant message just displayed a single candidate commit message, any short affirmative reply is treated as confirmation and allows commit execution, e.g. `confirm commit`, `commit`, `confirm`, `yes`, `y`, `ok`, `go`.
- If the user replies with `commit: <message>`, first validate against the project rules from Step 1; if the repo has no relevant config, validate against the built-in `<type>(<scope>): <subject>` format, English requirement, and `subject` length limit. Only use it to execute the commit after validation passes.
- If the user provides a final commit message directly, validate it against the same rules first; only allow commit execution after validation passes.
- Only allow commit execution when there is a single candidate message or the user has explicitly provided a final message; if the context is ambiguous, clarify first — do not commit.

---

### Step 5: Execute commit

```bash
git commit --file - <<'__COMMIT_MESSAGE__'
<type>(<scope>): <subject>
__COMMIT_MESSAGE__
```

Requirements:
- If the final message comes from user input rather than the previous turn's candidate message, it must be re-validated against the project rules from Step 1 before execution; if the repo has no relevant config, validate against the built-in format, English requirement, and `subject` length limit. If it does not comply, do not run `git commit` — return correction suggestions or ask the user to modify instead.
- Use a quoted heredoc to avoid shell interpolation.
- Choose a heredoc delimiter that will not appear in the message.
- Only run this step after the final message has been clearly determined.

---

### Step 6: Output result

If `git commit` exits with code 0, output:

```
✅ Committed

commit a1b2c3d
feat(auth): add JWT refresh token support
```

If `git commit` fails:

```
❌ Commit failed

<git commit stderr / key error summary>
```

Do not output "Committed" on failure. Preserve the real failure reason, such as pre-commit hook, commitlint, merge state, empty staging area, etc.

---

## Constraints

- ❌ Do not automatically run `git add`
- ❌ Do not commit before user confirmation; only execute when there is a single candidate message or the user provides a final message
- ❌ Do not run `git push` (left to user's manual control)
- ✅ If the repo has a commitlint config, follow project rules first; only fall back to built-in default conventions when config is missing or a specific rule cannot be reliably parsed
- ✅ Use a quoted heredoc when executing commit — do not splice free text directly into shell commands

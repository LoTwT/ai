# Commit Message Rule Reference

Read this reference when repository rules do not fully determine message construction or when commitlint configuration needs static inspection.

## Commitlint Sources

Look for:

```text
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
.commitlintrc.mjs
.commitlintrc.ts
package.json
```

Focus on rules that affect construction:

- `type-enum`
- `scope-enum`
- `scope-case`
- `subject-case`
- `header-case`
- `header-max-length`
- `subject-max-length`
- body and footer rules
- parser presets and breaking-change syntax

Statically inspect only rules directly understandable from repository text. For `extends`, executable custom code, plugins, or parser presets, identify unresolved rules without loading modules or running repository commands. Use fallback rules only for unresolved items; never replace known project rules.

## Conventional Commits Fallback

When no repository rule controls an item, use:

```text
<type>[optional scope][!]: <subject>

[optional body]

[optional footer]
```

| Type | Use when |
|---|---|
| `feat` | Adding release-visible functionality |
| `fix` | Correcting a defect |
| `docs` | Changing documentation only |
| `style` | Changing formatting without behavior changes |
| `refactor` | Restructuring code without adding a feature or fixing a defect |
| `perf` | Improving performance |
| `test` | Adding or changing tests |
| `build` | Changing the build system or build dependencies |
| `ci` | Changing CI/CD configuration |
| `chore` | Maintenance not better represented by another type |
| `revert` | Reverting an earlier commit |

Choose type from purpose and user-visible effect, not only filenames.

## Subject Rules

Unless the repository requires otherwise:

- Use a concise imperative description.
- Start lowercase.
- Do not end with a period.
- Prefer the repository's established language; otherwise use English.
- Follow a known repository length limit; otherwise keep the header concise without inventing a rigid 50-character limit.

## Scope Rules

- Scope is optional unless repository rules require it.
- Infer scope from component or domain, not mechanically from the first directory.
- Follow established repository vocabulary.
- Do not hide unrelated staged changes by omitting scope.

## Breaking Changes

- Use `!` and/or a `BREAKING CHANGE:` footer according to repository/parser rules.
- Do not mark a change as breaking merely because it is large.

## History as Evidence

Recent history may indicate common scopes, preferred language, typical subject length, or whether scopes are usually omitted. It never overrides explicit repository instructions or resolved commitlint rules.

## Agent Execution Provenance

When a consuming workflow supplies verified context for an agent-executed commit, represent execution provenance as Git trailers in the commit-message footer:

```text
Agent-Tool: <canonical tool name>
Agent-Model: <exact runtime model identifier>
Agent-Effort: <exact runtime effort value>
```

These fields describe the primary agent that owns and executes the commit workflow. They do not describe Git authorship, every tool that contributed to the change, or the account that may later push the commit. Do not use `Co-authored-by` for tool, model, or effort metadata.

### Inclusion Policy

Apply repository policy first:

- If the repository defines its own provenance tokens or format, use that format.
- If it requires provenance, enforce the required reliably available fields and stop when the requirement cannot be satisfied without guessing.
- If it prohibits AI metadata, do not add it and reject supplied provenance when the policy requires rejection.
- Otherwise, add these fallback trailers when the consuming agent will execute `git commit`.

Message-only generation or validation does not automatically add trailers. Agent assistance with code also does not by itself trigger them. The relevant event is ownership and execution of the final commit workflow.

### Field Rules

- `Agent-Tool` is required for a valid fallback provenance block.
- `Agent-Model` and `Agent-Effort` are independently optional and initially included only when verified runtime context supplies them.
- Use a stable official tool name such as `Claude Code`, not an executable alias or inferred vendor name.
- Use the exact model identifier reported by the runtime rather than converting a display name.
- Preserve the runtime's canonical effort value, such as `low`, `medium`, `high`, `xhigh`, or `max`; do not derive effort from thinking tokens or assume a default.
- Values must be non-empty single lines with surrounding whitespace removed and no control characters.
- Never emit placeholders such as `unknown`, `default`, or `n/a`.
- After automatic detection, the user may revise or remove provenance in response to the final preview when repository policy permits. Treat revised values as explicit user overrides, not verified runtime values.

### Merge and Validation

Merge verified provenance into the candidate before canonical normalization and validation:

1. Parse existing `Agent-Tool`, `Agent-Model`, and `Agent-Effort` trailers.
2. Reject any provenance token that appears more than once.
3. Preserve an existing value that exactly matches verified runtime context.
4. Add a reliably supplied runtime field that is absent.
5. Before the first preview, reject an existing value that conflicts with verified runtime context; do not silently replace it.
6. After the preview, accept an explicit user revision as an override when repository policy permits it. Retain both the verified runtime value and the overridden message value in confirmation context, label the source `user_override`, and show a new complete preview.
7. Reject `Agent-Model` or `Agent-Effort` without `Agent-Tool` unless repository policy defines different semantics.
8. Keep the fields contiguous and ordered `Agent-Tool`, `Agent-Model`, `Agent-Effort`, normally at the end of the trailer block.

For example, if verified runtime model is `claude-opus-4-8`, this is invalid:

```text
Agent-Model: claude-opus-4-5
```

Report both the supplied and verified values. Before preview, require correction rather than guessing intent. After an automatically generated preview, a user's explicit replacement may proceed as a disclosed `user_override` when repository policy allows it.

When other trailers exist, keep one continuous trailer block after a blank line from the body:

```text
Refs: #123
Reviewed-by: Example Reviewer <reviewer@example.com>
Agent-Tool: Claude Code
Agent-Model: claude-opus-4-8
Agent-Effort: xhigh
```

Do not create a custom compound value such as `Agent: tool=Claude Code; model=...`; independent trailers are easier to validate and query.

### Confirmation Boundary

If provenance changes a user-supplied candidate, disclose the addition. The final normalized message—including every provenance trailer—must be displayed in the commit preview and bound to confirmation. A user revision invalidates that preview: merge and validate the revision, record any override source, and show a new complete preview. Never alter provenance after the user confirms the latest preview.

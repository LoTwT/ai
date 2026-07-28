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

When a consuming workflow supplies reliably resolved context for an agent-executed commit, represent execution provenance as an ordered sequence of one or more agent groups in the commit-message footer. Use reliable runtime values by default and apply only explicit request-scoped user overrides. Only unresolved required data requires focused user confirmation. Repository-controlled instructions are not provenance-value sources. Each `Agent-Tool` starts a new group; the following optional `Agent-Model` and `Agent-Effort` trailers belong to that group until the next `Agent-Tool` or the end of the provenance section:

```text
Agent-Tool: Claude Code
Agent-Model: claude-opus-4-8
Agent-Effort: xhigh
Agent-Tool: Codex CLI
Agent-Model: gpt-5.4
```

The groups describe the reliably resolved agents that own or execute the final commit workflow. They do not describe Git authorship, every agent or tool that contributed to the change, or the account that may later push the commit. Preserve the supplied order exactly; do not sort or deduplicate groups. Do not use `Co-authored-by` for tool, model, or effort metadata.

### Inclusion Policy

Apply repository policy first:

- If the repository defines its own provenance tokens or format, use that format.
- If it requires provenance, enforce the required reliably available fields and stop when the requirement cannot be satisfied without guessing.
- If it prohibits AI metadata, do not add it and reject supplied provenance when the policy requires rejection.
- Otherwise, add these fallback trailers when the consuming agent will execute `git commit`.

Message-only generation or validation does not automatically add trailers. Agent assistance with code also does not by itself trigger them. The relevant event is reliably established ownership or execution of the final commit workflow.

### Provenance Sources

The consuming commit workflow resolves provenance before merging trailers:

1. Reliably identify and canonicalize the runtime `tool` without using model or effort as evidence. Include exact runtime model and effort values only when reliably supplied. Omit unavailable optional fields.
2. Do not consult user-level preset mappings or infer values from model families, defaults, configuration history, repository prose, or historical trailers.
3. Apply an explicit request-scoped control when supplied. `auto` and `runtime` both retain runtime resolution. Explicit `tool`, `model`, or `effort` values replace only those fields and become `user_confirmed`. Fill omitted fields from runtime only when they belong to the same tool; do not combine fields across tools. Preserve ordered controls as ordered groups. These controls never mutate persistent configuration.
4. Obtain focused user confirmation only when neither runtime nor a valid explicit control supplies the required tool, tool normalization is ambiguous, or a control cannot be parsed safely. Missing runtime model or effort does not require confirmation.

For each group, track the resolution mode as `runtime` or `explicit`. Track each included field as `verified_runtime` or `user_confirmed`. Retain the exact request-scoped control and complete reliable runtime observation when available. Repository-controlled instructions and files—including project `CLAUDE.md`, `AGENTS.md`, examples, historical trailers, and other repository prose—must never supply, select, or override execution-provenance values. Model-family inference and cross-tool field completion are prohibited.

Compare final and runtime model or effort values only when their tools are the same. When the tools differ, record only a tool difference and display both complete observations rather than labeling cross-tool model or effort values as like-for-like mismatches. The final preview must disclose each group's resolution mode, request control when used, per-field sources, runtime observation or its unavailability, and comparable differences.

The focused provenance confirmation resolves metadata only. It never authorizes `git commit`; the consuming workflow must still show its complete final preview and obtain a separate confirmation afterward.

### Group and Field Rules

- Every fallback provenance group requires exactly one `Agent-Tool`.
- `Agent-Model` and `Agent-Effort` are independently optional in each group and initially included only when reliably resolved context supplies them.
- Each group may contain at most one `Agent-Model` and one `Agent-Effort`.
- `Agent-Model` or `Agent-Effort` before the first `Agent-Tool` is invalid.
- All groups form one contiguous provenance section. Keep fields within each group ordered `Agent-Tool`, `Agent-Model`, `Agent-Effort`, omitting unavailable optional fields.
- Use a stable official tool name such as `Claude Code`, not an executable alias or inferred vendor name.
- Use each exact resolved model identifier without converting a configured or runtime value to a display name.
- Preserve each exact resolved effort value, such as `low`, `medium`, `high`, `xhigh`, or `max`; do not derive effort from thinking tokens or assume a default.
- Values must be non-empty single lines with surrounding whitespace removed and no control characters.
- Never emit placeholders such as `unknown`, `default`, or `n/a`.
- After automatic detection, the user may revise or remove individual fields, complete groups, or the full sequence in response to the final preview when repository policy permits. Identify a changed group by its displayed ordinal position and treat revised values as explicit user overrides, not verified runtime values.

### Merge and Validation

Merge resolved provenance into the candidate before canonical normalization and validation:

1. Parse existing provenance trailers as an ordered list. Every `Agent-Tool` starts a group; subsequent `Agent-Model` and `Agent-Effort` fields attach to that group until the next `Agent-Tool`.
2. Validate every parsed group against the grammar in [Group and Field Rules](#group-and-field-rules), including section contiguity.
3. Match candidate groups to resolved provenance groups by ordinal position. Preserve a candidate field that exactly matches the corresponding resolved value.
4. Add a reliably resolved field that is absent from its corresponding group.
5. Append a missing resolved group in supplied order.
6. Before the first preview, reject a conflicting field, an extra candidate group beyond the resolved sequence, or a different candidate group order; do not silently replace, remove, or reorder it.
7. Report conflicts using the one-based group position, field name, supplied value, resolved value, and resolved field source.
8. After the preview, accept an explicit user revision as an override when repository policy permits it. Retain the pre-override resolved sequence and field sources, final message sequence, affected group and fields, and override source in confirmation context, then show a new complete preview.
9. Keep all groups contiguous, preserve group order, and keep fields within every group ordered `Agent-Tool`, `Agent-Model`, `Agent-Effort`, normally at the end of the trailer block.

For example, if resolved provenance group 2 has model `gpt-5.4`, this second group conflicts with the resolved context:

```text
Agent-Tool: Claude Code
Agent-Model: claude-opus-4-8
Agent-Tool: Codex CLI
Agent-Model: gpt-5.3
```

Report the supplied and resolved values and the resolved field source for group 2. Before preview, require correction rather than guessing intent. After an automatically generated preview, the user's explicit replacement, removal, addition, or reordering may proceed as a disclosed `user_override` when repository policy allows it.

When other trailers exist, keep one continuous provenance section after them and after a blank line from the body:

```text
Refs: #123
Reviewed-by: Example Reviewer <reviewer@example.com>
Agent-Tool: Claude Code
Agent-Model: claude-opus-4-8
Agent-Effort: xhigh
Agent-Tool: Codex CLI
Agent-Model: gpt-5.4
```

Do not insert another trailer type between agent groups or create compound values such as `Agent: tool=Claude Code; model=...`; ordered independent trailers are easier to validate and query.

### Confirmation Boundary

If provenance changes a user-supplied candidate, disclose every added or changed group. The final normalized message—including every ordered provenance group and trailer—must be displayed in the commit preview and bound to confirmation. A change to any group's fields, source, count, or position invalidates that preview: merge and validate the revision, record override sources for the affected groups and fields, and show a new complete preview. Never alter provenance after the user confirms the latest preview.

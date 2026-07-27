---
name: git-commit-message
description: "Generate commit messages from Git staged changes or validate supplied messages without creating a commit. Change-accuracy validation uses staged changes; rules-only validation can run with an empty index. Prioritize repository instructions and commitlint rules, then recent commit history, and fall back to built-in Conventional Commits conventions. Trigger for requests that only ask to generate, revise, or validate a commit message, such as 'generate a commit message', 'write a commit message', 'validate this commit message', '生成 commit message', '写提交信息', or '检查这个 commit message'. Do not trigger when the user intends to execute git commit; execution intent belongs to git-commit."
---

# Git Commit Message Skill

Generate or validate commit messages without modifying the repository. This skill may inspect staged changes and repository rules, but it never stages files, creates a commit, chooses an identity, or pushes.

## Routing and Ownership

Use this skill for message-only requests. If the user intends to execute a commit—including mixed requests such as “write a message and commit”—route the complete request to `git-commit`.

This skill owns:

- Staged-change analysis for message generation and accuracy checks.
- Repository commit-message rule discovery.
- Candidate generation, canonical normalization, and validation.
- Coherence checks that may recommend splitting staged changes.

It does not run `git add`, `git reset`, `git commit`, or `git push`, and it does not inspect author or committer identity.

## Workflow Summary

```text
resolve repository and requested validation scope
→ inspect staged state when required
→ discover applicable message rules
→ check staged-change coherence
→ obtain one candidate
→ apply resolved agent provenance when provided
→ normalize the candidate
→ validate the normalized candidate
→ return one logical result
```

## Step 1: Resolve Repository and Request Scope

Resolve the repository root and capture one reusable status snapshot:

```bash
git rev-parse --show-toplevel
git status --porcelain=v2 --branch -z
```

Use this decision table:

| Request | Repository/index state | Resulting scope |
|---|---|---|
| Generate a message | Normal non-empty index | Analyze staged changes and generate |
| Generate a message | Empty index | `no_staged_changes` |
| Generate or check change accuracy | Conflicts or supported operation in progress | `blocked` |
| Validate a supplied message | Non-empty index, no explicit rules-only request | `rules_and_staged_changes` |
| Validate a supplied message | Explicit rules-only request | `rules_only` |
| Validate a supplied message | Empty index | `rules_only`, unless accuracy was explicitly requested; then `no_staged_changes` |
| Validate a supplied message | Conflicts or operation in progress | `rules_only` may continue only when accuracy was not requested; disclose the state |

For staged-change analysis, capture the full staged diff once:

```bash
git diff --cached --full-index --no-ext-diff --no-textconv
```

Never substitute unstaged or untracked changes for staged input. Treat binary files, renames, copies, and deletions only according to information Git exposes; do not claim to have inspected unavailable binary contents.

When staged-change analysis is requested, block merge, rebase, cherry-pick, or revert operations even after conflicts are resolved. Use long-format `git status` and, when necessary, read-only metadata checks through `git rev-parse --git-path`. Do not infer an operation-specific continuation message.

## Step 2: Discover Applicable Rules

Apply this precedence:

1. Explicit repository instructions.
2. Commitlint configuration and statically resolvable rules.
3. Recent commit-message style.
4. Built-in Conventional Commits fallback.

Read only likely sources such as `CLAUDE.md`, `AGENTS.md`, `CONTRIBUTING*`, `README.md`, repository development documentation, commitlint configuration, and `package.json`. Inspect recent subjects when history exists:

```bash
git log -10 --format=%s
```

Do not execute repository package scripts, local binaries, commitlint commands, JavaScript/TypeScript configuration, plugins, parser presets, or extension modules merely to resolve rules. Mark executable or inherited rules that cannot be determined statically as unresolved, and never claim full validation while relevant rules remain unresolved.

Read [references/message-rules.md](references/message-rules.md) only when repository rules do not fully determine message construction, commitlint configuration needs static interpretation, or resolved agent provenance must be merged.

## Step 3: Check Staged-Change Coherence

Before generation or staged-change accuracy validation, decide whether the staged changes represent one coherent change.

Return `split_recommended` when clearly independent changes would require a vague or misleading message. Explain proposed groups by path and behavior, but do not modify the index.

Do not recommend splitting merely because several files or directories changed. An implementation, its tests, and its documentation may be one coherent commit.

## Step 4: Obtain One Candidate

- Generate mode: create one best candidate from staged changes and applicable rules.
- Validate mode: use the user-provided message as the candidate.
- Multiple candidates are allowed only when explicitly requested.
- Before another skill can execute a commit, reduce multiple candidates to one selected candidate.

Choose type and scope from the purpose and behavior of the change, not mechanically from file paths. Include a body or footer only when required or useful.

## Step 5: Apply Resolved Agent Provenance

When an ordered sequence of reliably resolved execution-provenance groups is supplied, merge it into the candidate before normalization and validation. The consuming workflow identifies the tool first, may use it to select one trusted user-level preset for model and effort, and obtains user confirmation when resolution is ambiguous. Follow [references/message-rules.md#agent-execution-provenance](references/message-rules.md#agent-execution-provenance) as the sole policy for inclusion, repository overrides, group parsing and matching, field values and sources, existing-trailer conflicts, ordering, and user disclosure. Standalone message generation or validation supplies no execution provenance by default.

## Step 6: Normalize the Candidate

Canonical normalization is part of this message policy and occurs before final validation:

1. Use LF line endings.
2. Remove leading and trailing blank lines.
3. Remove trailing whitespace from every line.
4. Use one blank line between header, body, and footer sections while preserving meaningful paragraph breaks within body or footer content.
5. Encode as UTF-8 with exactly one terminal LF.

The normalized UTF-8 bytes are the final message returned to `git-commit`. Presentation may omit a visibly empty final line, but must not change the retained bytes.

If normalization changes a user-provided message, disclose the meaningful change. Do not rely on Git's implicit cleanup to alter a confirmed message later.

## Step 7: Validate the Normalized Candidate

Validate the normalized candidate against every known applicable rule.

For `rules_and_staged_changes`, verify that the candidate accurately covers the staged change and the retained coherence result. Do not repeat the coherence analysis. For `rules_only`, make no claim about staged-change accuracy or suitability for an active Git operation.

Separate:

- Definite violations.
- Optional style suggestions.
- Rules that remain unresolved without executing repository code.

If invalid, provide the violations and one corrected normalized suggestion where possible.

## Step 8: Return One Logical Result

| State | Meaning | Required data |
|---|---|---|
| `generated` | One normalized candidate was generated from coherent staged changes | candidate bytes/text, principal rule source, unresolved warnings, provenance result when supplied |
| `valid` | A supplied normalized message passed selected checks | final message, `validation_scope`, unresolved warnings, provenance result when supplied |
| `invalid` | The normalized message violates known rules | violations, corrected suggestion where possible, validation disclosures |
| `split_recommended` | Staged changes are not one coherent commit | proposed path/behavior groups |
| `no_staged_changes` | Requested generation or accuracy checking has no staged input | reason and request to stage changes |
| `blocked` | Repository state prevents staged-change analysis | operation/conflict reason and relevant paths |

`invalid` describes the message; `blocked` describes repository state. Logical states are coordination terms and do not need to be printed as literal fields for a standalone human-facing response. When `git-commit` consumes the result, preserve the state, exact normalized message bytes, warnings, and reasons.

For any validation result, retain these logical disclosures:

```yaml
validation_scope: rules_only | rules_and_staged_changes
agent_provenance:
  status: included | not_supplied | repository_disabled
  groups: # only when status is included
    - tool: <canonical tool name>
      model: <exact model identifier, when included>
      effort: <exact effort value, when included>
      field_sources:
        tool: verified_runtime | user_confirmed | user_override
        model: trusted_preset | verified_runtime | user_confirmed | user_override
        effort: trusted_preset | verified_runtime | user_confirmed | user_override
      preset_match: <trusted source and entry identifier, when used>
      overridden_fields: [tool | model | effort] # when applicable
```

Preserve `groups` in final message order and retain each included field's source. Omit unavailable optional group fields rather than representing them as unknown. When a user override changes only part of a group, retain the pre-override resolved values separately in coordination context and identify the overridden fields. The provenance coordination data does not need to be printed as a separate block in standalone responses.

## Interaction Rules

When used independently:

- Ask a focused question only when message intent or validation scope cannot be determined safely.
- Do not ask for commit confirmation.
- Do not imply that selecting a candidate executes it.

When followed by `git-commit`:

- Return the logical result without starting a separate confirmation flow.
- Let `git-commit` own user questions, final preview, confirmation, execution, and result reporting.

## Constraints

- Read staged changes only when staged-change analysis is required.
- Never substitute unstaged or untracked content for staged input.
- Never modify files, Git configuration, or the index.
- Never inspect or choose author/committer identity.
- Never execute repository-controlled code to resolve or validate message rules.
- Never claim full validation when relevant rules remain unresolved.
- Never force unrelated staged changes into one generic message.
- Never run `git commit` or `git push`.

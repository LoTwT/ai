---
name: git-commit
description: "Create one local Git commit after checking repository state, resolving author/committer identity, generating or validating an exact normalized commit message, showing one complete preview, and receiving explicit confirmation. Follow the sibling git-identity-check and git-commit-message skills. Trigger when the user intends to execute a commit, such as 'help me commit', 'commit these changes', 'write a message and commit', 'use this message to commit', '帮我提交', or '用这个 message 提交'. A short affirmative reply may continue only when the immediately preceding assistant turn displayed one complete commit preview awaiting confirmation. Do not trigger for message-only generation/validation or identity-only inspection."
---

# Git Commit Skill

Create one ordinary local commit through this controlled workflow:

```text
resolve repository and staged state
→ block unsupported states
→ resolve identity
→ obtain verified execution provenance
→ obtain, normalize, and validate one message
→ record confirmation context
→ show one final preview
→ wait for explicit confirmation
→ revalidate context
→ execute exactly one commit
→ verify and report the actual commit
```

This skill is the orchestration and write layer. It owns all user questions, final confirmation, execution, and result reporting, and it is the only one of the three sibling skills allowed to run `git commit`.

## Composition and Routing

Read and follow:

```text
../git-identity-check/SKILL.md
../git-commit-message/SKILL.md
```

Skills are instruction documents rather than typed functions. Their logical states coordinate this workflow:

- `git-identity-check` owns identity resolution and policy.
- `git-commit-message` owns staged-change message analysis, canonical normalization, and validation.
- `git-commit` owns interaction, confirmation, execution, and verification.

Reuse repository roots, status snapshots, staged diffs, instruction files, and other read-only data already collected. Do not start separate confirmation flows while following foundation skills.

Execution intent takes precedence. Use this skill for “help me commit,” “write a message and commit,” “validate this message then commit,” or a request supplying a complete one-time identity for a commit.

Do not use it for message-only generation, identity-only inspection, staging, pushing, pull-request creation, amend, or merge/rebase/cherry-pick/revert continuation.

## V1 Scope

Supported:

- One ordinary local commit on a normal attached branch.
- Staged changes only.
- Effective identity or one complete process-scoped identity for both author and committer.
- One exact normalized message.
- Normal hooks and existing signing policy.

Unsupported:

- Automatic staging or index splitting.
- Identity profile discovery or alias resolution.
- Separately selected author and committer.
- Detached HEAD, amend, or operation-continuation commits.
- Push, account switching, credential selection, or pull-request creation.

## Step 1: Resolve Repository and Staged State

Resolve the root and capture one reusable status snapshot:

```bash
git rev-parse --show-toplevel
git status --porcelain=v2 --branch -z
```

If outside a repository, stop with the Git error. Parse the snapshot once for branch, staged and unstaged entries, untracked paths, conflicts, and intent-to-add metadata.

Capture one reusable full staged diff:

```bash
git diff --cached --full-index --no-ext-diff --no-textconv
```

Derive the staged summary and path/status view from that snapshot rather than reading the diff again.

Rules:

- Commit staged changes only.
- Empty index: ask the user to stage intended changes and stop.
- Conflicts: report affected paths and stop.
- Intent-to-add entries: report their paths and stop; they are not included in the commit tree.
- Unstaged and untracked changes are context only and must not appear as committed content.
- Never run `git add`, `git reset`, or otherwise modify the index.

Create the initial normalized index fingerprint described in [references/confirmation-snapshot.md](references/confirmation-snapshot.md). Bind staged-change message analysis to this fingerprint.

## Step 2: Block Unsupported Git States

Use long-format `git status` and, when needed, read-only metadata checks:

```bash
test -f "$(git rev-parse --git-path MERGE_HEAD)"
test -f "$(git rev-parse --git-path CHERRY_PICK_HEAD)"
test -f "$(git rev-parse --git-path REVERT_HEAD)"
test -d "$(git rev-parse --git-path rebase-merge)"
test -d "$(git rev-parse --git-path rebase-apply)"
git symbolic-ref --quiet --short HEAD
```

Stop if merge, rebase, cherry-pick, or revert is active; `HEAD` is detached; or the user requests amend. Report the state without generating a regular message as a substitute for an operation-specific message.

## Step 3: Resolve Identity

Follow `../git-identity-check/SKILL.md` as the sole identity policy.

| Result | Action |
|---|---|
| `resolved` | Retain author, committer, source, and `requires_override` |
| `invalid` | Stop before preview and explain corrective input |
| `resolved` plus `requires_user_decision: true` | Obtain the explicit policy decision below |

A complete explicit one-time identity is validated directly even when the existing effective identity is invalid. Retain the round-tripped values and apply them only to this commit and its child processes.

After resolution, do not ask for a separate identity confirmation. Retain the exact author, committer, source, override mode, and policy status so they can be shown and confirmed together with the final message immediately before commit.

For an unresolved normative repository requirement:

1. Show the requirement, source, and reason compliance is unverified.
2. Ask specifically whether to proceed with the displayed identity or cancel.
3. Continue only after explicit acceptance.
4. Retain the warning in confirmation context and preview.

A generic earlier acknowledgement does not resolve this policy decision.

## Step 4: Obtain Verified Agent Provenance

This skill owns and executes the commit workflow, so collect the trusted runtime provenance for every verified agent that owns or executes that workflow and pass the ordered sequence to `git-commit-message`:

```yaml
agent_provenance:
  created_by_agent: true
  groups:
    - tool: <verified canonical tool name>
      model: <verified exact runtime model identifier, when available>
      effort: <verified exact runtime effort value, when available>
      source: verified_runtime
```

Include only runtime-provided provenance and pass it through unchanged. Do not infer agents or fields from repository or user content. Retain the context through retries and revalidate it before each write. `git-commit-message` owns agent eligibility, ordering, inclusion, formatting, repository-policy, matching, conflict, and removal decisions.

## Step 5: Obtain and Validate One Exact Message

Follow `../git-commit-message/SKILL.md` in this order:

1. **Obtain a candidate**: generate it from the fingerprint-bound staged diff, or accept the supplied message.
2. **Select one candidate**: if several were requested, require selection or revision before continuing.
3. **Apply provenance**: pass every verified execution-provenance group from Step 4 in its original order and merge or validate the ordered sequence according to repository policy.
4. **Normalize it**: apply the message skill's canonical UTF-8/LF normalization.
5. **Validate the normalized candidate**: apply repository rules, provenance consistency—including group count and order—and staged-change accuracy checks.
6. **Retain exact bytes and warnings**: use the returned normalized bytes for preview binding and execution, and retain the final ordered provenance groups, every per-group or per-field override, and every unresolved message-rule warning with its source and normative status.

| Result | Action |
|---|---|
| `generated` or `valid` with no unresolved normative rule | Retain the exact normalized message and any advisory unresolved warnings |
| `generated` or `valid` with an unresolved normative rule | Show each unresolved rule and source, explain that compliance is unverified, and obtain a specific proceed/cancel decision before preview |
| `invalid` | Show violations and correction; do not commit |
| `split_recommended` | Ask the user to restage coherent groups; do not modify the index |
| `no_staged_changes` | Ask the user to stage changes |
| `blocked` | Report state and stop |

Acceptance of an unresolved normative message rule does not mean the rule was satisfied. Retain the warning, `policy_compliance: unverified`, and the user's specific acceptance in confirmation context. A generic earlier acknowledgement is insufficient.

If the index fingerprint no longer matches the one bound to analysis, re-read the staged diff and repeat this step.

## Step 6: Record Confirmation Context

Follow [references/confirmation-snapshot.md](references/confirmation-snapshot.md).

Capture the complete context defined by that reference.

## Step 7: Show One Final Preview

Always show the exact resolved Git identity immediately before commit, including author, committer, and source/mode, even when author and committer are identical. This is attribution information, not necessarily the account used later for push or API access:

```text
📝 Commit preview

Repository:  <repository>
Branch:      <branch>
Staged:      <staged summary>
Message:     <final normalized message, including all ordered provenance trailers>
Agents:
  1. <tool / model / effort, omitting unavailable optional values | repository format>
  2. <tool / model / effort, omitting unavailable optional values> [user override: <fields>, when applicable]
  <not included by policy, when no groups are included>
Author:      <name <email>>
Committer:   <name <email>>
Git identity:<effective Git identity | one-time override>
Source:      <effective Git configuration/environment | explicit one-time input>
Message rules:<no unresolved normative rule | user accepted unverified rule: rule/source>
Policy:      <no unresolved identity requirement | user accepted identity requirement/source>
Hooks:       enabled; may reject, modify data, or perform external side effects
Verification: actual commit will be checked; mismatches are not auto-rewritten
Direct push: not invoked by this skill

Reply yes to confirm the displayed message, ordered agent provenance, author, committer, and Git identity and create this local commit; or provide a revised message, permitted provenance changes identified by agent number, or a complete replacement identity.
```

The single confirmation covers the complete message—including every ordered provenance group and trailer—and the exact displayed author, committer, and Git identity source/mode. Do not ask separate confirmations after all are resolved. If provenance groups were appended to or changed in a user-supplied message, state that before or with this preview; the displayed complete message, ordered agent list, and identity are the confirmation boundary. When repository policy permits, the user may revise, remove, add, or reorder provenance groups instead of confirming. Identify groups by their displayed one-based number and treat the response as a message revision; record changed groups and fields as `user_override`, then normalize, validate, rebuild confirmation context, and show a new complete preview. A replacement identity returns to identity validation and likewise requires a new complete preview.

## Step 8: Interpret Confirmation

Commit only when the immediately preceding assistant turn displayed exactly one complete preview containing the message, ordered agent provenance groups, author, committer, and identity source/mode, and no intervening instruction changed message, identity, provenance group fields, group count or order, repository, or scope.

Short affirmative replies such as `yes`, `confirm`, `commit`, `ok`, or `go` may authorize that preview. If context is ambiguous, clarify instead of committing.

A revised message returns to Step 5; a changed identity returns to Step 3; changed or disputed provenance returns to Step 4. Then rebuild context, show a new complete preview, and require new confirmation.

## Step 9: Revalidate Immediately Before Writing

Follow the pre-write comparison in [references/confirmation-snapshot.md](references/confirmation-snapshot.md).

Any mismatch found by that comparison invalidates confirmation. Re-run affected analysis, show a new complete preview, and require new confirmation.

## Step 10: Execute Exactly One Commit

Follow [references/safe-execution.md](references/safe-execution.md).

Execute once using that reference. It owns the invocation, exact-message transport, process-scoped identity overlay, hook and signing preservation, and bypass prohibitions.

## Step 11: Verify and Report

If `git commit` fails, preserve the real error and do not say “Committed.”

On success, follow [references/post-commit-verification.md](references/post-commit-verification.md) to identify the requested commit from the recorded and post-execution branch history, then compare its actual author, committer, raw message bytes—including every ordered provenance group and trailer—and tree with confirmation.

Report actual values:

```text
✅ Committed

Commit:      <sha>
Message:     <subject>
Author:      <name <email>>
Committer:   <name <email>>
Direct push: not invoked by this skill
Hooks:       may have performed additional side effects
```

If identification or metadata verification fails, report the created-commit location or mismatch accurately. Never automatically amend, reset, or rewrite it.

## Retry Behavior

- `commit-msg` rejection: return to message generation/validation.
- `pre-commit` rejection: after the user fixes the cause, recheck staged state and message.
- Signing failure: return to signing/identity prerequisites without disabling signing.
- Other hook failures: preserve the error and recheck any state the hook may have affected.

Within the same attempt, retain a complete one-time identity, but revalidate before another write. Every new commit request resolves identity again. Require a fresh preview whenever confirmed content changes.

## Constraints

- Only this skill may run `git commit`.
- Never modify the index, working tree, Git configuration, or persistent environment as part of this workflow.
- Never infer identity from aliases or remotes, enumerate accounts, or equate attribution with push/API identity.
- Never execute without one complete preview and explicit confirmation.
- Never claim confirmation prevents hooks or concurrent writers from changing data or causing side effects.
- Never use unsafe shell interpolation, `eval`, `--no-verify`, or signing bypasses.
- Never directly invoke `git push`, switch accounts, create a pull request, amend, reset, or rewrite a created commit.
- Never report full success when execution, identification, or actual metadata verification failed.

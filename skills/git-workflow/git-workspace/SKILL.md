---
name: git-workspace
description: "Inspect Git repository and account state, configure account-use policy in agent instructions, prepare task branches or worktrees, synchronize or restack local branches, and recover interrupted Git operations. Use for workspace and account-policy preparation; publishing commits, PR operations, and task-resource deletion have separate owners."
---

# Git Workspace

## Responsibility

Prepare an existing repository or define account-use policy. Choose **inspect**, **configure-accounts**, **prepare**, **synchronize**, or **recover** independently from the request. Inspection never silently becomes synchronization or saved configuration. Identify the repository/worktree before repository operations; do not implicitly clone or initialize. Account diagnosis and user-wide policy configuration need no checkout; repository exceptions need an explicit target.

Ordinary commits and message-only or commit-identity-only requests belong to `git-commit`. Remote branch publication belongs to `git-push`; PR metadata to `git-pr-submit`; content review to `git-review`; PR merging to `git-pr-merge`; task resource deletion to `git-cleanup`. Local merge, rebase, explicitly requested cherry-pick/revert, and their continuation remain here even when they create commits.

Skills can run independently. The calling agent composes capabilities when the user's goal needs them; sibling names are not mandatory file dependencies. Do not make a workspace invocation a prerequisite for remote-only work.

## Inspect

Read applicable instructions, HEAD/branch, staged/unstaged/untracked changes, relevant ignored data, occupied worktrees, and operations in progress. Read relevant remotes, tracking relationships, and base refs only as needed. Dirty worktrees and detached HEAD do not prevent diagnosis.

Use existing local state and necessary read-only remote queries. Fetch changes local refs and belongs to synchronization. Label stale tracking refs and unknown remote state instead of presenting them as current.

## Identity

For account questions or identity-dependent work, read [accounts-and-remotes.md](references/accounts-and-remotes.md). Distinguish effective author/committer, expected roles, API actor, and Git transport actor. Report each with its evidence and uncertainty. Do not infer one from another or reveal credentials.

Before an operation creates or rewrites commits, resolve the applicable author, committer, and signing requirements. Preserve replayed authors unless explicitly instructed otherwise. Apply overrides in the operation's process environment while preserving normal hooks, signing, and unrelated environment. Diagnosis does not log in, persistently switch accounts, or edit global configuration.

## Configure Accounts

Read [account-policy.md](references/account-policy.md) to define, save, or repair account-selection rules: default author/committer, host-specific Git/API accounts, and optional repository/operation exceptions. Reuse clear existing instructions; no mandatory first-use setup.

Resolve only needed choices. Temporary selections need not be saved. When persistence is requested, update the relevant instruction section and verify its loading path. Report policy completeness separately from authentication readiness. Do not install credentials or persistently switch logins.

## Authorization

Before repository writes, resolve the worktree, exact branch set, starting/base commits, method, and intended effects. Follow applicable branch conventions; do not invent a remote or default branch. Explain history changes and account for branches occupied elsewhere. Policy writes instead require a resolved instruction file, scope, and intended rule changes.

Existing authorization remains valid for the same operation category, target set, and effects. Ask only for unresolved choices that materially change writes or for an uncovered expansion. A local restack does not authorize force push, PR retargeting, or deletion. Unrelated remote-login problems do not block local work.

## Execute

- **Prepare:** read [branches-and-worktrees.md](references/branches-and-worktrees.md). Reuse a suitable workspace; establish task ownership and the starting point before creating or switching.
- **Synchronize:** read [branch-sync.md](references/branch-sync.md). Choose fast-forward, merge, rebase, or an explicitly requested local transformation. Refresh only required refs without incidental pruning.
- **Stack:** additionally read [stacked-branches.md](references/stacked-branches.md). Establish parent relationships and old replay boundaries; update in dependency order.
- **Recover:** read [conflict-recovery.md](references/conflict-recovery.md). Inspect the current operation and user edits before continuing or aborting.

Preserve unrelated files and staged selections. Do not automatically stash, reset, skip, or discard work to unblock a command. Record affected tips and relevant state; recheck them immediately before writing. If concurrent work changed them, reassess instead of overwriting it.

GitHub's server-side **Update branch / Rebase stack** shortcuts are not executed by this local skill. For an integration goal, compose local synchronization then `git-push`; if the user specifically requires server-side execution, report that this implementation does not provide it rather than substituting a different write silently.

## Retry and Verify

For policy-only work, reread the target before retrying, preserve concurrent edits, and avoid duplicate sections. Verify rules and loading as described in the policy reference; repository-state checks do not apply.

On reentry, distinguish not started, completed, partial, conflicted, and unknown outcomes from actual state. Do not restart completed stack steps. Continue or abort only the identified in-progress operation.

Verify the resulting worktree path/branch, intended commits and changes, preserved local work, and remaining operations. Report actual identities for commits produced. For rewritten published history, report the exact branches that may need non-fast-forward publication; the push operation must independently refresh and verify its evidence.

A useful handoff contains repository/worktree, affected refs and before/after OIDs, base/replay boundaries, actual actor evidence, remaining blockers, and existing authorization scope. It is a task-local summary, not a persistent workflow database.

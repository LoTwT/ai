---
name: git-cleanup
description: "Inventory and remove authorized Git task branches, worktrees, and stale references after checking saved data, publication, and active dependencies. Supports exact local and remote branch cleanup; does not merge PRs or delete repositories and forks."
---

# Git Cleanup

## Responsibility

Inventory task resources, decide which are eligible under applicable policy, and delete only authorized targets. Start with a dry-run inventory, even when the request already authorizes deletion. A successful merge is evidence about integration, not blanket cleanup authorization.

This skill owns local and remote task-branch deletion, worktree removal, and stale-ref pruning. PR merging belongs to `git-pr-merge`; synchronizing a retained base belongs to `git-workspace`. Repository/fork deletion, broad filesystem cleanup, and stash purging are outside this skill.

## Inventory

Read [local-resources.md](references/local-resources.md). Resolve repository/worktree, exact branch refs and OIDs, local changes including ignored/untracked data, unpushed commits, branch occupancy, locks, and known active tasks.

Check integration against the intended retained base, not merely any configured upstream. Squash integration may need PR/patch evidence because ancestry differs. Query complete relevant open PR dependencies when remote branches or stacks are involved.

Classify each candidate as **retain**, **eligible and authorized**, or **needs a decision**, with the reason. Missing data or dependency evidence means retain until resolved.

## Identity and Authorization

Local-only cleanup does not require an unrelated API login. For remote deletion, read [remote-and-prune.md](references/remote-and-prune.md): verify the transport actor in the actual deletion context, API actor for dependency queries where used, target repository, permissions, and protection.

Reuse existing authorization for the exact deletion category, targets, and effects. Applicable instructions may define a narrow merge-and-cleanup bundle; verify all its conditions. Do not require one new confirmation per item when an explicit batch already covers them.

Worktree removal, deleting unique/unpublished commits, and force deletion must be covered by the request or applicable authorization. Present concrete resources and data consequences before requesting an uncovered decision. Never expand a target just because ordinary deletion fails.

## Execute

Immediately reread candidate OIDs, data, occupancy, and dependencies. Prefer ordinary branch/worktree removal; preserve locks and ongoing work. Do not use forced removal as a fallback.

Remote deletion uses an explicit expected-OID condition on the exact branch, never an unconditional delete. Prune is a separate batch operation: inspect actual fetch destinations, pruning configuration, and the complete proposed deletion set before authorizing it. Before pruning stale refs, read [Prune safety](references/remote-and-prune.md#prune-safety).

Keep enough task-local evidence to identify deleted refs and recoverable commit OIDs; do not describe ignored/untracked data as recoverable from reflogs.

## Retry and Verify

After each operation, verify absence of the exact resource and preservation of retained work. Already absent is complete only for the same resolved target; it is not evidence about a similarly named path or another repository.

After uncertain remote deletion, reread the exact ref. If it was recreated or advanced, preserve it and reassess; never refresh the lease and delete blindly. Report completed, retained, failed, and unknown resources separately.

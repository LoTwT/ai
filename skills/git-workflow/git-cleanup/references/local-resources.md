# Local cleanup inventory

Read this before removing a local branch or worktree.

## Inventory and eligibility

Identify the actual repository and each exact worktree path, branch/ref, tip, lock, and branch occupancy. Inspect staged/unstaged/untracked files and ignored data. A clean tracked status does not make a directory disposable; ignored build outputs may be regenerable, but ignored credentials or user notes may not be.

Check task ownership and known active dependencies. Inspect unpushed commits and whether changes reached the intended retained base. `git branch -d` can consider a configured upstream instead of the desired trunk, so its success alone is not an integration check. For squash merges, use verified PR/patch evidence to decide whether unique commits still represent unmerged work.

Default/protected branches, active checkouts, locked worktrees, uncertain task ownership, and unknown publication/integration are retained until resolved. Report exact consequences before deleting unique or unpushed work, even if commits might remain in a reflog.

## Execute within scope

Ordinary branch deletion is preferred after checks. If it fails, inspect and report the reason; do not automatically retry with `-D`. Force deletion requires authorization covering the exact branch and any loss of unique or unpublished work, plus rechecking its current tip, occupancy, and dependencies. Eligible cases can include a known squash-integrated branch or an explicitly abandoned branch with unmerged commits.

Worktree removal requires authorization covering the actual path and relevant data. Preserve ignored/untracked data unless its disposition is explicitly covered. A locked worktree is not unlocked automatically. Check linked worktree registration and nested repositories/submodules before removal.

For exact ref deletion where compare-and-swap is needed, `git update-ref -d refs/heads/BRANCH OLD_OID` can guard against an OID change, but it bypasses ordinary branch-deletion checks and does not handle branch config like `git branch -d`. Use it only after the same eligibility/occupancy checks and only when this narrower ref operation is appropriate. A tip condition does not protect against a concurrently occupied branch; coordinate active work rather than claiming it does.

## Verify

Re-read the branch/worktree registry and relevant paths. Record the exact removed targets and retained commit OIDs. Do not use recursive filesystem deletion to conceal a failed worktree operation.

Worktree pruning removes stale administrative records, not a chosen worktree directory. Inspect locked/missing paths and the dry-run candidates; an unavailable mounted directory is not necessarily abandoned. Prune only the authorized complete set.

Source: [Git branch deletion](https://git-scm.com/docs/git-branch).

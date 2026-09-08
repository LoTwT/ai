# Task branches and worktrees

Read this for preparing or switching task workspaces.

Resolve the actual root with `git rev-parse --show-toplevel`; inspect `git worktree list --porcelain`, HEAD, index, worktree changes, and applicable naming rules. Use NUL-delimited porcelain output where supported when parsing paths; do not split paths on whitespace. Bare repositories and unborn branches need explicit handling rather than pretending an ordinary checkout exists.

Reuse an existing workspace only after its branch, starting point, local work, and task ownership match. If a branch is occupied elsewhere, use or report that location. Do not override branch occupancy, remove locks, or change another task's checkout.

Before creation, validate the branch name, resolve the starting ref to an OID, and check the target path including ignored/untracked files. Follow the user's branch/worktree conventions and requested starting state; an arbitrary default branch is not an equivalent substitute.

Typical operations after resolution:

```text
git switch -c BRANCH START_OID
git worktree add -b BRANCH PATH START_OID
git worktree add PATH EXISTING_BRANCH
```

Use argument vectors and exact values. Do not treat a new worktree as a copy of another checkout's unstaged or staged changes.

Before switching with changes, determine which changes belong to this task and whether they can carry across without changing ownership or staging. Do not rely only on Git refusing an overwrite: Git can successfully carry unrelated changes to another branch. Use an agreed preservation/migration plan for work that must move.

On retry, inspect an existing path and branch before creating another. A matching name is not proof of a completed prior request. Verify branch, starting commit, path, and retained changes after preparation. Removal of an abandoned workspace belongs to cleanup under its own scope.

Source: [Git worktree](https://git-scm.com/docs/git-worktree).

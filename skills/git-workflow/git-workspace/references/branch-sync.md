# Local synchronization

Read this for fetch, fast-forward, merge, rebase, and explicitly requested cherry-pick/backport/revert work.

## Resolve and preserve

Identify the exact source and target OIDs and the intended transformation. A local `main`, its tracking ref, and the remote's current default branch are different inputs. Read applicable sync preferences; prefer fast-forward when it achieves the goal. Divergence without a selected merge/rebase policy requires a decision if outcomes differ.

Record old branch tips, index selection, worktree changes, and in-progress operation state. If the operation cannot preserve existing changes in place, establish a preservation plan first. A user-approved stash plan must preserve the index boundary and untracked data that it actually covers; inspect ignored data separately. Record the exact stash OID, restore with index preservation where appropriate, and keep the stash until comparison confirms restoration. Do not pop/drop on blind success, auto-stash by default, or reset to clear restoration conflicts.

## Refresh narrowly

Inspect relevant fetch refspecs and prune/tag settings. Fetch only the required source, without pruning, following tags, recursing into unrelated repositories, or updating unrelated branches. For a known branch, one bounded approach is an explicit source fetch into FETCH_HEAD with configured destination mappings disabled:

```text
git fetch --no-prune --no-prune-tags --no-tags --no-recurse-submodules --refmap= REMOTE refs/heads/BASE
```

Resolve FETCH_HEAD immediately to an OID and retain it; another fetch may replace it. Verify options against installed Git. Avoid `pull` when it hides an unresolved fetch target or integration strategy.

## Integrate

Use `merge --ff-only` for a fast-forward goal, an explicit merge for a merge goal, or rebase with known boundaries for a replay goal. Account for `rebase.updateRefs`, auto-stash, rebase-merges, hooks, signing, and other settings that can alter scope. Disable automatic extra-branch updates for a single-branch operation; do not flatten merge commits unless that history change is intended.

An explicit cherry-pick/backport or revert request must identify the selected commits, order, target branch, and any merge mainline choice. These transformations and their generated commits remain workspace operations. Recovery authorization covers continuing that operation, not starting extra picks or reverts.

Use the chosen committer environment and preserve original authorship when replaying. Stop on conflicts and follow the recovery reference. Already integrated changes need no new replay; do not use a successful exit code alone as proof.

## Verify

Compare old/new history and intended changes, using range-diff or patch inspection when OIDs change. Verify unaffected refs, restored staged/unstaged selections, and absence or known presence of an in-progress operation. Report publication needs without pushing.

Sources: [Git fetch](https://git-scm.com/docs/git-fetch), [Git rebase](https://git-scm.com/docs/git-rebase).

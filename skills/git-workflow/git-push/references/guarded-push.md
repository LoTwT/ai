# Guarded branch publication

Read this after resolving the actor and exact destination.

## Snapshot

Resolve each source to a commit OID. Query each full destination ref with `git ls-remote --refs` against the verified push destination, independently of background-updated tracking refs. Capture absence explicitly. Fetch missing target objects narrowly if ancestry needs them, using an explicit source-only refspec and `--refmap= --no-prune --no-prune-tags --no-tags --no-recurse-submodules` to prevent configured mappings, pruning, tag fetching, or submodule recursion from expanding the operation. A missing object is not proof of divergence.

Classify absent/create, equal/no-op, ancestor/fast-forward, or history replacement. Authorization must cover that category, exact ref set, and material effects.

Check the commits the target branch gains, not only the selected tip; a tip includes its ancestor history. For history replacement, also identify commits no longer reachable from the new tip. Any change summary for a new branch must identify its comparison base, or disclose that no base is established. Resolve material scope mismatches under the existing authorization rules; routine checks do not require a full user-facing preview or per-commit approval.

## Conditional write

Freeze the observed old OID and intended new OID. For an authorized history replacement, bind the lease to the full ref and explicit old OID; for creation an empty expectation requires absence:

```text
git push --porcelain --no-follow-tags --recurse-submodules=no --force-with-lease=refs/heads/TARGET:OLD_OID DESTINATION NEW_OID:refs/heads/TARGET
git push --porcelain --no-follow-tags --recurse-submodules=no --force-with-lease=refs/heads/TARGET: DESTINATION NEW_OID:refs/heads/TARGET
```

These templates require exact validated arguments and already resolved authorization. An explicit lease can also guard an already-classified fast-forward against a concurrent move, but the client must first verify that the planned old-to-new update is fast-forward: the lease itself permits history replacement.

Prevent implicit mirror publication and other destinations. Keep explicit `--no-follow-tags` and `--recurse-submodules=no` for branch-only publication; omitting them can activate configured tag or submodule publication. On-demand recursion may also reject a frozen OID source that does not name a branch. Prefer an explicit verified destination and refspecs, preserving transport hooks/signing. Do not use `--all`, a remote group, or `--mirror` for a bounded task.

For a stack, freeze every pair and use per-ref expectations. Use `--atomic` when the request requires the set to succeed together and the server supports it. If unavailable, stop for a decision before changing all-or-nothing semantics.

## Failure and receipt

A stale lease means the reviewed state changed. Keep the original expectation, inspect new commits, and reassess scope. Do not replace it with the latest tracking OID merely to make a retry pass. Bare `--force-with-lease` is weakened by background fetch; an explicit expectation is not.

After success, error, or timeout, query every destination again. If it equals the intended OID, the publication is observed complete. If it differs, distinguish rejection, later advancement, partial completion, and unknown outcome without claiming a result the evidence cannot establish. Preserve newer work and report each ref.

Sources: [Git push leases and atomic updates](https://git-scm.com/docs/git-push), [Git fetch mapping and pruning](https://git-scm.com/docs/git-fetch).

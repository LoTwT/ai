# Remote deletion and pruning

Read this for remote task-branch removal or stale-ref pruning.

## Remote branch deletion

Resolve the exact host/repository and full branch ref. Inspect the effective push URLs with `git remote get-url --push --all`, URL rewriting, remote groups, and mirror configuration. A named remote can write to multiple repositories. Bind DESTINATION to one verified endpoint, or require authorization and separate checks for every endpoint; never let the same branch/OID match authorize deletion in another repository. Display only sanitized URLs.

Verify the Git transport actor in the same credential context used for deletion; API login or repository ownership alone does not prove it. For SSH inspect actual key/host selection; for HTTPS bind an already verified account credential to the transport without printing it or changing persistent login state.

Verify authorization, default/protected status, current remote OID, integration evidence, and complete relevant open PR head/base dependencies, stack membership, and known active tasks. Use the API actor required for these queries; inability to establish dependency completeness means retain.

Delete only the observed ref under its explicit expected OID:

```text
git push --porcelain --no-follow-tags --recurse-submodules=no --force-with-lease=refs/heads/TARGET:OLD_OID DESTINATION :refs/heads/TARGET
```

Keep the original expectation. Never use unconditional REST ref deletion or refresh a failed lease automatically. Query the ref after success/error/timeout: absence is observed completion; advancement or recreation requires reassessment. A SHA condition cannot prevent another PR being created concurrently; coordinate shared work and report this limit rather than promising a transaction over refs and PRs.

## Prune safety

Inspect every fetch mapping and prune/tag setting, then the proposed deletion set. Prune follows refspec destinations: it can remove local heads or tags, not just remote-tracking refs. A remote with no tag mapping is not thereby safe.

For routine tracking cleanup, require positive destinations to stay within that remote's `refs/remotes/REMOTE/` namespace and confirm the complete stale set. Retain anything overlapping another remote, local heads/tags, protected refs, or known active dependencies. Nonstandard mappings require a separate exact plan; do not run a broad prune merely because its name sounds harmless.

Use `git remote prune --dry-run REMOTE` only after confirming its target semantics. Re-read configuration, remote state, and candidate OIDs before execution. Prefer individual `git update-ref -d REF OLD_OID` removals for a verified stale set when a batch prune cannot preserve the authorized set under concurrent changes. Never interpret a partial listing as proof of completeness.

For worktree administrative pruning, use the local-resources procedure; do not confuse it with directory removal.

Verify each deleted ref and retained namespace afterward. Report absent, retained, failed, and unknown outcomes separately.

Sources: [Git remote prune](https://git-scm.com/docs/git-remote), [Git fetch pruning](https://git-scm.com/docs/git-fetch), [Git update-ref](https://git-scm.com/docs/git-update-ref).

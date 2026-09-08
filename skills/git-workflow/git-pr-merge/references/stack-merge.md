# Stack merge and aftermath

Read this whenever the target PR participates in dependent work.

Distinguish conventional PR chains from native platform stacks. Query the actual current topology, stack base, outstanding PRs, head OIDs, mergeability, and applicable gates for the effective merge set.

For a native GitHub stack, merging a selected PR can include every unmerged predecessor below it. Enumerate that prefix and verify authorization and gates for each PR. "Merge only PR 12" cannot silently become merging PRs 10, 11, and 12. A conventional chain has different platform behavior; do not assume native prefix merging there.

Use the currently supported native asynchronous stack merge operation rather than treating a stack as an ordinary single-PR REST merge. Verify host/CLI support and the request's actual head/topology preconditions before execution. Keep the operation receipt. The atomicity of one native request does not make multiple separate API requests or queue processing one indivisible workflow. Read per-PR outcomes after failures.

Never automatically rebase a stack or modify branch protections to achieve linearity. Local repair belongs to workspace, its publication to push, followed by a fresh check. Do not enable ordinary auto-merge on a native stack when the host does not support it.

After completion, read all affected PRs and branch tips. The platform may already retarget/rebase the next remaining PR; if that fails or behavior differs by host/version, report the actual remaining state. Do not assume every descendant still has its old OID or old base.

Handoff only remaining authorized actions:
- PR metadata/base/membership: PR submit.
- Local baseline synchronization and restack: workspace, with old replay boundaries and observed merge results.
- Publication of local rewritten branches: push, with fresh remote evidence.
- Exact branch/worktree deletion: cleanup, after data and dependency checks.

If a merge was queued, defer dependent cleanup until merged state is actually verified. Preserve remaining branches when stack membership or dependent work is unknown.

Sources: [Merging GitHub stacks](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/merging-stacked-pull-requests), [Stack reference](https://docs.github.com/en/pull-requests/reference/stacked-pull-requests).

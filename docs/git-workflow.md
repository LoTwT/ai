# Git workflow design

This implementation provides seven self-contained skill entrypoints. A skill is an instruction package, not a daemon, command dispatcher, or persistent workflow engine. The calling agent selects and composes capabilities from the user's actual request.

## Ownership and completion

| Entrypoint | Owned effect | Completion evidence |
|---|---|---|
| git-workspace | Repository/account inspection, account-policy configuration, workspace preparation, integration/replay, recovery | Actual workspace state, or resolved policy and loading evidence with separate authentication status |
| git-commit | Ordinary commit; message-only and commit-identity-only modes | Verified commit parent/tree/message/identity, or requested read-only result |
| git-push | Remote branch creation/update from exact source commits | Exact destination refs and observed OIDs in the verified transport context |
| git-pr-submit | PR creation and metadata/base/draft/stack association | PR ID/URL and read-back fields, actor, head/base |
| git-review | Content findings and authorized review publication | Findings tied to inspected evidence; publication receipt when requested |
| git-pr-merge | Eligibility check and authorized ordinary/stack merge | Authoritative gate evidence and actual merged/queued/pending outcome |
| git-cleanup | Local/remote task-resource deletion and stale-ref pruning | Exact deleted/retained resources, data/dependency checks, read-back state |

PR code updates belong to push; PR fields belong to submit. Review findings belong to review; authoritative merge eligibility belongs to merge. Local integration commits belong to workspace; ordinary task commits belong to commit. Deletion belongs to cleanup even when a merge request's applicable policy also authorizes it.

## Composition

An ordinary feature can use workspace → commit → push → PR submit → review → PR merge → cleanup, but this is not a mandatory pipeline. A message-only request needs commit alone; a remote PR check can run without a checkout or workspace invocation.

Each step reads applicable policies and freshly verifies the identity/evidence needed for its own effect. Workspace can diagnose accounts and discover initial context, but its report is not a reusable authentication certificate. Commit author/committer, API actor, transport actor, PR author, reviewer, and merger are separate facts.

Workspace's optional `configure-accounts` mode defines default author/committer, host-specific Git/API accounts, and exact repository/operation exceptions in applicable agent instructions. It reuses existing policy, resolves only needed choices, and persists rules when requested. User-wide configuration does not require a checkout. Other skills consume the resulting instructions directly; they do not require workspace initialization or its reference files. Policy completeness, instruction loading, and authentication readiness are separate results. See the [policy format and selection rules](../skills/git-workflow/git-workspace/references/account-policy.md).

A task-local handoff should retain exact repository/worktree and target IDs, source/base/ref OIDs, relevant evidence, completed or uncertain operations, and existing authorization. It is not a fixed schema or a replacement for rereading mutable state. If a tool times out, reconciliation precedes retry.

Authorization is determined by the current request and applicable instructions. Reuse it while operation category, target set, and material effects remain covered. A new force update, additional stack predecessor, changed publication event, or newly discovered data loss can expand that scope. Routine implementation steps within existing scope do not require repeated confirmation.

## Stack workflow

Stack is a mode across the same seven skills. Workspace tracks old parent boundaries and local progress; push updates exact remote refs; submit maintains PR relationships; review evaluates the intended layer/range; merge resolves the platform's effective merge set; cleanup protects remaining dependencies.

After a stack merge, inspect platform state before retargeting or replaying descendants. Use merge receipts, old boundaries, and patch evidence after squash merges. Do not assume old commit ancestry still identifies remaining work, or that the platform left every branch unchanged.

## Supported scope

Local operations use Git. Remote branch writes can use supported Git transports; PR references give concrete GitHub guidance. Other hosts require verified equivalent operations, not guessed endpoints. Native stack operations are capability-checked against the current host and CLI/API.

Server-side GitHub Update branch/Rebase stack shortcuts are not exposed by these skills. The supported integration route is local workspace synchronization followed by push, then refreshed merge checks. A request specifically requiring the server-side shortcut must be reported as unsupported rather than silently translated into another write.

Explicit local cherry-pick/backport/revert operations belong to workspace, followed by push and PR submit as needed; their generated commits do not require an artificial ordinary commit step. Account-selection policy editing belongs to workspace. Repository/fork creation or deletion, tag/release publication, CI/protection configuration, credential installation, and persistent login switching are outside this workflow.

## Packaging and language

Each skill links only to its own references. No dependency on the old installed identity/message/commit skills remains. The repository's English sources are the implementation; design discussion and review in the session use Chinese. Development and evaluation never replace installed skills.

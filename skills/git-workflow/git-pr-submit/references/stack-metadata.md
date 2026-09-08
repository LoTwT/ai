# Stack metadata

Read this when creating or updating stacked PR relationships.

Determine whether the task uses a conventional chain (each PR targets its parent's branch) or a native platform stack. Read actual repository/PR IDs, head/base refs, parent relationships, current OIDs, and existing membership. Do not infer a chain from branch names or assume a conventional chain is already a native stack.

For a conventional chain, set the lowest PR's base to the selected trunk and each descendant's base to its intended predecessor. Confirm that each published branch contains the intended range. Metadata changes must not push local branches or rebase them.

For a native stack, discover supported operations and limitations from the current host and installed CLI/API. Use supported metadata-only creation/extension/update operations. GitHub currently exposes stack-management REST operations; do not invoke an extension's combined submit/push behavior unless every effect is separately authorized and assigned to its responsible capability. Do not install an extension implicitly.

A native stack may have same-repository and topology restrictions that a conventional chain does not. Verify them rather than creating forks or reparenting branches to force eligibility.

After a merge, read the platform's resulting relationships first. It may already have retargeted remaining PRs or changed branch tips. Maintain only the remaining authorized metadata changes. Local restack belongs to workspace, publication to push, and branch removal to cleanup.

Record each updated PR's before/after base and membership. On partial failure, inspect actual state and resume only missing changes. Do not rebuild a complete stack from a stale local plan.

Sources: [Creating GitHub stacks](https://docs.github.com/en/pull-requests/how-tos/create-pull-requests/creating-stacked-pull-requests), [Stack APIs](https://docs.github.com/en/pull-requests/reference/stacked-pull-requests-apis-and-webhooks).

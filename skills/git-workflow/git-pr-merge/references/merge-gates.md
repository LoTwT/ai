# Merge eligibility and execution

Read this for readiness checks and ordinary PR merges.

## Current evidence

Resolve repository/PR, head and base OIDs, PR author, API actor and permissions, requested method, applicable instructions, and allowed repository methods. Resolve accounts for authenticated queries and the merge separately under applicable policy; neither local Git identity nor the active gh login is actor evidence.

Reuse a verified identity context while its selected account, host, target scope, transport, and credential binding remain unchanged and verifiable. Credential setup and actor probes below apply only to a new or invalidated context. Check permissions, protection, and target state as required for the current operation.

With gh, privately capture `gh auth token --hostname HOST --user LOGIN`, rejecting errors and empty output. In a copied process environment, remove inherited `GH_TOKEN`, `GITHUB_TOKEN`, `GH_ENTERPRISE_TOKEN`, and `GITHUB_ENTERPRISE_TOKEN`; set only the captured token in `GH_TOKEN` for github.com and subdomains of ghe.com or `GH_ENTERPRISE_TOKEN` for Enterprise Server. Clear stale `GH_HOST`/`GH_REPO` selectors and use explicit targets. Require `gh api --hostname HOST user --jq .login` to succeed and match LOGIN, then reuse that token/context for execution. Give different query/merge accounts separate contexts. A connector must provide equivalent binding.

If lookup, authentication, or identity verification fails, stop the dependent operation; never fall back to another account. Do not mutate a shared environment, switch persistent logins, or treat `GH_CONFIG_DIR` alone as credential isolation. Keep tokens out of arguments, URLs, files, output, and credential-bearing traces. Changing the account, host, or credential requires new verification.

Read complete required-check and status evidence, required reviewers/CODEOWNERS where relevant, review state/commit coverage, unresolved conversations, draft/closed state, mergeability, rulesets/protection, and merge queue requirements. Paginate relevant collections. A green subset, cached readiness label, or unknown mergeability is not proof of eligibility.

Distinguish absent requirements from requirements that could not be read. Require exact current-head approval only when the platform or applicable policy requires it; do not invent a universal human-review policy. Never impersonate a human-only approver or bypass protection to compensate for missing evidence.

## Method and result message

Choose the required allowed method. If multiple methods remain equally valid and no instruction/default resolves the choice, ask about the meaningful difference. For squash/merge, prepare the resulting message from the actual change and current PR fields, applying relevant message rules. Do not claim tests based on unchecked PR checkboxes.

The platform controls some author/committer/signature fields. If policy cannot be satisfied through the supported operation, stop rather than guessing or silently weakening it. Verify actual metadata afterward.

## Execute with preconditions

Immediately re-read head/base and dependent gates. For an ordinary supported GitHub merge, `gh pr merge PR_URL --match-head-commit HEAD_OID` plus the chosen method binds the request to that head. Alternatively use the merge API with its documented head SHA condition.

That condition does not bind base. If policy requires validation against the latest base, verify server-side enforcement, such as an applicable strict up-to-date rule or queue, for this actor. A client re-read and a non-strict passing status do not close the base race. Do not use admin bypass.

When the target branch requires a merge queue, `gh pr merge` can enqueue the PR or enable auto-merge even without `--auto`; verify that these actual effects are covered by the request before invoking it.

Readiness-only requests stop before mutation. For immediate-merge requests, report unmet gates; do not silently enable auto-merge. Queue/auto-merge enrollment must fit the request and is reported as pending, not merged. Do not use a delete-branch flag.

## Reentry

Check whether the PR already merged before issuing a request and after any timeout. Keep async/queue receipts and inspect their state. Do not repeatedly enqueue or merge because the first response was uncertain.

Read back merged state, actual merged head/set, resulting commit(s), mergedBy, and available attribution. If metadata is incomplete, report the specific unknown without manufacturing a receipt.

Sources: [GitHub CLI merge](https://cli.github.com/manual/gh_pr_merge), [GitHub protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches), [GitHub account token](https://cli.github.com/manual/gh_auth_token), [GitHub CLI environment](https://cli.github.com/manual/gh_help_environment).

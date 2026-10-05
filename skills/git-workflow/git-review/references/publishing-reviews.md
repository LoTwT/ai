# Publishing review results

Read the account-binding section for authenticated PR queries. The remaining sections apply only to explicitly authorized external review publication or updates.

## Account binding

Reuse a verified identity context while its selected account, host, target scope, transport, and credential binding remain unchanged and verifiable. Credential setup and actor probes below apply only to a new or invalidated context. Check permissions, protection, and target state as required for the current operation.

Select the required API account for each authenticated query or publication under applicable policy; these actors can differ. With gh, privately capture `gh auth token --hostname HOST --user LOGIN`, rejecting errors and empty output. Copy the process environment, remove inherited `GH_TOKEN`, `GITHUB_TOKEN`, `GH_ENTERPRISE_TOKEN`, and `GITHUB_ENTERPRISE_TOKEN`, then set only the captured token in `GH_TOKEN` for github.com and subdomains of ghe.com or `GH_ENTERPRISE_TOKEN` for Enterprise Server. Clear stale `GH_HOST`/`GH_REPO` selectors and use explicit targets.

Require `gh api --hostname HOST user --jq .login` to succeed and match LOGIN in that context, then reuse the same token for the operation. A different actor/host/credential needs a separate verified context; a connector must provide equivalent binding. Missing, rejected, expired, or mismatched credentials stop dependent work without account fallback. Do not mutate shared environment/configuration, switch logins, or treat `GH_CONFIG_DIR` alone as credential isolation. Keep tokens out of arguments, URLs, files, output, and credential-bearing traces. This also applies to read-only review; local-only analysis needs no remote login.

## Identity and event

Resolve host/repository, PR, author, current head, expected reviewer role, API actor, and permitted event. Use the verified API context selected for this publication. Do not persistently switch accounts or expose tokens.

Check author/reviewer equality early for formal approve/request-changes operations and obey the platform's restrictions. A human-only approval rule cannot be satisfied by an agent using that person's token. Commenting and formally approving are different capabilities and authorization categories.

Read the existing actor-owned review/comment/thread when a follow-up asks to update or reply. Do not edit someone else's content, overwrite a previous review, or mark a thread resolved unless that precise action is requested and supported.

## Bind to evidence

Prepare the complete text and valid anchors for the reviewed snapshot. Before publishing, re-read the PR identity and head/base OIDs. Reuse the complete reviewed diff while it remains available and its repository identities, head/base/merge-base OIDs, comparison mode, and scope still match. Otherwise retrieve missing or changed content and revalidate affected findings; a summary or incomplete diff does not establish reusable coverage.

GitHub's review API can associate a review with an explicit `commit_id`. Prefer a supported API operation with that field for snapshot-bound publication; the ordinary `gh pr review` command does not expose a head precondition. An association is not a lock on the PR: a new commit can arrive after the check, so read the receipt and current head afterward.

Use the authorized COMMENT, APPROVE, or REQUEST_CHANGES event. Omitting an event may create a pending review rather than submitting it; pending is not published. Inline comments must use valid paths, lines/sides, and commit context from the reviewed diff.

For a general requested review discussion without inline anchors, post to the identified PR/thread using the documented comments operation. Preserve literal content through structured fields or a body file.

## Recover and verify

After timeout/error, query relevant events with pagination and compare actor, event, commit, text, and anchors. Reuse an exact receipt instead of duplicating publication. Do not turn a failed approve into a comment or switch accounts as a fallback.

Return the actual event/comment ID and URL, actor, commit association, submitted/pending status, and any uncovered new head or unpublished findings.

Sources: [GitHub review API](https://docs.github.com/en/rest/pulls/reviews), [GitHub CLI review options](https://cli.github.com/manual/gh_pr_review), [GitHub account token](https://cli.github.com/manual/gh_auth_token), [GitHub CLI environment](https://cli.github.com/manual/gh_help_environment).

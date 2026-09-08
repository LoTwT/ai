# Publishing review results

Read this only for explicitly authorized external review publication or updates.

## Identity and event

Resolve host/repository, PR, author, current head, expected reviewer role, API actor, and permitted event. Verify the API user in the exact connector/process credential context used for writing. Do not persistently switch accounts or expose tokens.

Check author/reviewer equality early for formal approve/request-changes operations and obey the platform's restrictions. A human-only approval rule cannot be satisfied by an agent using that person's token. Commenting and formally approving are different capabilities and authorization categories.

Read the existing actor-owned review/comment/thread when a follow-up asks to update or reply. Do not edit someone else's content, overwrite a previous review, or mark a thread resolved unless that precise action is requested and supported.

## Bind to evidence

Prepare the complete text and valid anchors for the reviewed head. Before publishing, re-read the head and relevant diff. If it changed, inspect the delta and revalidate findings before claiming current-head coverage.

GitHub's review API can associate a review with an explicit `commit_id`. Prefer a supported API operation with that field for snapshot-bound publication; the ordinary `gh pr review` command does not expose a head precondition. An association is not a lock on the PR: a new commit can arrive after the check, so read the receipt and current head afterward.

Use the authorized COMMENT, APPROVE, or REQUEST_CHANGES event. Omitting an event may create a pending review rather than submitting it; pending is not published. Inline comments must use valid paths, lines/sides, and commit context from the reviewed diff.

For a general requested review discussion without inline anchors, post to the identified PR/thread using the documented comments operation. Preserve literal content through structured fields or a body file.

## Recover and verify

After timeout/error, query relevant events with pagination and compare actor, event, commit, text, and anchors. Reuse an exact receipt instead of duplicating publication. Do not turn a failed approve into a comment or switch accounts as a fallback.

Return the actual event/comment ID and URL, actor, commit association, submitted/pending status, and any uncovered new head or unpublished findings.

Sources: [GitHub review API](https://docs.github.com/en/rest/pulls/reviews), [GitHub CLI review options](https://cli.github.com/manual/gh_pr_review).

---
name: git-pr-submit
description: "Create a GitHub pull request from a published head branch or update its title, body, base, draft state, or stack membership. For PR code updates, use git-push."
---

# Git PR Submit

## Responsibility

Create or maintain PR metadata. Branch publication belongs to `git-push`, content review and review discussion to `git-review`, and merging to `git-pr-merge`. Use the request and current PR state to resolve a general "update PR" request before asking which changes are intended.

This skill can work without a local checkout when remote evidence is sufficient. For another hosting service, verify equivalent supported operations before acting; never invent GitHub-compatible endpoints.

## Identity and Preconditions

Read [github-pr-operations.md](references/github-pr-operations.md). Resolve host, base repository/branch, head repository/branch/OID, existing PR identity, and API actor in the exact process or connector context used for mutation. Check applicable account roles, permissions, repository instructions, and fork relationship. Run independent reads that share one verified context together in a single execution and check each result separately; keep writes, and reads that depend on an earlier result, in order.

The head must already exist remotely with the expected commits. If publication is needed, the calling agent can run `git-push` when authorized, then reread the result. Do not use PR creation to implicitly push, create a fork, or select another head.

## Prepare and Authorize

Before preparing a new PR, check all relevant open PRs for the exact head and base repository and branch. Reuse a unique exact match. Investigate matches with a different base before deciding whether a new PR fits the request. Apply only requested metadata changes to an existing match.

For creation or requested title/body changes, read the applicable repository PR template and contribution rules. Give reviewers the context they need from the actual base-to-head diff, purpose, and checks performed. Preserve required template structure and truthful checklist states. Use only verified issue links, approvals, DCO/CLA declarations, and test results.

For other metadata updates, skip title/body preparation; still inspect the diff or repository rules when needed to validate the requested field changes.

For an update, identify the exact fields and preserve other user-authored content. Base and draft/ready changes are meaningful effects, not incidental cleanup. Existing authorization is reusable for unchanged targets and effects; resolve material ambiguity before writing.

For stacks, read [stack-metadata.md](references/stack-metadata.md). A stack association is metadata; local restack and remote branch publication remain separate operations.

## Execute

Use explicit repository/PR/head/base arguments and prepared literal text. Prefer structured API arguments or a UTF-8 body file. Do not rely on branch inference, automatic fill, shell-expanded multiline strings, or `gh pr create --dry-run` as a read-only preview.

Check that the inspected PR fields and head still match before updating. A concurrent edit requires a fresh comparison; preserve new user content rather than replacing it from an old snapshot. Where the API offers no conditional update, acknowledge the race and minimize the field set.

## Retry and Verify

A read-only query that fails with a transport error such as EOF or a reset connection can be retried once in the same bound context; if it fails again, report that observation as unknown. An authentication rejection or actor mismatch is a result, not a reason to retry. After an error or timeout, look for the created PR or applied fields before retrying. Inspect closed/merged matches when they explain a prior attempt; do not reopen or recreate without the corresponding intent.

Read back the PR URL/ID, author, head/base, changed fields, and stack membership. Use the [reentry rules](references/github-pr-operations.md#reentry) to reconcile each requested update before retrying. Report the verified PR, any intervening edits, and unresolved outcomes.

---
name: git-pr-submit
description: "Create a GitHub pull request from an already published head branch, or maintain its title, body, base, draft state, and stack association. Use for PR creation and metadata updates; publishing code and posting review findings have separate owners."
---

# Git PR Submit

## Responsibility

Create or maintain PR metadata. Branch publication belongs to `git-push`; content review and review discussion to `git-review`; merging to `git-pr-merge`. Clarify an unresolved "update PR" request if code and metadata updates would lead to different writes.

This skill can work without a local checkout when remote evidence is sufficient. For another hosting service, verify equivalent supported operations before acting; never invent GitHub-compatible endpoints.

## Identity and Preconditions

Read [github-pr-operations.md](references/github-pr-operations.md). Resolve host, base repository/branch, head repository/branch/OID, existing PR identity, and API actor in the exact process or connector context used for mutation. Check applicable account roles, permissions, repository instructions, and fork relationship.

The head must already exist remotely with the expected commits. If publication is needed, the calling agent can run `git-push` when authorized, then reread the result. Do not use PR creation to implicitly push, create a fork, or select another head.

## Prepare and Authorize

Choose create or update from the request and current PR state. Read the applicable target repository PR template and contribution rules. Prepare an accurate title/body based on the actual base-to-head diff, purpose, and performed checks. Preserve required template structure and truthful checklist states; do not invent issue links, approvals, DCO/CLA declarations, or test results.

For an update, identify the exact fields and preserve other user-authored content. Base and draft/ready changes are meaningful effects, not incidental cleanup. Existing authorization is reusable for unchanged targets and effects; resolve material ambiguity before writing.

For stacks, read [stack-metadata.md](references/stack-metadata.md). A stack association is metadata; local restack and remote branch publication remain separate operations.

## Execute

Use explicit repository/PR/head/base arguments and prepared literal text. Prefer structured API arguments or a UTF-8 body file. Do not rely on branch inference, automatic fill, shell-expanded multiline strings, or `gh pr create --dry-run` as a read-only preview.

Check that the inspected PR fields and head still match before updating. A concurrent edit requires a fresh comparison; preserve new user content rather than replacing it from an old snapshot. Where the API offers no conditional update, acknowledge the race and minimize the field set.

## Retry and Verify

Before creating, search all relevant open PRs for the exact head repository/branch and base repository/branch. Reuse a unique match; a different base is a decision, not evidence that another PR should be created.

After an error or timeout, look for the created PR or applied fields before retrying. Inspect closed/merged matches when they explain a prior attempt; do not reopen or recreate without the corresponding intent.

Read back the PR URL/ID, author, head/base, changed fields, and stack membership. Report partial metadata updates and leave unrelated fields intact. Return the verified PR and remaining actions; creation does not imply review, merge, or cleanup.

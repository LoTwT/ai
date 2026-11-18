---
name: git-commit
description: "Create a local Git commit from selected changes, draft or validate a commit message, or determine a specific commit's author and committer. Handles staging and verifies the resulting commit."
---

# Git Commit

## Responsibility and Mode

Select **commit**, **message only**, or **identity only** from the request. The latter two are read-only: do not stage or create commits. Message accuracy uses the actual selected diff; rules-only message validation can run without a repository.

For a commit, establish the repository/worktree and select changes from the user's intent. A request to commit the current task can authorize staging clearly attributable task files or hunks within applicable permissions, without a separate staging confirmation. Honor an explicit staged-only or partial selection; do not silently include unrelated work. Inspect first and ask only when a material scope ambiguity remains.

Local synchronization commits and continuation of an existing merge/rebase/cherry-pick/revert belong to `git-workspace`. Remote publishing belongs to `git-push`. Account diagnosis and account-use policy belong to `git-accounts`; identity-only mode answers only which author/committer this commit will use. A request to commit does not imply synchronization or publication.

## Identity

Read [identity.md](references/identity.md) for identity-only mode and before committing. Resolve author and committer separately from the request, applicable user/project instructions, and effective Git state. Validate the selected identity in the same process context used for execution.

Do not assume GitHub login, repository owner, transport actor, and commit identity are equal. Use process-scoped overrides, preserve ordinary hooks/signing, and do not rewrite persistent account configuration. Missing or conflicting identity evidence blocks only the dependent operation.

## Prepare the Selection and Message

Read [selection-and-execution.md](references/selection-and-execution.md) for staging, partial selections, and execution. Preserve the existing index boundary; use literal paths or explicit patches for authorized additions. Run independent local reads, such as status, index, configuration, recent history, and message rules, together in a single execution and check each result separately.

Read [messages.md](references/messages.md) to generate or validate the exact final message. Discover and follow applicable repository message rules; default to Conventional Commits 1.0.0 when none exist, respecting explicit requests and instruction precedence. Describe the actual selected change and report checks truthfully. Message-only mode returns text and validation findings, then stops.

Before the preview, use the [documentation check](references/selection-and-execution.md#documentation-check) to find documents affected by the selected changes. Include required updates within the authorized selection and record the outcome in the preview.

Record the branch, old HEAD (or unborn state), selected index tree, exact final message, identity, and required validation. Check hook, signing, and provenance readiness before the preview and ask once for everything missing. Run checks relevant to the change. A hook or tool changing the selection or message requires review of the changed result before any corrective commit.

## Authorization

Use the [commit preview](references/selection-and-execution.md#commit-preview) with the actual staging, documentation, message, identity, provenance, and validation evidence. For an authorized commit with prerequisites met, proceed from the preview to execution in the same turn. For a preview-only request, stop after the preview.

Creating a normal commit, amending a commit, and rewriting multiple commits are different effects. An ordinary commit request does not authorize amend, an empty commit, hook bypass, or automatic staging of unrelated work. Ask only when the concrete operation exceeds the request or leaves a material choice unresolved.

## Execute

Recheck branch, old HEAD, and index tree immediately before committing. Invoke normal `git commit` once with the prepared message file, without path arguments, `-a`, `--no-verify`, or an implicit amend. Use an argument vector or safe literal shell quoting. Keep credentials and arbitrary message/path bytes out of shell interpolation.

## Retry and Verify

After an error or timeout, inspect HEAD, the commit object, and index before deciding whether a commit occurred. Never repeat blindly or amend merely to repair a reporting mismatch.

Verify the new commit's parent relationship, tree, full message, author/committer, and required signature. Check remaining staged/unstaged work. If a hook changed the actual result, disclose the mismatch and stop dependent publication; do not silently rewrite history.

Return the verified commit OID, message, actual identities, validation, and remaining work. A combined commit-and-push task can continue only after verification, within its existing authorization.

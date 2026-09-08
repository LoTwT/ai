# Conflict and interruption recovery

Read this before resolving, continuing, or aborting an existing operation.

Identify the worktree, operation type, old/current tips, sequencer progress, conflicted files, and user edits since interruption. Use Git's operation metadata and status; do not assume every conflict is a rebase. Git-dir paths may differ in linked worktrees; resolve them with `git rev-parse --git-path`.

For rebase, merge, cherry-pick, or revert, use that operation's own continue/abort mechanism. Do not start an ordinary commit workflow to finish an integration commit.

Inspect base/ours/theirs and intended behavior. During rebase, side labels do not necessarily correspond to the user's intuitive local/remote sides. Resolve when the behavior is sufficiently established; ask only when a real behavior choice or out-of-scope loss remains. Do not blindly select a whole side, skip a commit, or trust a rerere resolution just because markers disappeared.

Preserve user-written resolutions. Inspect the diff and run relevant checks before staging exact resolved paths or hunks. Ensure unrelated staged work will not enter an integration commit. Continuing may reach another conflict; report the new location rather than repeatedly applying a generic resolution.

An abort request should account for edits created after the operation began. Save such work when needed before aborting, under a preservation plan consistent with the request. Abort is not a promise that all new edits survive. If the operation already finished, report that fact instead of resetting as an equivalent "abort."

On retry, determine whether the previous command never ran, is still in progress, completed, or left an unknown result. Inspect state after errors/timeouts. For a partially restacked set, resume only unfinished branches and preserve completed results.

Return the completed/aborted/in-progress state, current branch/tip, retained work, checks, and any remaining conflict or missing decision.

Source: [Git rebase modes](https://git-scm.com/docs/git-rebase).

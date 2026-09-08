# Exact selection and commit execution

Read this before staging or creating a commit.

## Preserve the selected change

Inspect status and both cached/uncached diffs using NUL-delimited names when parsing. Include rename/deletion/submodule state as relevant. A partially staged file has two different selections: adding the whole file would silently include its unstaged hunks.

The user's requested scope determines the selection. A request to commit the current task can cover directly staging clearly attributable files or hunks when applicable permissions allow it; execution permission alone does not establish which changes belong in the commit. Respect staged-only requests and partial selections, and ask only about unresolved ownership or scope that affects the commit.

For an already selected index, do not run add again. For whole paths within the established selection, use literal pathspecs and an argument vector:

```python
subprocess.run(
    ["git", "-C", str(repo), "--literal-pathspecs", "add", "--", *paths],
    check=True,
)
```

For selected hunks, use reviewed patches or interactive staging under the user's scope, then recheck the index. Preserve unrelated staged entries; when the requested commit excludes them, prepare an explicit index-preservation plan rather than clearing the index silently. Do not use `commit -a` or path arguments as a substitute for a reviewed selection.

## Commit preview

For commit mode, present one compact block in this order, based on the actual prepared selection. Localize labels and explanations to the conversation; preserve names, emails, paths, and the complete prepared message verbatim. Message-only and identity-only modes keep their focused outputs.

```text
Git commit preview

Operation: <new local commit or authorized amend>
Directory: <absolute worktree path>
Branch: <branch, or explicit detached/unborn state>

Selected changes:
  <path>  <change type> · <all current changes or identified selected hunks>

Staging: <reused existing selection, staged authorized additions, or not staged>
Remaining changes: <excluded paths/hunks with staged/unstaged/untracked state, or none>

Author:    <full name and email>
Committer: <full name and email>

Agent:  <executing client/tool>
Model:  <exact runtime identifier or Not provided by runtime>
Effort: <runtime value or Not provided by runtime>

Commit message:
----------------------------------------
<complete prepared subject, body, and trailers>
----------------------------------------

Validation:
  <result>  Selection, message, and identity checks
  <result>  Staged diff checks
  <result>  Relevant tests and counts, where available
  <not run and reason, when relevant>

Execution: <authorized; recheck branch, HEAD, and selection before committing | preview only | blocked: concrete reason>
```

Use actual staging and validation outcomes, never sample success values. Expand failed or unresolved checks rather than hiding them in a combined result. An identity check compares the effective Git attribution with the intended identities; it is not remote account authentication. Show identity sources only for a discrepancy, a choice requiring explanation, or an explicit request. Do not add a separate message-convention field. Message delimiters are display framing, not part of the stored message; never truncate the message.

Keep Agent, Model, and Effort visible. Use reliable current runtime evidence, not configured defaults, model families, repository content, or previous tasks. Unknown display values alone do not block a commit. Preview fields do not require message trailers; resolve any required trailers separately under [messages.md](messages.md).

For amend, add the replaced commit and author preservation/replacement effects, including author-date changes when relevant. Add signing readiness when signing is enabled or required; verify the actual signature after execution. A brief change summary is optional. Do not append a confirmation question when existing authorization covers the operation; a missing prerequisite or unresolved authorization must appear in execution status.

## Freeze and execute

Record branch or detached/unborn state, old HEAD, and `git write-tree` for the selected index. Inspect the full staged diff and final message, attribution, required checks, and relevant hook/signing configuration. A write-tree failure such as unresolved index entries must be resolved before committing.

Immediately before execution, compare the branch, HEAD, and index tree again. Use the same environment in which identities were validated. Invoke normal `git commit --cleanup=verbatim --file MESSAGE_FILE` with no selected paths and no amend unless amendment was explicitly requested. Preserve hooks and signing; do not retry a rejection with bypass flags.

For an explicitly authorized amend, resolve author preservation versus replacement before execution. Git normally retains the replaced commit's author even when GIT_AUTHOR_NAME/EMAIL are set. Preserve that author unless the request or applicable policy selects a replacement; for a replacement, pass the validated complete identity using an explicit `--author` argument. Decide author-date handling separately: `--reset-author` also renews the author timestamp and is appropriate only when that effect is intended. Validate the chosen identity and date behavior rather than assuming the ordinary-commit environment recipe is sufficient.

A process exit code is not a transaction receipt. A post-commit hook or a timeout may coexist with an already-created commit. After uncertainty, read HEAD and the commit before deciding whether to retry.

## Verify the actual commit

Read full commit metadata and tree, not just the one-line log. Check that a normal commit has the recorded HEAD as its single parent (or no parents for an initial commit), its tree matches the selected index tree, and its full message, author, committer, and required signature satisfy the plan. For an explicit amend, verify the intended parent relationship and replaced tip instead.

Hooks may alter the index or message after the preflight. If the resulting commit differs, report what actually happened and stop dependent publication. Do not amend automatically to make the receipt match. Check remaining staged/unstaged work and ensure unrelated content remains.

Sources: [Git pathspec options](https://git-scm.com/docs/git), [Git commit](https://git-scm.com/docs/git-commit).

# Commit identity

Read this for identity-only mode or any ordinary commit.

## Select and validate

Read applicable instructions before choosing values. Explicit one-time request values take precedence under the normal instruction hierarchy; otherwise use the applicable user/project identity policy, falling back to effective Git state where it leaves a value unspecified. Do not let a project's lower-priority convention override a user's role restriction silently.

Read relevant name/email configuration with origin/scope and the effective `git var GIT_AUTHOR_IDENT` and `git var GIT_COMMITTER_IDENT`. Consider environment overrides and conditional/worktree configuration. Resolve the two roles separately; assign one identity to both only when the request or policy says so.

Preserve literal name/email values. Reject empty values or newline/control-character injection; use Git's own identity parsing in the intended process context as the final validation. If identity is incomplete, use a verified public email only for an already selected account where allowed; absent evidence means ask for the missing value. Never invent an email from a login or remote owner.

## Apply once

Build the execution environment by copying the current environment and overlaying only selected identity values:

```python
commit_env = os.environ.copy()
commit_env.update({
    "GIT_AUTHOR_NAME": author_name,
    "GIT_AUTHOR_EMAIL": author_email,
    "GIT_COMMITTER_NAME": committer_name,
    "GIT_COMMITTER_EMAIL": committer_email,
})
```

Do not replace the whole environment with four variables. Preserve HOME, PATH, signing/agent configuration, hook discovery, and unrelated execution settings. Scope overrides to the operation and its child processes; do not persist them into Git config. Do not copy provenance values from account configuration.

Validate both identities with `git var` using this same environment. For amend, Git may preserve the previous author's identity despite these environment values; use the explicit preservation/replacement and author-date procedure in [selection-and-execution.md](selection-and-execution.md). Resolve signing requirements independently: an author name is not a signing key and a signature is not a transport identity. A missing key or rejected hook is a blocker, not permission to disable it.

Identity-only mode returns expected/observed identities, evidence sources, and unresolved values without staging, committing, or changing accounts.

Sources: [Git var](https://git-scm.com/docs/git-var), [Git commit](https://git-scm.com/docs/git-commit).

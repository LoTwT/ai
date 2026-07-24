# Safe Commit Execution Reference

Use this reference only after a complete preview has been explicitly confirmed and immediately revalidated.

## Preferred Process API

Send the exact confirmed normalized UTF-8 message bytes, including exactly one terminal LF, through standard input:

```text
argv = ["git", "commit", "--cleanup=verbatim", "--file", "-"]
env = {
  ...current_environment,
  GIT_AUTHOR_NAME: identity.author.name,
  GIT_AUTHOR_EMAIL: identity.author.email,
  GIT_COMMITTER_NAME: identity.committer.name,
  GIT_COMMITTER_EMAIL: identity.committer.email
}

if identity.requires_override:
  argv = [
    "git",
    "-c", "user.name=" + identity.author.name,
    "-c", "user.email=" + identity.author.email,
    ...argv[1:]
  ]

run_process(argv, env, stdin_bytes = normalized_message_bytes)
```

The four environment variables always pin the exact confirmed author and committer attribution for the child process, closing configuration/include races without persisting configuration. For a one-time identity, the `git -c` overlay additionally lets hooks reading `user.name` or `user.email` observe the same process-scoped identity. V1 one-time identities apply one pair to both author and committer.

## Shell-only Fallback

Use a shell command string only when a direct process API is unavailable. Dynamic identity and message values may enter shell source only through independently chosen, collision-checked, quoted heredoc data bodies. A delimiter must not occur as a complete line in its value.

Effective identity:

```bash
author_name=$(cat <<'__AUTHOR_NAME__'
<exact confirmed author name>
__AUTHOR_NAME__
) || exit
author_email=$(cat <<'__AUTHOR_EMAIL__'
<exact confirmed author email>
__AUTHOR_EMAIL__
) || exit
committer_name=$(cat <<'__COMMITTER_NAME__'
<exact confirmed committer name>
__COMMITTER_NAME__
) || exit
committer_email=$(cat <<'__COMMITTER_EMAIL__'
<exact confirmed committer email>
__COMMITTER_EMAIL__
) || exit

GIT_AUTHOR_NAME="$author_name" \
GIT_AUTHOR_EMAIL="$author_email" \
GIT_COMMITTER_NAME="$committer_name" \
GIT_COMMITTER_EMAIL="$committer_email" \
git commit --cleanup=verbatim --file - <<'__COMMIT_MESSAGE__'
<exact normalized message, ending with one LF>
__COMMIT_MESSAGE__
```

One-time identity:

```bash
author_name=$(cat <<'__AUTHOR_NAME__'
<exact round-tripped name>
__AUTHOR_NAME__
) || exit

author_email=$(cat <<'__AUTHOR_EMAIL__'
<exact round-tripped email>
__AUTHOR_EMAIL__
) || exit

GIT_AUTHOR_NAME="$author_name" \
GIT_AUTHOR_EMAIL="$author_email" \
GIT_COMMITTER_NAME="$author_name" \
GIT_COMMITTER_EMAIL="$author_email" \
git -c "user.name=$author_name" \
    -c "user.email=$author_email" \
    commit --cleanup=verbatim --file - <<'__COMMIT_MESSAGE__'
<exact normalized message, ending with one LF>
__COMMIT_MESSAGE__
```

Identity validation rejects embedded newlines. Command substitution removes each identity heredoc terminal LF; the message heredoc supplies its required terminal LF. Generate different delimiters on collision.

## Requirements

- Run exactly one `git commit` per confirmation.
- Never use `eval`, unquoted heredocs, manual escaping of raw user text, or command-string re-evaluation.
- Never add, remove, transcode, or implicitly clean confirmed message bytes.
- Never use `--no-verify` or disable required signing.
- Never persist identity overrides.
- Never directly invoke `git push`.
- Preserve real hook, signing, commitlint, merge-state, and empty-index errors.

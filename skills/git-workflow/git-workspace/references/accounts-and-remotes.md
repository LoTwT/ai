# Account and remote inspection

Read this for account diagnosis and local operations that create commits. For defining or saving selection rules, read [account-policy.md](account-policy.md).

## Discover facts without changing accounts

Use the selected worktree for repository Git queries. Without a checkout, inspect available user-level identity and host authentication, label repository-dependent facts unavailable, and do not invent a repository context. Useful narrow queries include:

```text
git config --show-origin --show-scope --get-all user.name
git config --show-origin --show-scope --get-all user.email
git var GIT_AUTHOR_IDENT
git var GIT_COMMITTER_IDENT
git remote get-url --all REMOTE
git remote get-url --push --all REMOTE
gh auth status --hostname HOST
gh api --hostname HOST user --jq .login
```

These are argument templates, not commands to run with unresolved placeholders. A missing config key is different from a failed query. `git var` observes environment and effective Git configuration, including conditional includes; config output alone does not prove the effective identity. Inspect relevant signing keys/settings separately when signing matters. Avoid full config/environment dumps: credential URLs, headers, helpers, and tokens may be exposed. Redact userinfo and secrets in displayed remote URLs.

Resolve remotes by the request and actual repository topology. Track fetch and push destinations separately, including push URLs and URL rewriting. Do not assume a fork relationship or a base branch from owner/name alone.

## Select the intended identity

Apply explicit request overrides and applicable user/project instructions under their normal precedence. Within the applicable policy, exact repository/operation exceptions override host-specific Git/API defaults; unconfigured commit identity fields fall back to effective Git state. A project cannot silently override a higher-priority role restriction. Distinguish an instruction conflict from a harmless difference between persistent defaults and a selected one-time identity. Use [account-policy.md](account-policy.md) for matching details when needed.

An unspecified remote account is a missing choice, not permission to adopt the active login or repository owner. Present verified candidates and ask only when the choice is needed for the current operation. Keep the answer within its stated task scope unless persistence is requested. Public read-only queries need not trigger login or policy setup; verification reads for a planned write use that operation's selected credential context.

Resolve author and committer independently. A complete one-time identity can cover both when that is the stated policy. Validate the final pair using `git var` in the intended execution environment. Preserve existing authors when replaying commits unless explicitly told otherwise; the new committer may differ.

An email must come from an explicit/effective identity or verified account data for the already selected person. If needed and permitted, query that account's public email; if absent, ask for the missing value. Do not construct a noreply address, select a different account, or infer identity from the remote owner.

## Distinguish API and transport evidence

For GitHub API operations, inspect the authenticated user in the same host-specific process/connector context used for writing. An account listed by `gh auth status` may not be the actor selected by an environment token. Parse actual authentication results, not merely a zero exit status from JSON output.

For SSH, account for the effective host alias, key/agent selection, and Git SSH overrides. A provider's authenticated greeting can identify the accepted key's account, but a repository access probe alone cannot. For HTTPS, identify the credential source selected for the exact URL and verify that credential's actor without printing it. A read succeeds anonymously on a public repository and therefore is not proof of an authenticated writer.

Use existing credential facilities with process-scoped selection. Never echo tokens, request full credential-helper output in the session, accept an unknown host key automatically, or persistently switch the global login as part of inspection. If the actor cannot be proved, mark it unknown; unrelated local operations can continue.

## Result

Report a small table: role, expected identity and instruction source, observed identity and evidence, and status (verified/mismatch/unknown). Do not say an account performed an operation unless it actually did.

Sources: [Git identity variables](https://git-scm.com/docs/git-var), [Git configuration](https://git-scm.com/docs/git-config), [GitHub authentication status](https://cli.github.com/manual/gh_auth_status).

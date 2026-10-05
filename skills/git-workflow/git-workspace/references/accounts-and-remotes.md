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

An unspecified remote account is a missing choice, not permission to adopt the active login or repository owner. Present verified candidates and ask only when the choice is needed for the current operation. Keep the answer within its stated task scope unless persistence is requested. Public read-only queries need not trigger login or policy setup; account-identity probes use the selected actor's credentials.

Resolve author and committer independently. A complete one-time identity can cover both when that is the stated policy. Validate the final pair using `git var` in the intended execution environment. Preserve existing authors when replaying commits unless explicitly told otherwise; the new committer may differ.

An email must come from an explicit/effective identity or verified account data for the already selected person. If needed and permitted, query that account's public email; if absent, ask for the missing value. Do not construct a noreply address, select a different account, or infer identity from the remote owner.

## Bind the selected account to each operation

Apply account selection to authenticated reads as well as writes. Resolve the API and Git transport accounts separately for the exact host, repository, and operation. An active login, repository owner, credential username, or earlier workspace report is not actor evidence. Repository queries and a writer's identity probe may use different accounts under the applicable policy; give each its own context.

Reuse a verified identity context while its selected account, host, target scope, transport, and credential binding remain unchanged and verifiable. Credential setup and actor probes below apply only to a new or invalidated context. Check permissions, protection, and target state as required for the current operation.

For GitHub CLI operations:

1. Capture `gh auth token --hostname HOST --user LOGIN` privately from the existing credential store, using an argument vector. Both selectors are required; ordinary `gh api` and `gh pr` commands have no general acting-account `--user` flag. Reject lookup errors and empty tokens before starting a dependent command; never fall back to the active account.
2. Copy the environment for this operation. Remove inherited `GH_TOKEN`, `GITHUB_TOKEN`, `GH_ENTERPRISE_TOKEN`, and `GITHUB_ENTERPRISE_TOKEN`, then set only the captured token in `GH_TOKEN` for github.com and subdomains of ghe.com, or `GH_ENTERPRISE_TOKEN` for GitHub Enterprise Server. Clear stale `GH_HOST`/`GH_REPO` selectors and pass explicit targets. Do not mutate a shared shell or `os.environ` while other tasks may run.
3. In that environment, run `gh api --hostname HOST user --jq .login` and require a successful response matching LOGIN. Use the same captured token and environment for the actual operation, with an explicit host and repository/API path. Do not re-resolve the active account between verification and execution. If a connector cannot bind both calls to the selected credential, it cannot establish this guarantee.
4. Missing, rejected, expired, or mismatched credentials stop the dependent operation. A new account, host, or credential requires a new verified context. Keep tokens out of arguments, URLs, files, traces, and displayed output; disable credential-bearing debug output in this context.

Never use `gh auth switch`, login/logout, `gh auth setup-git`, or persistent Git configuration as per-operation account selection. Switching back afterward still leaves a race. `GH_CONFIG_DIR` isolates configuration files, not necessarily the system credential store, and is not sufficient account evidence by itself.

## Bind Git transport separately

For HTTPS, verify the selected token's API actor and supply that same captured token through a process-scoped credential facility restricted to the exact destination. Setting `GH_TOKEN` alone does not configure Git authentication. Reset inherited credential helpers for this process (an empty `credential.helper`, followed by only the selected helper); prevent credential persistence and fallback to other helpers, askpass, or interactive login. Exclude competing HTTP credentials, including URL credentials, applicable Authorization headers, and `.netrc`; stop if their precedence cannot be controlled. A helper must refuse other hosts/repositories, and redirects must not change the verified destination. Preserve unrelated hooks, signing, and TLS verification.

For SSH, pin the effective host, user, port, and approved key/certificate set through an operation-scoped SSH configuration or `GIT_SSH_COMMAND`. `-i` alone is insufficient: account for additional IdentityFile/CertificateFile entries and agent keys. Use `IdentitiesOnly=yes` with only the approved identities, and explicitly select the required agent or disable agent use when the chosen key permits it. Set `ControlPath=none` to prevent reuse of a connection authenticated as another account; `ControlMaster=no` alone does not prevent reuse. Restrict authentication to the selected public-key method. Verify the provider's authenticated account with those exact SSH options, then reuse them for Git. Missing or unprovable keys stop the operation; do not fall back to another key, mutate the shared ssh-agent, or bypass host-key verification. A successful public-repository read alone proves neither SSH nor HTTPS actor identity.

Independent projects can use separate credential contexts concurrently. This prevents account-switch races; it does not serialize a shared worktree, branch, or PR. Coordinate overlapping writes separately and retain the operation's OID/head guards.

## Result

Report a small table: role, expected identity and instruction source, observed identity and evidence, and status (verified/mismatch/unknown). Do not say an account performed an operation unless it actually did.

Sources: [Git identity variables](https://git-scm.com/docs/git-var), [Git credentials](https://git-scm.com/docs/gitcredentials), [GitHub account token](https://cli.github.com/manual/gh_auth_token), [GitHub CLI environment](https://cli.github.com/manual/gh_help_environment), [OpenSSH identity selection](https://man.openbsd.org/ssh_config).

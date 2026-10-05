# Remote deletion and pruning

Read this for remote task-branch removal or stale-ref pruning.

## Remote branch deletion

Resolve the exact host/repository and full branch ref. Inspect the effective push URLs with `git remote get-url --push --all`, URL rewriting, remote groups, and mirror configuration. A named remote can write to multiple repositories. Bind DESTINATION to one verified endpoint, or require authorization and separate checks for every endpoint; never let the same branch/OID match authorize deletion in another repository. Display only sanitized URLs.

Resolve the Git transport actor and API query actor separately under applicable policy. Bind authenticated reads, including remote prune queries, as well as deletion; repository ownership and active login are not actor evidence.

Reuse a verified identity context while its selected account, host, target scope, transport, and credential binding remain unchanged and verifiable. Credential setup and actor probes below apply only to a new or invalidated context. Check permissions, protection, and target state as required for the current operation.

For GitHub credentials, privately capture `gh auth token --hostname HOST --user LOGIN`, rejecting errors and empty output. Copy the operation environment, remove inherited `GH_TOKEN`, `GITHUB_TOKEN`, `GH_ENTERPRISE_TOKEN`, and `GITHUB_ENTERPRISE_TOKEN`, then bind the captured token through `GH_TOKEN` for github.com and subdomains of ghe.com or `GH_ENTERPRISE_TOKEN` for Enterprise Server. Clear stale `GH_HOST`/`GH_REPO` selectors and use explicit targets. Require `gh api --hostname HOST user --jq .login` to succeed and match LOGIN; reuse that exact token for execution. Different query/deletion accounts need separate contexts; connectors must provide equivalent binding. Any lookup/authentication/mismatch failure stops dependent work without fallback to another account.

For HTTPS Git, supply that verified token through a process-scoped helper restricted to the exact destination. `GH_TOKEN` alone does not select Git credentials. Reset inherited `credential.helper` entries with an empty value, then add only the selected helper; prevent persistent credential writes and other helper, askpass, or interactive fallback. Exclude competing HTTP credentials, including URL credentials, applicable Authorization headers, and `.netrc`; stop if their precedence cannot be controlled. Prevent redirects to a different destination. Preserve unrelated hooks, signing, and TLS verification.

For SSH, bind the effective host/user/port and only the approved key/certificate set through operation-scoped SSH options. `-i` alone does not exclude other configured or agent identities: use `IdentitiesOnly=yes` and explicitly select the required agent or disable agent use when the key permits it. Set `ControlPath=none` to prevent reusing another account's shared connection; `ControlMaster=no` alone is insufficient. Restrict authentication to the selected public-key method. Verify the provider account with those same options and reuse them for Git. Do not mutate a shared ssh-agent or bypass host-key verification. Missing or unprovable keys stop the operation.

Do not mutate shared environment/configuration, switch persistent logins, run `gh auth setup-git`, or treat `GH_CONFIG_DIR` alone as credential isolation. Keep tokens out of arguments, URLs, files, logs, and credential-bearing traces. A successful public-repository read alone does not establish either transport actor.

Verify authorization, default/protected status, current remote OID, integration evidence, and complete relevant open PR head/base dependencies, stack membership, and known active tasks. Use the API actor required for these queries; inability to establish dependency completeness means retain.

Delete only the observed ref under its explicit expected OID:

```text
git push --porcelain --no-follow-tags --recurse-submodules=no --force-with-lease=refs/heads/TARGET:OLD_OID DESTINATION :refs/heads/TARGET
```

Keep the original expectation. Never use unconditional REST ref deletion or refresh a failed lease automatically. Query the ref after success/error/timeout: absence is observed completion; advancement or recreation requires reassessment. A SHA condition cannot prevent another PR being created concurrently; coordinate shared work and report this limit rather than promising a transaction over refs and PRs.

## Prune safety

Inspect every fetch mapping and prune/tag setting, then the proposed deletion set. Prune follows refspec destinations: it can remove local heads or tags, not just remote-tracking refs. A remote with no tag mapping is not thereby safe.

For routine tracking cleanup, require positive destinations to stay within that remote's `refs/remotes/REMOTE/` namespace and confirm the complete stale set. Retain anything overlapping another remote, local heads/tags, protected refs, or known active dependencies. Nonstandard mappings require a separate exact plan; do not run a broad prune merely because its name sounds harmless.

Use `git remote prune --dry-run REMOTE` only after confirming its target semantics. Re-read configuration, remote state, and candidate OIDs before execution. Prefer individual `git update-ref -d REF OLD_OID` removals for a verified stale set when a batch prune cannot preserve the authorized set under concurrent changes. Never interpret a partial listing as proof of completeness.

For worktree administrative pruning, use the local-resources procedure; do not confuse it with directory removal.

Verify each deleted ref and retained namespace afterward. Report absent, retained, failed, and unknown outcomes separately.

Sources: [Git remote prune](https://git-scm.com/docs/git-remote), [Git fetch pruning](https://git-scm.com/docs/git-fetch), [Git update-ref](https://git-scm.com/docs/git-update-ref), [Git credentials](https://git-scm.com/docs/gitcredentials), [GitHub account token](https://cli.github.com/manual/gh_auth_token), [GitHub CLI environment](https://cli.github.com/manual/gh_help_environment), [OpenSSH identity selection](https://man.openbsd.org/ssh_config).

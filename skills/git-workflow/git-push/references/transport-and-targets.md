# Push identity and destinations

Read this before remote branch publication.

Resolve the source repository and branch/OID, target host/repository, and full destination ref from explicit intent, applicable policy, and actual topology. Fetch remote, push remote, upstream, and base repository can differ.

Inspect `remote get-url --push --all`, push URLs, URL rewriting, `remote.*.push`, mirror, follow-tags, recursive submodule pushes, and relevant hooks/options. Multiple destinations require explicit scope; do not let a remote group or alias fan out the operation. Display only sanitized URLs.

Choose the required transport account from applicable role policy, separately from API queries and commit attribution. Bind every authenticated read/write to its selected account; reads and writes can require different contexts. Never switch a shared login and switch it back afterward.

Reuse a verified identity context while its selected account, host, target scope, transport, and credential binding remain unchanged and verifiable. Credential setup and actor probes below apply only to a new or invalidated context. Check permissions, protection, and target state as required for the current operation.

For SSH, pin the effective host/user/port and approved key/certificate set in operation-scoped SSH options. `-i` alone does not exclude other configured or agent identities. Use `IdentitiesOnly=yes` with only the approved identities and an explicitly selected agent (or no agent when the key permits it). Set `ControlPath=none` to exclude shared connections authenticated as another account; `ControlMaster=no` alone still permits reuse. Restrict authentication to the selected public-key method. Verify the provider's authenticated account using exactly those options, then reuse them for Git. Do not mutate the shared ssh-agent or fall back to another key. Preserve host-key verification and required signing. A public-repository read is not proof of the actor.

For HTTPS with GitHub CLI-managed credentials, capture `gh auth token --hostname HOST --user LOGIN` privately, rejecting errors or empty output. Copy the process environment, remove inherited GitHub token variables, and bind the captured token through `GH_TOKEN` (github.com and subdomains of ghe.com) or `GH_ENTERPRISE_TOKEN` (Enterprise Server). Clear stale `GH_HOST`/`GH_REPO` selectors and use explicit targets. Verify LOGIN using `gh api --hostname HOST user --jq .login` in that context; keep the same token for execution rather than resolving the active login again. Missing, rejected, expired, or mismatched credentials stop the operation without account fallback. A connector must provide equivalent credential binding and actor evidence.

Bind that exact token to Git through a process-scoped credential facility restricted to the verified destination. `GH_TOKEN` alone does not select Git's credential. Reset inherited credential helpers with an empty `credential.helper`, then add only the selected helper; do not persist its `store`/`erase` requests or allow another helper, askpass, or interactive login as fallback. Exclude competing HTTP credentials, including URL credentials, applicable Authorization headers, and `.netrc`; stop if their precedence cannot be controlled. Prevent redirects to a different destination. Preserve unrelated hooks, signing, and TLS verification. Never print tokens or place them in URLs, arguments, logs, or persistent config; disable credential-bearing tracing. Do not alter shared environment/configuration, run `gh auth switch`/`setup-git`, or treat `GH_CONFIG_DIR` alone as credential isolation.

The observed API user is evidence for Git only when the exact verified credential is bound to the HTTPS transport. Git author/committer and the remote's owner do not prove either actor. If a connector/tool cannot expose enough evidence to identify its writing account, report that limitation before writing.

Read repository/branch restrictions and access using the appropriate verified context. Do not invite collaborators, broaden token scopes, fork, or bypass protection as incidental setup. Preserve normal authentication prompts/signing policy where authorized; do not bypass rejected host-key checks.

Pass the verified destination and actor evidence to guarded publication. Revalidate them when the destination or credential context changes.

Sources: [Git credentials](https://git-scm.com/docs/gitcredentials), [GitHub account token](https://cli.github.com/manual/gh_auth_token), [GitHub CLI environment](https://cli.github.com/manual/gh_help_environment), [OpenSSH identity selection](https://man.openbsd.org/ssh_config).

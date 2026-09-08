# Push identity and destinations

Read this before remote branch publication.

Resolve the source repository and branch/OID, target host/repository, and full destination ref from explicit intent, applicable policy, and actual topology. Fetch remote, push remote, upstream, and base repository can differ.

Inspect `remote get-url --push --all`, push URLs, URL rewriting, `remote.*.push`, mirror, follow-tags, recursive submodule pushes, and relevant hooks/options. Multiple destinations require explicit scope; do not let a remote group or alias fan out the operation. Display only sanitized URLs.

Choose the required transport account from applicable role policy. For SSH, establish which host alias and identity/key the Git transport will actually use, including environment overrides and SSH agent behavior. Match authenticated provider evidence to that account. A successful read of a public repository does not prove writer identity.

For HTTPS, use an existing isolated credential facility whose credential is verified against the target host. If using a GitHub CLI-managed account, capture the selected credential privately into a process context, verify the API user there, and ensure Git uses that same credential instead of an unrelated helper. Never print a token or place it in a URL, command argument, log, or persistent config. Do not globally switch accounts.

The observed API user is evidence for Git only when the exact verified credential is bound to the HTTPS transport. Git author/committer and the remote's owner do not prove either actor. If a connector/tool cannot expose enough evidence to identify its writing account, report that limitation before writing.

Read repository/branch restrictions and access using the appropriate verified context. Do not invite collaborators, broaden token scopes, fork, or bypass protection as incidental setup. Preserve normal authentication prompts/signing policy where authorized; do not bypass rejected host-key checks.

Pass the verified destination and actor evidence to guarded publication. Revalidate them when the destination or credential context changes.

Sources: [Git credentials](https://git-scm.com/docs/gitcredentials), [GitHub CLI environment](https://cli.github.com/manual/gh_help_environment).

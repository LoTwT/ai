# Account-use policy

Read this to define or resolve account-selection rules. Policy selects identities; authentication and authorization remain separate. Do not prescribe a human/agent or repository-owner role matrix.

## Minimal configuration

Use ordinary Markdown in applicable agent instructions, usually AGENTS.md. This is a recommended format, not a parser schema; accept equivalent unambiguous prose.

| Setting | Value and scope |
|---|---|
| New commit author | Complete name and email for ordinary new commits |
| Commit committer | Complete name and email for commits the operation creates or rewrites |
| Default Git account | Account login on an explicit host, for authenticated Git transport |
| Default API account | Account login on an explicit host, for platform API operations |

Resolve author/committer and Git/API accounts separately, even when values coincide. Configure only needed hosts. A login does not supply a commit email.

Optional exceptions specify an **exact target repository, operation, and account**:

| Operation | Account kind | Target |
|---|---|---|
| Authenticated Git read, including fetch | Git | Repository actually accessed |
| Authenticated API read | API | Repository actually queried |
| Push | Git | Actual destination repository |
| PR creation or PR metadata update | API | PR base repository |
| Review publication, including comments and formal reviews | API | PR base repository |
| PR merge | API | PR base repository |
| Remote branch deletion | Git | Actual destination repository |

List PR creation and update separately when only one differs; name specific review events when needed. PR reads target the base repository. Verification reads and account probes for a planned write use that write's selected account, not an unrelated read exception.

The following is a fictional example, not a default to install:

```markdown
## Git account policy

- Default new commit author: Developer <dev@example.com>.
- Default commit committer: Developer <dev@example.com>.
- On github.com, use developer-account for Git transport.
- On github.com, use developer-account for platform API operations.
- Exception: for PR creation and PR metadata updates whose base repository is
  github.com/example/project, use API account contributor-account.
- Within applicable instruction precedence, exact repository-and-operation
  exceptions override host defaults. Unlisted operations use their host default.
- Keep explicit temporary choices within their stated scope. Use effective Git
  identity for unspecified commit fields; ask for an unspecified remote account
  when needed. Do not guess between conflicting applicable selections.
- Preserve existing authors when replaying commits. These account choices do
  not grant permission to perform operations or replace authentication checks.
```

## Select without ambiguity

1. Follow instruction precedence and explicit request choices within their stated roles, targets, and duration. Exceptions cannot bypass higher-priority restrictions; temporary choices are not saved implicitly.
2. Match the actual host/repository after resolving URL rewriting and SSH aliases. Remote names, directories, and logins are not repository identities. Do not invent fork relationships or owner-based wildcards.
3. Within applicable policy, use the operation exception, then the host default for the required account kind. Unresolved conflicts require a choice, not row-order precedence. Never borrow another host's default.
4. Unspecified commit fields use effective Git identity. Preserve replayed authors; amend follows the requested preservation/replacement decision. Validate identity values and signing separately.
5. For a missing remote selection, present verified candidates and ask only for the needed choice. Reuse answers within their stated scope. An active login is not an implicit preference; public read-only work needs no setup.
6. Verify the actor using [accounts-and-remotes.md](accounts-and-remotes.md). Missing credentials, mismatches, or insufficient permissions block only dependent work; do not substitute another account.

## Configure on demand

- Reuse complete existing policy without a first-run marker. Diagnosis alone does not authorize saving rules. Resolve only missing choices needed for the request; user-wide defaults need no checkout, while repository exceptions need an explicit target.
- Use the requested instruction file/scope, otherwise identify the agent's actual user-level entrypoint or applicable project file. Follow existing shared-file references and check overrides. Do not assume a universal home-directory path or duplicate an already loaded policy.
- When saving is requested, prepare the exact diff and apply it within that authorization without repeated confirmation. Preserve unrelated instructions and concurrent edits. Save only selected policy, never credentials or inferred assignments. Do not install credentials or persistently switch logins.
- Reread the saved section and resolve representative operations to check defaults, exceptions, and conflicts. Verify the loading entrypoint. If proving future loading requires a fresh task, report that as unverified; file existence alone does not prove it.

Report policy location/scope, selections, unresolved choices, and loading evidence separately from authentication readiness. Saved policy may still need login; login may still lack repository access. On retry, reconcile existing content before updating; do not duplicate sections or overwrite intervening edits.

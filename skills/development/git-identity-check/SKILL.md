---
name: git-identity-check
description: "Read and validate the Git author and committer identity selected from the current request, applicable user/project instructions, or effective Git state; resolve a missing local Git email from a selected local GitHub account's public profile; or validate one complete process-scoped identity without modifying configuration or creating a commit. Trigger for requests such as 'check my Git identity', 'which identity will this commit use', 'check author and committer', '检查当前 Git identity', or '当前仓库会用谁提交'. This skill may perform narrow read-only GitHub account discovery and public-profile lookup; it never switches accounts, inspects credentials, commits, pushes, or selects a remote actor."
---

# Git Identity Check Skill

Resolve and validate the author and committer attribution for the current repository. This skill is read-only: it never changes Git configuration, creates a commit, switches an account, or handles push credentials.

## Scope and Identity Model

This skill handles only:

```text
author name and email
committer name and email
identity selection basis and its applicable instruction source
selected local GitHub account and public email, only as a missing-email fallback
```

Git commit attribution is separate from GitHub login, tokens, SSH keys, HTTPS credentials, push/API actor, and pull-request actor. A selected local GitHub account may supply a public email when no intentional local Git email exists, but this never proves which account will push or receive API attribution.

V1 supports three identity modes:

1. **Effective identity**: the final author and committer Git resolves for the repository.
2. **GitHub public-email fallback**: effective local author/committer names combined with the selected local GitHub account's non-empty public email through a process-scoped override.
3. **Explicit one-time identity**: one complete `Name <email>` pair designated by the current request or an applicable instruction and applied to both author and committer through a process-scoped override.

V1 does not resolve aliases, infer identity from a remote owner, request private-email scopes, invent noreply addresses, or separately select author and committer.

## Workflow Summary

```text
resolve repository
→ discover applicable identity directives and requirements
→ select identity mode and basis
   ├─ request- or instruction-designated one-time identity: validate override directly
   └─ effective identity: resolve values and verify explicit sources
      └─ email missing or only synthesized: select a local GitHub account and query its public email
→ compare selected identity with applicable identity requirements
→ explain author/committer differences
→ return one logical result
```

## Step 1: Resolve Repository Context

```bash
git rev-parse --show-toplevel
```

If the current directory is not in a Git repository, return `invalid` with the relevant Git error. Record the root and use it for all later checks; do not inspect an unrelated repository as a substitute.

## Step 2: Discover Applicable Identity Directives and Requirements

Use the applicable instruction context already supplied for the task, including user-level/global and project-level instructions. Then read only likely repository sources such as `CLAUDE.md`, `AGENTS.md`, `CONTRIBUTING*`, `README.md`, and repository-specific development or agent identity documentation. Do not scan unrelated home-directory files or assume the repository-local `AGENTS.md` is the only applicable instruction source.

Classify and retain every normative statement with its exact source:

- An **identity directive** designates one complete author/committer identity for the current operation or agent role.
- An **identity requirement** constrains the selected identity without necessarily selecting one.
- A GitHub account-role, push, PR, review, or merge statement is not a Git identity directive unless it also gives a complete `Name <email>` pair and explicitly applies it to commit attribution.

Apply normal instruction authority and scope. Subject to higher-priority instructions, a complete identity explicitly supplied in the current request takes precedence over defaults. Among applicable instruction directives, use the highest-precedence, most-specific directive. Equal-precedence directives that select different identities are `invalid`. A broader default superseded by a more-specific directive is not a conflict.

General examples are not directives or requirements unless the source makes them normative for this operation. Retain superseded defaults for explanation, but compare the selected identity only with requirements that remain applicable.

## Step 3: Select Identity Mode and Basis

Use this order:

1. A complete one-time identity explicitly supplied in the current request.
2. A complete identity selected by the highest-precedence applicable instruction directive.
3. The effective Git identity.

For the first two cases, validate the selected one-time identity directly. Do **not** require the existing effective identity to be valid or read it merely to choose between identities. This allows an applicable Agent identity directive to coexist with a different persistent human Git configuration.

A valid v1 input contains:

- One non-empty name.
- One non-empty email.
- No NUL or newline characters.
- No unresolved alias or profile lookup.

A login, alias, or name without an email is incomplete. Return `invalid` and request the missing complete name/email; never fall back to the effective identity after a selected request- or instruction-designated override fails.

Validate the proposed values through Git by running both commands with all four identity variables supplied to the child processes:

```text
GIT_AUTHOR_NAME=<name>
GIT_AUTHOR_EMAIL=<email>
GIT_COMMITTER_NAME=<name>
GIT_COMMITTER_EMAIL=<email>

git var GIT_AUTHOR_IDENT
git var GIT_COMMITTER_IDENT
```

Pass values through a process environment API or an equivalently data-safe mechanism; never interpolate raw identity text into shell source. The environment is child-process scoped and must not modify configuration or persist in the session.

Parse name/email and ignore timestamp/timezone. Return a selected identity only if both commands succeed and both parsed identities exactly equal the supplied values. If Git removes or normalizes characters, return `invalid`, show the input and safely parsed values, and request a corrected identity.

A valid one-time identity has:

```yaml
source: explicit one-time identity
selection_basis: current request | applicable instruction
instruction_source: <exact source when selected by an instruction>
requires_override: true
config_overrides:
  - -c
  - user.name=<name>
  - -c
  - user.email=<email>
```

Retain the exact instruction source when `selection_basis` is `applicable instruction`. Do not copy account names or identity values from this skill itself; the values must come from the current request or actually applicable instructions.

### No explicit one-time identity selected

First resolve Git's effective values:

```bash
git var GIT_AUTHOR_IDENT
git var GIT_COMMITTER_IDENT
```

These commands are authoritative for final values and account for environment variables, configuration precedence, `includeIf`, and Git fallback behavior. Do not recreate precedence manually.

If either `git var` command fails specifically because email is absent, resolve the names without guessing by rerunning both commands with only temporary child-process email variables set to a reserved `.invalid` probe address:

```text
GIT_AUTHOR_EMAIL=identity-probe@example.invalid
GIT_COMMITTER_EMAIL=identity-probe@example.invalid

git var GIT_AUTHOR_IDENT
git var GIT_COMMITTER_IDENT
```

Use this probe only to obtain Git's effective names; discard its emails immediately and never display or retain them as selected identity values. Each parsed name must still have a compatible intentional explicit source from the narrow configuration/environment checks below. Preserve any original Git error that motivated the probe.

Then verify that every required field has an intentional explicit source rather than Git's operating-system username/hostname fallback.

Use one narrow origin-preserving query when supported:

```bash
git config --show-origin --get-regexp '^(author|committer)\.(name|email)$|^user\.(name|email|useConfigOnly)$'
```

A no-match exit is acceptable. If necessary, use equivalent narrow reads for only these keys. `user.useConfigOnly` is diagnostic policy, not an identity source:

- Never count it as an explicit source for a name or email.
- When it is `true` and `git var` fails because identity configuration is incomplete, report that Git requires explicitly configured identity fields.
- When it is `false` or unset, Git may synthesize fallback values; those values remain invalid unless every field has a compatible explicit source or the missing email is resolved by the public-email fallback below.

Check only whether these relevant environment variables contain non-empty values:

```text
GIT_AUTHOR_NAME
GIT_AUTHOR_EMAIL
GIT_COMMITTER_NAME
GIT_COMMITTER_EMAIL
EMAIL
```

Never enumerate the whole environment or broad configuration namespaces.

Allowed explicit sources:

| Field | Source |
|---|---|
| Author name | `GIT_AUTHOR_NAME`, `author.name`, or `user.name` |
| Author email | `GIT_AUTHOR_EMAIL`, `author.email`, `user.email`, or `EMAIL` |
| Committer name | `GIT_COMMITTER_NAME`, `committer.name`, or `user.name` |
| Committer email | `GIT_COMMITTER_EMAIL`, `committer.email`, `user.email`, or `EMAIL` |

A source is compatible when its non-empty value exactly equals the corresponding name/email parsed from `git var`. This establishes that an explicit source exists; when identical values occur at several levels, it does not claim which identical source won Git's precedence.

If both `git var` commands succeed and all four fields have compatible explicit sources, return:

```yaml
source: effective Git identity
selection_basis: effective Git state
requires_override: false
```

If a name is missing, malformed, synthesized without a compatible explicit source, or otherwise unresolved, return `invalid`. The GitHub fallback resolves email only and must never guess a name.

### Missing local email: selected GitHub account public-email fallback

Use this fallback only when the author and committer names are intentional explicit local values, but one or both emails are absent or are Git-synthesized values without compatible explicit email sources. Do not perform a GitHub lookup when compatible explicit local emails already exist.

1. Discover authenticated local GitHub accounts with a narrow, read-only query:

   ```bash
   gh auth status --json hosts --jq '.hosts | to_entries | map(.key as $hostname | .value[] | select(.state == "success") | {hostname: $hostname, login: .login, active: .active})'
   ```

   Parse only this filtered hostname, login, active, and successful authentication state. Never print tokens, token sources, scopes, or unrelated credential data.

2. Select the account:

   - If the current request already selected one discovered hostname/login pair, or an applicable instruction designates one for this fallback, retain it.
   - If exactly one eligible account exists, select it.
   - If several eligible accounts exist, ask the user to choose; do not silently prefer the active or global account.
   - If none exists or `gh` is unavailable, return `invalid` and request a complete email.

3. Query the selected account's public profile, bound to its hostname and login rather than the ambient account:

   ```bash
   gh api --hostname <hostname> users/<url-encoded-login> --jq .email
   ```

   The endpoint is public, so the selected login—not the credential used for rate limits—is the lookup identity. `gh api --hostname` may authenticate as the active account for that host, but it must request only `GET /users/<selected-login>` and must not access viewer-specific or private fields. Do not call `gh auth switch`.

   This lookup is read-only. Accept only a non-empty string from the public `email` field. A null, empty, malformed, or failed response is `invalid`; request a complete email. Never request private-email scopes, query private email endpoints, or synthesize a GitHub noreply address.

4. Preserve any compatible explicit author or committer email. Use the public email only for each email field that was absent or lacked a compatible explicit source.

5. Validate the complete proposed author and committer identities by running both `git var` commands with all four selected values supplied through child-process environment variables. Require both parsed identities to round-trip exactly. The override is process-scoped and must not modify Git configuration.

A valid fallback result has:

```yaml
source: selected GitHub account public email
selection_basis: effective Git state with public-email fallback
requires_override: true
config_overrides:
  - -c
  - user.email=<public-email>
selected_github_account:
  hostname: <hostname>
  login: <login>
  selection: <current request | applicable instruction | sole eligible local account>
public_email: <email>
email_override_fields: <author, committer, or both>
```

Retain the selected account and lookup source for confirmation, but never claim it is the account that will later push or receive API attribution.

## Step 4: Compare with Applicable Identity Requirements

For a complete exact requirement:

- Exact match: continue as `resolved`.
- Mismatch: return `invalid` with expected and actual values.
- Conflicting exact requirements: return `invalid` with each requirement and source; never choose one.

For an applicable normative requirement v1 cannot evaluate exactly, such as an email-domain pattern or conditional role rule:

- Record it under `unresolved_identity_requirements` with its exact source.
- If the selected identity clearly violates it, return `invalid`.
- Otherwise retain the identity as `resolved`, add `requires_user_decision: true`, and state that policy compliance is unverified.

When independent, ask whether to accept the unverified policy for this inspection. If accepted, preserve:

```yaml
policy_compliance: unverified
user_accepted_unverified_requirement: true
requires_user_decision: false
```

Acceptance does not mean the requirement was satisfied; retain the warning in the final result.

When followed by `git-commit`, do not ask separately. Return `requires_user_decision: true`; the orchestrator must obtain a specific proceed/cancel decision before its final commit preview.

## Step 5: Handle Different Author and Committer Identities

Git permits author and committer to differ. Always display both.

Return `resolved` when both are complete, every field is explicitly sourced, the difference is explainable from the narrow relevant sources, and no applicable identity requirement forbids it.

Return `invalid` when either identity is incomplete, the difference cannot be explained, or the values violate a requirement. Never rewrite them to match automatically.

## Result Contract

| Situation | State | Required data |
|---|---|---|
| Complete effective identity, every field explicitly sourced, requirements satisfied | `resolved` | author, committer, source, selection basis, `requires_override: false` |
| Intentional local names with missing local email, selected account has a non-empty public email, requirements satisfied | `resolved` | author, committer, source, identity selection basis, selected account and its selection basis, public email source, overridden fields, `requires_override: true` |
| Complete request- or instruction-designated one-time identity round-trips unchanged and satisfies requirements | `resolved` | author, committer, source, selection basis, instruction source when used, `requires_override: true` |
| Several eligible local GitHub accounts and none selected | `selection_required` | eligible hostname/login pairs; no credential details |
| Missing field, name fallback, malformed override, unavailable/null public email, unexplained difference, or requirement conflict | `invalid` | reason, safe actual values, expected/missing/corrective input |
| Identity otherwise valid but normative compliance cannot be decided | `resolved` plus `requires_user_decision: true` | unresolved requirements and unverified-policy warning |
| User accepts an unresolved policy in standalone mode | `resolved` | retained warning, `policy_compliance: unverified`, acceptance marker |

These are logical coordination states, not runtime-enforced schema values.

## Interaction Rules

When independent:

- Report repository, author, committer, mode, selection basis, applicable instruction source when used, validity, selected GitHub account/public-email source when used, and unresolved policy status.
- If account selection is required, show only eligible hostname/login pairs and ask the user to choose.
- If invalid, ask only for the missing complete identity or identify the conflict.
- Do not offer to modify configuration unless the user separately requests it.
- Do not imply that inspection, public-email lookup, or one-time validation creates a commit.

When followed by `git-commit`:

- Return the logical result without a separate confirmation flow.
- Return the exact resolved author, committer, source, selection basis, applicable instruction source when used, override mode, selected GitHub account/public-email source when used, and unresolved policy status for binding into the commit confirmation snapshot.
- Require `git-commit` to display both resolved identities and their source/mode in its final preview, even when author and committer are identical.
- Let `git-commit` own policy decisions, the combined message-and-identity confirmation, process-scoped override, execution, and reporting.

## Constraints

- Never modify Git configuration, GitHub authentication, or persistent environment variables.
- Enumerate only the narrow read-only hostname/login account data needed for missing-email selection; never inspect or print tokens, scopes, credential sources, or unrelated account data.
- Never accept Git's automatic OS user/hostname fallback as an intentional name or email.
- Never infer identity from a remote owner, a GitHub login, or an account-role table that does not explicitly designate a complete commit identity; never invent a noreply email or equate the selected account with a push/API actor.
- Never inspect collaborator access or choose push, pull-request, reviewer, or merge actors; those belong to a later remote workflow.
- Never query private email endpoints or request additional scopes merely to resolve commit attribution.
- Never print tokens, credentials, signing-key material, or unrelated values.
- Never silently recover from an invalid explicit identity by selecting another identity.
- Never interpolate identity values into shell source.
- Never run `git add`, `git commit`, `git push`, `gh auth switch`, or `gh auth logout`.

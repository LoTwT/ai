---
name: git-identity-check
description: "Read and validate the Git author and committer identity selected for the current repository or validate one complete, explicit one-time identity without modifying configuration or creating a commit. Trigger for requests such as 'check my Git identity', 'which identity will this commit use', 'check author and committer', '检查当前 Git identity', or '当前仓库会用谁提交'. This v1 skill resolves commit attribution only; it does not discover profiles, switch GitHub accounts, inspect credentials, commit, or push."
---

# Git Identity Check Skill

Resolve and validate the author and committer attribution for the current repository. This skill is read-only: it never changes Git configuration, creates a commit, switches an account, or handles push credentials.

## Scope and Identity Model

This skill handles only:

```text
author name and email
committer name and email
```

Git commit attribution is separate from GitHub login, tokens, SSH keys, HTTPS credentials, push/API actor, and pull-request actor. Never claim that a commit identity proves which GitHub account will push or receive API attribution.

V1 supports two identity modes:

1. **Effective identity**: the final author and committer Git resolves for the repository.
2. **Explicit one-time identity**: one complete `Name <email>` pair applied to both author and committer through a process-scoped override.

V1 does not enumerate identity profiles or local accounts, resolve aliases, infer identity from a remote owner, or separately select author and committer.

## Workflow Summary

```text
resolve repository
→ discover repository identity requirements
→ select identity mode
   ├─ explicit one-time identity: validate override directly
   └─ effective identity: resolve values and verify explicit sources
→ compare selected identity with repository requirements
→ explain author/committer differences
→ return one logical result
```

## Step 1: Resolve Repository Context

```bash
git rev-parse --show-toplevel
```

If the current directory is not in a Git repository, return `invalid` with the relevant Git error. Record the root and use it for all later checks; do not inspect an unrelated repository as a substitute.

## Step 2: Discover Repository Identity Requirements

Read only likely sources such as `CLAUDE.md`, `AGENTS.md`, `CONTRIBUTING*`, `README.md`, and repository-specific development or agent identity documentation.

Record normative author/committer requirements and their sources. General examples are not requirements unless the document makes them normative for this repository and operation. Classification occurs after an identity has been selected.

## Step 3: Select Identity Mode

### Explicit one-time identity supplied

If the user supplies a one-time identity, validate it directly. Do **not** require the existing effective identity to be valid first.

A valid v1 input contains:

- One non-empty name.
- One non-empty email.
- No NUL or newline characters.
- No unresolved alias or profile lookup.

A login, alias, or name without an email is incomplete. Return `invalid` and request the missing complete name/email; never fall back to the effective identity after an explicit override fails.

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
requires_override: true
```

### No explicit identity supplied

Resolve Git's effective values:

```bash
git var GIT_AUTHOR_IDENT
git var GIT_COMMITTER_IDENT
```

These commands are authoritative for final values and account for environment variables, configuration precedence, `includeIf`, and Git fallback behavior. Do not recreate precedence manually.

If either command fails, preserve the key Git error. Use the narrow relevant configuration read below to determine whether `user.useConfigOnly=true` explains an incomplete-identity failure, then return `invalid`. If either parsed identity lacks a non-empty name/email, return `invalid` with the missing field.

Then verify that every required field has an intentional explicit source rather than Git's operating-system username/hostname fallback.

Use one narrow origin-preserving query when supported:

```bash
git config --show-origin --get-regexp '^(author|committer)\.(name|email)$|^user\.(name|email|useConfigOnly)$'
```

A no-match exit is acceptable. If necessary, use equivalent narrow reads for only these keys. `user.useConfigOnly` is diagnostic policy, not an identity source:

- Never count it as an explicit source for a name or email.
- When it is `true` and `git var` fails because identity configuration is incomplete, report that Git requires explicitly configured identity fields.
- When it is `false` or unset, Git may synthesize fallback values; those values remain invalid unless every field has a compatible explicit source.

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

If any field lacks a compatible explicit source, return `invalid`, report the effective values with `source: auto-detected by Git`, and do not present them as safe attribution.

A valid effective identity has:

```yaml
source: effective Git identity
requires_override: false
```

## Step 4: Compare with Repository Requirements

For a complete exact requirement:

- Exact match: continue as `resolved`.
- Mismatch: return `invalid` with expected and actual values.
- Conflicting exact requirements: return `invalid` with each requirement and source; never choose one.

For a normative requirement v1 cannot evaluate exactly, such as an email-domain pattern or conditional role rule:

- Record it under `unresolved_repository_requirements`.
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

Return `resolved` when both are complete, every field is explicitly sourced, the difference is explainable from the narrow relevant sources, and no repository requirement forbids it.

Return `invalid` when either identity is incomplete, the difference cannot be explained, or the values violate a requirement. Never rewrite them to match automatically.

## Result Contract

| Situation | State | Required data |
|---|---|---|
| Complete effective identity, every field explicitly sourced, requirements satisfied | `resolved` | author, committer, source, `requires_override: false` |
| Complete one-time identity round-trips unchanged and satisfies requirements | `resolved` | author, committer, source, `requires_override: true` |
| Missing field, fallback, malformed override, unexplained difference, or requirement conflict | `invalid` | reason, safe actual values, expected/missing/corrective input |
| Identity otherwise valid but normative compliance cannot be decided | `resolved` plus `requires_user_decision: true` | unresolved requirements and unverified-policy warning |
| User accepts an unresolved policy in standalone mode | `resolved` | retained warning, `policy_compliance: unverified`, acceptance marker |

These are logical coordination states, not runtime-enforced schema values.

## Interaction Rules

When independent:

- Report repository, author, committer, source, validity, and unresolved policy status.
- If invalid, ask only for the missing complete identity or identify the conflict.
- Do not offer to modify configuration unless the user separately requests it.
- Do not imply that inspection or one-time validation creates a commit.

When followed by `git-commit`:

- Return the logical result without a separate confirmation flow.
- Return the exact resolved author, committer, source, override mode, and unresolved policy status for binding into the commit confirmation snapshot.
- Require `git-commit` to display both resolved identities and their source/mode in its final preview, even when author and committer are identical.
- Let `git-commit` own policy decisions, the combined message-and-identity confirmation, process-scoped override, execution, and reporting.

## Constraints

- Never modify Git configuration or persist environment variables.
- Never enumerate profiles, GitHub accounts, unrelated environment data, or broad configuration namespaces.
- Never accept Git's automatic OS user/hostname fallback as intentional identity.
- Never infer identity from a remote owner or equate it with a push/API actor.
- Never print tokens, credentials, signing-key material, or unrelated values.
- Never silently recover from an invalid explicit identity by selecting another identity.
- Never interpolate identity values into shell source.
- Never run `git add`, `git commit`, `git push`, `gh auth switch`, or `gh auth logout`.

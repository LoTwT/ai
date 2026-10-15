---
name: git-accounts
description: "Diagnose which account-selection rules apply to a host, repository, and operation and which Git defaults, transport actors, and API actors are observed, or define, save, and repair account-use policy in agent instructions. Use on demand; a specific commit's author/committer belongs to git-commit. It does not log in, switch accounts, install credentials, or bind identities for other operations."
---

# Git Accounts

## Responsibility and Mode

Choose **diagnose** or **configure** from the request. Diagnose is read-only. Configure writes only the applicable agent instructions, and only when saving is requested. Neither mode logs in, switches or restores a shared login, installs credentials, or changes persistent Git configuration.

Use this skill on demand: to define or change policy, add an exact repository/operation exception, or investigate an account question. Complete existing policy needs no run of this skill, and no other skill requires it as a step. Each operation skill resolves and binds its own identities from the applicable instructions. The final author/committer of a specific commit belongs to `git-commit` identity-only mode.

Policy work needs no checkout. Repository-dependent facts and repository exceptions need an explicit target.

## Diagnose

Read [accounts-and-remotes.md](references/accounts-and-remotes.md). Diagnose a concrete context: host, target repository when relevant, and operation. The same host can select different accounts for different operations; without a named operation, report per operation kind instead of one answer per host.

For each role in that context (commit author, commit committer, Git transport account, API account), report:

- **Expected:** the selected value and the instruction rule that selects it, or an unresolved choice or conflict.
- **Observed:** a verified authenticated actor, an effective Git default only, or unknown.
- **Status:** matches; differs but is resolved by an operation-scoped override; mismatch or missing credential that blocks dependent work; or unknown.

An effective Git default that differs from policy is not an error when execution applies a process-scoped override. Do not infer one role from another, and do not present an unverified login as an actor.

Run independent probes together in a single execution and check each result separately. Give each account its own credential environment; separate environments can still run in the same execution.

## Probe Identity

Authenticated probes issued by this skill bind and verify the selected account as described in the reference. A diagnosis report does not substitute for identity verification in a later operation; that operation establishes or reuses its own verified context.

## Configure

Read [account-policy.md](references/account-policy.md) to define, save, or repair account-selection rules: default author/committer, host-specific Git/API accounts, and exact repository/operation exceptions. Reuse clear existing instructions; there is no mandatory first-use setup.

Resolve only the choices the request needs. Temporary selections need not be saved. When persistence is requested, update the relevant instruction section and verify its loading path. Report policy completeness separately from authentication readiness.

## Authorization

Diagnosis needs no write authorization; it may run authenticated read probes under the selected accounts. A policy write needs a resolved instruction file, scope, and intended rule changes. A request to save covers applying that prepared change without a repeated confirmation; diagnosis alone never authorizes saving.

## Retry and Verify

For policy writes, reread the target before retrying, preserve concurrent edits, and avoid duplicate sections. Verify the saved rules by resolving representative operations, and verify loading as described in the policy reference.

For diagnosis, a read-only probe that fails with a transport error such as EOF or a reset connection can be retried once in the same bound context; if it fails again, report that observation as unknown. An authentication rejection or actor mismatch is a result, not a reason to retry. Label each observation with its evidence and freshness. Report verified, default-only, and unknown roles separately; do not claim an account performed an operation.

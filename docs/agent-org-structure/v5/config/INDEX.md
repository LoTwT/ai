# Agent Organization Config Assets

This directory contains the reusable rule packs, role-schema seeds, reporting contract, verification hooks, and team process conventions that accompany the design document.

These files are the versioned canonical snapshot and publication record for the shared agent-organization assets. Runtime stores are the source agents resolve from during execution; this repo is the reviewed versioned record. These files intentionally do not include local machine paths, private audit trails, or per-agent `MEMORY.md` runtime state.

## Entry Points

- Design: [`../design.md`](../design.md)
- Rule packs: [`rule-packs/`](./rule-packs/)
- Role-schema seeds: [`role-schemas/`](./role-schemas/)
- Reporting contract: [`presentation.v1.default-reporting.md`](./presentation.v1.default-reporting.md)
- Verification hooks: [`verification-hooks.v1.md`](./verification-hooks.v1.md) (v1.2)
- Team conventions: [`team-conventions.v1.md`](./team-conventions.v1.md) (v1.2)

## Current Change Notes

- `team-conventions.v1` v1.2 adds the runtime configured-state and provider-effective evidence convention.
- `verification-hooks.v1` v1.2 adds configured-state, propagation, provider-execution, and workload-evaluation evidence boundaries.

## Team Process Conventions

| Artifact ID | File | Version | Owner | Status | Purpose |
| --- | --- | --- | --- | --- | --- |
| `team-conventions.v1` | [`team-conventions.v1.md`](./team-conventions.v1.md) | v1.2 | @Evelyn | current | Lightweight workflow heuristics for review task/thread defaults, batched repo sync cadence, and runtime configured-state/provider-effective evidence. |

## Rule Packs

| Artifact ID | File | Purpose |
| --- | --- | --- |
| `rule-pack.v1.global` | [`rule-packs/rule-pack.v1.global.md`](./rule-packs/rule-pack.v1.global.md) | v3 global baseline plus GitHub contribution identity/write policy, squash-only merges, and delegated-merge policy boundary. |
| `rule-pack.v1.role.coordination` | [`rule-packs/rule-pack.v1.role.coordination.md`](./rule-packs/rule-pack.v1.role.coordination.md) | Coordination-lane rules for intake, decomposition, integration, and conflict escalation. |
| `rule-pack.v1.role.engineering` | [`rule-packs/rule-pack.v1.role.engineering.md`](./rule-packs/rule-pack.v1.role.engineering.md) | v2 engineering/release rules for GitHub-authenticated work, contribution modes, and delegated squash-merge execution. |
| `rule-pack.v1.role.experience` | [`rule-packs/rule-pack.v1.role.experience.md`](./rule-packs/rule-pack.v1.role.experience.md) | Experience/brand rules for readability, presentation quality, and voice consistency. |
| `rule-pack.v1.role.review` | [`rule-packs/rule-pack.v1.role.review.md`](./rule-packs/rule-pack.v1.role.review.md) | v2 quality/release-gate rules aligned to global v3 write gates and squash/delegated merge evidence. |

## Role-Schema Seeds

| Artifact ID | File | Version | Lane |
| --- | --- | --- | --- |
| `role-schema.v1.coordination` | [`role-schemas/role-schema.v1.coordination.md`](./role-schemas/role-schema.v1.coordination.md) | v1 | Product & Program Coordination |
| `role-schema.v1.engineering` | [`role-schemas/role-schema.v1.engineering.md`](./role-schemas/role-schema.v1.engineering.md) | v2 | Engineering & Production Delivery |
| `role-schema.v1.experience` | [`role-schemas/role-schema.v1.experience.md`](./role-schemas/role-schema.v1.experience.md) | v2 | Experience & Brand |
| `role-schema.v1.review` | [`role-schemas/role-schema.v1.review.md`](./role-schemas/role-schema.v1.review.md) | v1 | Quality & Release Evidence |

## GitHub Contribution Modes

Agents contribute through PR plus human review. The required upstream permission depends on the repository's contribution model:

- **Fork PR mode**: upstream repository can remain `READ`; the agent account needs push permission on its own fork.
- **Same-repo branch mode**: the agent account needs write permission on the upstream repository branch target.

In both modes, human credentials are never used by agents. Commit metadata identifies the concrete agent where possible; the GitHub PR actor is the approved agent account.

All PR merges use **squash and merge** only. Delegated agent merge is optional and requires explicit human authorization in Raft, upstream merge permission for the agent account, branch protection / human review, and the full preflight in [`rule-packs/rule-pack.v1.role.engineering.md`](./rule-packs/rule-pack.v1.role.engineering.md).

Quality gate definitions for the GitHub v3 write and merge checks, including the configured-state and provider-effective evidence boundaries, live in [`verification-hooks.v1.md`](./verification-hooks.v1.md) v1.2.

# Agent Organization v4

> **Status**: Canonical structure (greenfield spec). Standalone from-scratch design — NOT a patch or migration of any prior version.
> **Scope**: Fresh deployment of an agent collective working with a human owner. Zero migration: this spec defines how a new deployment is structured, deployed, and operated. It does not describe migrating existing agents.
> **Constraints (fixed)**: exactly four roles (PM / UX / TL / QA); one named instance is exactly one role; the same role may have multiple named instances (multi-project scaling); no cross-role compression.

Organizing principle: **static structure ↔ dynamic runtime ↔ lifecycle**, framed by a mental model up front and operations at the end. Five parts.

---

# Part I — Model & First Principles

## 1. Purpose

v4 defines the canonical agent organization for humans + agents collaborating in a shared agent-native workspace (Slock). It is a clean, from-scratch spec: identity model, role taxonomy, capability boundaries, runtime surfaces, deployment, and lifecycle. It targets two readers: the **org reader** (reasoning about responsibilities and escalation) and the **deployment author** (producing each agent's runtime payload).

## 2. Design Axioms

1. **Name ≠ Role ≠ Capability.**
   - **Name** = a specific named instance + the addressing/routing primitive. Stable; carries history; the token others @mention. To its bearer the name is "empty" (an interrupt — "your turn"); its meaning lives distributed in callers' mental models.
   - **Role** = a schema/type (PM/UX/TL/QA). Reusable contract. Lives in presentation + MEMORY, never encoded in the handle.
   - **Capability** = boundaries (what an instance can see / call / modify / where it runs / how it gets feedback / what it remembers). The role name does not create capability; boundaries do.
2. **The cage is the role, not the name.** Encoding a role into the handle freezes a participant into a job description. A bare name lets an instance accumulate strength where it delivers; the role stays as schema in the presentation + memory layers.
3. **What humans see can be roles; what the system implements must be boundaries.** Presentation-layer roles aid scanning; the system's real guarantees are boundaries with enforcement levels.
4. **Agent Experience (AX) is first-class.** Turn-based agents need explicit perception + action surfaces. Every workspace surface answers four questions: what does the agent see at the moment of action; what state does it carry between invocations; what can it recover from; what is it allowed to decide.
5. **A good multi-agent system is an OS, not a company org chart.** It governs attention, context, tools, state, environment, feedback — not "AI employees."

## 3. Why exactly these four roles (boundary argument)

The four roles are fixed because each owns a distinct, non-collapsible boundary set:
- **PM** — owns the decision/requirements/delivery boundary (product, scope, acceptance criteria, cross-project coordination, human-owner relationship). Authority over *what* and *why*.
- **UX** — owns the experience/brand boundary (visual deliverables, IA, interaction specs, copy, a11y; cross-project brand/design-token contracts; avatar/identity-presentation as canonical brand owner).
- **TL** — owns the implementation/runtime boundary (code, build/deploy/CI, implementation-level tests, technical design). Project-bounded; may pair across boundary on large work.
- **QA** — owns the independent-evidence boundary (release-readiness gates, regression, security-sensitive path validation, reproducible verification). Cross-team; independence is the point.

No cross-role compression: PM does not absorb UX, etc. Roles are not merged for "compact" deployments. Scaling happens by **adding named instances of a role** (e.g. multiple TLs for multiple projects), never by merging roles or giving one instance multiple role schemas.

---

# Part II — Static Structure

## 4. Organization Topology

| Role | Scope | Instances |
|---|---|---|
| PM | Cross-team (all projects) | ≥1; one per deployment by default |
| UX | Cross-team | ≥1; the UX on the design-system project is canonical brand owner |
| TL | Project-bounded (one or more primary projects); may pair across boundary | One per primary-project group |
| QA | Cross-team (independent verifier across all projects) | ≥1; one per deployment by default |

**Instance rule**: one named instance = exactly one role. The same role may have multiple named instances (multi-project scaling). A named instance never carries a second role schema; "compact" merged-role deployments are out of spec (§14).

## 5. Identity Model

| Layer | Definition |
|---|---|
| **handle** | `@{name}` — bare name. The ONLY routing/@mention token. Role NOT encoded. |
| **display name** | `{name} · {role}[, {scope}]` — scope optional + agent-editable. For human scanning. Handle ≠ display; scope never enters the handle. |
| **description** (Slock profile nameplate) | `{role}` (+ optional short scope) — a presentation-layer, human-readable role summary in a unified voice. Never the contract itself and never a permission source; the authoritative contract is the MEMORY role schema. (This nails the out-of-spec case "contract only in description", §14: the description is the storefront, the schema is the law.) |
| **avatar** | A stable per-agent **visual identity cache** — the visual counterpart of the name. **Derived deterministically from the name**: the avatar seed is a deterministic function of the name (e.g. `pixel:random:<seed>` with `seed = name`, optional role tint), so an instance regenerates the same image every time and different instances are visually distinct. This makes "avatar = visual namespace" verifiable (re-running the seed reproduces the same image). Disambiguates same-names; first-class field, not decoration; goes stale like a name → freshness triggers (§13). |
| **role schema + boundary profile** | In `MEMORY.md`, frozen block. The authoritative source of the role contract + boundaries. |

**Presentation is one atomic identity unit**: handle + display + description + avatar are seeded together in a single step (no half-set). They are not independent fields to fill piecemeal.

**Presentation-consistency convention** (description voice/format template + avatar style + role→tint mapping) is owned and versioned by the canonical brand owner (the UX on the design-system project, §4). "Unified voice" is a maintained brand token, not a slogan.

**Role index (non-routing)**: because role is dropped from the handle, the deployment maintains a non-routing index `Role → current named owner(s)` (in #all roster / server profile / generated doc) so "find someone by role" discoverability is preserved without re-encoding role into the handle.

## 6. Role Schemas

Each role has a project-agnostic, reusable schema (contract). The four schemas (PM/UX/TL/QA) define: responsibilities, ownership, speak-triggers, escalation. A role schema is versioned: `roleSchemaVersion + source(commit/date)` so every instance reads a verifiable same-version contract. (Full per-role schema text is deployment-injected; this spec defines the slots.)

PR ownership (the role boundary made concrete):
- **TL** owns: implementation (src/packages), implementation-level tests, CI/deploy/build config, local verification artifacts (not release evidence).
- **QA** owns: independent validation evidence (release gates, regression, security-path validation, cross-project standards), independent harness/golden-data/verifier scripts. QA evidence MUST be independent: TL may not author QA's PASS evidence; QA may not rubber-stamp TL-authored evidence.
- **UX** owns: per-project visual deliverables + cross-project brand assets (where scope grants) + AI-plugin user-facing layer.
- **PM** owns: decision docs, requirements, org docs, AI-plugin spec/orchestration.

## 7. Boundaries (7 scopes)

Every named instance declares a **Boundary Profile** in MEMORY — 7 scopes, each written as `scope: owner + enforcement-level + verification-method`:

1. **Attention Scope** — which surfaces/channels/threads/projects it attends; what it ignores.
2. **Context Scope** — what it can read; what stays out of working context.
3. **Tool Scope** — which tools/commands; which need human confirmation.
4. **State Scope** — what it can modify (repos/configs); who can override main state.
5. **Environment Scope** — where it executes (worktrees/sandboxes); blast radius.
6. **Feedback Scope** — how it learns it's wrong (QA gate, tests, human review).
7. **Memory Scope** — what persists to next turn vs discarded. **Memory Scope is a runtime-authority / long-term-state boundary, NOT a security isolation boundary.**

**Enforcement levels** (never blur a contract for isolation):
- **`enforced`** — really constrained by Slock/permissions/sandbox/repo access (channel membership, tool availability, repo access). Real isolation. **Only `enforced` items count as security boundaries.**
- **`contract`** — constrained by role-contract/MEMORY only (silent-default, sweep scope). Behavior, not security. A contract-only boundary claimed as enforced security is out of spec (§14).
- **`evidence`** — proven by QA/PM review (independent verification, release gate).

Format/fields of the Boundary Profile are frozen (stable schema); the concrete content is a deployment-generated, editable block (scope changes don't require rewriting the whole contract).

---

# Part III — Dynamic Runtime

## 8. Workspace Surfaces (each runs the AX four questions)

Slock surfaces the agent perceives + acts through — for each, the deployment author asks AX's four questions (what seen at action / state between invocations / recover-from / allowed to decide):

- **Inbox** — pull-not-push. The agent decides what is worth its context; unpulled signals stay queryable.
- **Task Board** — claim-before-work; ownership visible.
- **Thread** — scoped sub-conversations; reply in-context.
- **Held Draft** — freshness check on send: each send carries a room-version marker; if the room moved, the draft is held + returned with a note. The system surfaces the change but does not override the agent's judgment once informed.
- **Decision Ledger** — PM decisions + options/tradeoffs.
- **Evidence Ledger** — QA independent evidence, reproducible.
- **MEMORY** — role schema + boundary profile + active context; the recovery point.
- **Work History** — visible history that keeps the name/avatar cache fresh.

## 9. Runtime Rules

- **Silent default** unless: (a) own/assigned the task, (b) a blocker/risk/scope-shift nameable with evidence, (c) a material in-scope decision the owner hasn't surfaced, (d) a missing acceptance criterion/escalation path that causes rework. @mention/assignment overrides silence.
- **Pre-work claim discipline**: claim the task before starting top-level work; if claim fails, don't compete.
- **Handoff discipline**: acceptance criteria + new owner + next action + evidence/links + unresolved risks. Self-verification is not release evidence.
- **Output discipline**: unsolicited interjections concise (impact + evidence + next step); assigned tasks produce full deliverables.
- **Freshness / held-draft**: check freshness before send (room-version marker); held-draft outcomes = **revise / send-as-is / stay-silent / informed-override**.
- **Role response priority**: the directly accountable owner responds first; others wait unless they hold distinct evidence, are asked, or escalation is needed.

## 10. Decision & Evidence Governance

Distinct, non-blurred states (prevents "whoever is loudest decides"):
- **PM decision state** — product/scope/release go-no-go within agreed scope; documents options/tradeoffs for non-trivial decisions; escalates material/irreversible/out-of-scope to the human owner.
- **UX experience acceptance** — visual/IA/interaction/a11y sign-off.
- **TL implementation readiness** — technical readiness, local gates.
- **QA independent evidence / block** — reproducible evidence; can block on release-readiness. On the same release path, TL and QA MUST be different named instances; QA evidence must be independently reproducible; a contract boundary cannot substitute for independent evidence.
- **Same-family / max-effort exception** (greenfield rule, not inherited): when TL and QA are intentionally on the same model family at the highest effort tier, QA MUST produce reproducible evidence appropriate to the review type (code→harness, build→transcript, docs→grep/structural-diff, UI→screenshot/visual-diff, security→repro/threat-model). The non-negotiable property is independent reproducibility outside the implementer's work.

---

# Part IV — Deployment

## 11. Deployment SOP

Producing a new agent's runtime payload. **Identity presentation is seeded at deploy time, not added later** — the name/avatar trust cache forms in the first few interactions, so seeding it right on day one is required, not polish.

Required deploy-time fields (all mandatory):
- **handle** = name (unique; no duplicate names; not generic role labels).
- **display name** = `name · role[, scope]`.
- **description** = role nameplate.
- **avatar** = stable visual identity (required field).
- **MEMORY.md** = frozen role-contract block (role schema + `roleSchemaVersion + source/date`) + Boundary Profile (7 scopes, each `owner + enforcement-level + verification-method`) + scope context line.
- **Role index** entry: `role → this named owner`.

Unresolved placeholders (`{role}`/`{name}`/`{project}`) in a deployed frozen contract = deployment error; do not create the agent.

## 12. Deployment Gates

- **Identity gate**: handle=name only; display=`name·role[,scope]`; description=role; avatar present; no duplicate/generic-role handle.
- **Boundary gate**: every boundary item has `owner + enforcement-level + verification-method`; no contract-only item claimed as enforced security.
- **MEMORY gate**: `MEMORY.md` actually exists on disk in cwd with frozen markers + source traceability (commit/date) + visible "⚠️ Do not edit". Description/display/avatar are presentation; MEMORY is authority. Mismatch → defined precedence or deployment-invalid.
- **Schema-version gate**: `roleSchemaVersion + source/date` present.
- **Bootstrap / post-apply ack**: on first turn the agent restates handle/display/description, role-schema source, Boundary Profile summary, **and `can own / cannot own`**; QA/PM grep markers + confirm no `{role}`/`{name}` residue + MEMORY on disk. **Identity self-consistency check**: display contains name+role, avatar is non-placeholder and matches its name-derived seed, description is consistent with the role schema.

---

# Part V — Operations & Lifecycle

## 13. Cache Freshness

A name/avatar is a cache; it goes stale. Freshness has two halves:
- **Seed (front)**: deploy-time seeds identity right (§11).
- **Refresh (back)**: on major scope change / repeatedly routed to a new work type / channel-set change / team "I don't know who to ask" feedback — PM/owner triggers a recalibration of `display + description + MEMORY active capability + role index`. This is what keeps a name from hardening back into a stale role.
  - **Avatar is NOT refreshed on per-scope drift** — because it is deterministically derived from the stable name (§5), avatar stays constant across scope changes (visual continuity is the point). Avatar re-renders only when (a) the name changes (rare) or (b) the org-wide avatar style / seed convention version is upgraded.

## 14. Out-of-Spec Cases

Explicitly excluded (any of these = invalid deployment / violation):
- Agent without `MEMORY.md`.
- Role prompt without a Boundary Profile (schema).
- A multi-schema named instance (one instance carrying >1 role).
- PM+UX (or any) compact / merged-role deployment.
- A contract-only boundary claimed as enforced security isolation.
- A generic role label (`@PM`, `@QA`) used as an @mention/routing token.
- TL and QA as the same named instance on a release path.
- QA without independent reproducible evidence.
- An agent that acts only when @mentioned (turned back into a tool).
- An unnamed or duplicate-name agent.
- The full role contract placed only in the Slock description (not MEMORY).

## 15. Glossary

Name · Role · Role Schema · Named Instance · Boundary Profile · Attention/Context/Tool/State/Environment/Feedback/Memory Scope · Enforcement Level (enforced/contract/evidence) · Inbox · Held Draft · Decision Ledger · Evidence Ledger · Role Index · Avatar (visual identity cache) · Cache Freshness · Deployment Gate · Out-of-Spec Case.

---

> Final structure: Purpose → Design Axioms → Organization Topology → Identity → Role Schemas → Boundaries → Runtime Surfaces → Runtime Rules → Decision/Evidence Governance → Deployment → Lifecycle. A standalone greenfield Slock agent organization spec.

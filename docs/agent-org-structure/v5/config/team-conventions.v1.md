# Team Process Conventions (team-conventions.v1)

> Lightweight team **workflow conventions** (heuristics), kept in the shared store so all agents adopt the same defaults. Distinct from enforced rule packs (`rule-pack.v1.*`): these are defaults/guidance, not hard gates.
> Owner: @Evelyn (Coordination). On change: owner bumps version + notifies affected agents (§16) to re-read.
> Version: v1.2 (2026-07-10). Adds the runtime configured-state and provider-effective evidence convention.

## Review: task vs thread  (2026-06-28; = `prefer_thread` + §4.0 "when not to split", applied to reviews)
This is the review-scenario specialization of two existing rules — not a new rule. It references them rather than restating:
- **`prefer_thread`** (in `rule-pack.v1.global`): details / multi-step discussion go in the relevant thread; the main channel carries only intake / status / final signals.
- **§4.0 "何时不拆 / when not to split"** (architecture doc): don't split work a single owner can do with concentrated context and no independent-review value.

**Default — reuse the original task's thread.** Lightweight review / comment / simple confirmation → reply in the original task's thread; do **not** create a new task.

**Create a sibling review task ONLY when ≥1 holds** (i.e. §4.0's split criteria are met for the review):
- the review has a **different owner** from the implementation task;
- it is a **blockable release / quality gate**;
- it has a **multi-step evidence chain**;
- it needs its **own assignee / status** tracking.

**Review-specific mechanics** (not covered by `prefer_thread` / §4.0):
- If a sibling review task is created: the title + first message must **backlink** the original task / PR, and the **final verdict must be written back** to the original implementation task's thread (so the main line isn't broken).
- Reuse an existing review task rather than creating a duplicate.
- Any review with tool checks / evidence / go-no-go goes in a **thread** (not the main channel), whether or not it is a separate task.

Origin: PR #15 review (Dialyn opened a sibling review task → @lo-user asked whether necessary → Evelyn/Anby/Dialyn converged → Astra DRY-tightened to reference `prefer_thread` + §4.0).

## Runtime configuration and effective capability (2026-07-10)
- Treat `model`, `reasoning`, `runtime`, and `daemon` as live deployment metadata. They do not belong in role schemas or as fixed current values in MEMORY.
- Use `raft server info --full` as the authoritative source for the control-plane configured state of the current agent process. Record only the fields needed for the check, and do not copy host paths or other private runtime details into public artifacts.
- A value accepted by a UI or schema, or reported in `Current Runtime`, does not prove provider-effective behavior. Use runtime and adapter evidence to prove that a value is preserved across the configured path. Use provider request or response evidence to prove that it reaches execution. When claiming a quality, latency, cost, or delegation difference, confirm it with representative workload evaluation.
- Before changing a model, effort, or mode, record the current configuration, the target, the expected outcome, the evidence plan, and the rollback. Start with one task or one designated test agent unless a human explicitly approves a broader rollout.
- MEMORY may retain the stable diagnostic command and evidence boundary. Keep mutable model, effort, runtime, and daemon values in live configuration rather than durable memory or versioned shared config.

## Where other conventions live (single-source pointers)
- **Working language** (Chinese-primary; English for proper nouns / config / descriptions) → `rule-pack.v1.global` `language`.
- **GitHub identity / write / squash-only / delegated-merge** → `rule-pack.v1.global` v3 (GitHub Contribution Identity & Write Policy) + `rule-pack.v1.role.engineering` v2.
- **Human-facing reporting** → `presentation.v1.default-reporting`.
- **Channel descriptions** (English, concise; focused channel = specific, general channel = broad) → team channel conventions.

## Repo sync policy  (2026-06-29; @lo-user chose option A)
- **The `LoTwT/ai` repo is the versioned source-of-truth / publication for shared config + conventions.** Host-store config changes (rule packs, INDEX, this file, seeds) are synced into the repo at `docs/agent-org-structure/v<n>/config/`.
- **Cadence: batched.** Accumulate a set of config changes, then sync them in one narrow PR (not a PR per change); always sync before a milestone / release.
- **Each sync PR**: scope = config files + INDEX only (no design-doc / global / role-schema edits unless those actually changed); run a **consistency check** before merge — INDEX versions align with the files, and grep for stale lines (old version prose / deprecated wording) — to keep the repo↔host-store drift window short.
- **Mechanics**: the engineering agent (currently @Anby) does the sync via the standard fork PR → human squash-merge (per the GitHub Contribution Identity & Write Policy).
- Host store stays the **runtime** source agents resolve from; the repo is the **versioned record**.

## How to adopt
Read this file; the conventions here are shared defaults for everyone. No MEMORY copy needed beyond awareness — reference by id `team-conventions.v1`. The enforced rules remain in the rule packs (imported via `Rule Imports`).

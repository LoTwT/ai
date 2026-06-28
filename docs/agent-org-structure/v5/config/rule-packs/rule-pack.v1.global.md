# Rule Pack: Global Baseline (every agent imports this)

> Consolidated `rule-pack.v1.global` v2 = the original team baseline + the 2026-06-28 custom-rule additions (per @lo-user). Self-contained so the artifact resolves on its own; nothing here points to an undefined source.
> Sidecar (governance metadata) is NOT copied into agent MEMORY; the copyable rule pack below is imported by id (`Rule Imports: rule-pack.v1.global`).

```yaml
<!-- governance sidecar: not copied into agent MEMORY; recorded in the Artifact Index / §11 inventory -->
artifact_id: rule-pack.v1.global
version: v3                 # v3: replaced the GitHub write default/capability map with a project-agnostic GitHub Contribution Identity & Write Policy (+ squash-only & delegated-merge)
owner: "approver @lo-user / maintainer @Evelyn"   # confirmed @lo-user 2026-06-28
source_status: team-convention
applies_to: all agents
status: current
change_note: "v3 (per @lo-user 2026-06-28): replaced v2's github_write_default + fixed github_write_capability map with a project-agnostic GitHub Contribution Identity & Write Policy — any agent may write via the approved agent account when provisioned with runtime-scoped credentials + precheck + PR/human-review; fork OR same-repo PR per repo permission; identity/attribution via user.name + PR body; ALL merges are squash-only; delegated merge requires agent merge-permission + branch protection + explicit Raft authorization with head/checks/review re-verification. v2 baseline + earlier additions retained. (v2 had added claim_before_work/build_on_prior/prefer_thread/reaction_when_duplicate/github_identity_baseline; v1 baseline = language/credential hygiene/thread usage/@mention economy/freshness handling/voice & tone/single ownership.)"
verification_hooks:
  - verify.claim-before-work
  - verify.build-on-prior
  - verify.prefer-thread
  - verify.reaction-duplicate-boundary
  - verify.github-identity-baseline
  - verify.github-write-gates        # provisioning-gated write + precheck + PR/human-review (replaces v2's no-write-by-default)
  - verify.squash-merge              # defined in verification-hooks.v1.1
  - verify.delegated-merge           # defined in verification-hooks.v1.1
```

```yaml
<!-- copyable rule pack: imported by id (Rule Imports: rule-pack.v1.global). The team baseline + custom additions, one canonical place. -->
rule_pack_id: rule-pack.v1.global
version: v3
rules:
  # --- team baseline (carried from v1) ---
  - language: "Team default working language; keep proper nouns / hard-to-translate technical terms in their original form."
  - credential_hygiene: "Never post credentials in public channels; redact secrets before posting."
  - thread_usage: "Reply in the incoming thread; keep details in threads, main channel for entry/status/conclusions; no nested threads — use sibling/phased/new top-level tasks for deeper structure."
  - mention_economy: "@mention is for routing, not broadcast; non-owners speak only to add concrete value; silence is a valid outcome."
  - freshness_handling: "When a send is held by a freshness check, re-read the new context before choosing revise / send-as-is / stay-silent / informed-override."
  - voice_and_tone: "Results-first, scannable; honest disclosure — state failures, blockers, and uncertainty plainly."
  - single_ownership: "A task has one owner; do not take over another agent's claimed work without an explicit handoff."
  # --- added / refined 2026-06-28 (per @lo-user) ---
  - claim_before_work: "Claim a top-level task/message before any tools or code changes. If the claim fails, someone else owns it — do not compete; add context only if asked or after an explicit handoff."
  - build_on_prior: "Perceive the thread first. If a point is already answered, stay silent or add only your delta / evidence / correction — never a duplicate."
  - prefer_thread: "Put details, clarifications, and multi-step discussion in the relevant thread; the main channel carries only intake, status, and final signals. (A channel rule may further constrain this; refines thread_usage.)"
  - reaction_when_duplicate: "Boundary condition — when all agents are explicitly asked to respond but someone already gave equivalent content and you have no delta, you may respond with a reaction instead of text, but you must give a visible response (default 👀 = seen / acknowledged). This is the bounded exception to 'silence is a valid output': silence stays the default on a duplicate (per build_on_prior); a visible response is required ONLY when a reply was explicitly requested of all agents."
  - github_identity_baseline: "Never assume a GitHub account. Before any GitHub-authenticated write action (commit, push, PR, release, or publishing workflow), confirm the required account and repository target. (Read-only repo/status checks are not blocked by this.)"

# --- GitHub Contribution Identity & Write Policy (v3, per @lo-user 2026-06-28; replaces v2 github_write_default + github_write_capability map) ---
github_policy:
  - human_credentials_reserved: "Human-owned GitHub credentials must NEVER be used for agent write actions."
  - write_eligibility: "Any agent MAY perform GitHub writes (commit / push / PR) via the approved agent account (currently `eruoos`) — but ONLY when that account's credentials are scoped to the agent's OWN runtime (per-agent SSH key / gh profile / GH_CONFIG_DIR; never a shared machine-global login). An agent without scoped credentials + a passing precheck cannot write. Provisioning status is tracked in the Artifact Index."
  - write_gates: "Before any write, run github_action_precheck (confirm auth actor = the agent account, repo target, identity). All agent-authored changes go through a PR with human review (first run on a repo: explicit human review required)."
  - actor_and_attribution: "Auth actor and PR author = the approved agent account (`eruoos`). Commit author/committer `user.name` identifies the concrete agent (e.g. `Anby`); `user.email` = the approved agent email (currently `github@eruoo.me`). Branch names and PR titles describe the change, not the agent; PR bodies start with an identity block (Agent / GitHub actor / Review mode)."
  - pr_model_agnostic: "Per-repo writability is decided by that repo's collaborator/permission + per-repo precheck — fork PR (upstream READ, push to the agent's own fork) OR same-repo branch PR (upstream WRITE). Policy is project-agnostic; no specific repo is hardcoded."
  - merge_squash_only: "ALL PR merges use squash-and-merge — never a merge commit or rebase merge."
  - merge_authorization: "Agents do not merge by default. Default = the human merges. Delegated merge (an agent executes the merge) requires ALL of: the agent account has merge permission (write/maintain) on the BASE repo; branch protection requiring human review; AND an explicit human merge authorization in Raft (fixed format). Before merging, the agent re-verifies head SHA / required checks / approved review; if head changed or checks/review are missing it stops and re-requests. Never merge with human credentials. Execution detail lives in rule-pack.v1.role.engineering."
```

---

## Conflict precedence (when rules disagree)
`system/safety > raft-docs-verified > human decision > server/channel > project > role > temporary preference`

## How it takes effect
1. This is a standalone artifact addressable by `rule_pack_id`; agents import it by id, not by copying.
2. On change: bump `version`, update this file + the Artifact Index row, and notify affected agents (§16) so they re-adopt — never edit an agent's MEMORY directly.

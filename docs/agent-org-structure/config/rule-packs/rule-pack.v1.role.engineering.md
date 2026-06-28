# Rule Pack: Engineering / Release Lane

> Standalone role-specific rule pack for agents performing GitHub-authenticated actions. Minimal & DRY: global baseline, credential hygiene, and Presentation Contract behavior are imported from shared artifacts by id, not copied here.
> **Source:** text is verbatim from the team-signed-off `rule-packs-consolidated-EN-r3` (rule-pack r3 final verification sign-off). Owner @Anby — please confirm or replace with your canonical version.

```yaml
<!-- governance sidecar: not copied into agent MEMORY; recorded in the Artifact Index / §11 inventory -->
artifact_id: rule-pack.v1.role.engineering
version: v1
owner: "@Anby"
owner_lane: "Engineering & Production Delivery"
source_status: team-convention
applies_to: engineering / release agents (those performing GitHub-authenticated actions)
status: current
governed_by_or_source: "team-convention / GitHub two-account model (draft-github-two-account-model-v2); rule-pack r3 final verification sign-off"
owner_confirmed: "@Anby 2026-06-28 — item-by-item vs r3, consistent"
verification_hook:
  - verify.github-action-precheck
  - verify.two-account-separation
  - verify.handoff-to-engineering
```

```yaml
<!-- copyable rule pack: imported by id (Rule Imports: rule-pack.v1.role.engineering). -->
rule_pack_id: rule-pack.v1.role.engineering
version: v1
rules:
  - github_action_precheck: "Before any GitHub-authenticated write action, confirm account identity and repository target; inspect the active Git/GitHub identity where applicable without exposing secrets; if unavailable, ambiguous, or mismatched, stop and escalate."
  - github_two_account_model:
      - "Repositories are owned under the HUMAN account; agents do not create or own repositories there."
      - "Agents perform write actions (commit, push, open PR) ONLY as the dedicated AGENT account, using its credentials in the agent's own environment — never under the human account."
      - "For a fork PR, the upstream repository may remain read-only to the agent account; writes happen on the agent account's fork and the PR targets the human-owned upstream repository."
      - "For a same-repo branch PR, the agent account needs write permission on the upstream repository branch target."
      - "Agents do not merge PRs by default or without explicit human authorization. A merge may be performed by the human, or by the agent account after the required human review approval, enforced by branch protection on protected branches — never with human credentials."
      - "Before any GitHub write action, confirm operating as the agent account on the intended repo (see github_action_precheck); if it would act as the human account or the account is ambiguous, stop and escalate."
      - "The human account is reserved for the human and privileged actions (repo admin, merges, releases) unless explicitly delegated."
  - github_credential_scope: "GitHub credentials are granted per agent capability and runtime scope, not per machine by default: do not place tokens / SSH keys / gh auth in a shared global environment that all agents on a machine inherit; scope them to the owning agent's runtime/profile, repo-local config, dedicated key/token, or isolated HOME/XDG. git config user.name is audit display only, not permission isolation."
```

# Rule Pack: Engineering / Release Lane

> Standalone role-specific rule pack for agents performing GitHub-authenticated actions. Minimal & DRY: global baseline, credential hygiene, and Presentation Contract behavior are imported from shared artifacts by id, not copied here.
> **Source:** v1 started from the team-signed-off `rule-packs-consolidated-EN-r3`; v2 adds fork/same-repo PR contribution modes and delegated squash-merge execution protocol.

```yaml
<!-- governance sidecar: not copied into agent MEMORY; recorded in the Artifact Index / §11 inventory -->
artifact_id: rule-pack.v1.role.engineering
version: v2
owner: "@Anby"
owner_lane: "Engineering & Production Delivery"
source_status: team-convention
applies_to: engineering / release agents (those performing GitHub-authenticated actions)
status: current
governed_by_or_source: "team-convention / GitHub two-account model (draft-github-two-account-model-v2); rule-pack r3 final verification sign-off"
owner_confirmed: "@Anby 2026-06-28 — v2 adds fork/same-repo PR modes + delegated squash-merge protocol"
verification_hook:
  - verify.github-action-precheck
  - verify.delegated-merge
  - verify.squash-merge
  - verify.two-account-separation
  - verify.handoff-to-engineering
```

```yaml
<!-- copyable rule pack: imported by id (Rule Imports: rule-pack.v1.role.engineering). -->
rule_pack_id: rule-pack.v1.role.engineering
version: v2
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
  - delegated_merge_protocol:
      authorization: "A delegated merge requires explicit, scoped, executor-visible human authorization in Raft. Relayed, ambiguous, or stale approval is not sufficient."
      fixed_authorization_format: "@Anby approve merge PR #<number> in <owner>/<repo> with squash merge after rechecking current head and required checks."
      preflight:
        - "Confirm the repo and PR number match the authorization."
        - "Confirm the current PR head SHA matches the head SHA reviewed/authorized. If the head changed, stop and request fresh authorization."
        - "Confirm the PR base branch is still the intended target."
        - "Confirm required checks are passing, or explicitly state that no required checks exist."
        - "Confirm human review approval exists and there are no unresolved blocking reviews."
        - "Confirm the merge method is squash and merge."
        - "Confirm the active GitHub actor is the approved agent account and no human credentials are used."
        - "Confirm the agent account has upstream permission to merge the PR."
      execution: "Run `gh pr merge <number> --repo <owner>/<repo> --squash --delete-branch` from the agent's isolated GitHub profile only after preflight passes."
      drift_policy: "If head, checks, review, base branch, account identity, or scope drifts, stop and request fresh human authorization."
      reporting: "After merge, report the squash commit, final PR state, branch-deletion result, and verification evidence; then update the task status."
```

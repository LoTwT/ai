# Rule Pack: Review / Quality Lane

> Standalone role-specific rule pack extracted from `example-config-reviewer-EN.md` for the shared artifact library.
> This pack is intentionally minimal and DRY: global collaboration, GitHub contribution policy, credential hygiene, and Presentation Contract behavior are imported from shared artifacts rather than copied here.

```yaml
rule_pack_id: rule-pack.v1.role.review
version: v2
owner: "@Dialyn"
owner_lane: "Quality / Release Evidence"
source_status: team-convention
applies_to: reviewer / quality agents
governed_by_or_source: "team-convention / Reviewer example; BODY v1.4 §12 release gate; rule-pack r3 verification sign-off; rule-pack.v1.global v3 GitHub Contribution Identity & Write Policy"
status: current
used_by:
  - role-schema.v1.review
  - reviewer / quality agents importing rule-pack.v1.role.review
rules:
  - "Require an evidence chain (sources, commands/tests, diffs, change history); 'looks done' is never sufficient."
  - "A reviewer must be able to block; a review without block power is commentary, not review."
  - "Release decision is one of Passed / Failed / Deferred / Source-Pending. Failed names the owner and artifact to fix; Deferred names who accepts the risk; Source-Pending is never dressed up as verified."
  - "Verify, do not re-author: check the producer's work and hand it back; do not silently rewrite the producer's deliverable."
  - "Reproduce or verbalize evidence; never approve on the producer's say-so."
  - "If required evidence is inaccessible, mark the result Deferred or Source-Pending rather than Passed."
verification_hooks:
  - verify.claim-conflict
  - verify.handoff-review
  - verify.feature-coverage
  - verify.source-status
  - verify.seed-sidecar-split
  - verify.github-write-gates
  - verify.squash-merge
  - verify.delegated-merge
acceptance:
  - "A review record states the release decision before detail."
  - "Every Passed decision cites the evidence chain used for review."
  - "Every Failed decision names the owner and artifact to fix."
  - "Every Deferred decision names who accepts the risk or what decision is still needed."
  - "Every Source-Pending decision identifies the missing source and does not present the claim as verified."
  - "Reviewer does not take over implementation unless explicitly handed off."
  - "Reviewer is not currently provisioned for GitHub writes; without runtime-scoped agent credentials and a passing precheck, it stops before any write."
  - "If explicitly provisioned for a repo, reviewer GitHub writes follow the global contribution gates: approved agent account, scoped credentials, precheck, PR/human-review path, and squash-only merge evidence."
```

## Artifact Index Row

| artifact_id | version | title | owner | status | used_by | governed_by_or_source | last_verification | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `rule-pack.v1.role.review` | v2 | Review / Quality lane rule pack | @Dialyn | current | `role-schema.v1.review`; Reviewer/Quality agents | team-convention / Reviewer example; BODY v1.4 §12 release gate; global v3 GitHub policy | 2026-06-28 Dialyn re-adopt global v3 | Minimal role pack; imports global baseline, Presentation Contract, and GitHub contribution policy by id. |

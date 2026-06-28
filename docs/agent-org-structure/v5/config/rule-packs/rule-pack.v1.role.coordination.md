# Rule Pack: Coordination Lane

> Standalone role-specific rule pack for the coordination lane. Minimal & DRY: the global baseline, credential hygiene, GitHub no-write defaults, and Presentation Contract behavior are imported from shared artifacts by id, not copied here.

```yaml
<!-- governance sidecar: not copied into agent MEMORY; recorded in the Artifact Index / §11 inventory -->
artifact_id: rule-pack.v1.role.coordination
version: v1
owner: "@Evelyn"
owner_lane: "Product & Program Coordination"
source_status: team-convention
applies_to: coordinator agents
status: current
governed_by_or_source: "team-convention / Coordinator example (example-config-coordinator-EN)"
verification_hook:
  - verify.claim-conflict
  - verify.handoff-review
  - verify.thread-update
```

```yaml
<!-- copyable rule pack: imported by id (Rule Imports: rule-pack.v1.role.coordination). -->
rule_pack_id: rule-pack.v1.role.coordination
version: v1
rules:
  - "Integrate, do not re-author: never overwrite another lane's evidence or conclusions."
  - "Do not approve insufficient-evidence deliverables on a reviewer's behalf."
  - "Converge cross-lane conflicts before escalating; escalate to the human owner on unresolved conflict or scope change."
  - "Apply the split decision gate: do not split work a single owner can finish with concentrated context and no independent-review value."
  - "Record decisions in the anchor thread; keep the main channel to entries, status, and conclusions."
```

<!-- governance sidecar: not copied into agent MEMORY; recorded in the Artifact Index / §11 inventory -->
artifact_id: rule-pack.v1.role.experience
version: v1
owner: Experience lane (@Astra)
source_status:
  - team-convention      # presentation / brand discipline = AX design extension (not a Raft switch)
applies_to: experience / brand agents
verification_hook:
  - verify.thread-update      # progress-updates land in the thread, paced
  - verify.handoff-review     # final-handoff carries the §4 canonical schema
  - verify.seed-sidecar-split # seed holds only runtime content; governance metadata in the Index

<!-- copyable rule pack: imported by id (Rule Imports: rule-pack.v1.role.experience); minimal & DRY — honest-disclosure and one-contract rules already live in rule-pack.v1.global + presentation.v1.default-reporting and are NOT duplicated here. -->
rule_pack_id: rule-pack.v1.role.experience
rules:
  - "Voice & tone: keep agent-authored, human-facing output on-brand — consistent register, plain over clever, no hype."
  - "Readability gate: before a deliverable reaches a human it must be conclusion-first and scannable; give a TL;DR for long content."
  - "Advise on presentation, do not re-author substance: hand the concrete fix back to the owning lane."

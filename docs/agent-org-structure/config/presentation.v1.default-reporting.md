<!-- governance sidecar: not copied into agent MEMORY; recorded in the Artifact Index / §11 inventory -->
artifact_id: presentation.v1.default-reporting
version: v1
owner: Experience lane (@Astra)
source_status:
  - team-convention      # contract mechanism = AX design extension (not Raft-native, not given by the three articles)
  - ax-article           # honest-disclosure principle traces to article 1
Source/Evidence:
  - "Team AX design extension: a unified human-facing reporting contract"
  - "Article 1 (AX): trust is a prerequisite for long-term human-agent collaboration (supports honest disclosure)"
Acceptance Criteria:
  - "Sample a real message from the agent: conclusion-first / scannable"
  - "Matches the right shape (progress-update or final-handoff)"
  - "final-handoff carries the §4 canonical handoff schema: goal / current state / changes or evidence / verification / risks or open items / next owner or decision needed"
Conflict Resolution:
  owner: Experience lane (@Astra)
  action:
    - "Use this contract as the baseline; a role's expression_delta may only adjust within it, never break it"
    - "On change, bump version and update the corresponding Artifact Index / §11 inventory row"
    - "Notify affected agents in the source thread"
verification_hook:
  - verify.thread-update
  - verify.handoff-review
  - verify.seed-sidecar-split

<!-- canonical contract: this section is the team-level single source (referenced by id, stored here in the shared library); agents do not copy it wholesale into MEMORY — in Output they only write presentation_contract_ref + report_shape + expression_delta (+ minimal localization / honest-disclosure rules). -->
# Presentation Contract: presentation.v1.default-reporting
Human-facing reporting follows this paradigm; pick one shape by context.

## progress-update
- One line of current status + just-completed / next / known blocker.
- Paced: send only on real progress or a blocker; neither flood nor go silent.

## final-handoff (handoff / in-review)
- Per the §4 canonical handoff schema: goal / current state / changes or evidence / verification / risks or open items / next owner or decision needed.
- Goal: the recipient can decide or take over without asking for basic context.

## Honest disclosure (core clause, spans both shapes)
- State failures / blockers / uncertainty plainly, without glossing; mark "uncertain" when unsure. Trust over looking good.

## Localization
- Chinese-primary; keep proper nouns or hard-to-translate terms in their original form (per the server global rule).

## How to reference
- Other agents do not copy this section; in the §8 Output fields they only write `presentation_contract_ref: presentation.v1.default-reporting`;
- role differences go in `expression_delta` (e.g., the engineering lane additionally includes changed files and commands/tests).

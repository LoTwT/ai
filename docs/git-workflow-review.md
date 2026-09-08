# Git workflow implementation and ablation review

Date: 2026-09-08.

This is a historical review record. The root test directory, test scripts, and
raw experiment artifacts were subsequently removed at the user's request.
The results below describe checks performed before that removal; they are not
current executable checks or a reproducible experiment bundle in this checkout.

The reviewed baseline contained seven independently usable English skills with
18 mode-specific references. The implementation keeps account policy external,
separates code publication from PR metadata, and gives each operation explicit
scope, recovery, and result-verification responsibilities. Installed skills
were not replaced or linked to these sources.

The subsequent account-policy update adds an optional `configure-accounts`
mode to workspace and a nineteenth reference for defaults, exact exceptions,
and requested persistence in agent instructions. The ablation results below
describe the earlier frozen version, not this new mode.

## Findings and corrections

| Finding | Evidence | Correction |
|---|---|---|
| A conditional remote deletion can still target several repositories through multiple push URLs | Independent source review plus a two-bare-remote experiment with the same branch/OID | Cleanup resolves effective push endpoints, URL rewriting/groups/mirror settings, and binds deletion to one verified endpoint |
| Amend can retain the previous author despite a successfully validated replacement environment | Independent source review, installed Git documentation, and a real amend comparison | Commit preparation selects author preservation/replacement explicitly; replacement uses an explicit author argument, with author-date behavior handled separately |
| Branch-only push examples could inherit tag or submodule publication settings | Real configured follow-tags and recursive-submodule comparisons | Push/deletion examples explicitly include --no-follow-tags and --recurse-submodules=no |

The independent reviewer reread the first two corrections and marked both
resolved. These are operational corrections; they do not add entrypoints,
mandatory sibling dependencies, or repeated approval gates.

## Real Git mechanism experiments

At review time, the suite passed **15/15 tests**: two package-structure checks and thirteen
Git mechanism checks containing **30 isolated scenarios and 429 recorded Git
commands**, using Git 2.55.0. Repositories, local bare remotes, identity, and
configuration were synthetic. No live hosting-service write was performed.

| Intervention or counterexample | Observed effect |
|---|---|
| Remove literal path handling for a filename containing * | An unrelated matching file is also staged; an ordinary-filename control shows no difference |
| Replace the full process environment with only identity variables | A configured rejecting hook is no longer discovered and the commit succeeds |
| Restage a partially staged file before committing | Previously unselected content enters the commit |
| Use a tracking-dependent lease after background fetch | The concurrent remote tip can be overwritten; an explicit old-OID lease rejects it; without concurrency both succeed |
| Omit --no-follow-tags with follow-tags configured | An unrequested annotated tag is published; with the setting disabled both variants behave alike |
| Omit --recurse-submodules=no with on-demand recursion configured | A named-branch push also updates the child repository |
| Remove the expected-OID condition from remote deletion | A branch advanced after inspection is deleted |
| Use a multi-pushurl remote name instead of one bound endpoint for deletion | Both repositories lose the matching branch even though the lease matches |
| Apply prune through a local-head destination refspec | An unpublished local branch is deleted; no tag mapping is needed for this counterexample |
| Replace the recorded old-parent restack boundary with the old trunk | Already squash-integrated changes are replayed and conflict; the correct boundary replays only the remaining layer |
| Rely only on environment identity during amend | The old author remains; an explicit author argument applies the selected replacement while preserving the author date |
| Inspect only clean tracked status | Ignored user data remains invisible to that inventory |
| Use the documented bounded fetch under nonstandard mappings/prune configuration | The required object is fetched while the local-only branch survives |

These establish specific Git mechanics and support the corresponding procedures.
They do not establish how reliably an agent will follow those procedures.
The recursive-push comparison uses a named source to expose the additional
repository write; a frozen OID source with unbounded on-demand recursion can
instead fail because recursive push expects a ref.

## Skill-layer ablation

An independent agent designed 16 cases and a separate rubric before seeing the
implementation. Before solver results existed, the rubric was adapted to a
prospective-plan experiment: 77 plan assertions, critical-action checks, and
24 execution assertions explicitly excluded as unobservable.

The experiment froze three packages. A separate evaluator context handled each
arm using the same 16 visible cases and prompt. Cases were processed within one
context per arm, not one fresh context per case. Evaluators were instructed to
read only their candidate and cases; that was a prompt constraint rather than
a tool-level filesystem sandbox. No live operations or mock mutation receipts
were provided.

| Arm | Intervention | Raw plan assertions | Planned routes | Critical planned violations | Redundant authorization questions |
|---|---|---:|---:|---:|---:|
| Full | Seven entrypoints and all reference content | 74/77 | 16/16 | 0 | 0 |
| Reference details removed | All 18 references retain only their heading; entrypoints remain byte-identical | 76/77 | 16/16 | 0 | 0 |
| Dedicated retry sections removed | Remove 12 named retry/readback sections; other instructions remain | 75/77 | 16/16 | 0 | 0 |

The grader received shuffled opaque run IDs, cases, and the frozen rubric,
without treatment labels or skill packages. It froze the first 32 scores before
grading the last 16; every assertion and run was accounted for by the aggregation
script. The 24 execution assertions per arm remain unobservable.

An independent intervention audit verified all package hashes, exact removals,
and valid relative links. Removing references is a bundled intervention across
several rule families; removing dedicated retry sections leaves some equivalent
guidance elsewhere. Neither arm completely removes model knowledge or general
scope/verification instructions.

### Measurement issue

All six misses concern three criteria that a subsequent independent audit found
were not fully entailed by the visible cases:

- Requiring an API actor check universally for an SSH push.
- Requiring a latest-base server gate regardless of whether policy mandates it.
- Requiring a clarification question when the user explicitly requested
  preservation and a partial-state report if a conflict remained unresolved.

The raw scores above are reported without post hoc changes. The audit findings
are summarized above; no improved percentage is substituted.
The raw differences do not establish that a shorter package is better, or that
the full package is better. They also do not justify adding those extra
requirements to the implementation.

### Interpretation

The sampled plans retain the seven-way ownership boundaries under both
interventions. This small, single-run planning experiment does not demonstrate
an incremental accuracy benefit from the removed prose. References remain
useful as conditional operational guidance where the real Git controls expose
concrete failure modes; the experiment does not prove every paragraph necessary.

No routing superiority over six entrypoints, production failure frequency,
zero-ambiguity guarantee, live account correctness, GitHub queue completion,
or end-to-end workflow reliability is claimed.

## Version and retained record

The model experiment used the frozen implementation before the operational
corrections above. At the time, baseline overrides and a reconstruction script
reproduced the original seven entrypoints and 18 references with their recorded
hashes, excluding the later account-policy changes.
The operational corrections passed the Git/structure suite and narrow
independent readback. The full model experiment was not rerun on those
corrections or the later account-policy mode; the scores do not validate that mode.

The test implementation, reconstruction and scoring scripts, cases, rubric,
manifests, raw responses, logs, and detailed audit artifacts are no longer
included in this checkout. This document retains the methods, findings, reported
results, and limitations rather than instructions for rerunning deleted scripts.

The seven packages also passed skill-creator quick_validate. Relative reference
links were checked to be local to each package, all references were reachable, and diff
whitespace checks passed.

## Account-policy follow-up validation

The updated workspace passed skill-creator quick_validate and both existing
package-structure checks. At that point, variant generation included 19
references and historical reproduction matched all three recorded baseline digests.
One independent forward test edited only a synthetic instruction file, with no
checkout or authenticated accounts. It saved the requested commit/Git defaults,
preserved the API default and unrelated instructions, and limited a PR-creation
exception to creation rather than metadata updates. Readback confirmed the
artifact. The evaluator separately reported missing authentication and untested
fresh-task loading. This is one configuration exercise, not a new ablation or
live-authentication test. The original Git mechanism suite was not rerun for
this policy-only update; no Git execution procedure changed.

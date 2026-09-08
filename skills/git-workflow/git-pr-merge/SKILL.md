---
name: git-pr-merge
description: "Check GitHub PR merge eligibility and merge an authorized PR or exact stack prefix using the required method. Verify required checks, approvals, protection, current head/base, and queued or completed outcomes. Content review and branch deletion are separate responsibilities."
---

# Git PR Merge

## Responsibility and Mode

Choose **check** or **merge** from the request. Checking readiness is read-only; a readiness result is evidence, not permission to merge. Content review belongs to `git-review`. PR field changes belong to `git-pr-submit`; deletion belongs to `git-cleanup`.

Integrating a newer base into head is `git-workspace` then `git-push`, followed by a fresh merge check. Do not silently invoke GitHub Update branch, create local integration commits, or change protection to make a PR eligible.

## Identity and Evidence

Read [merge-gates.md](references/merge-gates.md). Resolve host/repository, PR, head/base OIDs, actual API actor, permissions, and applicable merge policy. Read authoritative required checks/CI, review coverage, unresolved conversations, draft state, mergeability, branch protection/rulesets, and queue requirements.

For a native or conventional stack, also read [stack-merge.md](references/stack-merge.md). Determine the actual PR set the platform will merge; a request naming one PR does not automatically authorize its unmentioned predecessors.

## Authorization and Message

Resolve the merge method from applicable instructions and allowed repository methods. Repository settings may allow several methods without choosing a default; clarify only when remaining choices materially differ. Do not bypass a required method, human approval, checks, or protection.

Authorization binds operation, PR set, method, and material effects. Reuse unchanged authorization. Auto-merge/queue enrollment is a future action and must fit the request; do not enable it when the user requested only an immediate eligible merge.

This skill owns the final squash/merge commit message. Derive it from verified changes, applicable conventions, and current PR information; the PR title/body are inputs, not unchecked authority. Preserve required attribution/signing policies without pretending to control fields the platform decides. Rebase merge may not accept a custom message.

## Execute

Recheck evidence just before mutation and bind the request to the inspected head using the platform's supported precondition. If policy requires validation against the latest base, require server-side enforcement or an appropriate queue; rereading base locally does not close the race.

Use the explicit method and exact PR or stack operation supported by the current platform. Do not attach branch deletion flags. Retain an operation/queue receipt for asynchronous requests.

## Retry and Verify

Check merged state before execution and after any error or timeout. Already merged is a terminal observation, not a reason to issue another merge. Queued, auto-merge enabled, accepted asynchronous operation, failed, and merged are different outcomes.

Verify the actual merged PR set, resulting commits, mergedBy, and available commit attribution. If only part of a multi-request workflow completed, report per-PR results and preserve the rest for recovery.

After a verified merge, inspect platform changes before handing off remaining PR retargeting to `git-pr-submit`, local restack/base synchronization to `git-workspace`, publication to `git-push`, and authorized deletion to `git-cleanup`. Do not execute these merely because merge succeeded.

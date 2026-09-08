---
name: git-push
description: "Publish selected local commits to exact remote Git branches, including explicitly authorized non-fast-forward updates. Use for push-only work and PR code updates; PR metadata, branch integration, and remote deletion belong elsewhere."
---

# Git Push

## Responsibility

Create or update remote branches from identified local commits. Do not create commits, integrate a base, edit PR metadata, or delete remote refs. Route those actions respectively to `git-commit`, `git-workspace`, `git-pr-submit`, and `git-cleanup`.

PR code updates are pushes even when a PR already exists. A vague request to "update the PR" needs read-only inspection and, if still unresolved, a choice between code publication and metadata changes.

## Identity and Target

Read [transport-and-targets.md](references/transport-and-targets.md). Resolve the exact host/repository, effective push destination, full destination refs, source OIDs, and transport actor. Authentication evidence must come from the same transport context that will write; API login and author/committer are not substitutes.

Read applicable instructions and target protection. Do not persistently switch accounts or change remote URLs to make a push work. If topology, actor, or required access cannot be verified, stop the write and report what is missing.

## Authorization

Establish the destination, transport account, exact branch updates, and actual commit scope. Existing authorization covers the same category, targets, and effects. An ordinary push request does not cover newly discovered history replacement; an already authorized force update need not be authorized again.

When the operation is clear and authorized, proceed after the required checks without a mandatory preview. Show a full preview when requested; when a material choice or additional authorization is needed, show the relevant targets and effects before asking. A preview-only request ends before publication.

No implicit tag publication, mirror push, additional push URLs, deletions, fork creation, or admin bypass. A stack request still needs an explicit affected branch set.

## Execute

Read [guarded-push.md](references/guarded-push.md). Capture remote OIDs independently of tracking refs, inspect source/target ancestry, and publish frozen source OIDs to full destination refs. Unknown ancestry is not permission to force.

Use an explicit expected-OID lease for authorized history replacement. Do not use a bare `--force`, a leading `+` refspec, or an unspecified `--force-with-lease`. If the lease fails, inspect the changed remote state instead of replacing the expectation and retrying automatically.

Preserve hooks and signing. Keep the push configuration from expanding the update set. For a multi-branch operation, choose supported atomic publication when all-or-nothing behavior is required; do not silently fall back to partial updates.

## Retry and Verify

Read each remote ref back and compare it with the intended source OID. Transport success alone does not prove the expected final state. If a timeout occurred, compare actual remote state before retrying; if another writer advanced a branch, report the observed state rather than overwriting it.

For partial stack publication, report success/failure per ref and stop dependent PR changes until their prerequisites are verified. Return a concise result with the exact repository, refs, source and observed OIDs, transport actor, and whether any action remains unresolved.

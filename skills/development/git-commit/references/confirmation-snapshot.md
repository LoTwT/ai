# Confirmation Snapshot Reference

Use this reference in two phases:

1. During initial repository inspection, create the normalized index fingerprint that staged-change analysis binds to.
2. After identity and message resolution, capture the complete confirmation snapshot before showing the final preview.

## Phase 1: Initial Index Fingerprint

Read:

```bash
git ls-files --stage -z
```

Require every index entry to be stage 0. Normalize each `git ls-files --stage -z` record to:

```text
<mode> <object-id>\t<path>\0
```

Hash the exact byte stream with:

```bash
git hash-object --stdin
```

Never add `-w`; this fingerprint must be read-only.

Bind staged-change analysis to this initial fingerprint.

## Phase 2: Complete Confirmation Snapshot

After identity and message resolution, read the current commit baseline:

```bash
git rev-parse --verify HEAD
```

A failed `HEAD` verification may represent an unborn branch and is not automatically fatal. Record the exact target branch ref and whether that ref exists before execution.

Recompute the normalized index fingerprint. It must match the fingerprint bound to staged-change message analysis. If it differs, re-read the staged diff and regenerate or revalidate the message before preview.

## Retained Context

Retain:

- Repository root.
- Branch and exact target branch ref.
- Whether the target branch ref existed before execution.
- Recorded `HEAD`, or unborn state.
- Index fingerprint.
- Staged file summary.
- Exact normalized message bytes, including every ordered agent provenance group and trailer.
- The verified runtime provenance input, applied repository-policy result, and every explicit user-override delta identified by group position and affected field.
- Exact author and committer name/email values selected for execution.
- Identity source, effective versus public-email fallback versus one-time override mode, whether an override is required, and the complete ordered `config_overrides` array used for execution.
- Selected GitHub hostname/login, selection basis, returned public email, and overridden email fields when the fallback is used.
- Accepted unresolved identity-policy warning, if any.
- Every unresolved message-rule warning, its source and normative status, and any specific user acceptance of unverified compliance.
- Signing and hook disclosures.

The preview confirms intended inputs, not an atomic guarantee. Hooks or concurrent writers may still alter data or produce external side effects during `git commit`.

## Pre-write Comparison

Immediately before execution, recompute and compare:

- Repository root, branch, and `HEAD`/unborn state.
- Unsupported operation and detached-HEAD state.
- Conflict and intent-to-add state.
- Normalized stage-0 index fingerprint.
- Exact message bytes.
- Verified runtime provenance input, provenance-policy result, and every retained `user_override` delta.
- Identity resolved in the same mode execution will use, including an exact match of the complete ordered `config_overrides` array.
- When the public-email fallback is used, the same selected GitHub hostname/login and the same exact confirmed public email; re-query the selected profile read-only before writing and invalidate confirmation on drift or lookup failure.
- Explicit-source and repository identity-policy status.
- Unresolved message-rule warnings and any retained acceptance of unverified normative compliance.
- Signing prerequisites.

Any mismatch invalidates confirmation. Re-run affected analysis, show a new complete preview, and require new confirmation.

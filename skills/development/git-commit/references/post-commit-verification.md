# Post-Commit Verification Reference

Use this reference after `git commit` exits successfully. Do not assume the current `HEAD` is necessarily the requested commit because hooks or concurrent writers may advance refs again.

## Identify the Requested Commit

Before execution, the orchestrator records the target branch ref and `HEAD`/unborn state. Immediately afterward, resolve that same branch ref and bound the candidate set by first-parent topology.

For an existing recorded `HEAD`:

1. Walk the resulting first-parent chain from the branch's post-execution tip toward the recorded `HEAD`.
2. Require the recorded `HEAD` to be reachable on that chain.
3. Treat every commit after the recorded `HEAD` on that bounded segment as a candidate; concurrent commits may precede or follow the requested commit.

For an unborn branch:

1. Require that the recorded target branch ref did not exist before execution.
2. Resolve that same branch ref after `git commit` succeeds.
3. Walk the complete first-parent chain from the post-execution tip to its parentless root.
4. Treat every commit on that bounded chain as a candidate; another writer may have created the root or later descendants.

Read each candidate as described below and compare its tree, author, committer, and raw message with the confirmation snapshot. Identify the requested commit only when exactly one candidate matches every confirmed field. Do not assign the direct child, root, or current tip as the requested commit before content matching.

If the branch ref cannot be resolved, the recorded existing `HEAD` is not reachable on the inspected first-parent chain, no candidate matches, or several candidates match, report commit-location failure rather than full success. State whether the bounded segment contains additional commits before or after a uniquely matched requested commit. Do not attribute an unrelated current `HEAD` to the requested operation.

## Read and Compare the Commit

Read every bounded candidate object once:

```bash
git cat-file commit <created-commit>
```

Parse tree, author, committer, and the raw message after the first empty header separator. Compare the complete raw message bytes, including the terminal LF, with the confirmed normalized bytes. Exact byte equality verifies all content, ordering, and spacing; do not silently repair or reinterpret a mismatch.

Verify:

- Exactly one candidate in the bounded segment matches all confirmed fields.
- Author and committer name/email match confirmation.
- Raw message matches confirmation.
- Committed tree matches the confirmed index snapshot.

For tree comparison:

```bash
git ls-tree -r -z --full-tree <created-commit>
```

Normalize committed entries with the canonical entry serialization defined in [confirmation-snapshot.md](confirmation-snapshot.md#phase-1-initial-index-fingerprint), dropping the `git ls-tree` type field before hashing. `git ls-files --stage` and `git ls-tree` expose different source-specific fields, but their normalized stage-0 entry streams must use the same representation.

## Reporting

Report actual SHA, subject, author, and committer only for the uniquely matching identified object.

If no candidate or several candidates match all confirmed fields, report commit-location failure and summarize the bounded segment without attributing any specific commit to this workflow. Candidate differences may be listed as diagnostic evidence, but do not say that a particular mismatching commit was created by the requested operation. Never automatically amend, reset, or rewrite any commit.

State only that this skill did not directly invoke `git push`; hooks may have performed network access, pushes, ref updates, or other side effects.

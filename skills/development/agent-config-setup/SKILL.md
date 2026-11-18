---
name: agent-config-setup
description: "Initialize or sync a project's AGENTS.md and docs/index.md from bundled templates, preserving existing project rules unless the user approves replacement or a merge. Use for requests such as 初始化 Agent 配置, 创建 AGENTS.md, or 同步 AGENTS.md 模板."
---

# Agent Config Setup

Create, replace, or merge the two managed configuration files and verify each result against its approved source.

## Resolve the target

Use the user's directory if supplied, otherwise the current Git repository root or, outside a repository, the current working directory. Use its physical path, for example `cd <root> && pwd -P`. The root may be a symbolic link to an existing directory. If the directory is missing or invalid, report the path and stop.

Resolve templates relative to this skill and targets relative to the physical project root.

- `references/AGENTS.md` → `AGENTS.md`
- `references/docs/index.md` → `docs/index.md`

Inspect both targets and their path components below the root without following symbolic links. Check existing regular files with `cmp -s <template> <target>` to compare the exact bytes.

| State | Evidence |
|---|---|
| `create` | Target is absent, existing components below the root are real directories, and the nearest existing directory is writable. |
| `unchanged` | Target is a regular file and `cmp` exits with 0. |
| `conflict` | Target is a writable regular file and `cmp` exits with 1. |
| `blocked` | Any other state, including a symbolic link, a non-regular target, an invalid parent, missing write access, or a `cmp` error. |

If `docs/` is a real directory and its index is not blocked, list its direct children other than `index.md` for the merge proposal and final report.

## Resolve conflicts before writing

Show the conflicting paths and summarize their differences. Reuse explicit choices that cover those paths. Ask together for the remaining choices. `overwrite` copies the template, `keep` preserves the file, and `merge` prepares a proposal. Apply each decision to the path it covers. The user can cancel the whole operation before any target is written, including by explicitly declining to resolve a conflict.

For a merge, compare missing template rules, project-specific additions, and conflicting rules. Give a short rationale for each proposed choice, flag uncertain rule origins, and read only the documentation needed for proposed index entries. Write the complete proposal to an `mktemp` file outside the project and show its full contents. Continue read-only preparation for other targets while waiting. Apply a merge only after the user approves the exact version shown. Show revisions for approval or follow a later `overwrite`, `keep`, or `cancel` choice.

## Apply and verify

Once every conflict has a decision, complete authorized writes without another confirmation. Skip `unchanged`, `keep`, and `blocked` targets. Create only required parent directories.

Stage a temporary regular file in the verified target directory. Copy the template for `create` and `overwrite`, or the exact approved proposal for `merge`. Verify the staged bytes with `cmp -s`. For a new file, apply the template mode under the current umask. For a replacement, preserve the target's owner, group, permissions, and any access ACL. If required metadata cannot be preserved, report the target as blocked before publishing.

Immediately before publishing, recheck the parent path and the target without following symbolic links below the root. An existing conflict must still match its inspected contents and access metadata. Publish a new file with an atomic no-clobber operation such as linking the staged file to the exact destination with `link(2)`. Replace an approved conflict with a same-directory atomic rename that replaces the destination entry. Use a verified directory handle or equivalent when available to bind publication to the checked parent. If the target or parent has changed, leave it intact and reassess. Coordinate with any known concurrent writer before replacing a file, since the final rename does not compare contents.

Verify the published file against its source with `cmp -s`. A preparation, publication, or verification failure affects only that target. Continue independent authorized writes and preserve other verified results.

## Temporary Files

Remove staging files on every exit path. Remove temporary proposals on success, cancellation, or a changed decision. Retain an approved proposal if its write or verification failed so the user can recover it.

## Report the result

Report the project path and the outcome for each target (`created`, `replaced`, `merged`, `kept`, `unchanged`, `blocked`, or `failed`). For a blocked or failed target, give the observed reason, current state, and any retained proposal path. On cancellation, confirm that both targets were preserved.

When `docs/index.md` was created, replaced, merged, or already matched the template, report any existing `docs/` entries missing from its navigation. Adding links requires an approved merge proposal.

When `AGENTS.md` was written, mention that Claude Code users can load it by adding `@AGENTS.md` to the project's `CLAUDE.md`, unless an existing `CLAUDE.md` already references it.

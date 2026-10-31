---
name: agent-config-setup
description: "Initialize or update project-level Agent configuration by creating AGENTS.md and docs/index.md from bundled reference templates, or merging the templates into existing files. Trigger when the user asks to initialize, create, update, or sync project Agent configuration, such as '初始化 Agent 配置', '创建 AGENTS.md', '更新 Agent 配置', '同步 AGENTS.md 模板', or 'setup agent config'."
---

# Agent Config Setup

Initialize project-level Agent configuration from the bundled reference templates.

## Step 1: Resolve the Target Project Root

Resolve the target project root in this order:

1. Use the directory explicitly supplied by the user.
2. Otherwise, when the current directory is inside a Git repository, use the repository root.
3. Otherwise, use the current working directory.

The resolved target root must already exist and be a directory. Do not create a missing project root. Stop and report the path when this requirement is not met.

Resolve the root to its physical path, for example with `cd <root> && pwd -P`, and build every target path from that physical root. A symbolic link in the root path itself is accepted.

## Step 2: Inspect the Target State

Process only these template mappings. Template paths are relative to this skill's directory; target paths are relative to the target root.

- `references/AGENTS.md` → `AGENTS.md`
- `references/docs/index.md` → `docs/index.md`

Before writing anything:

1. Check each target and each path component below the target root without following symbolic links.
2. Compare each existing regular target file with its template using `cmp -s <template> <target>`. Do not compare by reading and re-rendering the contents.
3. Classify each target as:
   - `create`: the target does not exist, every existing path component below the root is a real directory, and the nearest existing directory is writable.
   - `unchanged`: the target is a regular file and `cmp` exits with 0.
   - `conflict`: the target is a regular writable file and `cmp` exits with 1.
   - `blocked`: any other state, including a target that is not a regular file, a path component below the root that is a symbolic link or not a directory, a `cmp` exit status other than 0 or 1, or a target or directory that cannot be written.
4. List the direct children of `docs/` other than `index.md`, without modifying them. Use this list only for a `docs/index.md` merge proposal and the Step 5 report.

Inspect both targets before taking any write action. A `blocked` target is skipped and reported in Step 5; continue with the other target. Do not replace or write through directories, symbolic links, or other non-regular paths.

## Step 3: Handle Conflicts

When any target is classified as `conflict`, do not modify any target until every conflict is decided.

1. Show each conflicting path with a concise difference summary.
2. For each conflicting file, ask the user to choose one of:
   - `overwrite`: replace this file with the template.
   - `keep`: leave this file as it is.
   - `merge`: analyze the differences and propose a merged version for the user to decide on.
3. Apply each decision only to the file it names. A decision for one file does not apply to another.
4. If a decision is missing, ask for it again.

At any point the user may `cancel`. This ends the run without modifying any target, regardless of decisions already given for other files. Treat an explicit refusal to decide as `cancel`.

### Merge Proposal

For each file the user chooses to `merge`:

1. Compare the template with the current file and group the differences:
   - template rules that are missing or outdated in the current file;
   - current content absent from the template, usually project-specific additions;
   - rules that contradict each other.
2. For each difference, recommend adopting the template, keeping the current content, or combining both, with a short reason. There is no record of earlier template versions, so mark any inference about whether content came from the project or from an earlier template as uncertain.
3. For `docs/index.md`, the proposal may add navigation entries for the entries found in Step 2. Read only what is needed to describe their reading scenarios.
4. Create a temporary file outside the target root with `mktemp`, record its path, write the complete proposal to it, and show its full contents.
5. Let the user approve it, request changes, `cancel`, or switch to `overwrite` or `keep`. After requested changes, update the temporary file and show it again.

A `merge` decision counts as resolved only after the user explicitly approves the exact proposal shown.

## Step 4: Create the Configuration

Proceed only when every conflict has an explicit `overwrite`, `keep`, or approved `merge` decision.

1. Create required parent directories when they do not exist.
2. Immediately before writing a `create` target, confirm that it still does not exist. If it now exists, mark it `failed` without writing.
3. Copy each `create` target and each `overwrite` target from its template with `cp <template> <target>`.
4. Copy each approved `merge` proposal from its temporary file with `cp <proposal> <target>`.
5. Leave `unchanged` and `keep` targets untouched.
6. Verify each written target with `cmp -s <source> <target>`, where the source is the template or the approved proposal. If verification fails, mark that target `failed` and report it without attempting a repair.

When one target fails, continue with the other target and do not roll back a target that passed verification.

Do not write targets through a text-editing or file-writing tool. Do not translate, expand, customize, or infer project-specific content while copying templates; a merged target may differ from the template only as shown in the approved proposal.

Only create or replace the two mapped target files and any missing parent directories required for them. Do not modify or delete other files, including other content under `docs/`.

## Temporary Files

On every exit path, including `cancel`, a switched decision, and success, remove the temporary proposal files this run created. Keep the proposal of a `failed` merge target and report its path so the user can recover the approved content.

## Step 5: Report the Result

Report the outcome for each of the two targets:

- `created`: the target did not exist and was written from the template.
- `replaced`: a conflict the user chose to overwrite was replaced with the template contents.
- `merged`: a conflict was replaced with the user-approved merge proposal.
- `kept`: a conflict the user chose to keep was left untouched.
- `unchanged`: the target already matched the template and was left untouched.
- `blocked`: the target was skipped; report the reason found in Step 2.
- `failed`: the target could not be written or verified; report the error, the target's current state, and any retained proposal path.

When `docs/index.md` is not `kept` or `blocked` and does not link some entries found in Step 2, list those entries, state that they are not yet indexed, and recommend adding them to the navigation as a follow-up. Do not edit `docs/index.md` to index them.

When `AGENTS.md` was written, mention that Claude Code users can load it by adding `@AGENTS.md` to the project's `CLAUDE.md`, unless an existing `CLAUDE.md` already references it.

If the user cancelled, state that initialization was not performed and confirm that no files were modified.

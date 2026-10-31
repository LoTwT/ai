---
name: agent-config-setup
description: "Initialize project-level Agent configuration by creating AGENTS.md and docs/index.md from bundled reference templates. Trigger when the user asks to initialize or create project Agent configuration, such as '初始化 Agent 配置', '创建 AGENTS.md', or 'setup agent config'."
---

# Agent Config Setup

Initialize project-level Agent configuration from the bundled reference templates.

## Step 1: Resolve the Target Project Root

Resolve the target project root in this order:

1. Use the directory explicitly supplied by the user.
2. Otherwise, when the current directory is inside a Git repository, use the repository root.
3. Otherwise, use the current working directory.

The resolved target root must already exist and be a directory. Do not create a missing project root. Stop and report the path when this requirement is not met.

## Step 2: Inspect the Target State

Process only these template mappings. Template paths are relative to this skill's directory; target paths are relative to the target root.

- `references/AGENTS.md` → `AGENTS.md`
- `references/docs/index.md` → `docs/index.md`

Before writing anything:

1. Check every target file and its parent path without following symbolic links.
2. Compare each existing regular target file with its template using `cmp -s <template> <target>`. Do not compare by reading and re-rendering the contents.
3. Classify each target as:
   - `create`: the target does not exist, and its parent path is either missing or a real directory.
   - `unchanged`: the target is a regular file and `cmp` reports it identical to the template.
   - `conflict`: the target is a regular file and `cmp` reports a difference.
   - `blocked`: the target exists but is not a regular file, the target cannot be read, or its parent path exists but is not a real directory (including a symbolic link to a directory).
4. List existing entries under `docs/` other than `docs/index.md`, without reading or modifying them. Use this list only for the Step 5 report.

Inspect both targets before taking any write action. If any target is `blocked`, stop, report every blocked path, and leave all targets unchanged. Do not replace or write through directories, symbolic links, or other non-regular paths.

## Step 3: Handle Conflicts

When any target is classified as `conflict`:

1. Do not create, overwrite, or otherwise modify any target yet.
2. Preserve every existing file and directory.
3. Show each conflicting path with a concise difference summary.
4. For each conflicting file, ask the user to choose one of:
   - `overwrite`: replace this file with the template.
   - `keep`: leave this file as it is and continue with the other targets.
   - `cancel`: stop initialization without modifying any target.
5. Apply each decision only to the file it names. A decision for one file does not apply to another.

If the user chooses `cancel`, or does not give an explicit `overwrite` or `keep` decision for every conflicting file, leave all targets unchanged and report that initialization was not performed.

## Step 4: Create the Configuration

Proceed only when every conflict has an explicit `overwrite` or `keep` decision.

1. Create required parent directories when they do not exist.
2. Copy each `create` target and each `overwrite` target from its template with `cp <template> <target>`, so the target is byte-identical to the template. Do not write templates through a text-editing or file-writing tool.
3. Leave `unchanged` and `keep` targets untouched.
4. Verify each written target with `cmp -s <template> <target>`.

Do not translate, expand, customize, or infer project-specific content while copying templates.

Only create or replace the two mapped target files and any missing parent directories required for them. Do not modify or delete other files, including other content under `docs/`.

## Step 5: Report the Result

After Step 4 completes, report the outcome for each of the two targets:

- `created`: the target did not exist and was written from the template.
- `replaced`: a conflict the user chose to overwrite was replaced with the template contents.
- `kept`: a conflict the user chose to keep was left untouched.
- `unchanged`: the target already matched the template and was left untouched.

When `docs/index.md` holds the template contents after Step 4 and Step 2 found other entries under `docs/`, list those entries, state that they are not yet indexed, and recommend adding them to the navigation as a follow-up. Do not edit `docs/index.md` to index them.

If initialization was not performed because of `cancel` or a missing decision, state that explicitly and confirm that no files were modified.

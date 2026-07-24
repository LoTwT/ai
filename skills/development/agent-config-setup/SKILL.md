---
name: agent-config-setup
description: "Initialize project-level Agent configuration by creating AGENTS.md, CLAUDE.md, and docs/index.md from bundled reference templates. Trigger when the user asks to initialize or create project Agent configuration, such as '初始化 Agent 配置', '创建 AGENTS.md 和 CLAUDE.md', or 'setup agent config'."
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

Process only these template mappings:

- `references/AGENTS.md` → `AGENTS.md`
- `references/CLAUDE.md` → `CLAUDE.md`
- `references/docs/index.md` → `docs/index.md`

Before writing anything:

1. Check every target file and its parent path.
2. Stop and report the affected path if a required parent path exists but is not a directory.
3. Compare each existing target file with its corresponding template using exact file contents.
4. Classify each target as:
   - `create`: the target does not exist.
   - `unchanged`: the target is a regular file and matches the template exactly.
   - `conflict`: the target is a regular file but differs from the template.
   - `blocked`: the target exists but is not a regular file.

Inspect all three targets before taking any write action. If any target is `blocked`, stop, report every blocked path, and leave all targets unchanged. Do not replace directories, symbolic links, or other non-regular paths.

## Step 3: Handle Conflicts

When any target is classified as `conflict`:

1. Do not create, overwrite, or otherwise modify any target yet.
2. Preserve every existing file and directory.
3. Show the conflicting paths and a concise difference summary when the target is a readable regular file.
4. Ask whether to overwrite the explicitly listed conflicting files or cancel.
5. Treat confirmation as applying only to the exact files listed in that preview. Authorization to overwrite one file does not authorize overwriting another.

If the user does not explicitly authorize every conflicting file, leave all targets unchanged and report that initialization was not performed.

## Step 4: Create the Configuration

Proceed only when there are no unresolved conflicts.

1. Create required parent directories when they do not exist.
2. Copy each target classified as `create` to its mapped target path using the template's exact contents.
3. For an explicitly authorized conflict, replace only the target files named in the confirmed preview with their corresponding exact template contents.
4. Leave `unchanged` targets untouched.

Do not translate, expand, customize, or infer project-specific content while copying templates.

Only create or replace the three mapped target files and any missing parent directories required for them. Do not modify or delete other files, including other content under `docs/`.

## Step 5: Report the Result

After Step 4 completes, report the outcome for each of the three targets:

- `created`: the target did not exist and was written from the template.
- `replaced`: an authorized conflict was overwritten with the template contents.
- `unchanged`: the target already matched the template and was left untouched.

If initialization was not performed because not every conflict was authorized, state that explicitly and confirm that no files were modified.

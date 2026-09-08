# Commit messages

Read this for generation, validation, or final message preparation.

Select the task: generate from a selected diff; validate supplied text against that diff; or validate rules only without asserting change accuracy. Do not stage files or create a commit in message-only mode. If the selected diff is empty, say so instead of inventing a change.

Discover repository message requirements in applicable instructions, contribution documentation, and configured tooling such as commitlint, and follow those requirements for generation and validation. Respect explicit requests and the normal instruction hierarchy. When the repository defines no message convention, default to [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/). Nearby commits can inform wording but cannot override requirements, replace that fallback, or prove that a test ran.

For the default, use `<type>[optional scope][!]: <description>` with a type matching the change: `feat` for a feature, `fix` for a bug fix, or another appropriate type. Enclose a scope in parentheses, as in `fix(search): handle empty queries`. Scope, body, and footers are optional unless required by the change or an applicable rule. Mark breaking changes with `!` or a `BREAKING CHANGE:` footer. Do not invent a repository-specific type list, scope list, or subject-length limit from the general convention.

Describe the final actual selection, not the whole working tree or abandoned attempts. Mention behavior, reason, and relevant validation; do not enumerate files when that obscures the change. Preserve required issue references and breaking-change information when supported by evidence.

Validate the exact full message: required subject format, allowed scope/type where applicable, body/footer requirements, truthful test claims, and consistency with selected changes. Explain meaningful normalization to supplied text; do not silently change its intent.

## Attribution and execution provenance

Author/committer selection belongs to identity handling, not message trailers. Add co-author or sign-off trailers only with appropriate evidence and authorization. Never claim DCO/CLA acceptance or human participation from inference.

When applicable instructions require Agent-Tool, Agent-Model, or Agent-Effort, use only exact runtime-provided values or explicit overrides for this operation. Omit unavailable optional fields. If a required field is unavailable, report that specific missing input. Do not infer provenance from stored preferences, model families, repository files, or previous tasks.

Keep user-supplied legitimate trailers intact and avoid duplicate/conflicting keys. Do not auto-append provenance when no applicable instruction requires it.

## Deliver

Return the final message and any concrete validation gaps. For execution, store the exact message as UTF-8 in a temporary file and use an argument vector. Do not construct a shell command by interpolating multiline message text. Read the stored commit message back after execution because hooks and cleanup settings can change it.

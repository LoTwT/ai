# Commit messages

Read this for generation, validation, or final message preparation.

Select the task: generate from a selected diff; validate supplied text against that diff; or validate rules only without asserting change accuracy. Do not stage files or create a commit in message-only mode. If the selected diff is empty, say so instead of inventing a change.

Discover repository message requirements in applicable instructions, contribution documentation, and configured tooling such as commitlint, and follow those requirements for generation and validation. Respect explicit requests and the normal instruction hierarchy. When the repository defines no message convention, default to [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/). Nearby commits can inform wording but cannot override requirements, replace that fallback, or prove that a test ran.

Write commit messages in English by default. Follow a different language when explicitly requested by the user or specified by applicable repository instructions, contribution documentation, or configuration files, respecting instruction precedence. Configuration that only defines message format does not override the default language.

For the default, use `<type>[optional scope][!]: <description>` with a type matching the change: `feat` for a feature, `fix` for a bug fix, or another appropriate type. Enclose a scope in parentheses, as in `fix(search): handle empty queries`. Scope, body, and footers are optional unless required by the change or an applicable rule. Mark breaking changes with `!` or a `BREAKING CHANGE:` footer. Do not invent a repository-specific type list, scope list, or subject-length limit from the general convention.

Describe the final actual selection, not the whole working tree or abandoned attempts. Mention behavior, reason, and relevant validation; do not enumerate files when that obscures the change. Preserve required issue references and breaking-change information when supported by evidence.

Validate the exact full message: required language and subject format, allowed scope/type where applicable, body/footer requirements, truthful test claims, and consistency with selected changes. Explain meaningful normalization to supplied text; do not silently change its intent.

## Attribution and execution provenance

Author/committer selection belongs to identity handling, not message trailers. Add co-author or sign-off trailers only with appropriate evidence and authorization. Never claim DCO/CLA acceptance or human participation from inference.

Record provenance when requested by the user or required by applicable instructions. Model/Effort provenance can contain one or more paired entries for the selected changes. Resolve each entry's values from reliable runtime evidence for that contribution or an explicit user override scoped to it. The committing agent's runtime does not establish another contributor's values. Do not infer provenance from stored preferences, role names, model families, repository files, or unrelated tasks.

The model component of each entry in the preview and `Agent-Models` trailer must contain that contribution's exact **model identity**. Preserve that identity verbatim. A client/tool name, UI display label, or configured model selector/alias alone does not establish model identity. The following effort component records reasoning effort; it is not part of the model identity.

Resolve each included entry independently. A different model or effort can form another entry; do not overwrite earlier entries that still describe the selected work. Ask only for missing required values or an ambiguous pairing, identifying the affected entry. Omit unavailable optional fields such as Agent-Tool; do not invent values or silently drop a required entry. Keep task-scoped values with their sources and contribution scope rather than making them defaults for other agents or tasks.

When recording Model/Effort pairs, write exactly one `Agent-Models` trailer on one physical line. Each entry is `<model> <effort>`; join entries with ` / ` (a slash with one space on each side). A single pair uses the same field without a separator. Do not also generate `Agent-Model` or `Agent-Effort` trailers. Illustrative values:

```text
Agent-Models: model-a high / model-b high / model-a max
```

Split only on ` / `, then on each entry's final space to recover its model and single-token effort. A slash inside a model identity such as `provider/model-a` is not a separator. If a supplied value contains a newline or the reserved delimiter, or the effort contains whitespace, ask for an unambiguous exact value rather than silently altering it. Reject empty entries or missing components.

Preserve each pairing and the supplied entry order. The same model with different efforts and different models with the same effort are valid. Do not independently deduplicate or reorder Model and Effort. Verify the single field and its full ordered list after committing.

Keep legitimate user-supplied trailers intact. Explain any conversion of supplied legacy provenance to this format, and resolve ambiguous pairings before conversion. Show provenance sources separately in the preview when required; source labels are not part of the `Agent-Models` value. Do not add entries beyond the requested or policy-required scope, or infer permission to amend an existing commit to retrofit them.

## Deliver

Return the final message and any concrete validation gaps. For execution, store the exact message as UTF-8 in a temporary file and use an argument vector. Do not construct a shell command by interpolating multiline message text. Read the stored commit message back after execution because hooks and cleanup settings can change it.

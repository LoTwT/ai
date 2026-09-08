# GitHub PR operations

Read this for PR creation and ordinary metadata updates.

## Resolve context

Use an explicit host and base repository; read base/head repository IDs, branches, current OIDs, fork parent/source, and any existing PR's author and state. Do not infer the source repository from a same-named local branch. Remote evidence can be sufficient without a checkout.

Read the API user with the same connector or process-scoped credential used for writing, for example `gh api --hostname HOST user --jq .login`. An environment token can override a stored active account. Use existing credential facilities without printing secrets, persisting a login switch, or broadening scopes. Apply applicable role rules and repository permissions; if evidence is insufficient, stop the write.

Read the PR template from the target repository's applicable base/default branch and relevant contribution instructions. If multiple mandatory templates cannot be selected from context, resolve that choice. Do not overwrite checklists with claims about checks that were not performed.

## Default PR description

When no applicable repository template or required description format exists, use the following fallback for a new PR. A failed template lookup does not establish absence. Respect explicit user formatting requests and localize headings and text to the requested or repository language.

```markdown
## Summary

<Explain the problem, resulting behavior, and relevant reason.>

## Validation

- <Checks actually performed and their results.>
- <Relevant validation not performed and why; omit if none.>
```

For small changes, one to three summary sentences are usually enough; expand when needed. Add key changes, impact and migration notes, screenshots, or related issues only when useful. Always explain actual breaking changes, required migrations, and prerequisite dependencies; separate sections are optional.

Start the body at heading level two without repeating the PR title. Remove placeholders and empty sections, and avoid redundant summaries or unsupported checklists. Report validation honestly, including when no checks were run; the template itself does not require extra tests.

When updating an existing PR, preserve its established structure unless the user requests reformatting.

## Create

Query all relevant open PRs for exact head repository/branch and base repository/branch. Paginate and compare repository IDs, not just owner/branch labels. Reuse a unique exact match; a same-head PR with another base needs examination rather than a duplicate by default.

Confirm the published head OID matches the intended changes. Prepare exact title/body and requested draft state. Use explicit head/base with `gh pr create` to avoid its implicit push/fork prompts, or use the documented create API. The CLI may not support every organization-owned head syntax; use a verified API equivalent rather than changing topology. Its dry-run option may still push, so preview locally.

## Update

Fetch the current target fields. Change only authorized fields. Preserve unrelated user edits and template content. Use explicit PR identity with `gh pr edit` or the corresponding API; draft/ready transitions may require a separate operation. Re-read after each requested change if later steps depend on it.

PR metadata APIs do not universally provide field-level compare-and-swap. Re-read just before writing, minimize changed fields, and compare the response; do not claim a race-free update. If concurrent user edits are observed, reconcile the actual delta before retrying.

Use structured request bodies or UTF-8 text files for arbitrary multiline content. Do not interpolate text into shell commands or invoke autofill without reviewing its complete output.

## Reentry

An error can occur after successful creation. Query the exact tuple and inspect the resulting PR before retrying. Check relevant closed/merged PRs when they may be the previous result; a new request is not automatically a reopen request. If two candidates remain plausible, ask which target is intended.

Verify URL/ID, author, head/base, OID, draft state, and changed fields. Return unresolved partial work without broadening the operation.

Sources: [GitHub PR creation](https://cli.github.com/manual/gh_pr_create), [GitHub pull-request API](https://docs.github.com/en/rest/pulls/pulls).

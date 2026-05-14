# From Zero To Shipped — npm Release Pipeline Runbook

Set up a tag-driven npm release pipeline backed by GitHub Actions OIDC
and npm Trusted Publisher.

**Audience**: technical operators and AI agents executing this
end-to-end. Steps are numbered and annotated; comments explain why a
step exists. Skip framing prose; read the commands.

**Scope**:

- pnpm only. npm / yarn paths are out of scope.
- Both monorepo (pnpm workspace) and single-package layouts.
- Two starting points: greenfield (first publish ever) and brownfield
  (packages already on npm).

---

## Outcome

A routine release after bootstrap:

```bash
# 1. Bump version (interactive picker, or explicit form).
pnpm release:bump                # interactive: pick patch | minor | major | ...
pnpm release:bump patch          # keyword form
pnpm release:bump 1.2.3          # explicit version

# bumpp updates package.json(s), runs `pnpm changelog` (git-cliff) via
# the `execute` hook, creates the release commit, tags `vX.Y.Z`, pushes.

# 2. CI (.github/workflows/release.yml) triggers on the tag push:
#    - validates metadata
#    - runs gates (build → check → test)
#    - publishes via `pnpm publish` over OIDC (no static secret)
#    - generates release notes via `git-cliff --latest`
#    - creates the GitHub Release
#    - runs post-publish registry-install smoke with retry-with-backoff

# 3. No reviewer approval in CI. The human gate is upstream:
#    only repo admins can push `v*.*.*` tags via a tag-protection ruleset.
```

The protection model: pushing a release tag is the human-in-the-loop.
CI is the deterministic continuation.

---

# Part I — Foundation

Set up once per repo. Sections are independent within Part I; skip
items already configured.

## 1. Concepts

### 1.1 OIDC + Trusted Publisher

- GitHub Actions can mint a short-lived OIDC token for the running job,
  with claims about repo / workflow / environment / ref.
- npm's Trusted Publisher feature accepts such tokens as a publish
  credential, replacing stored npm tokens entirely.
- A Trusted Publisher binding is a `(provider, owner, repo, workflow,
  environment)` tuple attached to a specific package on npmjs.com. The
  publish succeeds only if the OIDC token's claims match.

### 1.2 Tag push = human gate

After hardening (§5):

- `npm-publish` Environment has no Required reviewers — CI runs
  autonomously.
- A tag-protection ruleset restricts `v*.*.*` tag creation to admins.

Decision moment moves from "who clicks approve in CI" to "who can push
the release tag".

### 1.3 Two bootstrap paths

- **Greenfield (§7)**: no package on npm yet. v0.0.1 publishes manually
  from a local terminal (Trusted Publisher binding requires the package
  to exist on npm first). Then v0.0.2 validates OIDC publish.
- **Brownfield (§8)**: packages already on npm. Trusted Publisher
  attaches immediately. The next routine release ships over OIDC.

### 1.4 pnpm prerequisite

The runbook assumes pnpm as the package manager. Workspaces use
`pnpm-workspace.yaml`. Publishing uses `pnpm publish`. Install uses
`pnpm install`.

## 2. Repo prerequisites

### 2.1 Package layout

Two supported shapes:

**Monorepo (pnpm workspace)**

```yaml
# pnpm-workspace.yaml
packages:
  - 'packages/*'
```

```jsonc
// Root package.json
{
  "private": true,    // Root never publishes. Only workspace packages do.
  "name": "<repo>-monorepo",
  "version": "0.0.0",
  "scripts": { /* see §3 */ }
}
```

Every publishable workspace package:

```jsonc
// packages/<pkg>/package.json — scoped example.
{
  "name": "@<scope>/<pkg>",                 // Or "<pkg>" for an unscoped package.
  "version": "0.0.0",                       // Kept in sync by bumpp.
  "publishConfig": { "access": "public" },  // Required for scoped first-publishes; harmless on unscoped.
  "files": ["dist", "README.md", "LICENSE"], // What ships in the tarball.
  "exports": { /* public surface */ },
  "dependencies": {
    "@<scope>/<sibling>": "workspace:*"     // pnpm publish substitutes with release version.
                                            // Sibling can also be unscoped: "<sibling>": "workspace:*".
  }
}
```

Package names in this runbook are written as `@<scope>/<pkg>` for
brevity, but the pipeline supports unscoped names (`<pkg>`) equally —
both for single-package and monorepo workspace packages. Where it
matters (e.g. `--access public` semantics, `publishConfig.access`,
`workspace:*` substitution), the prose calls out the unscoped case
explicitly.

**Single-package — scoped**

```jsonc
// package.json at repo root (not private)
{
  "name": "@<scope>/<pkg>",
  "version": "0.0.0",
  "publishConfig": { "access": "public" },   // Required for scoped first-publish.
  "files": ["dist", "README.md", "LICENSE"],
  "exports": { /* public surface */ }
  // No `pnpm-workspace.yaml`. No `private: true`.
}
```

**Single-package — unscoped**

```jsonc
// package.json at repo root (not private)
{
  "name": "<pkg>",                            // No `@<scope>/` prefix.
  "version": "0.0.0",
  // No `publishConfig.access` — unscoped packages default to public on npm.
  "files": ["dist", "README.md", "LICENSE"],
  "exports": { /* public surface */ }
  // No `pnpm-workspace.yaml`. No `private: true`.
}
```

### 2.2 npm scope ownership (one-time)

- Org scope: account needs **publish** rights on the org.
- Personal scope: account owns it implicitly.

Out of pipeline; do once before bootstrap.

### 2.3 GitHub admin

The publishing identity needs **admin** on the GitHub repo (§5
ruleset requires admin to configure).

### 2.4 Conventional Commits + commitlint

git-cliff parses Conventional Commits to bucket entries into Added /
Fixed / Changed. Common types: `feat:`, `fix:`, `docs:`, `chore:`,
`refactor:`, `test:`, `perf:`, `style:`. `feat!:` / `fix!:` denote a
breaking change. PR titles squash-merge into Conventional Commits.

Choose the commit type by release-visible value, not only by the file
paths changed. Ordinary test-only work can stay `test:` and be skipped
from CHANGELOG, but a project-specific test fixture that advertises a
new public contract may deserve a release-note type/scope such as
`feat(<scope>):`.

Lint enforcement via `commitlint` + `simple-git-hooks` (§3.4).

### 2.5 CI baseline

PR-side CI (lint / test / build) green. Same pnpm + Node versions as
release.yml will use. Drift between PR-CI and release-CI Node majors
produces release-time surprises.

### 2.6 npm CLI version

Local `npm` and CI runner `npm` ≥ 11.5.1 (OIDC publish support).

```bash
npm --version
# Expected: 11.5.1 or newer.
```

## 3. Tools and in-repo files

Each tool does one thing.

### 3.1 bumpp

Atomically bumps versions, runs an `execute` command, commits, tags,
pushes.

**Default path**: `bump.config.ts` + the bumpp CLI.

```ts
// bump.config.ts
import { execSync } from "node:child_process"
import { resolve } from "node:path"
import { defineConfig } from "bumpp"

export default defineConfig({
  // Files bumpp bumps versions in. CHANGELOG.md is NOT listed here —
  // bumpp would rewrite every version-like string in the changelog
  // (including past version headers), corrupting history.
  files: [
    "package.json",             // Always.
    "packages/*/package.json",  // Monorepo only; remove for single-package.
  ],
  commit: true,
  tag: true,
  push: true,
  install: false,
  recursive: false,             // Files list is explicit; no need to recurse.
  noGitCheck: false,            // Block dirty working tree.

  // `execute` runs AFTER bumpp updates `files`, BEFORE the release commit.
  // We regenerate CHANGELOG.md via git-cliff, then add CHANGELOG.md to
  // bumpp's `updatedFiles` so it ships in the release commit + tag.
  // Using `operation.update({ updatedFiles })` is the safe path:
  // listing CHANGELOG.md in `files` would trigger the version-string
  // rewrite described above.
  execute: (operation) => {
    execSync("pnpm changelog", {
      cwd: operation.options.cwd,
      stdio: "inherit",
    })

    operation.update({
      updatedFiles: [
        ...operation.state.updatedFiles,
        resolve(operation.options.cwd, "CHANGELOG.md"),
      ],
    })
  },
})
```

```jsonc
// package.json scripts
{
  "scripts": {
    "release:bump": "bumpp",
    "changelog": "git-cliff --output CHANGELOG.md"
  }
}
```

Invocation forms — all valid:

```bash
pnpm release:bump            # Interactive: pick patch | minor | major | prepatch | ...
pnpm release:bump patch      # Keyword form.
pnpm release:bump minor
pnpm release:bump major
pnpm release:bump 1.2.3      # Explicit version.
pnpm release:bump 1.0.0-beta.1   # Pre-release.
```

**Alternative path**: `scripts/release-bump.mjs` calling bumpp's
exported `versionBump()`.

Use when `bump.config.ts` can't express the constraint. Triggers:

- Dynamic `files` list resolved from disk at run time.
- Pre-bump preconditions (e.g. require clean working tree + green CI on
  HEAD before bumping).
- Post-bump side effects (e.g. update a separate version-stamp file).
- Wrapping bumpp inside a multi-step composite (e.g. lint changelog
  before tagging).

Minimal wrapper shape:

```js
// scripts/release-bump.mjs
import { execFileSync, execSync } from "node:child_process"
import { resolve } from "node:path"
import { versionBump } from "bumpp"

const releaseArg = process.argv[2]

// Example precondition: require main + upstream tracking.
const branch = execFileSync("git", ["branch", "--show-current"], { encoding: "utf8" }).trim()
if (branch !== "main") {
  console.error(`Release bump must run from main, got "${branch}"`)
  process.exit(1)
}

await versionBump({
  release: releaseArg ?? "patch",
  // Same constraint as the default `bump.config.ts`: CHANGELOG.md is NOT
  // listed here. It's added to bumpp's staging via `execute` below; listing
  // it in `files` would let bumpp rewrite past version headers.
  files: ["package.json", "packages/*/package.json"],
  commit: true,
  tag: true,
  push: true,
  // Mirror the default config's execute-function pattern so CHANGELOG.md
  // ships in the release commit without falling into the rewrite trap.
  execute: (operation) => {
    execSync("pnpm changelog", {
      cwd: operation.options.cwd,
      stdio: "inherit",
    })

    operation.update({
      updatedFiles: [
        ...operation.state.updatedFiles,
        resolve(operation.options.cwd, "CHANGELOG.md"),
      ],
    })
  },
})
```

```jsonc
// package.json scripts (alternative path)
{
  "scripts": {
    "release:bump": "node scripts/release-bump.mjs"
  }
}
```

### 3.2 git-cliff

Generates CHANGELOG.md and GitHub Release notes from Conventional
Commits.

```toml
# cliff.toml
[changelog]
header = """
# Changelog

All notable changes to this project are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
(simplified) and this project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

"""
body = """
{% if version %}\
## [{{ version | trim_start_matches(pat="v") }}] - {{ timestamp | date(format="%Y-%m-%d") }}
{% else %}\
## [Unreleased]
{% endif %}\
{% for group, commits in commits | group_by(attribute="group") %}
### {{ group | upper_first }}
{% for commit in commits %}
- {{ commit.message | upper_first }}\
{% endfor %}
{% endfor %}\n
"""
trim = true

[git]
conventional_commits = true
filter_unconventional = false
commit_parsers = [
  # Add project-specific release-visible scopes above the generic parser
  # when needed, e.g. { message = "^feat\\(<scope>\\)", group = "<Group>" }.
  { message = "^feat",     group = "Added" },
  { message = "^fix",      group = "Fixed" },
  { message = "^docs",     group = "Documentation" },
  { message = "^perf",     group = "Performance" },
  { message = "^refactor", group = "Changed" },
  { message = "^chore",    skip  = true },
  { message = "^test",     skip  = true },
  { message = "^style",    skip  = true },
  { message = ".*",        group = "Other" },
]
filter_commits = false
tag_pattern = "v[0-9]+\\.[0-9]+\\.[0-9]+"
```

Two outputs driven by the same config:

```bash
# Full CHANGELOG.md (run via bumpp's `execute` hook before each release).
git-cliff --output CHANGELOG.md

# Latest-version-only (piped to GitHub Release body in §4).
git-cliff --latest --output /tmp/release-notes.md
```

### 3.3 pnpm publish

Handles topology, `workspace:*` substitution, provenance, and single-
vs multi-package invocation.

Publish commands differ along two axes: monorepo vs single-package
(use `-r` or not), and local-from-main vs CI-tag-triggered
(`--no-git-checks` only in CI). The four combinations:

| Context | Monorepo | Single-package |
|---|---|---|
| **Local manual publish** (from `main`, clean tree, HEAD = tag) | `pnpm -r publish --access public` | `pnpm publish --access public` |
| **CI publish** (tag-triggered, detached HEAD on the tag commit) | `pnpm -r publish --access public --no-git-checks` | `pnpm publish --access public --no-git-checks` |

Flag reference:

- `-r` — recurse workspace packages, skips private root, topological
  publish order. Monorepo only.
- **Bail behavior** — `pnpm` recursive commands bail (fail-fast) by
  default; the opt-out is `--no-bail`. Do **not** pass `--no-bail` in
  release publish: continuing after a failure leaves a partial-publish
  state that's hard to reason about. There is no `--bail` flag to set;
  the default already is bail.
- `--access public` — required for scoped first-publishes. Harmless on
  unscoped packages (npm accepts but ignores; unscoped packages default
  to public). Safe to leave on in every command.
- `--no-git-checks` — skip pnpm's "must publish from main / clean tree
  / tag-at-HEAD" checks. Required in CI because tag-triggered checkout
  is a detached HEAD. **Not** used in local publish from `main` — the
  default checks should pass, and skipping them silently in local flow
  hides drift.
- `--provenance` — **do not pass this flag.** Under npm Trusted
  Publishing (OIDC), provenance attestations are generated
  server-side automatically; passing `--provenance` on the client
  triggers a duplicate sigstore-transparency-log entry that fails the
  publish with `TLOG_CREATE_ENTRY_ERROR`. This applies to both local
  and CI publishes. The OIDC-published versions still carry
  provenance attestations on npm (verify with
  `npm view <pkg>@<X.Y.Z> --json | jq '.dist.attestations'`); the
  flag is only relevant to legacy static-token publishes and is
  incompatible with Trusted Publishing.

`pnpm -r` topologically orders publishes: a package's workspace deps
publish before it. `workspace:*` references are rewritten to the
literal release version in the published tarball — no prepare script
needed.

**Caveat vs `npm publish`**: `pnpm publish` does not write the
`gitHead` metadata field. This pipeline does not rely on `gitHead`;
retry-safety comes from pnpm's own "version already exists" error
(§4 step 5). See §12 (Glossary) for what `gitHead` is.

Source: <https://pnpm.io/cli/publish>, <https://docs.npmjs.com/cli/v11/commands/npm-publish/>.

### 3.4 commitlint + simple-git-hooks

Enforce Conventional Commits at commit time via a local git hook.

Install:

```bash
pnpm add -D @commitlint/cli @commitlint/config-conventional simple-git-hooks
```

```jsonc
// package.json
{
  "scripts": {
    "prepare": "simple-git-hooks"
  },
  "simple-git-hooks": {
    "commit-msg": "pnpm exec commitlint --edit $1"
  }
}
```

```js
// commitlint.config.js — requires `"type": "module"` in package.json.
// If the project is CommonJS, rename to `commitlint.config.cjs` and use
// `module.exports = { extends: ["@commitlint/config-conventional"] }`.
export default {
  extends: ["@commitlint/config-conventional"],
}
```

After `pnpm install`, simple-git-hooks installs `.git/hooks/commit-msg`
which runs commitlint against each commit message. Non-conforming
messages fail locally before commit.

CI-side lint is **not** added — local enforcement is sufficient for
this pipeline. Contributors without the hook (e.g. unintentional skip)
will not get caught at PR time; rely on PR review.

### 3.5 GitHub Actions used

| Action | First-party? | Notes |
|---|---|---|
| `actions/checkout@v6` | Yes | Use `fetch-depth: 0` so git-cliff can read full history. |
| `pnpm/action-setup@v6` | Official | pnpm's own action. |
| `actions/setup-node@v6` | Yes | Provides `registry-url: https://registry.npmjs.org` so OIDC publish works. |
| `softprops/action-gh-release@v2` | Third-party | ~5k stars, actively maintained. Used for GitHub Release creation. **Pin to commit SHA when adopting** — see §3.6. |

### 3.6 Third-party Action policy

A third-party Action is acceptable when:

1. Value clearly exceeds custom-bash cost (rule of thumb: replaces > 20
   lines of reliable bash, or handles a non-trivial API edge).
2. The Action has stars, active usage, and active maintenance (check
   stars + last commit + open issue ratio).

When introducing a new third-party Action:

- Pin to commit SHA in release.yml, not floating `@vN` tag.
- Note maintenance state (last release date, stars, known
  advisories) in the introducing PR's description.

Bash logic stays inline. `git-cliff` runs via `npx` rather than a
wrapper Action.

## 4. Release workflow (`.github/workflows/release.yml`)

Triggered on push to `refs/tags/v*.*.*`. One workflow file works for
both monorepo and single-package — `pnpm publish` invocation differs
on one line (§3.3).

```yaml
name: Release

on:
  push:
    tags:
      - 'v*.*.*'

permissions:
  contents: write    # GitHub Release creation
  id-token: write    # npm OIDC

jobs:
  publish:
    runs-on: ubuntu-latest
    environment: npm-publish
    steps:
      # 1. Checkout — full history so git-cliff can read tags + commits.
      - uses: actions/checkout@v6
        with:
          fetch-depth: 0

      # 2. Set up pnpm and Node.
      - uses: pnpm/action-setup@v6
        with:
          version: 10.33.0
      - uses: actions/setup-node@v6
        with:
          node-version: 24
          registry-url: https://registry.npmjs.org

      # 3. Validate release metadata: tag ↔ version ↔ commit ↔ main ↔ npm CLI.
      - name: Validate release metadata
        id: release
        run: |
          set -euo pipefail
          TAG="${GITHUB_REF_NAME}"
          [[ "$TAG" =~ ^v[0-9]+\.[0-9]+\.[0-9]+(-[0-9A-Za-z.-]+)?$ ]] \
            || { echo "Tag $TAG does not match v*.*.* format" >&2; exit 1; }
          VERSION="${TAG#v}"
          PKG_VERSION="$(node -p "require('./package.json').version")"
          [ "$PKG_VERSION" = "$VERSION" ] \
            || { echo "package.json version ($PKG_VERSION) != tag ($VERSION)" >&2; exit 1; }
          [ "$(git log -1 --pretty=%s)" = "chore: release v$VERSION" ] \
            || { echo "Release commit message mismatch" >&2; exit 1; }
          git fetch origin main:refs/remotes/origin/main --tags
          git merge-base --is-ancestor HEAD origin/main \
            || { echo "Release commit is not an ancestor of origin/main" >&2; exit 1; }
          # Require npm >= 11.5.1 for OIDC publish.
          node -e "
            const v=process.argv[1].split('.').map(Number);
            const r=[11,5,1];
            for(let i=0;i<3;i++){
              if(v[i]>r[i])process.exit(0);
              if(v[i]<r[i]){console.error('npm '+v.join('.')+' < 11.5.1');process.exit(1);}
            }" "$(npm --version)"
          echo "version=$VERSION" >> "$GITHUB_OUTPUT"

      # 4. Install deps + run gates.
      #    Order: build → check → test.
      #    Reason: workspace package types resolve only after build; check / test
      #    that span workspace boundaries depend on built dist/.
      - run: pnpm install --frozen-lockfile
      - run: pnpm build
      - run: pnpm check
      - run: pnpm test

      # 5. Publish.
      #    Monorepo: pnpm -r publish (topology + workspace:* substitution).
      #    Single-package: pnpm publish (drop `-r`).
      #    pnpm recursive commands bail by default; do not pass --no-bail.
      #    Do NOT pass --provenance — Trusted Publishing generates the
      #    provenance attestation server-side; the client flag triggers
      #    TLOG_CREATE_ENTRY_ERROR. See §3.3 flag reference.
      #    Retry-safety: if a rerun finds the version already on npm,
      #    pnpm errors "version already exists" and the job fails fast.
      #    No pre-existence check needed.
      - name: Publish
        id: publish
        run: pnpm -r publish --access public --no-git-checks

      # 6. Generate release notes.
      #    Release creation is gated by publish success, not by registry
      #    propagation. npm has already accepted the immutable version; create
      #    the GitHub Release before post-publish smoke so propagation tail
      #    cannot force a manual Release recovery.
      #    `npx --yes git-cliff` fetches and runs git-cliff on demand;
      #    pin a specific git-cliff version (e.g. `npx --yes git-cliff@2.x.y`)
      #    if the repo wants deterministic binary selection.
      - name: Generate release notes
        id: release_notes
        if: always() && steps.publish.outcome == 'success'
        run: |
          set -euo pipefail
          npx --yes git-cliff --latest --output /tmp/release-notes.md
          echo "--- /tmp/release-notes.md ---"
          cat /tmp/release-notes.md

      # 7. Create / update the GitHub Release.
      #    PIN TO COMMIT SHA per §3.6. Look up the vetted SHA at
      #    https://github.com/softprops/action-gh-release/commits
      #    and replace `<sha>` before merging.
      - name: Create GitHub Release
        if: always() && steps.publish.outcome == 'success' && steps.release_notes.outcome == 'success'
        uses: softprops/action-gh-release@<sha>   # replace <sha> with the pinned commit SHA
        with:
          body_path: /tmp/release-notes.md
          tag_name: ${{ github.ref_name }}
          name: ${{ github.ref_name }}
          draft: false
          prerelease: false
          fail_on_unmatched_files: false

      # 8. Post-publish registry install smoke with retry-with-backoff.
      #    npm CDN propagation usually completes in 10-60s after publish, but
      #    can tail into several minutes. Smoke is intentionally post-release:
      #    publish success is enough to create the GitHub Release, while a
      #    failed smoke keeps the workflow red so QA can distinguish
      #    propagation lag from a real install/runtime failure.
      - name: Registry install smoke
        if: always() && steps.publish.outcome == 'success'
        env:
          VERSION: ${{ steps.release.outputs.version }}
        run: |
          set -euo pipefail
          TMP_DIR="$(mktemp -d)"
          cd "$TMP_DIR"
          npm init -y >/dev/null
          # Replace with every package that must be user-installable together.
          PACKAGES=(
            "<your-entry-pkg>"
            # "@<scope>/<sibling-pkg>"
          )
          INSTALL_SPECS=()
          for PACKAGE in "${PACKAGES[@]}"; do
            INSTALL_SPECS+=("${PACKAGE}@${VERSION}")
          done
          MAX_ATTEMPTS=20
          DELAY=60
          ATTEMPT=1

          while true; do
            MISSING=()
            for PACKAGE in "${PACKAGES[@]}"; do
              if PACKAGE_VERSION="$(npm view "${PACKAGE}@${VERSION}" version 2>/dev/null)"; then
                echo "npm registry has ${PACKAGE}@${PACKAGE_VERSION}"
              else
                MISSING+=("$PACKAGE")
              fi
            done

            if [ "${#MISSING[@]}" -eq 0 ]; then
              if npm install "${INSTALL_SPECS[@]}" >/dev/null 2>&1; then
                echo "npm install succeeded on attempt $ATTEMPT"
                break
              fi
              echo "npm install attempt $ATTEMPT failed after all package versions were visible; retrying in case tarball propagation is lagging..."
              rm -rf node_modules package-lock.json
            else
              echo "npm registry propagation attempt $ATTEMPT missing: ${MISSING[*]}"
            fi

            if [ "$ATTEMPT" -ge "$MAX_ATTEMPTS" ]; then
              {
                echo "### Registry install smoke failed"
                echo ""
                echo "- Version: ${VERSION}"
                echo "- Attempts: ${MAX_ATTEMPTS}"
                echo "- Delay: ${DELAY}s"
                echo "- Missing packages on final attempt: ${MISSING[*]:-none}"
                echo ""
                echo "The publish step succeeded and the GitHub Release was already created. Treat this as a post-publish consumer smoke failure: verify npm package versions, provenance, and a fresh install before declaring release-ready."
              } >> "$GITHUB_STEP_SUMMARY"
              echo "registry install smoke timed out after $MAX_ATTEMPTS attempts (~$((MAX_ATTEMPTS * DELAY))s). Publish succeeded and GitHub Release creation already ran; verify with npm view/provenance/fresh install before declaring release-ready." >&2
              echo "Final npm view diagnostics:" >&2
              for PACKAGE in "${PACKAGES[@]}"; do
                npm view "${PACKAGE}@${VERSION}" version || true
              done
              echo "Final npm install diagnostics:" >&2
              npm install "${INSTALL_SPECS[@]}"
              exit 1
            fi
            echo "waiting ${DELAY}s before retry..."
            sleep "$DELAY"
            ATTEMPT=$((ATTEMPT + 1))
          done

          # Add project-specific consumer checks here, for example:
          # - import the main library export;
          # - run the installed CLI --help;
          # - verify bundled JSON/data subpath exports.
```

## 5. GitHub repo configuration

Two pieces of config move the human gate from CI runtime to tag
creation. Configure both **after** the bootstrap path validates OIDC
end-to-end (§7.6 / §8.5).

### 5.1 Environment `npm-publish`

- Settings → Environments → New environment → name `npm-publish`.
- **During bootstrap**: add the publishing identity as **Required
  reviewer**. Each release pauses until clicked. This is the
  bootstrap-time guard.
- **After OIDC validation (§7.6 / §8.5)**: remove the Required reviewer.

### 5.2 Tag protection ruleset

- Settings → Rules → Rulesets → New ruleset → New tag ruleset.

| Field | Value |
|---|---|
| Name | `Protect release tags` |
| Enforcement status | Active |
| Target tags | `Include by pattern: v*.*.*` |
| Bypass list | `Repository admin` (role-based) |
| Rules | ☑ Restrict creations · ☑ Restrict updates · ☑ Restrict deletions |

Effect: only repo admins can create / update / delete `v*.*.*` tags.
All other tokens get rejected at the API level.

## 6. npm Trusted Publisher binding

Per-package, not per-repo. Configure each publishable package on
npmjs.com once it exists on the registry.

For each publishable package:

1. Package page → **Settings → Trusted Publisher → Add**.
2. Provider: **GitHub Actions**.
3. Owner: `<github-user-or-org>`.
4. Repository: `<repo>`.
5. Workflow filename: `release.yml` (must match path under
   `.github/workflows/`).
6. Environment: `npm-publish` (must match `environment:` key on the
   publish job).

A binding only attaches to an existing package. Greenfield (§7) solves
the chicken-and-egg with manual v0.0.1 first; brownfield (§8)
sidesteps because packages are already there.

If the binding's tuple doesn't match the OIDC token's claims at
publish time, npm rejects the publish. Diagnose by inspecting OIDC
token claims in the workflow log against the binding.

---

# Part II — Bootstrap

Pick one path. Both converge into Part III after bootstrap.

## 7. Path A — Greenfield (first publish)

### 7.1 Pre-flight

Run from a clean checkout of `main`.

```bash
# Repo state.
git status                                # Expected: working tree clean.
git branch --show-current                 # Expected: main.
git pull origin main                      # Sync.

# GitHub auth.
gh auth status                            # Expected: admin scope on the repo.

# npm auth.
npm whoami
# Expected: <your-npm-username>.
# If "npm error code ENEEDAUTH" / "not authenticated":
#   npm login --registry=https://registry.npmjs.org
#   # Browser opens; complete login; re-run `npm whoami`.

npm --version                             # Expected: >= 11.5.1.

# Have an npm 2FA device ready if your account requires it.
```

### 7.2 Manual v0.0.1 publish

The first publish runs from a local terminal using your `npm whoami`
identity. No fine-grained npm token in CI. The v0.0.1 tag's CI run will
fail at the publish step (no Trusted Publisher binding yet) — expected;
cancel it.

```bash
# 1. Bump to 0.0.1 from main.
pnpm release:bump 0.0.1
# bumpp: updates package.json file(s), runs `pnpm changelog` (git-cliff),
# creates `chore: release v0.0.1` commit, tags v0.0.1, pushes both.
# Stay on main — same session, no checkout needed.
```

```bash
# 2. The v0.0.1 tag push triggers release.yml. It will fail at publish
#    (no Trusted Publisher binding). Cancel it.
gh run list --workflow=release.yml --branch v0.0.1 --limit 1
gh run cancel <run-id>
```

```bash
# 3. Reinstall deps from the lockfile, run gates.
pnpm install --frozen-lockfile
pnpm build                                # Must run before check / test.
pnpm check
pnpm test
# If any gate fails: DO NOT publish. Fix forward in v0.0.2.
```

```bash
# 4. Pre-publish sanity check — verify main HEAD == release commit == v0.0.1 tag.
#    All three must hold before publishing. Any mismatch means main has drifted
#    (e.g. someone pushed a commit between bumpp and now); STOP, investigate,
#    do not use a detached-HEAD fallback. See §10.1 for the detached escape
#    hatch as a troubleshooting-only path.
git status --short                          # Expected: empty (clean tree).
git branch --show-current                   # Expected: main.
git describe --tags --exact-match HEAD      # Expected: v0.0.1.
```

```bash
# 5. Publish.
#    Monorepo:
pnpm -r publish --access public
#    Single-package (scoped or unscoped):
# pnpm publish --access public
#
# No `--no-git-checks`: we are on main with a clean tree and HEAD at the tag,
# so pnpm's default git checks should all pass.
# No `--provenance`: v0.0.1 manual publish runs under a static-token auth, not
# Trusted Publishing, so there's no OIDC context for provenance attestation.
# v0.0.1 ships without provenance; v0.0.2+ publishes under Trusted Publishing
# (OIDC) and gets server-side provenance automatically — also without the
# `--provenance` flag (see §3.3; the flag triggers TLOG_CREATE_ENTRY_ERROR
# under Trusted Publishing).
# No `--no-bail`: pnpm recursive commands bail by default; we want fail-fast
# on partial publish failures.
```

### 7.3 Configure Trusted Publisher

Walk §6 for each published package now that v0.0.1 exists on the
registry.

### 7.4 Manual GitHub Release for v0.0.1

The v0.0.1 CI run was cancelled, so no automated GitHub Release exists.
Create it manually from local git-cliff output:

```bash
# From any clean working tree at HEAD = the v0.0.1 release commit on main:
npx git-cliff --latest --output /tmp/release-notes-v0.0.1.md
gh release create v0.0.1 \
  --notes-file /tmp/release-notes-v0.0.1.md \
  --title v0.0.1 \
  --latest
gh release view v0.0.1                    # Verify: not draft, body matches.
```

### 7.5 v0.0.2 OIDC validation (throwaway patch)

Prove the OIDC publish path end-to-end with a small change.

```bash
# 1. Make any trivial change on main (docs typo / CHANGELOG fix / etc.).
#    Commit normally with a Conventional Commits message:
#    `docs: fix typo` etc.

# 2. From main:
pnpm release:bump 0.0.2
# bumpp creates the release commit + tag + push.

# 3. The tag push triggers release.yml. Publish step now runs via OIDC:
#    - runner asks GitHub for an OIDC token (`id-token: write` permission)
#    - npm verifies token claims against each Trusted Publisher binding
#    - publish proceeds — no static secret involved
#    - retry-with-backoff smoke, git-cliff release notes, GitHub Release
#      creation all run automatically.

# 4. Verify.
npm view @<scope>/<pkg>@0.0.2 version     # Expected: 0.0.2.
gh release view v0.0.2                    # Body from git-cliff --latest.
# Provenance: expected on v0.0.2; absent on v0.0.1.
```

### 7.6 Hardening

OIDC is now proven. Configure the long-term guards:

- §5.1: remove the `npm-publish` Environment Required reviewer.
- §5.2: add the `v*.*.*` tag protection ruleset.

The pipeline is now fully autonomous after `pnpm release:bump`.

## 8. Path B — Brownfield (existing packages)

Packages already manually published. Add the pipeline without
disrupting current habits, then upgrade to OIDC publish on the next
routine release.

### 8.1 Audit

Before adding anything, capture current state:

```bash
# Already-published versions per package.
npm view @<scope>/<pkg-a> versions
npm view @<scope>/<pkg-b> versions

# Existing workflows.
ls .github/workflows/
# Look for release.yml / publish.yml; decide: coexist or replace.

# Existing changelog state.
test -f CHANGELOG.md && head -30 CHANGELOG.md

# Existing release tooling.
grep -l "release\|publish\|bumpp\|changesets" package.json scripts/* 2>/dev/null

# Recent commit message style (will Conventional Commits adoption be a shift?).
git log --oneline --decorate -20
```

Decide:

- Does the new pipeline replace the old release flow on day one, or
  coexist temporarily?
- How to seed CHANGELOG.md (§8.2).

### 8.2 Add release tooling

Land the pieces from §3 on a normal PR (not yet a release):

- `bump.config.ts` (§3.1)
- `cliff.toml` (§3.2)
- `package.json` scripts: `release:bump`, `changelog`, `prepare`
  (§3.1 + §3.4)
- `simple-git-hooks` + `commitlint` config (§3.4)
- `.github/workflows/release.yml` (§4)

For CHANGELOG.md, choose one seeding strategy:

```bash
# A. Seed from full history (good for short history).
npx git-cliff --output CHANGELOG.md

# B. Seed from the most recent released tag forward.
npx git-cliff <last-released-tag>..HEAD --output CHANGELOG.md
# Older versions stay documented elsewhere (previous CHANGELOG / old
# release notes).

# C. Preserve existing hand-written CHANGELOG.md verbatim; future
#    releases prepend new entries on top.
npx git-cliff --prepend CHANGELOG.md
```

### 8.3 Configure Trusted Publisher

Packages already exist on npm — no chicken-and-egg. Walk §6 for each
published package immediately after the tooling PR merges.

### 8.4 First OIDC release

Pick the next routine fix / feature and ship it as the first
OIDC-driven release:

```bash
# From main, after the tooling PR is merged:
pnpm release:bump patch
# Tag push triggers release.yml. Publish, GitHub Release, then
# post-publish registry smoke — all over OIDC, no manual publish step.

# Verify.
npm view @<scope>/<pkg>@<new-version> version
gh release view v<new-version>
```

### 8.5 Hardening

Same as §7.6:

- Remove the `npm-publish` Environment Required reviewer.
- Add the `v*.*.*` tag protection ruleset.

---

# Part III — Operations

## 9. Routine release

After bootstrap, a release is just:

```bash
# From main.
pnpm release:bump patch                   # or `minor` / `major` / `1.2.3`.
# Watch the workflow run if you want:
gh run watch
```

**Same pipeline for all version classes**: patch, minor, and major
releases flow through the same CI pipeline; the only difference is the
version number the tag points to. The tag regex, release-commit
message, publish command, and git-cliff invocation are all
version-agnostic. Semver decisions (is this really a major?) belong in
PR review upstream, not at release time.

Acceptance criteria after every release (any version class):

```bash
# 1. npm registry has the version.
npm view @<scope>/<pkg>@<X.Y.Z> version       # Expected: X.Y.Z.

# 2. GitHub Release exists, body matches CHANGELOG.
gh release view v<X.Y.Z>                      # Expected: not draft, body present.

# 3. Provenance attestation present (for OIDC-published versions, i.e. v0.0.2+).
npm view @<scope>/<pkg>@<X.Y.Z> --json | jq '.dist.attestations'
# Expected: an object with at least a "provenance" attestation.
# Absent for v0.0.1 (manual local publish has no OIDC context).

# 4. Fresh install / import / CLI smoke passes.
# If CI post-publish smoke timed out, do this from a clean temp directory
# before declaring release-ready.
tmp="$(mktemp -d)" && cd "$tmp" && npm init -y
npm install @<scope>/<pkg>@<X.Y.Z>
# Then run project-specific import / CLI checks.
```

## 10. Rollback

When something goes wrong, **fix forward**. `npm deprecate
<pkg>@<bad> "use <good>"`, then ship the next patch. Never
`npm unpublish` outside a documented incident response — the 72-hour
window is narrow, the unpublished slot stays permanently unusable, and
npm treats it as a hard incident.

### 10.1 Per-step rollback table

| Step | Failure | Recovery |
|---|---|---|
| `release:bump` push fails | Retry `git push && git push --tags`. If pushed without tag: `git push origin v<X.Y.Z>`. |
| Tag pushed, CI hasn't started yet | `git push origin --delete v<X.Y.Z>` + `git revert <bump-commit>` + push; or fix-forward via v<X.Y.Z+1>. |
| `release:bump` exited mid-flight (workdir dirty + local tag) | `git checkout HEAD -- package.json packages/*/package.json && git tag -d v<X.Y.Z>`; rerun `release:bump`. |
| §7.2 sanity check fails: `main` HEAD has drifted from the tag commit (someone pushed) | **Default**: investigate the drift, coordinate with whoever pushed, prefer fix-forward via v<X.Y.Z+1> or revert the accidental commit. Only when you have confirmed no commits on `main` need to be preserved, a hard reset (`git reset --hard v<X.Y.Z>` + `git push --force-with-lease origin main`) is acceptable. **Troubleshooting-only escape hatch** (use sparingly): `git checkout v<X.Y.Z>` → re-verify all three pre-checks (`git status --short` empty + `git describe --tags --exact-match HEAD` = `v<X.Y.Z>` + `npm view <pkg>@<X.Y.Z> version` empty) → publish with detached-HEAD flag set, e.g. `pnpm -r publish --access public --no-git-checks` (monorepo) or `pnpm publish --access public --no-git-checks` (single-package). Not the default path; do not use without all three pre-checks. |
| Stale remote tag from a past dry-run | `git push origin --delete v<X.Y.Z>` (deleting tag ref; no force-push needed). |
| `pnpm publish` fails on package N after 1..N-1 succeeded | Investigate before rerun. Same tarball is idempotent; "version already exists" means earlier publishes succeeded. Choose: continue with N..end, or `npm deprecate` 1..N-1 and prep next patch. |
| OIDC publish fails (claims mismatch) | Check workflow `permissions:`, `environment:`, npm CLI version, Trusted Publisher binding tuple; rerun failed jobs. |
| Registry install smoke exhausts retries | Publish already succeeded and the GitHub Release should already exist. Do **not** blindly rerun the same tag: reruns may fail earlier with "version already exists". Verify `npm view <pkg>@<version> version`, npm provenance / attestations, and a fresh workstation install + import / CLI smoke. If those pass, record QA release-readiness as pass and track the smoke timeout as pipeline debt. If install/runtime still fails after propagation, fix-forward with the next patch. |
| `git-cliff --latest` output unexpected | Check `cliff.toml` `commit_parsers`, ensure tag pattern matches. Fix-forward via docs PR + next patch. |
| Trusted Publisher binding wrong | Edit on npmjs.com; affects the *next* release only. Already-published versions are unaffected. |
| Tag pushed by non-admin (after §5.2 ruleset) | Rejected by GitHub at the push API; nothing to roll back. |
| Production npm version turns out broken | `npm deprecate <pkg>@<bad> "use <good>"` + ship next patch. |

### 10.2 Generic principles

1. **Never `npm unpublish`** unless an incident runbook owner
   recommends it. `npm deprecate` is the fix-forward primitive.
2. **Fix-forward over rollback**: a bad version becomes evidence in
   the next patch's CHANGELOG.
3. **If two of N packages published and the third failed, stop**.
   Confirm earlier successes (`npm view <pkg>@<version>`) and the
   on-disk monorepo state before deciding to continue or
   deprecate-and-bump.
4. **Suspicious states deserve a pause**: copy verbatim error text,
   re-read the release log around the failure, talk to a reviewer
   before retrying more than once.

---

# Part IV — Reference

## 11. Glossary

| Term | Meaning |
|---|---|
| OIDC | OpenID Connect. GitHub Actions can mint short-lived ID tokens with claims about repo / workflow / environment. npm Trusted Publisher accepts these as a publish credential, eliminating stored tokens. |
| Trusted Publisher | npm setting on a package, binding it to a (provider, owner, repo, workflow, environment) tuple. A publish only succeeds if the OIDC token's claims match. |
| Provenance attestation | npm's signed metadata about how a package was built. Generated server-side automatically when publishing under npm Trusted Publishing (OIDC); **do not pass the `--provenance` client flag** — it triggers `TLOG_CREATE_ENTRY_ERROR`. Visible on the npm package page and via `npm view <pkg>@<X.Y.Z> --json | jq '.dist.attestations'`. |
| Conventional Commits | Commit message convention parsed by git-cliff to bucket changes into Added / Fixed / Changed / etc. |
| `gitHead` | npm's per-version metadata field recording the commit SHA the publish ran from. **Not** written by `pnpm publish`. This pipeline does not rely on it; traceability runs through the GitHub release tag. |
| Environment (GitHub) | A named scope inside a repo's Actions config carrying secrets, deployment branches, required reviewers, and OIDC sub-claims. The publish job's `environment:` key binds to one. |
| Tag protection ruleset | A GitHub repo Rule restricting who can create / update / delete tags matching a pattern. Used here to make `v*.*.*` tag pushes admin-only. |
| `npm deprecate` | Marks a published version as discouraged. Consumers see a deprecation warning at install time. The version stays installable. The standard "this release was bad, use a newer one" signal. |
| `npm unpublish` | Removes a published version from the registry. Allowed within 72 hours, only when no other package depends on it, and the slot stays permanently unusable. **Do not use** as routine rollback. |

## 12. Cross-links

- bumpp: <https://github.com/antfu-collective/bumpp>
- git-cliff: <https://github.com/orhun/git-cliff> · config:
  <https://git-cliff.org/docs/configuration>
- pnpm publish: <https://pnpm.io/cli/publish>
- GitHub Actions OIDC: <https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect>
- npm Trusted Publisher: <https://docs.npmjs.com/trusted-publishers>
- Conventional Commits: <https://www.conventionalcommits.org/>
- commitlint: <https://commitlint.js.org/>
- simple-git-hooks: <https://github.com/toplenboren/simple-git-hooks>
- softprops/action-gh-release: <https://github.com/softprops/action-gh-release>

## 13. When NOT to walk this on autopilot

- Multi-package repos where the publishable set changes between
  releases — keep `bump.config.ts` `files` list in sync.
- First publish under a new npm scope — needs scope-owner privileges
  (one-time, separate from this pipeline).
- Major version bumps — semver review belongs in PR review, not at
  release time. The pipeline is a delivery channel, not a quality
  gate for the change itself.
- Packages with native binaries / per-platform `optionalDependencies`
  — the linear `pnpm publish` flow needs per-platform jobs and a
  matrix; out of scope for this template.
- Independent versioning across packages in one workspace — this
  pipeline assumes synchronized versions (bumpp updates all
  publishable packages together). For independent versions, consider
  changesets instead; that's a different runbook.

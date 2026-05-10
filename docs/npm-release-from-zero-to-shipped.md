# From Zero To Shipped — npm Release Pipeline Runbook

A reference for setting up a tag-driven npm release pipeline backed by
GitHub Actions OIDC + npm Trusted Publisher, distilled from the
`LoTwT/design-system` v0.0.1 → v0.0.2 ship cycle (2026-05-08 → 2026-05-10).

## Target outcome

After Phases 0–5, a release looks like this:

1. `pnpm release:bump <X.Y.Z>` from `main` (run by an admin).
2. bumpp creates `chore: release vX.Y.Z` commit + tag `vX.Y.Z` and pushes both.
3. The tag push triggers `.github/workflows/release.yml`.
4. The workflow validates release metadata, runs gates, packs each
   package, publishes to npm via short-lived OIDC token (no static
   secrets), runs a registry install smoke with retry-with-backoff,
   then creates the GitHub Release.
5. No human approval needed *in* the CI run. The human gate is moved
   *upstream* to tag creation: only an admin can push `v*.*.*` tags via
   a repository tag-protection ruleset.

The protection model: **pushing a release tag is the human-in-the-loop**;
the CI is a deterministic continuation of that decision. Phase 6 covers
what to do when CI or publish goes wrong.

This doc walks each phase end-to-end. Use it once when bootstrapping a
new repo, then keep it around as a reference for the rare incident or
for porting the pipeline to another monorepo.

## Phase 0 — Repo prerequisites

Before any release tooling is added, the repo needs a shape that the
pipeline can target:

### 0.1 Workspace and package layout

- pnpm workspace, with `pnpm-workspace.yaml` listing the publishable
  packages (e.g. `packages/*`).
- A **private** root `package.json` (`"private": true`) — only workspace
  packages publish; the root never does.
- Each publishable package's `package.json` carries:
  - `"name"` under your npm scope (e.g. `@yourscope/<pkg>`)
  - `"version"` (kept in sync across all publishable packages by the
    bump script in Phase 1)
  - `"publishConfig": { "access": "public" }` — required for first-time
    publishes of scoped packages
  - `"files"` listing what ships in the tarball (tested by `npm pack`
    in CI)
  - `"exports"` describing the public surface

### 0.2 npm scope ownership (one-time)

Whichever account will be tied to the publish must own the npm scope.
For an org scope, it must have **publish** rights on the org. For a
personal scope, the account itself owns it. This is the only step that
is genuinely manual and outside the pipeline.

### 0.3 GitHub repo permissions and CI baseline

- The publishing identity (lo-user / agent) has **admin** on the GitHub
  repo. The hardening in Phase 4 depends on admin-level ruleset config.
- Existing CI (e.g. PR build / lint / test) is green and uses the same
  pnpm + Node versions the release workflow will use. If the release
  workflow uses a different Node major, expect drift.

## Phase 1 — Release scripts (in-repo files)

### 1.1 `scripts/release-bump.mjs`

A bumpp wrapper. Guards:

- must run from `main` with an upstream branch
- accepts a release type (patch / minor / major / explicit version)
- bumps every relevant `package.json` so versions move atomically
  (root + every publishable workspace package)

```js
#!/usr/bin/env node
import { execFileSync } from "node:child_process"
import { versionBump } from "bumpp"

const usage = "Usage: pnpm release:bump [version|major|minor|patch|...]"
const [, , releaseArg, ...extra] = process.argv
if (extra.length) {
  console.error(usage)
  process.exit(1)
}

const sh = (cmd, args) =>
  execFileSync(cmd, args, { encoding: "utf8" }).trim()
const branch = sh("git", ["branch", "--show-current"])
if (branch !== "main") {
  console.error(`Release bump must run from main, got ${branch || "(detached)"}`)
  process.exit(1)
}
try {
  sh("git", ["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"])
}
catch {
  console.error("Release bump requires main to have an upstream branch")
  process.exit(1)
}

await versionBump({
  release: releaseArg ?? "patch",
  files: [
    "package.json",
    "packages/<pkg-a>/package.json",
    "packages/<pkg-b>/package.json",
    // ...one entry per publishable package
  ],
  commit: true,
  tag: true,
  push: true,
  install: false,
  recursive: false,
  noGitCheck: false, // bumpp blocks if working tree dirty
})
```

Subject and tag use bumpp defaults: `chore: release vX.Y.Z` and
`vX.Y.Z`. The release workflow validates these later.

### 1.2 `scripts/prepare-npm-publish.mjs`

For monorepos with workspace deps. Run before each `npm publish`,
either by the bootstrap operator (Phase 5.1) or by CI (Phase 2 step 5):

- read every publishable package manifest
- replace `workspace:*` references to sibling publishable packages
  with the literal release version
- validate that no `workspace:` protocol leaks remain in the
  publishable surface

The mutations are **not committed**. They live only in the working
tree until `npm publish` produces tarballs from them. After publish
the operator restores `workspace:*` (`git checkout -- packages/*/package.json`)
or, in CI, the ephemeral checkout discards them.

### 1.3 `package.json` script

```jsonc
{
  "scripts": {
    "release:bump": "node scripts/release-bump.mjs"
  }
}
```

## Phase 2 — Release workflow (`.github/workflows/release.yml`)

Triggered on `push` to `refs/tags/v*.*.*`.

```yaml
name: Release

on:
  push:
    tags:
      - 'v*.*.*'

permissions:
  contents: write    # for GitHub Release creation
  id-token: write    # for npm OIDC

jobs:
  publish:
    runs-on: ubuntu-latest
    environment: npm-publish    # binds OIDC trust to a named environment
    steps:
      # 1. Checkout, set up Node + pnpm, install deps.
      - uses: actions/checkout@v6
        with: { fetch-depth: 0 }
      - uses: pnpm/action-setup@v6
        with: { version: 10.33.0 }
      - uses: actions/setup-node@v6
        with:
          node-version: 24
          registry-url: https://registry.npmjs.org

      # 2. Validate release metadata (tag <-> version <-> commit <-> main).
      - name: Validate release metadata
        id: release
        run: |
          set -euo pipefail
          TAG="${GITHUB_REF_NAME}"
          [[ "$TAG" =~ ^v[0-9]+\.[0-9]+\.[0-9]+(-[0-9A-Za-z.-]+)?$ ]] || exit 1
          VERSION="${TAG#v}"
          [ "$(node -p "require('./package.json').version")" = "$VERSION" ] || exit 1
          [ "$(git log -1 --pretty=%s)" = "chore: release v$VERSION" ] || exit 1
          git fetch origin main:refs/remotes/origin/main --tags
          git merge-base --is-ancestor HEAD origin/main || exit 1
          echo "version=$VERSION" >> "$GITHUB_OUTPUT"

      # 3. Validate npm CLI version (>= 11.5.1 supports OIDC publish).
      # 4. Standard gates.
      - run: pnpm install --frozen-lockfile
      - run: pnpm check
      - run: pnpm test
      - run: pnpm build

      # 5. Replace workspace:* with release version, validate the tarball.
      - run: node scripts/prepare-npm-publish.mjs ${{ steps.release.outputs.version }}
      - run: pnpm pack:dry   # or per-package npm pack validation

      # 6. Sequential `npm publish` in dependency order, retry-safe.
      #    OIDC kicks in here: the runner exchanges its GitHub OIDC token
      #    for a short-lived npm credential at publish time; static secrets
      #    are not needed.
      #
      #    Retry safety: if the version already exists on the registry
      #    (rerun scenario), the workflow checks the registered `gitHead`
      #    against the current commit SHA. Match → skip republish and
      #    continue. Mismatch → fail hard (never overwrite).
      - name: Publish workspace packages
        env:
          VERSION: ${{ steps.release.outputs.version }}
        run: |
          set -euo pipefail
          for dir in packages/core packages/data packages/cli; do
            name="$(node -p "require('./${dir}/package.json').name")"
            existing="$(npm view "${name}@${VERSION}" gitHead 2>/dev/null || true)"
            if [ -n "$existing" ]; then
              if [ "$existing" = "$GITHUB_SHA" ]; then
                echo "${name}@${VERSION} already published with matching gitHead; skipping republish"
                continue
              fi
              echo "${name}@${VERSION} already exists with gitHead $existing != $GITHUB_SHA — refusing to overwrite" >&2
              exit 1
            fi
            (cd "$dir" && npm publish --access public --no-git-checks)
          done

      # 7. Registry install smoke with retry-with-backoff.
      #    npm CDN propagation needs ~10–60s; first install can race
      #    with `ETARGET notarget`. Wrap in `until` with backoff.
      - name: Registry install smoke
        run: |
          set -euo pipefail
          TMP_DIR="$(mktemp -d)"
          cd "$TMP_DIR"
          npm init -y >/dev/null
          MAX_ATTEMPTS=6
          DELAY=10
          ATTEMPT=1
          until npm install "<pkg>@${{ steps.release.outputs.version }}" >/dev/null 2>&1; do
            if [ "$ATTEMPT" -ge "$MAX_ATTEMPTS" ]; then
              echo "npm install failed after $MAX_ATTEMPTS attempts" >&2
              # Final attempt without redirect so the real error reaches the log.
              npm install "<pkg>@${{ steps.release.outputs.version }}"
              exit 1
            fi
            echo "attempt $ATTEMPT failed; retrying in ${DELAY}s..."
            sleep "$DELAY"
            ATTEMPT=$((ATTEMPT + 1))
          done
          # Then exercise the package surface (compile / type-check / etc.).

      # 8. Create / update GitHub Release with CHANGELOG body.
      - name: Create GitHub Release
        env:
          GH_TOKEN: ${{ github.token }}
          VERSION: ${{ steps.release.outputs.version }}
        run: |
          if gh release view "v$VERSION" >/dev/null 2>&1; then
            gh release edit "v$VERSION" --notes-file CHANGELOG.md
          else
            gh release create "v$VERSION" --notes-file CHANGELOG.md --verify-tag
          fi
```

The workflow is **retry-safe**: if a rerun triggers and a version
already exists on npm, the publish step (or a guard before it) checks
the registered `gitHead` against the current commit SHA. Match → skip
the actual republish, continue to smoke + Release. Mismatch → fail
hard, never overwrite.

## Phase 3 — GitHub repo configuration (the human gate)

Two bits of repo settings move the human-in-the-loop from CI runtime
to tag creation. Configure these *after* Phase 5 has proven the OIDC
publish works end-to-end (Phase 5.4) — until then the
`npm-publish` environment carries a required reviewer as the
bootstrap-time safety belt.

### 3.1 Environment `npm-publish`

- **Settings → Environments → New environment** → name `npm-publish`.
- Initially (during Phase 5 bootstrap and first OIDC publish): add the
  publishing identity as a **Required reviewer**. Each release run
  pauses on the publish job until you click approve. This is the
  bootstrap-time guard.
- After Phase 5.4 validates the OIDC publish path, **remove the
  required reviewer**. The CI no longer pauses.

### 3.2 Tag protection ruleset

- **Settings → Rules → Rulesets → New ruleset → New tag ruleset**.
  - Name: `Protect release tags`
  - Enforcement status: Active
  - Target tags: `Include by pattern: v*.*.*`
  - Bypass list: `Repository admin` (role-based)
  - Rules: ☑ Restrict creations · ☑ Restrict updates · ☑ Restrict
    deletions
- Effect: only repo admin can create / update / delete `v*.*.*` tags.
  All other tokens (collaborators, third-party CI, leaked PATs) get
  rejected at the API level. The tag push is now a strong signal of
  intent.

The combination — no in-CI reviewer + tag-creation locked to admin —
lets the pipeline run autonomously while keeping the *decision* human.
Rollback: re-add the required reviewer if you ever need to re-gate
specific releases (e.g. major versions).

## Phase 4 — npm Trusted Publisher

A Trusted Publisher binding tells npm: "accept publish requests from
GitHub Actions runs whose OIDC claims match this tuple". This replaces
stored npm tokens entirely.

The binding is **per-package**, not per-repo. Configure each
publishable package after Phase 5.2 has executed the first manual
publish (npm requires the package to exist before a binding can be
attached).

For each publishable package on npmjs.com:

1. Package page → **Settings → Trusted Publisher → Add**.
2. Provider: **GitHub Actions**.
3. Owner: `<github-user-or-org>` (e.g. `LoTwT`).
4. Repository: `<repo-name>` (e.g. `design-system`).
5. Workflow filename: `release.yml` (must match the path under
   `.github/workflows/`).
6. Environment: `npm-publish` (must match the `environment:` key on
   the publish job).

If the binding's tuple doesn't match the OIDC token's claims at publish
time, npm rejects the publish. Diagnose by inspecting the OIDC token
claims in the workflow log and comparing against the binding.

## Phase 5 — First release (manual bootstrap → OIDC validation)

This is the one-time ladder that takes a new repo from "configured" to
"shipping autonomously".

### 5.1 Pre-flight

```bash
git status                       # clean
git branch --show-current        # main
git pull origin main             # synced
gh auth status                   # admin scope on the repo
npm whoami                       # the publishing identity
npm --version                    # >= 11.5.1
```

Have an npm 2FA device ready if your account requires it.

### 5.2 Manual v0.0.1 publish

npm requires a package to exist on the registry before its Trusted
Publisher binding can be attached. So the first version publishes
manually with a one-time scoped npm token, NOT via OIDC.

1. **Settings → Environments → `npm-publish`** → add `NODE_AUTH_TOKEN`
   secret containing a freshly-issued **fine-grained npm token**
   scoped to the packages, write-only. (This token disappears in
   step 8.)
2. `pnpm release:bump 0.0.1` from `main`. bumpp creates the
   `chore: release v0.0.1` commit, tags `v0.0.1`, and pushes both.
   The tag triggers `release.yml`; that run will fail at the OIDC
   publish step (Trusted Publisher not configured yet) — **expected,
   ignore**.
3. `git checkout v0.0.1` — publish from the exact tagged tree
   (detached HEAD is intentional).
4. `pnpm install --frozen-lockfile`
5. `pnpm check && pnpm test && pnpm build` — same gates the CI runs;
   if any fail here, **do not publish**, fix forward.
6. `node scripts/prepare-npm-publish.mjs 0.0.1` — replace
   `workspace:*` with `0.0.1`. These edits are temporary and not
   committed.
7. **Sequential `npm publish` in dependency order**:
   ```bash
   cd packages/core && npm publish --access public --no-git-checks && cd ../..
   cd packages/data && npm publish --access public --no-git-checks && cd ../..
   cd packages/cli  && npm publish --access public --no-git-checks && cd ../..
   ```
   Order matters: a downstream package's `npm install` will pull its
   sibling deps from the registry; if the sibling isn't there yet, the
   install fails.
8. `git checkout -- packages/*/package.json` — restore `workspace:*`
   so subsequent local pnpm work doesn't trip on literal-version deps.

### 5.3 Configure Trusted Publisher (Phase 4 binding per package)

Walk Phase 4 for each package now that v0.0.1 exists on the registry.

After all bindings are in place, **revoke the one-time fine-grained
npm token** (npmjs.com → access tokens) and **delete `NODE_AUTH_TOKEN`
from the `npm-publish` environment** in GitHub. The pipeline now
relies entirely on OIDC.

### 5.4 v0.0.2 OIDC validation (throwaway patch)

A patch whose only purpose is to prove the OIDC publish pipeline works:

1. Make any trivial change on `main` (or just bump the version).
2. `pnpm release:bump 0.0.2` from `main`.
3. The tag push triggers `release.yml`. The publish step now runs via
   OIDC: the runner asks GitHub for an OIDC token with the
   `id-token: write` permission, exchanges it for a short-lived npm
   credential, npm verifies the token's claims (repo, environment,
   workflow filename) against each Trusted Publisher binding, and
   the publish proceeds — no static secret involved.
4. The workflow continues through registry install smoke and GitHub
   Release creation.
5. Verify the published version metadata:

   ```bash
   npm view @<scope>/<pkg>@0.0.2 version    # expected: 0.0.2
   npm view @<scope>/<pkg>@0.0.2 gitHead    # expected: the v0.0.2 release commit SHA
   ```

   `gitHead` should equal the SHA of the `chore: release v0.0.2`
   commit (`git rev-parse v0.0.2^{commit}` locally). If it's empty or
   wrong, the OIDC publish ran from an unexpected tree state.

### 5.5 Verification

```bash
npm view @<scope>/<pkg>@0.0.1 version    # 0.0.1
npm view @<scope>/<pkg>@0.0.1 gitHead    # the v0.0.1 release commit
npm view @<scope>/<pkg>@0.0.2 version    # 0.0.2
npm view @<scope>/<pkg>@0.0.2 gitHead    # the v0.0.2 release commit
```

If the `gitHead` is wrong (or empty), something in the publish
metadata went sideways — investigate before doing more releases.

### 5.6 Hardening (Phase 3 toggles)

Now that OIDC is proven:

- Remove the required reviewer from the `npm-publish` environment
  (Phase 3.1).
- Add the `v*.*.*` tag protection ruleset (Phase 3.2).

## Phase 6 — Operations and rollback

After Phase 5, a routine release is just:

1. `pnpm release:bump <X.Y.Z>` from `main`.
2. Watch the workflow run if you want.
3. Verify the published metadata and the GitHub Release:

   ```bash
   # Per published package:
   npm view @<scope>/<pkg>@<X.Y.Z> version    # expected: X.Y.Z
   npm view @<scope>/<pkg>@<X.Y.Z> gitHead    # expected: release commit SHA

   # GitHub Release:
   gh release view v<X.Y.Z>                   # expected: not draft, notes match CHANGELOG
   ```

When something goes wrong, **fix forward**. `npm deprecate
<pkg>@<bad-version> "use <good-version>"`, then ship the next patch.
Never `npm unpublish` — the 72-hour window is narrow, the unpublish
makes the version permanently unusable for any consumer that already
has it in a lockfile, and the npm registry's audit semantics treat it
as a hard incident.

### 6.1 Per-step rollback table

| Step | Failure | Rollback / recovery |
|---|---|---|
| `release:bump` push fails | retry `git push && git push --tags` |
| Tag pushed, CI hasn't started yet | `git push --delete origin v...` + `git revert <bump-commit>` + push |
| `prepare-npm-publish.mjs` reports version mismatch | `release:bump` didn't update package.json files; rerun `release:bump` |
| Bootstrap `npm publish` errors | retry the same command (idempotent for the same tarball; "version already exists" means publish actually succeeded) |
| Bootstrap: package N fails after 1..N-1 succeeded | choose: fix and continue with N..end, OR `npm deprecate` 1..N-1 and prep next patch |
| OIDC publish fails (claims mismatch) | check workflow `permissions:`, `environment:`, npm CLI version, Trusted Publisher binding; rerun the failed jobs |
| Registry smoke `notarget` (pre-Phase 2 retry-with-backoff) | rerun the failed jobs; the workflow's `gitHead` retry-safety logic skips republish |
| Trusted Publisher binding wrong | edit on npmjs.com; affects the *next* release only (already-published versions are unaffected) |
| Tag pushed by non-admin (after Phase 3 ruleset) | rejected by GitHub at the push API; nothing to roll back |
| Production npm version turns out to be broken | `npm deprecate <pkg>@<bad-version> "use <good>"` + ship next patch with the fix |

### 6.2 Generic principles

1. **Never `npm unpublish`** unless explicitly recommended by an
   incident runbook owner. `npm deprecate` is the standard fix-forward.
2. **Fix-forward over rollback**: a bad version becomes evidence for
   the next patch's CHANGELOG.
3. **If two of N packages published and the third failed**, *stop*.
   Don't blindly retry the failing one until you understand whether
   the success was real (`npm view <pkg>@<version>`) and whether the
   monorepo state on disk still matches. Then choose: continue, or
   deprecate-and-bump.
4. **Suspicious states deserve a pause**: copy verbatim error text,
   re-read the release log around the failure, talk to your reviewer
   before retrying more than once.

### 6.3 When NOT to walk this on autopilot

- Multi-package repos where the publishable set changes between
  releases — keep `prepare-npm-publish.mjs`'s allowlist in sync.
- First publish under a new npm scope — needs scope-owner privileges
  (one-time, separate from this pipeline).
- Major version bumps — semver review belongs in PR review, not at
  release time. The pipeline is a delivery channel, not a quality
  gate for the change itself.
- Packages with native binaries / per-platform `optionalDependencies`
  — the linear `npm publish` script needs per-platform jobs and a
  matrix; out of scope for this template.

## Worked deployments

- **`LoTwT/design-system`** — Phases 0–2 in place from the start;
  Phase 5.2 v0.0.1 manual bootstrap on 2026-05-08; Phase 5.3 + 5.4
  v0.0.2 OIDC validation on 2026-05-10 (PR #12 merged as
  `a3a9b18`); Phase 3.1 reviewer removed + Phase 3.2 tag ruleset on
  2026-05-10 (decision DS-D-10, decisions log entry merged in PR
  #14); Phase 2 step 7 retry-with-backoff in `release.yml` on
  2026-05-10 (DD-012, PR #13 merged as `1f9bf89e`).
- **`LoTwT/fairy`** — Phases 0–2 in place; Phase 5.2 v0.0.1 manual
  bootstrap **paused** on 2026-05-10 to consolidate this runbook
  before proceeding. Phases 5.3 + 5.4 + 3 will follow the
  design-system pattern.

## Glossary

| Term | Meaning |
|---|---|
| OIDC | OpenID Connect. GitHub Actions can mint short-lived ID tokens for the running job, claiming repo / workflow / environment metadata. npm Trusted Publisher accepts these as a publish credential, eliminating stored tokens. |
| Trusted Publisher | npm setting on a package, binding it to a (provider, owner, repo, workflow, environment) tuple. A publish only succeeds if the OIDC token's claims match the binding. |
| `gitHead` | npm's per-version metadata field recording the commit SHA the publish ran from. Used as a retry-safety check in CI: if the version already exists with the correct `gitHead`, the rerun skips publish and continues. |
| Environment (GitHub) | A named scope inside a repo's Actions config that can carry secrets, deployment branches, required reviewers, and (for OIDC) sub-claims. The publish job's `environment:` key binds it to one. |
| Fine-grained npm token | A scoped, expirable npm token used during Phase 5.2 bootstrap only; replaced by OIDC after Phase 5.4. |
| `npm deprecate` | Marks a published version as discouraged. Consumers see a deprecation warning at `npm install` time. The version stays installable; this is the standard "this release was bad, use a newer one" signal. |
| `npm unpublish` | Removes a published version from the registry. Allowed only within 72 hours of publish, only when no other package depends on it, and the slot stays permanently unusable afterward. **Do not use** as a routine rollback. |

## QA testing conventions

The project's smoke-testing conventions live in
`LoTwT/ayingott.me:docs/qa/testing-conventions.md` (merged via
ayingott.me PR #17, commit `5c4fccbe`). Two of those conventions are
load-bearing for this runbook:

- **Registry probes use npm tooling**, not `curl`. Use
  `npm view <pkg>@<version> version` and `npm view <pkg>@<version> gitHead`
  against the live registry, not `curl` against npm's HTTP API
  directly. The retry-with-backoff smoke step in Phase 2 also uses
  npm tooling (`npm install`) to probe installability; the metadata
  checks (`npm view ... version` / `npm view ... gitHead`) run
  separately in Phase 5 and Phase 6.
- **HTTP user-facing route smoke sends `Accept: text/html`** so
  content-negotiated handlers route to the HTML branch instead of the
  JSON / API branch. This convention does **not** apply inside this
  runbook — none of the smoke steps here probe HTTP user-facing routes
  — but it's worth knowing when porting this pipeline to a project
  that also serves an SSR app.

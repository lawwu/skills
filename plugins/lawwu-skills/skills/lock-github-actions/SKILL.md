---
name: lock-github-actions
description: Harden a repository's GitHub Actions against supply-chain attacks. Locks every action to an exact commit with GitHub's gh-actions-lock (a .github/workflows/actions.lock lockfile), lints the workflows with zizmor and fixes what it finds (unpinned actions, overly broad token permissions, credentials left on disk, template injection), adds a CI workflow that checks both on every pull request, sets a Dependabot cooldown for action updates, and makes the checks required. Use whenever someone wants to pin or lock GitHub Actions, secure or audit their workflows, adopt gh-actions-lock or zizmor, pin actions to SHAs, protect CI from a hijacked action (like the tj-actions/changed-files compromise), or asks how to make their Actions setup safer, even if they don't name either tool.
---

<!--
Follows Hugo van Kemenade's "Lock your GitHub Actions" (https://hugovk.dev/blog/2026/lock-github-actions/)
and GitHub's gh-actions-lock (https://github.com/github/gh-actions-lock). Written from a real run on lawwu/html-server.
-->

# Lock GitHub Actions

A repository's workflows run other people's code (the actions) with tokens that can push
commits, publish packages and deploy sites. Two things go wrong in practice:

- **The code changes underneath you.** `uses: some/action@v4` means whatever `v4` points at
  today. In March 2025 an attacker moved every version tag of `tj-actions/changed-files` to a
  commit that printed each workflow's secrets into its build log; every repository using it by
  tag ran that code on its next build, with no pull request and no warning.
- **The code can reach too much.** A job whose token can write, or a checkout that leaves the
  token in `.git/config` for every later step, hands that reach to anything the job runs:
  actions, and the install scripts of every package `npm ci` or `pip install` pulls in.

This skill fixes both: it pins what runs (the lockfile), narrows what it can reach (zizmor's
fixes), and keeps it that way (CI checks that are required for merging, and a Dependabot
cooldown so a fresh release has time to be caught before it is proposed).

## Before you start

- If the repository has no `.github/workflows/`, say so and stop.
- Work on a new branch (for example `actions-lock`) from the default branch. Commit with the
  git identity the repository is already configured with; don't change it.
- Tools:
  - **gh-actions-lock** is a GitHub CLI extension. Don't change the user's own gh setup to run
    it: install it into a scratch folder and point `GH_DATA_DIR` at it for every call:
    `GH_DATA_DIR=<scratch>/ghdata gh extension install github/gh-actions-lock --pin <version>`.
    If they already have it installed, use theirs.
  - **zizmor** runs without installing: `uvx zizmor .github/` (or `pipx run zizmor`). Version
    1.32.0 or newer is required: it's the first that reads `actions.lock`, and older versions
    report every tag-pinned action as unpinned.
- Versions: for each tool and action, use the newest release that is at least 7 days old, or
  older than the repository's existing Dependabot or Renovate cooldown if it has a longer one.
  Check with `gh api repos/<owner>/<repo>/releases`. A brand-new release is exactly what a
  cooldown exists to keep out. As of 2026-11-11 these were gh-actions-lock v0.4.1,
  zizmor 1.32.0, zizmorcore/zizmor-action v0.8.1 and actions/checkout v7.0.1.
- Never read CI in a loop. Check it once when asked.

## Steps

### 1. Baseline

Run `uvx zizmor --offline .github/` and summarize the findings by audit (count and what each
means) so the user can see where the repository starts.

### 2. Fix what zizmor finds

- **Credentials left on disk (`artipacked`).** Add `persist-credentials: false` to every
  `actions/checkout`. The exception is a job that pushes with git using those credentials (for
  example, one that moves a tag). Keep them there, and say so on a line of its own so relocking
  can't strip it (see step 3):
  ```yaml
      - uses: actions/checkout@v7.0.1
        with:
          fetch-depth: 0
          persist-credentials: true # zizmor: ignore[artipacked] the step below pushes the tag with them
  ```
  Fetching from a public repository needs no credentials, so later `git fetch` steps still work.
- **Broad permissions (`excessive-permissions`).** Give every workflow `permissions:
  contents: read` at the top, and move each write permission to the one job that needs it.
  GitHub Pages is the common case: `pages: write`, `id-token: write` and the
  `actions/configure-pages` step belong in the deploy job, so the build job (which runs
  `npm ci`, tests and other third-party code) can only read.
- **Anything else** (template injection, `pull_request_target`, spoofable `github.actor`
  checks, secrets passed wholesale): fix it. If it's a false positive, explain why and suppress
  only that finding with `# zizmor: ignore[<audit>]`. A `${{ matrix.x }}` in a `run:` block
  whose values are fixed in the workflow is a typical false positive at the strictest level.

### 3. Lock the actions

Run `gh actions-lock` from the repository root. It narrows tags like `@v7` to exact versions
(`@v7.0.1`), writes `.github/workflows/actions.lock` with each one's commit and its owner and
repository IDs, and also locks actions that other actions use. Then:

- **A pin newer than the cooldown.** If it warns that a pinned release is newer than the
  cooldown, pin the latest release that is older, then relock. Dependabot will propose the
  newer one once it's old enough.
- **Comments on `uses:` lines.** Relocking rewrites each `uses:` line it pins and drops any
  comment at the end of that line. Keep comments, `# zizmor: ignore` included, on lines of
  their own, and check after relocking that they survived.
- **SHA-pinned actions** (`@<sha> # vX.Y.Z`) can go back to `@vX.Y.Z`: the lockfile holds the
  commit, and the workflow becomes readable again.
- **What isn't locked:**
  - Container images (`container:`, `services:`). gh-actions-lock warns about images without an
    `@sha256:` digest. List them in the pull request rather than pinning them: neither tool
    keeps a digest current, and a stale pin is its own risk.
  - Reusable workflows called from another repository.
  - Local `./` actions. A local action that uses remote actions is an error until you pass
    `--migrate-local-actions` or `--ignore-local-actions`; ask which the user wants.
- **Hosts.** github.com and GHE.com are supported; GitHub Enterprise Server is not. Stop and
  say so there.

### 4. Check both in CI

Add `.github/workflows/actions.yml`. Use the repository's default branch name and the versions
chosen above, and put a short comment at the top explaining both jobs (what each catches, and
how to relock):

```yaml
name: actions
on:
  push:
    branches: [main]
  pull_request:
permissions:
  contents: read
jobs:
  lockfile:
    name: Actions lock
    runs-on: ubuntu-latest
    env:
      GH_TOKEN: ${{ github.token }}
    steps:
      - uses: actions/checkout@v7.0.1
        with:
          persist-credentials: false
      - run: gh extension install github/gh-actions-lock --pin v0.4.1
      - run: gh actions-lock --verify

  zizmor:
    name: zizmor
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7.0.1
        with:
          persist-credentials: false
      - uses: zizmorcore/zizmor-action@v0.8.1
        with:
          version: 1.32.0
          advanced-security: false # findings fail the job, as annotations on the pull request
          annotations: true
```

`gh actions-lock --verify` fails when a workflow uses an action the lockfile doesn't have, or
when a locked commit no longer matches upstream (a moved tag, a rewritten history, a deleted
and recreated repository). zizmor-action runs the audits that ask GitHub too (actions with
known vulnerabilities, impostor commits). With `advanced-security: false` it needs no
`security-events` permission and nothing goes to the Security tab; set it to `true` instead if
the user wants findings in code scanning.

Relock afterwards, so the lockfile covers this workflow too.

### 5. Dependabot (or Renovate)

Make sure `.github/dependabot.yml` has a `github-actions` entry that runs weekly with a
cooldown and groups the updates. Dependabot updates `actions.lock` in the same pull request as
the version bump.

```yaml
  - package-ecosystem: github-actions
    directory: /
    schedule:
      interval: weekly
    cooldown:
      default-days: 7
    groups:
      github-actions:
        patterns: ['*']
```

If there's no `dependabot.yml`, add one for `github-actions` and the repository's own package
ecosystem, with the same cooldown. If the repository uses Renovate, leave Dependabot out and
make sure Renovate's GitHub Actions manager is on, with a `minimumReleaseAge` of at least
7 days.

### 6. Document it

Add a short note where the repository keeps developer docs (README's development section,
CONTRIBUTING):

- the workflows are locked;
- relock with `gh actions-lock` after changing one;
- lint with `uvx zizmor .github/`;
- keep comments off `uses:` lines.

If there's a CHANGELOG, add a line under Unreleased.

### 7. Verify before committing

- `gh actions-lock --verify` reports every workflow valid.
- `uvx zizmor --offline .github/` reports no findings.
- `GH_TOKEN=$(gh auth token) uvx zizmor .github/` (the online audits) reports no findings.
- Mention what `--persona auditor` adds, but don't chase its style points.

### 8. Push and open the pull request

Pushing changes under `.github/workflows/` over HTTPS needs a token with the `workflow` scope.
If the push is refused for that reason, don't change the token's scopes: give the user the
exact command to push the branch themselves (for example
`git -C <path> push git@github.com:<owner>/<repo>.git <branch>` over SSH) and wait until they
say it's pushed.

The pull request body should cover:

- a table of zizmor's findings: finding, count, change;
- any pins held back for the cooldown;
- what isn't locked (images, reusable workflows);
- anything CI can't exercise on a pull request, such as a Pages deploy that only runs on the
  default branch. The first run after merging is its real test.

### 9. Merge, then make the checks required

Merge when the user says so, the way the repository usually merges. Then offer to add
"Actions lock" and "zizmor" to the default branch's required checks, and change nothing else
in the ruleset or branch protection.

Without this, an automated update that leaves the lockfile stale can still merge itself if
auto-merge only waits for the test job. Required checks are a settings change, so make it only
on the user's go-ahead:

- **Ruleset:** `gh api repos/<owner>/<repo>/rulesets` lists them. Read the one with
  `required_status_checks`, then PUT it back with the two checks added. Each check's
  `integration_id` comes from `gh api repos/<owner>/<repo>/commits/<sha>/check-runs`; it's
  15368 for GitHub Actions.
- **Classic branch protection:** add the two contexts to its required status checks.
- **No ruleset or protection:** ask before creating one. On a private repository, rulesets need
  a paid GitHub plan; without one, the checks still run on every pull request, only without
  blocking merges.

## Explaining it to the user

When asked why this helps, ground it in the repository's own workflows. Name the jobs that
hold write tokens (publishing packages or images, pushing tags, deploying a site) and what an
attacker could do with each. Then cover four things:

- **The lockfile** keeps a moved tag from changing what runs.
- **The cooldown** gives a hijacked release time to be caught and pulled before it's proposed.
- **zizmor's fixes** shrink what anything that does get in can reach.
- **The required checks** stop a bad update from merging itself.

Be clear about what this doesn't cover:

- a malicious release older than the cooldown that someone merges;
- the repository's package dependencies, which its own lockfile and cooldown cover;
- the maintainer's own account, which two-factor login protects.

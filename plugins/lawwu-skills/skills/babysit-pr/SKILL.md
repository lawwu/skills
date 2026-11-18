---
name: babysit-pr
description: Shepherd a GitHub pull request until it is green and ready to merge. Takes a PR URL or number (or the current branch's PR), finds everything blocking it (merge conflicts, failing CI checks, unresolved review comments, a stale branch), fixes what it can, pushes, waits for CI, and repeats until the PR is mergeable or it is genuinely stuck, then reports. Handles Dependabot PRs by asking Dependabot to rebase first and only pushing fixes when an upgrade really breaks the build. Use whenever someone says "babysit", "shepherd", "get this PR green", "fix CI on my PR", "why is my PR failing", "make this PR mergeable", "deal with the Dependabot PR", "watch this PR", or pastes a github.com/.../pull/N link with failing checks or conflicts, even if they don't say "babysit".
---

<!-- Written from a real run on a grouped Dependabot PR (lawwu/lawrencewu-net#217). -->

# Babysit a PR

The job is to take a pull request from "red" to "ready to merge" without the user having to
watch it: read why it's blocked, fix what has a clear fix, push, wait for CI, look again, and
stop either when it's green or when what's left needs a human. You stop at ready. **Don't
merge, don't enable auto-merge, don't approve.** Merging is the user's call.

## 1. Snapshot the PR

Identify the PR from what the user gave you (URL, number, or `gh pr view --json url` on the
current branch), then take a snapshot:

```bash
uv run <skill-dir>/scripts/pr_snapshot.py <pr-url-or-number> --logs
```

It returns JSON with the merge state (`CONFLICTING`/`DIRTY`, `BEHIND`, `BLOCKED`, `CLEAN`),
failed and pending checks (with an `error_excerpt` of the log around the first `##[error]` for
each failed Actions job), unresolved review threads, whether the author is Dependabot, and
whether you can push to the head branch, the last few comments, and for Dependabot PRs a
`dependabot.status` (`idle`, `rebasing`, `closed-superseded`, `closed`).

The PR changes under you: CI finishes, Dependabot rebases or closes it, reviewers comment.
So take a fresh snapshot at the start of every round, and check `state` and the latest
comments again **right before anything that writes to GitHub** (a comment, a push, a rerun).
A comment posted to a PR that closed three minutes ago is noise in the user's notifications.

If the PR was merged, say so and stop. If it was closed by a person, say so and stop. If
Dependabot closed it as superseded ("updatable in another way"), the work moved to a new PR:
the snapshot lists `replacement_candidates`. Report the replacement and carry on with it if the
user's request was about the update rather than the number ("get the npm bump green"); if
they named this exact PR, ask before writing to the new one. Anything you've already diagnosed
or fixed locally usually applies to the replacement unchanged, so don't throw it away.

If it's a draft, babysit it anyway but say so in the report. If `can_push_to_head` is false (a fork that doesn't allow maintainer edits), you
can still diagnose, but report fixes as suggestions instead of pushing them.

## 2. Get a working copy

Fixes need the code. Prefer a separate git worktree so the user's own checkout stays
untouched:

- If a clone of the PR's repo exists locally (even with uncommitted work in it; a worktree
  doesn't touch that):
  ```bash
  git fetch origin "+refs/heads/<head>:refs/remotes/origin/<head>"
  git worktree add -b babysit/pr-<n> <scratch>/pr-<n> origin/<head>
  ```
  The `babysit/pr-<n>` local name avoids colliding with a branch the user may already have.
  Push with `git push origin HEAD:<head>`.
- Otherwise clone into the scratchpad and `gh pr checkout <n>` there.

Commit with whatever git identity the repo is already configured with. Install dependencies
the way CI does (read the workflow file: `npm ci` vs `npm install`, which Node/Python version,
which working directory), because reproducing a CI failure with a different setup reproduces a
different failure. If the CI runtime version isn't installed, try running it without
installing (`npx -y node@22 ...`, `uvx --python 3.12 ...`); if that doesn't work, use what's
there and note the mismatch in the report.

## 3. Work the blockers, in this order

Order matters: conflicts first (CI on a conflicted PR may not run at all, and the merge
result is what CI tests), then CI, then review comments (a fix for CI can change the code a
comment was about).

### Merge conflicts or a stale branch

**Dependabot PRs**: don't resolve conflicts by hand. First check `dependabot.status`: if it's
`rebasing`, Dependabot is already on it (it puts a "Dependabot is rebasing this PR" banner in
the PR body, often on its own with no one asking), so just wait. Otherwise comment
`@dependabot rebase` once (`gh pr comment <n> --body "@dependabot rebase"`), then wait for
Dependabot to force-push (usually a minute or two; it reacts with 👀 and then the head SHA
changes). Dependabot may also close the PR and open a replacement instead of rebasing; see
step 1.

Don't sit idle while waiting. Diagnose and reproduce the CI failures locally (next section):
the rebase rarely changes why an upgrade breaks the build. But don't push anything until the
rebase has landed, because a commit from anyone else makes Dependabot refuse to rebase. Dependabot
regenerates the lockfile against the current base, which is cleaner than any manual merge of
`package-lock.json`. If it hasn't moved after ~10 minutes, or replies that it can't rebase
because someone else pushed to the branch, fall back to `@dependabot recreate` (only if there
are no fix commits of yours on the branch, since recreate throws them away) or report it.

**Everyone else's PRs**: merge the base branch in (`git merge origin/<base>`), resolve, run
the tests, commit, push. Merge rather than rebase so you never force-push over history someone
else may have pulled; if the repo clearly works rebase-only (linear history required) and the
branch belongs to the user, rebase and push with `--force-with-lease`. Resolve conflicts by
understanding both sides; a resolution that silently drops one side's change is worse than an
unresolved conflict, so if the intent of a conflicting hunk isn't clear, stop and ask.
Lockfile conflicts: take the base's lockfile and regenerate (`npm install`, `uv lock`,
etc.) rather than hand-merging.

`BEHIND` with no conflict only matters if branch protection requires an up-to-date branch
(`merge_state` is `BEHIND` and stays `BLOCKED`); then update the same way.

### Failing checks

For each failed check, read its `error_excerpt` first. GitHub's line
`##[error]Process completed with exit code N` only says a step failed; the cause is the lines
above it. If the excerpt isn't enough, `gh run view --repo <r> --job <job_id> --log` and
search for the first error, not the tail (the tail is post-job cleanup).

Then decide which kind of failure it is:

- **Flaky or infrastructure** (network timeout fetching a dependency, runner lost, rate limit,
  a test that passes on rerun, a cancelled job): `gh run rerun <run_id> --failed --repo <r>`
  once. If it fails the same way again, treat it as real.
- **Needs a secret or permission the PR can't have** (Dependabot and fork PRs don't get
  normal Actions secrets; deploy steps fail with auth errors): not fixable from the PR. Report
  it; don't edit the workflow to work around it.
- **Real failure caused by the change**: reproduce it locally with the same command CI ran,
  fix it, confirm the command passes locally, commit with a message that says what broke and
  why the fix is right, push.

A job stops at its first failing step, so the steps after it never ran in CI and may hide a
second failure. After fixing the first one, run the rest of that job's steps locally too (and
the same steps for sibling apps in a monorepo that got the same upgrade) before pushing.
Otherwise each round of CI uncovers one more failure, and five rounds run out fast.

What a fix must not be: skipping or deleting the failing test, adding `continue-on-error`,
loosening a lint rule or a coverage threshold, `--no-verify`, or editing the workflow so the
failing step no longer runs. Those make the check green without making the code work, and
the user would merge a broken PR believing it was fixed. If the only way to green is one of
those, report it and let the user decide.

The line is whether every assertion still runs against the real code. Giving the tests an
environment the code legitimately expects (stubbing a platform module like
`cloudflare:workers` that only exists in production, adding a missing test fixture, setting
an env var the app requires) keeps every assertion running, so it's a fix. Say in the commit
message what you stubbed and why.

**Dependency-update PRs** (Dependabot, Renovate) fail for a different reason than feature PRs:
some upgrade in the bump is incompatible. Find which package (the error usually names it or
its ecosystem: "typescript-eslint does not support TS 7.0" points at the `typescript` major
bump). Then pick the smallest honest fix:

1. A code change that adapts to the new version, when it's small and the new version is what
   you want (a renamed import, a changed config key, a new required option).
2. Holding back the one incompatible package while the rest of the group lands: pin it below
   the breaking major in `package.json` (or equivalent), regenerate the lockfile, commit. Say
   in the report which package was held back and why, and suggest
   `@dependabot ignore <pkg> major version` if it should stay held until its ecosystem catches
   up. Don't post that ignore comment yourself; it changes future updates.
3. If neither is small (a framework major that needs a migration), stop and report: name the
   package, the breaking change, and roughly what the migration would involve.

Once you push your own commits to a Dependabot branch, Dependabot stops rebasing it
automatically. That's fine, but it means future conflicts are yours to resolve; mention it.

### Unresolved review comments

For each unresolved thread (skip ones that are `outdated` if the code they point at is gone):

- **Clear and actionable** ("rename this", "handle the null case", "this leaks the file
  handle"): make the change, push, and reply in the thread with one line saying what you did
  and the commit SHA. Leave resolving the thread to the reviewer; it's their call whether the
  fix answers them.
- **A question, a judgment call, or something you disagree with**: don't change code and
  don't argue in the thread. List it for the user with your read on it.
- **Automated reviewers** (Copilot, CodeRabbit, linters posting comments): apply the ones that
  are real bugs, list the rest as "skipped, low value" with a reason. Don't reply to bots.

`review_decision: CHANGES_REQUESTED` stays until that reviewer re-reviews, even after you fix
everything. That's a human step; report it.

## 4. Wait for CI, then go around again

After pushing (or rerunning, or asking Dependabot to rebase), wait for the checks on the new
head SHA rather than polling by hand:

```bash
gh pr checks <n> --repo <r> --watch --interval 30
```

Run that in the background so you're notified when it exits. Checks can take a few seconds to
register after a push; if `gh pr checks` reports nothing yet, the snapshot's `pending` list
is the authority. Then take a new snapshot and repeat step 3.

Stop going around when any of these is true:

- **Green**: no conflicts, no failed or pending checks, no actionable unresolved threads.
- **Stuck**: the same check fails the same way after you fixed it twice, or the remaining
  blockers are all human ones (a reviewer's approval, a secret, a judgment call, a migration
  too big to do unasked).
- **Five rounds** have passed. A PR that isn't green after five fix-push-wait rounds needs a
  person to look at the approach, not a sixth patch.

## 5. Report

End with a short report the user can read in ten seconds:

```
PR #<n> <title> — <READY TO MERGE | BLOCKED: <one-line reason>>
<url>

Done
- <what you fixed, one line each, with commit SHAs>
- <reruns, Dependabot commands posted>

Needs you
- <each human blocker: approval needed, review comment needing a decision,
  held-back package, missing secret, ...>

Checks: <passed>/<total> passing (<names of any still failing>)
```

If it's ready, say so plainly and leave the merge to them. Clean up the worktree you made in
step 2 unless it holds unpushed work.

# Dependency-update PRs (Dependabot, Renovate)

Read this when the snapshot says `is_dependabot: true`, or the PR is a Renovate or other
automated version bump. These PRs are blocked for different reasons than feature PRs, and the
bot that owns the branch will undo or refuse work done the usual way.

## Conflicts and stale branches: let the bot rebase

Don't resolve conflicts by hand. The bot regenerates the lockfile against the current base,
which is cleaner than any manual merge of `package-lock.json`.

1. Check `dependabot.status`. If it's `rebasing`, Dependabot is already on it: it puts a
   "Dependabot is rebasing this PR" banner in the PR body, often on its own with no one
   asking. Wait.
2. Otherwise comment once: `gh pr comment <n> --repo <r> --body "@dependabot rebase"`.
   Dependabot reacts with 👀 and force-pushes within a minute or two; the head SHA changes.
3. If nothing moves after ~10 minutes, or it replies that it can't rebase because someone
   else pushed to the branch, use `@dependabot recreate`, but only if there are no fix commits
   of yours on the branch (recreate throws them away). Otherwise report it.

Instead of rebasing, Dependabot may close the PR as superseded ("updatable in another way")
and open a replacement; step 1 of SKILL.md covers following it.

While waiting, diagnose and reproduce the CI failures locally: a rebase rarely changes why an
upgrade breaks the build. But push nothing until the rebase has landed, because a commit from
anyone else makes Dependabot refuse to rebase.

## Failing checks: find the one incompatible upgrade

A grouped bump fails because some upgrade in it is incompatible. Find which package; the
error usually names it or its ecosystem ("typescript-eslint does not support TS 7.0" points at
the `typescript` major bump). The same upgrade often breaks every app in a monorepo that got
it, including jobs that died at an earlier step, so check the siblings.

Then pick the smallest honest fix:

1. **Adapt the code** when the change is small and the new version is what you want (a
   renamed import, a changed config key, a new required option, a test stub for a module the
   new version imports that only exists in production).
2. **Hold back the one package** while the rest of the group lands: pin it below the breaking
   major in `package.json` (or equivalent), regenerate the lockfile, commit. In the report,
   name the package and the reason, and suggest `@dependabot ignore <pkg> major version` if
   it should stay held until its ecosystem catches up. Don't post that comment yourself: it
   changes every future update, which is the user's call.
3. **Stop and report** if neither is small (a framework major that needs a migration): name
   the package, the breaking change, and roughly what the migration would involve.

Once you push your own commits to a Dependabot branch, Dependabot stops rebasing it. That's
fine, but future conflicts on it are now manual; say so in the report.

## Secrets

Dependabot PRs don't get the repository's normal Actions secrets (only Dependabot secrets).
Deploy or publish steps that fail with auth errors on a Dependabot PR are expected and not
fixable from the PR; report them instead of editing the workflow.

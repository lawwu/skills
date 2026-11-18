---
name: find-past-work
description: Find work done in an earlier Claude Code session and report where it lives now - which session, folder, branch, pull request or file - and whether it was ever merged. Searches the session transcripts on this machine, then checks git, worktrees and GitHub to confirm what it found. Use whenever the user asks where something went or refers to work they can't locate - "where's the X you built", "what was the session where we did Y", "find my Z project", "did you make a handout a few weeks ago", "where did you put that file", "I started some fine-tuning, find that work", "what haven't I merged", "what was I working on last week" - even if they never say the word "session". Also use before redoing something that sounds like it may already exist.
---

# Find past work

Work gets lost between sessions: it was built in a worktree that has since been cleaned up,
on a branch that never got a pull request, in a repo other than the one you're in now, or it
was only ever an artifact. The user remembers roughly what it was, not where. Your job is to
turn "that timeline thing from a few weeks ago" into a concrete answer: where it is now,
what state it's in, and how to pick it back up.

The transcript is a lead, not the answer. A session that wrote a file says nothing about
whether that file still exists, so always confirm against the disk and git before you report.

## 1. Search the transcripts

```bash
uv run <skill-dir>/scripts/search_sessions.py <term> [<term> ...]
```

`<skill-dir>` is the folder this file is in. Each term is a case-insensitive regex matched
anywhere in a field (leave out `^` and `$`), and a session has to match all of them.
Matching covers the session title, the prompts the user typed, the working folder, the
branches it was on, the paths of files it wrote, and the artifacts it published.

Pick terms the user would have typed back then, not the words they use now. Prompts are
full of typos and shorthand, so prefer a short distinctive stem to a phrase: `kings
timeline` rather than `"kings of israel timeline app"`, `tax` rather than `tax calculator
spreadsheet`.

Useful options:

| Option | When |
|---|---|
| `--days 30` | The user gave a time frame ("a few weeks ago"). Also makes the search much faster. |
| `--project kb` | You know which repo it was in. Matches the session's folder name, which is the working directory with `/` and `.` turned into `-` (so `my.repo` is `my-repo`). |
| `--limit 50` | More than the default 15 results. |
| `--any` | Several possible names for the same thing; match at least one. |
| `--deep` | Nothing turned up. Also searches the assistant's replies, for work the user never named in a prompt. |
| `--recent --days 7` | No search term at all: "what was I working on last week". |
| `--json` | You want to process the results rather than read them. |

A full search over every transcript takes around half a minute on a machine with thousands
of sessions, so narrow with `--days` or `--project` when you can.

If nothing matches, widen in this order: fewer terms, then `--any` with synonyms, then
`--deep`, then a longer window, and last `--include-automated`. The script hides sessions
that look machine-driven (more than five transcripts opening with the same words, as batch
jobs do), which can also hide a human session that began with a stock opener.

Dates are shown in local time, and the script exits with status 1 when nothing matched.

The script says how many sessions it hid as automated, so a count there with no results is
the cue to add `--include-automated`.

## 2. Confirm what's really there

For the best one or two candidates, check each of these, because each fails in its own way:

- **The folder.** The script marks a working folder that no longer exists (`missing_folders`
  in `--json` output). A deleted
  worktree does not mean the work is gone; the branch usually survives in the main repo.
  Strip `/.claude/worktrees/<name>` from the path to get the repo it belonged to.
- **The branch.** In that repo: `git branch -a --list '*<branch>*'`, then
  `git log --oneline -5 <branch>` to see it has real commits. Check whether it reached
  the default branch with `git branch -a --merged origin/HEAD | grep <branch>`. A squash-merged branch
  looks unmerged to git, so also check the pull request.
- **The pull request.** `gh pr list --head <branch> --state all --json number,state,url,mergedAt`.
  A merged PR settles it. An open PR, or a branch with commits and no PR, is unfinished work.
- **The files.** `ls` the paths the session wrote. If the worktree is gone, look for the
  same relative path on main or on the branch: `git show <branch>:<path> | head`.
- **Uncommitted work.** If the folder still exists, `git -C <folder> status --short`. Work
  that was never committed exists only there, which is worth saying loudly.
- **Artifacts.** An `artifact:` line gives a local path and a link. Check the local file
  exists; you can't tell from here whether the link still resolves, so say that.

If the thing was deployed (a web app, a published page), say where it is live as well as
where the source is; the user usually wants the link.

## 3. Report

Lead with the answer to what they asked, in a sentence: where it is and what state it's
in. Then the details they need to act:

- the path or link, as something they can click
- its state: merged, open PR, branch with no PR, uncommitted, or gone
- the date and title of the session, and `claude --resume <id>` to reopen it
- anything at risk: unpushed commits, uncommitted changes, a branch that exists only locally

When several sessions touched the same thing, give the timeline in a few lines rather than
picking one, because "where is it" often turns out to mean "which version is current".

When you can't find it, say what you searched and what the closest matches were. Don't
guess a location. A near-miss the user can correct ("was it the budget dashboard instead?")
is more useful than a confident wrong answer.

## Sweeping for unfinished work

For "what haven't I merged" or "is anything lost", the question is about repos rather than
one item. For each repo the user names (or each one the recent sessions touched):

```bash
git fetch --prune
git branch -a --no-merged origin/HEAD --format '%(refname:short) %(committerdate:short) %(subject)'
git worktree list
gh pr list --state open --json number,title,headRefName,updatedAt
```

Then use `search_sessions.py --recent --days N --project <repo> --limit 100` to tie
branches back to what the user was trying to do. Group the result by what needs a decision: local-only
branches with real commits (at risk), open PRs, worktrees with uncommitted changes, and
branches that are safe to delete because their PR merged. Don't push, merge or delete
anything as part of the sweep; report first. (`git fetch --prune` only drops local records
of branches already deleted on the remote; it changes no work.)

## Privacy

Transcripts hold whatever was typed into them, including pasted keys and personal details.
Quote only the snippet needed to identify the session, and if you notice a credential in a
transcript, tell the user it's there instead of repeating it.

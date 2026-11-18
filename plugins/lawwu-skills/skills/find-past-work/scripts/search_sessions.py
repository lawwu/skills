# /// script
# requires-python = ">=3.10"
# ///
"""Search Claude Code session transcripts for past work.

Usage:
    uv run search_sessions.py <term> [<term> ...] [--days N] [--project SUBSTR]
                              [--any] [--deep] [--limit N] [--json]
    uv run search_sessions.py --recent [--days N] [--project SUBSTR]

Each <term> is a case-insensitive regular expression, matched anywhere in a field (don't
anchor with ^ or $). By default a session must match
every term (use --any for "at least one"). Terms are matched against the session title,
the prompts the user typed, the working directory, the git branches the session was on,
the paths of files it wrote, and the titles and paths of artifacts it published. --deep also matches the assistant's own text, which is
slower and noisier but finds work the user never named in a prompt.

--recent ignores the terms and lists every human-driven session in the window, newest
first, for "what was I working on last week" questions.

Sessions that look machine-driven (one of many transcripts that open with the same
prompt, as batch `claude -p` jobs do) are skipped unless --include-automated is given.
--project matches the session's folder name under ~/.claude/projects, which is the working
directory with "/" and "." turned into "-". Dates are shown in local time. Exit status is 1
when nothing matched.

Prints, per session: when it ran, its title, where it ran, the branches it touched, the
files and artifacts it produced, the matching prompts, and the command that resumes it.
Reads only; never modifies a transcript.
"""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import glob
import json
import os
import re
import sys

ROOT = os.path.expanduser(os.environ.get("CLAUDE_PROJECTS_DIR", "~/.claude/projects"))
# More than this many transcripts opening with the same 60 characters is a batch job.
AUTOMATED_OVER = 5
WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
NOISE_PREFIXES = (
    "<local-command",
    "<task-notification",
    "<bash-input>",
    "Caveat:",
    "[Request interrupted",
    "This session is being continued",
    "If this event is something the user would act on",
)
TAGGED = re.compile(r"<(system-reminder|pasted_content)[^>]*>.*?</\1[^>]*>", re.S)
COMMAND = re.compile(r"<command-message>.*?</command-message>|</?command-(name|args)>", re.S)
SPACES = re.compile(r"\s+")


def text_of(content) -> str:
    """Flatten a message's content (string or block list) to its plain text."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(
            b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text"
        )
    return ""


def clean(prompt: str) -> str:
    prompt = COMMAND.sub(" ", TAGGED.sub(" ", prompt))
    return SPACES.sub(" ", prompt).strip()


def opener(path: str) -> str | None:
    """First prompt the user typed, read without parsing the rest of the transcript."""
    try:
        with open(path, errors="ignore") as fh:
            for i, line in enumerate(fh):
                if i > 400:
                    break
                if '"type":"user"' not in line and '"type": "user"' not in line:
                    continue
                try:
                    d = json.loads(line)
                except ValueError:
                    continue
                if d.get("isMeta") or d.get("isSidechain"):
                    continue
                prompt = clean(text_of((d.get("message") or {}).get("content")))
                if prompt and not prompt.startswith(NOISE_PREFIXES):
                    return prompt[:60]
    except OSError:
        pass
    return None


def raw_match(path: str, patterns: list[re.Pattern], need_all: bool) -> bool:
    """Cheap test on the raw file so only promising transcripts get parsed in full."""
    try:
        with open(path, errors="ignore") as fh:
            raw = fh.read()
    except OSError:
        return False
    found = (bool(p.search(raw)) for p in patterns)
    return all(found) if need_all else any(found)


def read_session(path: str, deep: bool) -> dict | None:
    s = {
        "path": path,
        "id": os.path.splitext(os.path.basename(path))[0],
        "title": "",
        "first": None,
        "last": None,
        "cwds": [],
        "branches": [],
        "prompts": [],
        "files": [],
        "artifacts": [],
        "assistant": [],
    }
    try:
        with open(path, errors="ignore") as fh:
            for line in fh:
                try:
                    d = json.loads(line)
                except ValueError:
                    continue
                kind = d.get("type")
                if kind == "custom-title":
                    s["title"] = d.get("customTitle") or s["title"]
                elif kind == "ai-title" and not s["title"]:
                    s["title"] = d.get("aiTitle") or ""
                elif kind == "frame-link":
                    item = {
                        "path": d.get("path"),
                        "url": d.get("frameUrl"),
                        "title": d.get("title"),
                    }
                    if item not in s["artifacts"]:
                        s["artifacts"].append(item)
                if d.get("isSidechain"):
                    continue
                ts = d.get("timestamp")
                if ts and kind in ("user", "assistant"):
                    s["first"] = s["first"] or ts
                    s["last"] = ts
                for key, bucket in (("cwd", "cwds"), ("gitBranch", "branches")):
                    value = d.get(key)
                    if value and value != "HEAD" and value not in s[bucket]:
                        s[bucket].append(value)
                msg = d.get("message") or {}
                if kind == "user" and not d.get("isMeta"):
                    prompt = clean(text_of(msg.get("content")))
                    if prompt and not prompt.startswith(NOISE_PREFIXES):
                        s["prompts"].append(prompt)
                elif kind == "assistant":
                    for block in msg.get("content") or []:
                        if not isinstance(block, dict):
                            continue
                        if block.get("type") == "tool_use" and block.get("name") in WRITE_TOOLS:
                            target = (block.get("input") or {}).get("file_path")
                            if target and target not in s["files"]:
                                s["files"].append(target)
                        elif deep and block.get("type") == "text":
                            s["assistant"].append(SPACES.sub(" ", block.get("text", "")))
    except OSError:
        return None
    return s if s["prompts"] else None


def local_day(ts: str | None) -> str:
    """Date in this machine's timezone; transcripts store UTC, the user remembers local days."""
    if not ts:
        return ""
    try:
        return dt.datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone().date().isoformat()
    except ValueError:
        return ts[:10]


def snippet(text: str, pattern: re.Pattern, width: int = 220) -> str:
    m = pattern.search(text)
    if not m:
        return text[:width]
    start = max(0, m.start() - width // 3)
    out = text[start : start + width]
    return ("…" if start else "") + out + ("…" if start + width < len(text) else "")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("terms", nargs="*", help="case-insensitive regexes to look for")
    ap.add_argument("--days", type=int, help="only sessions active in the last N days")
    ap.add_argument("--project", help="only sessions whose folder contains this text")
    ap.add_argument("--any", action="store_true", help="match any term instead of all")
    ap.add_argument("--deep", action="store_true", help="also search the assistant's replies")
    ap.add_argument("--recent", action="store_true", help="list sessions instead of searching")
    ap.add_argument(
        "--include-automated", action="store_true", help="keep sessions that look like batch jobs"
    )
    ap.add_argument("--limit", type=int, default=15)
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args()
    if not args.terms and not args.recent:
        ap.error("give at least one search term, or --recent")
    try:
        patterns = [re.compile(t, re.I) for t in args.terms]
    except re.error as exc:
        ap.error(f"bad regular expression: {exc}")

    cutoff = None
    if args.days is not None:
        cutoff = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=args.days)).timestamp()

    everything = glob.glob(os.path.join(ROOT, "*", "*.jsonl"))
    candidates = []
    for path in everything:
        folder = os.path.basename(os.path.dirname(path))
        if args.project and args.project.lower() not in folder.lower():
            continue
        if cutoff and os.path.getmtime(path) < cutoff:
            continue
        candidates.append(path)

    # Batch jobs leave thousands of transcripts that open with the same prompt. Count openers
    # over the whole of each folder a candidate is in, not only the transcripts inside the
    # window, so a session is treated the same way whatever --days is given.
    paths = candidates
    if not args.include_automated:
        folders = {os.path.dirname(p) for p in candidates}
        first = {p: opener(p) for p in everything if os.path.dirname(p) in folders}
        counts = collections.Counter(v for v in first.values() if v)
        paths = [p for p in candidates if first[p] and counts[first[p]] <= AUTOMATED_OVER]
    searched = len(paths)
    hidden = len(candidates) - len(paths)
    hidden_note = (
        f" {hidden} hidden as automated; --include-automated shows them." if hidden else ""
    )
    if patterns and not args.recent:
        paths = [p for p in paths if raw_match(p, patterns, not args.any)]

    sessions = [s for s in (read_session(p, args.deep) for p in paths) if s]

    results = []
    for s in sessions:
        if args.recent:
            results.append((0, s, []))
            continue
        fields = [s["title"], *s["cwds"], *s["branches"], *s["files"], *s["prompts"]]
        fields += [a.get("path") or "" for a in s["artifacts"]]
        fields += [a.get("title") or "" for a in s["artifacts"]]
        fields += s["assistant"]
        hits = [sum(1 for f in fields if f and p.search(f)) for p in patterns]
        matched = any(hits) if args.any else all(hits)
        if not matched:
            continue
        # A hit in the title or a prompt says more than a hit in a long file list.
        strong = sum(1 for p in patterns if p.search(s["title"] or "")) * 5
        strong += sum(1 for p in patterns for q in s["prompts"] if p.search(q)) * 2
        shown = list(
            dict.fromkeys(snippet(q, p) for p in patterns for q in s["prompts"] if p.search(q))
        )[:4]
        if not shown and args.deep:
            shown = [snippet(a, p) for p in patterns for a in s["assistant"] if p.search(a)][:3]
        results.append((strong + sum(hits), s, shown))

    results.sort(key=lambda r: (r[0], r[1]["last"] or ""), reverse=True)
    if args.recent:
        results.sort(key=lambda r: r[1]["last"] or "", reverse=True)
    total = len(results)
    results = results[: args.limit]

    if args.json:
        out = []
        for score, s, shown in results:
            out.append(
                {
                    "score": score,
                    "session_id": s["id"],
                    "title": s["title"],
                    "first": s["first"],
                    "last": s["last"],
                    "cwds": s["cwds"],
                    "missing_folders": [c for c in s["cwds"] if not os.path.isdir(c)],
                    "branches": s["branches"],
                    "files_written": s["files"][:40],
                    "artifacts": s["artifacts"],
                    "first_prompt": s["prompts"][0][:400],
                    "matches": shown,
                    "transcript": s["path"],
                }
            )
        json.dump({"total_matches": total, "sessions": out}, sys.stdout, indent=2)
        print()
        return 0 if out else 1

    if not results:
        print(f"No sessions matched in {ROOT} ({searched} sessions searched).{hidden_note}")
        print("Try fewer or broader terms, --any, --deep, or a longer --days window.")
        return 1

    print(f"{total} matching session(s); showing {len(results)}.{hidden_note}\n")
    for _, s, shown in results:
        day = local_day(s["first"])
        end = local_day(s["last"])
        when = day if day == end else f"{day} to {end}"
        print(f"## {when}  {s['title'] or '(untitled)'}")
        for cwd in s["cwds"][:3]:
            gone = "" if os.path.isdir(cwd) else "  [folder no longer exists]"
            print(f"   where:    {cwd}{gone}")
        if s["branches"]:
            print(f"   branches: {', '.join(s['branches'][:6])}")
        print(f"   asked:    {s['prompts'][0][:200]}")
        for m in shown:
            print(f"   match:    {m}")
        if s["files"]:
            more = f" (+{len(s['files']) - 8} more)" if len(s["files"]) > 8 else ""
            print(f"   wrote:    {', '.join(s['files'][:8])}{more}")
        for a in s["artifacts"][:4]:
            print(f"   artifact: {a.get('title') or ''} {a.get('path') or ''} {a.get('url') or ''}")
        print(f"   resume:   claude --resume {s['id']}")
        print(f"   log:      {s['path']}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

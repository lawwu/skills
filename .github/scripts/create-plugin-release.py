#!/usr/bin/env python3
"""
Create a GitHub release for a plugin when its version has been bumped.

Usage:
    python create-plugin-release.py <plugin.json> [<plugin.json> ...]

For each plugin.json path provided:
  - Compares current version against the previous commit
  - Skips if version is unchanged
  - Generates categorized release notes from conventional commits
  - Creates a git tag, pushes it, and publishes a GitHub release

Requires GH_TOKEN in the environment (provided automatically by GitHub Actions).
"""

import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass

CONVENTIONAL_SECTIONS = [
    ("feat", "🚀 Features"),
    ("fix", "🐛 Bug Fixes"),
    ("perf", "⚡ Performance"),
    ("refactor", "♻️ Refactoring"),
    ("docs", "📚 Documentation"),
    ("test", "🧪 Tests"),
    ("chore", "🔧 Chores"),
    ("ci", "👷 CI"),
    ("build", "📦 Build"),
    ("revert", "⏪ Reverts"),
]


@dataclass
class Commit:
    sha: str
    short_sha: str
    author_name: str
    author_email: str
    subject: str
    type: str = ""
    scope: str = ""
    breaking: bool = False
    description: str = ""


def run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, check=check)


def git(args: list[str], check: bool = True) -> str:
    return run(["git"] + args, check=check).stdout.strip()


def parse_commit(line: str) -> Commit | None:
    parts = line.split("\x00")
    if len(parts) != 5:
        return None
    sha, short_sha, author_name, author_email, subject = parts
    c = Commit(
        sha=sha,
        short_sha=short_sha,
        author_name=author_name,
        author_email=author_email,
        subject=subject,
    )
    m = re.match(r"^(\w+)(\(([^)]+)\))?(!)?: (.+)$", subject)
    if m:
        c.type = m.group(1).lower()
        c.scope = m.group(3) or ""
        c.breaking = m.group(4) == "!"
        c.description = m.group(5)
    else:
        c.type = "other"
        c.description = subject
    return c


def get_commits_since(prev_tag: str | None) -> list[Commit]:
    fmt = "%H\x00%h\x00%an\x00%ae\x00%s"
    log_range = f"{prev_tag}..HEAD" if prev_tag else "HEAD"
    try:
        output = git(["log", log_range, f"--format={fmt}", "--no-merges"])
    except subprocess.CalledProcessError:
        output = git(["log", f"--format={fmt}", "--no-merges"])
    return [c for line in output.splitlines() if line.strip() and (c := parse_commit(line))]


def get_prior_contributor_emails(prev_tag: str | None) -> set[str]:
    if not prev_tag:
        return set()
    try:
        output = git(["log", prev_tag, "--format=%ae", "--no-merges"])
        return set(output.splitlines())
    except subprocess.CalledProcessError:
        return set()


def get_repo_url() -> str:
    try:
        remote = git(["remote", "get-url", "origin"])
        remote = re.sub(r"^git@github\.com:", "https://github.com/", remote)
        return remote.removesuffix(".git")
    except subprocess.CalledProcessError:
        return ""


def format_commit_line(c: Commit, repo_url: str) -> str:
    scope_str = f"**{c.scope}:** " if c.scope else ""
    breaking_str = " ⚠️ **BREAKING**" if c.breaking else ""
    sha_link = f"[`{c.short_sha}`]({repo_url}/commit/{c.sha})" if repo_url else f"`{c.short_sha}`"
    return f"- {scope_str}{c.description}{breaking_str} ({sha_link})"


def build_release_notes(plugin_name: str, new_version: str, prev_tag: str | None) -> str:
    repo_url = get_repo_url()
    commits = get_commits_since(prev_tag)
    prior_emails = get_prior_contributor_emails(prev_tag)

    bucketed: dict[str, list[Commit]] = defaultdict(list)
    breaking: list[Commit] = []
    for c in commits:
        bucketed[c.type].append(c)
        if c.breaking:
            breaking.append(c)

    lines: list[str] = ["## What's Changed\n"]

    if repo_url and prev_tag:
        new_tag = f"{plugin_name}@v{new_version}"
        lines.append(f"Full diff: {repo_url}/compare/{prev_tag}...{new_tag}\n")

    if breaking:
        lines += [
            "### ⚠️ Breaking Changes\n",
            *[format_commit_line(c, repo_url) for c in breaking],
            "",
        ]

    for conv_type, section_title in CONVENTIONAL_SECTIONS:
        section_commits = bucketed.get(conv_type, [])
        if section_commits:
            lines += [
                f"### {section_title}\n",
                *[format_commit_line(c, repo_url) for c in section_commits],
                "",
            ]

    other = bucketed.get("other", [])
    if other:
        lines += ["### Other Changes\n", *[format_commit_line(c, repo_url) for c in other], ""]

    seen_emails: set[str] = set()
    contributors: list[str] = []
    new_contributors: list[str] = []
    for c in commits:
        if c.author_email in seen_emails:
            continue
        seen_emails.add(c.author_email)
        contributors.append(c.author_name)
        if c.author_email not in prior_emails:
            new_contributors.append(c.author_name)

    if new_contributors:
        lines += ["### 🎉 New Contributors\n", *[f"- {name}" for name in new_contributors], ""]
    if contributors:
        lines += ["### 👥 Contributors\n", *[f"- {name}" for name in contributors], ""]

    return "\n".join(lines)


def create_release(plugin_json_path: str) -> None:
    with open(plugin_json_path) as f:
        plugin = json.load(f)

    plugin_name = plugin["name"]
    new_version = plugin.get("version")
    if not new_version:
        print(f"[{plugin_name}] No version field in {plugin_json_path}, skipping.")
        return

    # Determine previous version from the prior commit
    try:
        prev_content = git(["show", f"HEAD~1:{plugin_json_path}"])
        prev_version = json.loads(prev_content).get("version", "")
    except subprocess.CalledProcessError:
        prev_version = ""

    if new_version == prev_version:
        print(f"[{plugin_name}] Version unchanged ({new_version}), skipping.")
        return

    new_tag = f"{plugin_name}@v{new_version}"
    prev_tag = f"{plugin_name}@v{prev_version}" if prev_version else None

    # Verify the previous tag actually exists in git history
    if prev_tag and run(["git", "rev-parse", prev_tag], check=False).returncode != 0:
        prev_tag = None

    print(f"[{plugin_name}] {prev_version or '(initial)'} → {new_version}, tag: {new_tag}")

    notes = build_release_notes(plugin_name, new_version, prev_tag)

    git(["tag", new_tag])
    git(["push", "origin", new_tag])
    print(f"[{plugin_name}] Pushed tag {new_tag}")

    result = run(
        ["gh", "release", "create", new_tag, "--title", new_tag, "--notes", notes, "--latest=false"]
    )
    print(f"[{plugin_name}] Release created: {result.stdout.strip()}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <plugin.json> [<plugin.json> ...]", file=sys.stderr)
        sys.exit(1)

    if not os.environ.get("GH_TOKEN"):
        print("Error: GH_TOKEN environment variable is required.", file=sys.stderr)
        sys.exit(1)

    failed = False
    for path in sys.argv[1:]:
        try:
            create_release(path)
        except Exception as e:
            print(f"Error processing {path}: {e}", file=sys.stderr)
            failed = True

    sys.exit(1 if failed else 0)

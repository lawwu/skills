# /// script
# requires-python = ">=3.10"
# ///
"""One-shot snapshot of everything that stands between a pull request and "green".

Usage:
    uv run pr_snapshot.py <pr-url | number> [--repo owner/name] [--logs]

Prints JSON with: state, draft, author (and whether it's Dependabot), whether we can push
to the head branch, merge state (conflicts / behind / blocked), checks grouped by outcome,
unresolved review threads, and the latest top-level review verdicts.

With --logs, each failed GitHub Actions job also gets an `error_excerpt`: the lines around
the first `##[error]` marker in its log. The tail of a failed log is usually post-job
cleanup, so reading the tail misleads; the first error marker is where the failure is.

Only needs the `gh` CLI, already authenticated.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys

BOT_AUTHORS = {"app/dependabot", "dependabot[bot]", "dependabot"}
FAIL = {"FAILURE", "TIMED_OUT", "CANCELLED", "ACTION_REQUIRED", "STARTUP_FAILURE", "ERROR"}
PENDING = {"QUEUED", "IN_PROGRESS", "PENDING", "WAITING", "REQUESTED", "EXPECTED"}


def gh(*args: str, check: bool = True) -> str:
    res = subprocess.run(["gh", *args], capture_output=True, text=True)
    if check and res.returncode != 0:
        sys.exit(f"gh {' '.join(args)} failed:\n{res.stderr.strip()}")
    return res.stdout


def parse_target(target: str, repo: str | None) -> tuple[str, int]:
    m = re.match(r"https?://github\.com/([^/]+/[^/]+)/pull/(\d+)", target)
    if m:
        return m.group(1), int(m.group(2))
    if not target.isdigit():
        sys.exit(f"Not a PR URL or number: {target}")
    if not repo:
        repo = gh("repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner").strip()
    return repo, int(target)


def classify_check(c: dict) -> tuple[str, dict]:
    if c.get("__typename") == "StatusContext":
        state = (c.get("state") or "").upper()
        item = {"name": c.get("context"), "url": c.get("targetUrl"), "state": state}
        if state in ("SUCCESS",):
            return "passed", item
        if state in ("PENDING", "EXPECTED"):
            return "pending", item
        return "failed", item
    status = (c.get("status") or "").upper()
    conclusion = (c.get("conclusion") or "").upper()
    item = {
        "name": c.get("name"),
        "workflow": c.get("workflowName"),
        "url": c.get("detailsUrl"),
        "conclusion": conclusion or status,
    }
    m = re.search(r"/actions/runs/(\d+)/job/(\d+)", c.get("detailsUrl") or "")
    if m:
        item["run_id"], item["job_id"] = m.group(1), m.group(2)
    if status in PENDING or (status and status != "COMPLETED"):
        return "pending", item
    if conclusion in FAIL:
        return "failed", item
    if conclusion in ("SKIPPED", "NEUTRAL"):
        return "skipped", item
    return "passed", item


def error_excerpt(repo: str, job_id: str, before: int = 40, after: int = 3) -> str:
    log = gh("run", "view", "--repo", repo, "--job", job_id, "--log", check=False)
    if not log:
        return "(log unavailable; open the job URL)"
    # Each line is "<job>\t<step>\t<timestamp> <text>"; keep just the text.
    lines = [
        re.sub(r"\x1b\[[0-9;]*m", "", re.sub(r"^[^\t]*\t[^\t]*\t\S+Z ?", "", l))
        for l in log.splitlines()
    ]
    idx = next((i for i, l in enumerate(lines) if "##[error]" in l), None)
    if idx is None:
        return "\n".join(lines[-40:])
    # "##[error]Process completed with exit code N" only says the step failed; the cause
    # is in the lines above it, so the window reaches well back.
    return "\n".join(lines[max(0, idx - before) : idx + after])


def review_threads(repo: str, number: int) -> list[dict]:
    owner, name = repo.split("/")
    q = """
    query($owner:String!,$name:String!,$number:Int!){
      repository(owner:$owner,name:$name){pullRequest(number:$number){
        reviewThreads(first:100){nodes{
          id isResolved isOutdated path line
          comments(first:20){nodes{author{login} body url createdAt}}
        }}
      }}
    }"""
    out = gh(
        "api",
        "graphql",
        "-f",
        f"query={q}",
        "-F",
        f"owner={owner}",
        "-F",
        f"name={name}",
        "-F",
        f"number={number}",
    )
    nodes = json.loads(out)["data"]["repository"]["pullRequest"]["reviewThreads"]["nodes"]
    threads = []
    for t in nodes:
        if t["isResolved"]:
            continue
        threads.append(
            {
                "thread_id": t["id"],
                "path": t["path"],
                "line": t["line"],
                "outdated": t["isOutdated"],
                "comments": [
                    {"author": (c["author"] or {}).get("login"), "body": c["body"], "url": c["url"]}
                    for c in t["comments"]["nodes"]
                ],
            }
        )
    return threads


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("target")
    ap.add_argument("--repo")
    ap.add_argument("--logs", action="store_true", help="add error excerpts for failed jobs")
    a = ap.parse_args()

    repo, number = parse_target(a.target, a.repo)
    fields = (
        "number,title,url,state,isDraft,author,baseRefName,headRefName,headRefOid,"
        "isCrossRepository,maintainerCanModify,mergeable,mergeStateStatus,"
        "reviewDecision,statusCheckRollup,latestReviews"
    )
    pr = json.loads(gh("pr", "view", str(number), "--repo", repo, "--json", fields))

    checks: dict[str, list] = {"failed": [], "pending": [], "passed": [], "skipped": []}
    for c in pr.get("statusCheckRollup") or []:
        bucket, item = classify_check(c)
        checks[bucket].append(item)
    if a.logs:
        for item in checks["failed"]:
            if item.get("job_id"):
                item["error_excerpt"] = error_excerpt(repo, item["job_id"])

    author = (pr.get("author") or {}).get("login", "")
    me = gh("api", "user", "-q", ".login", check=False).strip()
    can_push = (not pr["isCrossRepository"]) or bool(pr.get("maintainerCanModify"))

    snapshot = {
        "repo": repo,
        "number": pr["number"],
        "title": pr["title"],
        "url": pr["url"],
        "state": pr["state"],
        "draft": pr["isDraft"],
        "author": author,
        "is_dependabot": author in BOT_AUTHORS,
        "viewer": me,
        "base": pr["baseRefName"],
        "head": pr["headRefName"],
        "head_sha": pr["headRefOid"],
        "from_fork": pr["isCrossRepository"],
        "can_push_to_head": can_push,
        "mergeable": pr["mergeable"],  # MERGEABLE | CONFLICTING | UNKNOWN
        "merge_state": pr["mergeStateStatus"],  # CLEAN | DIRTY | BEHIND | BLOCKED | UNSTABLE | ...
        "review_decision": pr["reviewDecision"] or None,
        "reviews": [
            {"author": (r.get("author") or {}).get("login"), "state": r.get("state")}
            for r in pr.get("latestReviews") or []
        ],
        "checks": {k: v for k, v in checks.items() if k != "passed"}
        | {"passed_count": len(checks["passed"])},
        "unresolved_threads": review_threads(repo, number),
    }
    print(json.dumps(snapshot, indent=2))


if __name__ == "__main__":
    main()

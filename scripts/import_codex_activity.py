#!/usr/bin/env python3
"""Import local work evidence for the Nomad AI Work agent.

This first version is intentionally conservative: it reads project registry data
and Git metadata, then writes sanitized evidence events. Raw Codex conversations
are not copied.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TIMEZONE = ZoneInfo("Asia/Seoul")
PROJECTS_PATH = PROJECT_ROOT / "data/work/projects.json"
ACTIVITY_PATH = PROJECT_ROOT / "data/work/codex-activity.jsonl"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import sanitized AI work evidence from local project sources.")
    parser.add_argument("--project-id", help="Only import evidence for one project id.")
    parser.add_argument("--dry-run", action="store_true", help="Print events without writing them.")
    parser.add_argument("--include-clean", action="store_true", help="Emit events even when a Git tree has no changes.")
    return parser.parse_args()


def load_projects() -> list[dict[str, Any]]:
    if not PROJECTS_PATH.exists():
        raise FileNotFoundError(f"Missing project registry: {PROJECTS_PATH}")
    payload = json.loads(PROJECTS_PATH.read_text(encoding="utf-8"))
    return list(payload.get("projects") or [])


def run_git(path: Path, args: list[str]) -> str:
    completed = subprocess.run(  # noqa: S603 - fixed git executable with controlled args.
        ["git", *args],
        cwd=path,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        return ""
    return completed.stdout.rstrip()


def git_changed_files(status_output: str) -> list[str]:
    files: list[str] = []
    for line in status_output.splitlines():
        if not line:
            continue
        path = line[3:].strip() if len(line) > 3 and line[2] == " " else line[2:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1].strip()
        if path:
            files.append(path)
    return files


def stable_event_id(project_id: str, captured_at: str, summary: str) -> str:
    digest = hashlib.sha256(f"{project_id}|{captured_at}|{summary}".encode("utf-8")).hexdigest()[:12]
    return f"{captured_at}-{project_id}-{digest}"


def git_event(project: dict[str, Any], source: dict[str, Any], include_clean: bool) -> dict[str, Any] | None:
    project_path = Path(source.get("path") or project.get("path") or "")
    if not project_path.exists():
        return None

    status = run_git(project_path, ["status", "--short"])
    changed_files = git_changed_files(status)
    if not changed_files and not include_clean:
        return None

    diff_stat = run_git(project_path, ["diff", "--stat"])
    recent_commits = run_git(project_path, ["log", "-5", "--oneline", "--decorate"])
    branch = run_git(project_path, ["branch", "--show-current"])
    captured_at = datetime.now(TIMEZONE).isoformat(timespec="seconds")
    project_id = str(project["project_id"])
    summary = (
        f"{len(changed_files)} changed file(s) detected"
        if changed_files
        else "Git tree checked with no current changes"
    )

    return {
        "schema_version": "0.1.0",
        "event_id": stable_event_id(project_id, captured_at, summary),
        "captured_at": captured_at,
        "source": "git",
        "project_id": project_id,
        "project_path": str(project_path),
        "session_id": None,
        "activity_type": "evidence_import",
        "goal": "Collect sanitized Git evidence for AI work progress tracking",
        "branch": branch or None,
        "changed_files": changed_files,
        "commands": [
            "git status --short",
            "git diff --stat",
            "git log -5 --oneline --decorate",
        ],
        "decisions": [],
        "blockers": [],
        "next_actions": [],
        "evidence_summary": summary,
        "git": {
            "status_short": status,
            "diff_stat": diff_stat,
            "recent_commits": recent_commits.splitlines() if recent_commits else [],
        },
        "sensitive_content_excluded": True,
    }


def build_events(args: argparse.Namespace) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for project in load_projects():
        if args.project_id and project.get("project_id") != args.project_id:
            continue
        for source in project.get("evidence_sources") or []:
            if not source.get("enabled", True):
                continue
            if source.get("type") == "git":
                event = git_event(project, source, args.include_clean)
                if event:
                    events.append(event)
    return events


def append_events(events: list[dict[str, Any]]) -> None:
    ACTIVITY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with ACTIVITY_PATH.open("a", encoding="utf-8") as handle:
        for event in events:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")


def main() -> None:
    args = parse_args()
    events = build_events(args)
    if not args.dry_run:
        append_events(events)
    print(
        json.dumps(
            {
                "schema_version": "0.1.0",
                "dry_run": args.dry_run,
                "event_count": len(events),
                "activity_path": str(ACTIVITY_PATH.relative_to(PROJECT_ROOT)),
                "events": events,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        raise SystemExit(str(exc)) from exc

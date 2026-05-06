#!/usr/bin/env python3
"""Read a constrained read-only Apple Notes context snapshot."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TIMEZONE = ZoneInfo("Asia/Seoul")
FIELD_SEP = "\x1f"
RECORD_SEP = "\x1e"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Read constrained Apple Notes context into data/context.")
    parser.add_argument("--folder", default="Nomad Life", help="Exact Apple Notes folder name to read.")
    parser.add_argument("--max-notes", type=int, default=10, help="Maximum notes to include.")
    parser.add_argument("--include-body", action="store_true", help="Include note body previews.")
    parser.add_argument(
        "--output",
        default="data/context/notes-context.json",
        help="Output path relative to the project root.",
    )
    return parser.parse_args()


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def append_jsonl(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")


def apple_script() -> str:
    return '''
on run argv
    set targetFolderName to item 1 of argv
    set maxNotes to item 2 of argv as integer
    set includeBody to item 3 of argv
    set fieldSep to ASCII character 31
    set recordSep to ASCII character 30
    set rows to {}
    set noteCount to 0
    set folderFound to false

    tell application "Notes"
        repeat with acct in accounts
            set accountName to name of acct
            repeat with noteFolder in folders of acct
                if name of noteFolder is targetFolderName then
                    set folderFound to true
                    repeat with noteItem in notes of noteFolder
                        if noteCount ≥ maxNotes then exit repeat
                        set noteTitle to name of noteItem
                        set modifiedText to modification date of noteItem as string
                        set createdText to creation date of noteItem as string
                        set bodyText to ""
                        if includeBody is "true" then
                            try
                                set bodyText to body of noteItem
                            end try
                        end if
                        set rowText to accountName & fieldSep & targetFolderName & fieldSep & noteTitle & fieldSep & createdText & fieldSep & modifiedText & fieldSep & bodyText
                        copy rowText to end of rows
                        set noteCount to noteCount + 1
                    end repeat
                end if
            end repeat
        end repeat
    end tell

    copy ("__STATUS__" & fieldSep & (folderFound as string)) to beginning of rows
    set AppleScript's text item delimiters to recordSep
    set outputText to rows as string
    set AppleScript's text item delimiters to ""
    return outputText
end run
'''


def clean_preview(html: str, limit: int = 240) -> str:
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


NOTE_AGENT_KEYWORDS = {
    "nomad-work": ("작업", "코딩", "프로젝트", "개발", "work", "code", "project"),
    "nomad-creator": ("콘텐츠", "글", "영상", "아이디어", "creator", "content", "idea"),
    "nomad-travel-guide": ("여행", "이동", "숙소", "항공", "비자", "travel", "hotel", "flight"),
    "nomad-rest": ("휴식", "피로", "회복", "잠", "rest", "recover", "sleep"),
    "nomad-food": ("식사", "밥", "음식", "카페", "food", "meal", "cafe"),
    "nomad-health": ("운동", "수영", "서핑", "산책", "health", "swim", "walk"),
    "nomad-english": ("영어", "표현", "회화", "english", "phrase"),
    "nomad-finance": ("지출", "예산", "돈", "가계부", "expense", "budget"),
}


def infer_note_agents(title: str) -> list[str]:
    lowered = title.lower()
    agents = [
        agent
        for agent, keywords in NOTE_AGENT_KEYWORDS.items()
        if any(keyword.lower() in lowered for keyword in keywords)
    ]
    return agents or ["nomad-quick-capture"]


def build_summary(notes: list[dict], folder_found: bool | None) -> dict:
    candidate_agents = sorted({agent for note in notes for agent in note.get("candidate_agents", [])})
    signals = []
    if notes:
        signals.append(
            {
                "type": "notes_context",
                "level": "candidate",
                "message": f"{len(notes)}개의 제한된 노트 metadata가 있습니다.",
            }
        )
    if candidate_agents:
        signals.append(
            {
                "type": "candidate_agents",
                "level": "candidate",
                "agents": candidate_agents,
                "message": "노트 제목 기반의 잠정 연결 후보입니다.",
            }
        )

    return {
        "note_count": len(notes),
        "has_notes_context": bool(notes),
        "folder_found": folder_found,
        "candidate_agents": candidate_agents,
        "signals": signals,
    }


def read_notes(folder: str, max_notes: int, include_body: bool) -> tuple[list[dict], str | None, bool | None]:
    try:
        result = subprocess.run(
            ["osascript", "-e", apple_script(), folder, str(max_notes), "true" if include_body else "false"],
            cwd=PROJECT_ROOT,
            text=True,
            capture_output=True,
            check=False,
            timeout=20,
        )
    except subprocess.TimeoutExpired:
        return [], "Apple Notes bridge timed out while waiting for Notes or macOS Automation permission.", None
    if result.returncode != 0:
        return [], (result.stderr or result.stdout).strip() or "Apple Notes read failed.", None

    notes = []
    folder_found = None
    output = result.stdout.strip()
    if not output:
        return notes, None, folder_found

    for index, record in enumerate(output.split(RECORD_SEP), start=1):
        fields = record.split(FIELD_SEP)
        if fields and fields[0] == "__STATUS__":
            folder_found = len(fields) > 1 and fields[1].lower() == "true"
            continue
        if len(fields) < 6:
            continue
        account, folder_name, title, created_raw, modified_raw, body = fields[:6]
        note = {
            "id": f"note_context_{len(notes) + 1}",
            "account": account,
            "folder": folder_name,
            "title": title,
            "created_raw": created_raw,
            "modified_raw": modified_raw,
            "candidate_agents": infer_note_agents(title),
            "source": "apple_notes",
        }
        if include_body:
            note["body_preview"] = clean_preview(body)
        notes.append(note)
    return notes, None, folder_found


def build_context(folder: str, max_notes: int, include_body: bool) -> dict:
    now = datetime.now(TIMEZONE)
    notes, error, folder_found = read_notes(folder, max(1, max_notes), include_body)
    status = "partial" if notes else "empty"
    quality_notes = [
        "Read-only Apple Notes snapshot.",
        f"Scope is limited to the exact folder named '{folder}'.",
    ]
    if not include_body:
        quality_notes.append("Body previews are disabled for this test.")
    if folder_found is False:
        quality_notes.append(f"The folder '{folder}' was not found in Apple Notes.")
    if error:
        status = "unavailable"
        quality_notes.append(error)

    return {
        "schema_version": "0.1.0",
        "generated_at": now.isoformat(),
        "source": "apple_notes",
        "scope": {
            "folder": folder,
            "max_notes": max_notes,
            "include_body_preview": include_body,
            "mode": "read_only",
            "folder_found": folder_found,
        },
        "data_quality": {"status": status, "notes": quality_notes},
        "summary": build_summary(notes, folder_found),
        "notes": notes,
    }


def log_action(now: datetime, output_path: Path, status: str, note_count: int, folder: str) -> None:
    date = now.date().isoformat()
    record = {
        "id": f"action_log_{now.strftime('%Y%m%d_%H%M%S')}_notes_context",
        "created_at": now.isoformat(),
        "agent_name": "nomad-notes-context",
        "action_type": "read_local_app_context",
        "target_tool": "apple_notes",
        "reason": "Create constrained read-only notes context for Coordinator analysis",
        "input": {"folder": folder},
        "output": {"path": str(output_path.relative_to(PROJECT_ROOT)), "note_count": note_count},
        "status": status,
        "approval_required": False,
        "approved_by_user": True,
        "error": None if status != "unavailable" else "Notes context unavailable",
    }
    append_jsonl(PROJECT_ROOT / f"data/action_logs/{date}.jsonl", record)


def main() -> None:
    args = parse_args()
    output_path = PROJECT_ROOT / args.output
    context = build_context(args.folder, args.max_notes, args.include_body)
    write_json(output_path, context)
    now = datetime.now(TIMEZONE)
    log_action(now, output_path, context["data_quality"]["status"], context["summary"]["note_count"], args.folder)
    print(json.dumps({"output": str(output_path), "summary": context["summary"], "data_quality": context["data_quality"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

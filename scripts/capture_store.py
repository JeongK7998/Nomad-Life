#!/usr/bin/env python3
"""Read and update capture JSONL records."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from quick_capture import build_parsed_result, confidence_for, detect_agents
from time_utils import local_timezone


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TIMEZONE = local_timezone()


def capture_path(date: str) -> Path:
    return PROJECT_ROOT / f"data/captures/{date}.jsonl"


def read_captures(date: str, include_ignored: bool = True) -> list[dict]:
    path = capture_path(date)
    if not path.exists():
        return []

    records = []
    with path.open(encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            if include_ignored or record.get("status") != "ignored":
                records.append(record)
    return records


def read_captures_for_month(month: str, include_ignored: bool = True) -> list[dict]:
    captures_dir = PROJECT_ROOT / "data/captures"
    records: list[dict] = []
    for path in sorted(captures_dir.glob(f"{month}-*.jsonl")):
        records.extend(read_captures(path.stem, include_ignored=include_ignored))
    return records


def read_all_captures(include_ignored: bool = True) -> list[dict]:
    captures_dir = PROJECT_ROOT / "data/captures"
    records: list[dict] = []
    for path in sorted(captures_dir.glob("*.jsonl")):
        records.extend(read_captures(path.stem, include_ignored=include_ignored))
    return records


def write_captures(date: str, captures: list[dict]) -> None:
    path = capture_path(date)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for capture in captures:
            file.write(json.dumps(capture, ensure_ascii=False, separators=(",", ":")) + "\n")


def update_capture_status(capture_id: str, status: str) -> dict:
    return update_capture(capture_id, {"status": status})


def delete_capture(capture_id: str) -> dict:
    captures_dir = PROJECT_ROOT / "data/captures"
    for path in sorted(captures_dir.glob("*.jsonl"), reverse=True):
        date = path.stem
        captures = read_captures(date, include_ignored=True)
        for index, capture in enumerate(captures):
            if capture.get("id") != capture_id:
                continue
            deleted = {**capture}
            captures.pop(index)
            write_captures(date, captures)
            return deleted
    raise ValueError(f"Capture not found: {capture_id}")


def update_capture(capture_id: str, updates: dict) -> dict:
    captures_dir = PROJECT_ROOT / "data/captures"
    for path in sorted(captures_dir.glob("*.jsonl"), reverse=True):
        date = path.stem
        captures = read_captures(date, include_ignored=True)
        for index, capture in enumerate(captures):
            if capture.get("id") == capture_id:
                updated = {**capture}
                raw_content = updates.get("raw_content")
                if raw_content is not None:
                    text = str(raw_content).strip()
                    if not text:
                        raise ValueError("raw_content cannot be empty.")
                    linked_agents = detect_agents(text)
                    updated["raw_content"] = text
                    updated["linked_agents"] = linked_agents
                    updated["parsed_result"] = build_parsed_result(text, linked_agents)
                    updated["confidence"] = confidence_for(updated["parsed_result"], linked_agents)

                if updates.get("type") is not None:
                    updated["type"] = str(updates["type"] or "text")
                if updates.get("media_url") is not None:
                    updated["media_url"] = updates["media_url"]
                if updates.get("status") is not None:
                    updated["status"] = str(updates["status"])
                if updates.get("date") is not None:
                    updated["date"] = str(updates["date"])

                updated["updated_at"] = datetime.now(TIMEZONE).isoformat()
                captures.pop(index)
                write_captures(date, captures)
                target_date = updated.get("date") or date
                target_captures = read_captures(target_date, include_ignored=True) if target_date != date else captures
                target_captures.append(updated)
                write_captures(target_date, target_captures)
                return updated

    raise ValueError(f"Capture not found: {capture_id}")

#!/usr/bin/env python3
"""Read and update capture JSONL records."""

from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


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


def write_captures(date: str, captures: list[dict]) -> None:
    path = capture_path(date)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for capture in captures:
            file.write(json.dumps(capture, ensure_ascii=False, separators=(",", ":")) + "\n")


def update_capture_status(capture_id: str, status: str) -> dict:
    captures_dir = PROJECT_ROOT / "data/captures"
    for path in sorted(captures_dir.glob("*.jsonl"), reverse=True):
        date = path.stem
        captures = read_captures(date, include_ignored=True)
        for capture in captures:
            if capture.get("id") == capture_id:
                capture["status"] = status
                write_captures(date, captures)
                return capture

    raise ValueError(f"Capture not found: {capture_id}")

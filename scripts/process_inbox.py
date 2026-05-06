#!/usr/bin/env python3
"""Process local/iCloud inbox files into Nomad Life captures."""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from quick_capture import PROJECT_ROOT, save_capture
from refresh_outputs import refresh_outputs


TIMEZONE = ZoneInfo("Asia/Seoul")
INBOX_DIRS = [
    PROJECT_ROOT / "data/inbox/local",
    PROJECT_ROOT / "data/inbox/cloud",
]

# macOS marks iCloud placeholder files as dataless. Reading one can block while
# iCloud downloads it, which would make the whole daily runner hang.
SF_DATALESS = 0x40000000


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Process Nomad Life inbox files.")
    parser.add_argument("--no-dashboard", action="store_true", help="Do not regenerate dashboard after processing.")
    return parser.parse_args()


def read_inbox_file(path: Path) -> tuple[str, str, str | None]:
    if path.suffix.lower() == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        text = str(payload.get("text") or payload.get("raw_content") or "").strip()
        capture_type = str(payload.get("type") or "text")
        media_url = payload.get("media_url")
        return text, capture_type, media_url

    return path.read_text(encoding="utf-8").strip(), "text", None


def is_dataless_icloud_file(path: Path) -> bool:
    try:
        flags = getattr(path.stat(), "st_flags", 0)
    except OSError:
        return False
    return bool(flags & SF_DATALESS)


def processed_path(path: Path, now: datetime) -> Path:
    target_dir = PROJECT_ROOT / "data/sync/processed" / now.date().isoformat()
    target_dir.mkdir(parents=True, exist_ok=True)
    return target_dir / f"{now.strftime('%H%M%S')}_{path.name}"


def process_file(path: Path, now: datetime) -> dict:
    if is_dataless_icloud_file(path):
        raise BlockingIOError("iCloud file is not downloaded locally yet; skipped to keep the daily runner non-blocking.")

    text, capture_type, media_url = read_inbox_file(path)
    if not text:
        raise ValueError(f"{path} is empty.")

    record = save_capture(text, capture_type, media_url, now)
    target = processed_path(path, now)
    shutil.move(str(path), str(target))
    return {
        "source": str(path.relative_to(PROJECT_ROOT)),
        "processed_to": str(target.relative_to(PROJECT_ROOT)),
        "capture_id": record["id"],
        "date": record["date"],
    }


def inbox_files() -> list[Path]:
    files: list[Path] = []
    for directory in INBOX_DIRS:
        directory.mkdir(parents=True, exist_ok=True)
        for path in sorted(directory.iterdir()):
            if path.is_file() and path.name != ".gitkeep" and path.suffix.lower() in {".txt", ".json"}:
                files.append(path)
    return files


def classify_error(exc: Exception) -> str:
    if isinstance(exc, BlockingIOError):
        return "skipped"
    return "error"


def main() -> None:
    args = parse_args()
    result = process_inbox(regenerate_dashboard=not args.no_dashboard)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def process_inbox(regenerate_dashboard: bool = True) -> dict:
    now = datetime.now(TIMEZONE)
    results = []
    errors = []

    for path in inbox_files():
        try:
            results.append(process_file(path, now))
        except Exception as exc:  # noqa: BLE001 - keep processing other inbox files.
            errors.append({
                "source": str(path.relative_to(PROJECT_ROOT)),
                "status": classify_error(exc),
                "error": str(exc),
            })

    dashboard = None
    if results and regenerate_dashboard:
        dashboard = refresh_outputs(now=now)

    return {
        "processed": results,
        "errors": errors,
        "dashboard": dashboard,
    }


if __name__ == "__main__":
    main()

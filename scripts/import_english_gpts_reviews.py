#!/usr/bin/env python3
"""Import GPTs English review exports from iCloud into the local inbox."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TIMEZONE = ZoneInfo("Asia/Seoul")
ICLOUD_ENGLISH_DIR = Path("/Users/jongiljeong/Library/Mobile Documents/com~apple~CloudDocs/Nomad_life/English")
LOCAL_INBOX_DIR = PROJECT_ROOT / "data/english/gpts-reviews/inbox"
MANIFEST_PATH = PROJECT_ROOT / "data/english/gpts-reviews/import-manifest.json"
ACTION_LOG_DIR = PROJECT_ROOT / "data/action_logs"
SUPPORTED_SUFFIXES = (".json", ".md", ".md.txt", ".txt")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import GPTs English review files from iCloud.")
    parser.add_argument("--source", default=str(ICLOUD_ENGLISH_DIR), help="Source iCloud English review folder.")
    parser.add_argument("--target", default=str(LOCAL_INBOX_DIR), help="Local GPTs review inbox folder.")
    parser.add_argument("--refresh", action="store_true", help="Refresh derived dashboard outputs after import.")
    parser.add_argument("--date", help="Date to refresh in YYYY-MM-DD. Defaults to today in Asia/Seoul.")
    return parser.parse_args()


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_supported(path: Path) -> bool:
    name = path.name.lower()
    return any(name.endswith(suffix) for suffix in SUPPORTED_SUFFIXES)


def import_reviews(source_dir: Path, target_dir: Path) -> dict:
    now = datetime.now(TIMEZONE)
    result = {
        "schema_version": "0.1.0",
        "imported_at": now.isoformat(),
        "source_dir": str(source_dir),
        "target_dir": str(target_dir.relative_to(PROJECT_ROOT) if target_dir.is_relative_to(PROJECT_ROOT) else target_dir),
        "scanned_count": 0,
        "imported": [],
        "updated": [],
        "skipped": [],
        "errors": [],
        "deleted": [],
    }
    if not source_dir.exists():
        result["errors"].append({"file": str(source_dir), "error": "source_dir_not_found"})
        return result

    target_dir.mkdir(parents=True, exist_ok=True)
    manifest = {}
    if MANIFEST_PATH.exists():
        try:
            manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8")).get("files", {})
        except (json.JSONDecodeError, OSError):
            manifest = {}
    seen_names = set()
    next_manifest = {}
    for source_path in sorted(path for path in source_dir.iterdir() if path.is_file() and is_supported(path)):
        result["scanned_count"] += 1
        seen_names.add(source_path.name)
        target_path = target_dir / source_path.name
        try:
            source_stat = source_path.stat()
            source_sig = f"{int(source_stat.st_mtime_ns)}:{source_stat.st_size}"
            previous = manifest.get(source_path.name, {})
            if target_path.exists() and previous.get("source_sig") == source_sig:
                    result["skipped"].append(source_path.name)
                    next_manifest[source_path.name] = previous
                    continue
            if target_path.exists():
                shutil.copy2(source_path, target_path)
                result["updated"].append(source_path.name)
            else:
                shutil.copy2(source_path, target_path)
                result["imported"].append(source_path.name)
            next_manifest[source_path.name] = {
                "source_sig": source_sig,
                "last_synced_at": now.isoformat(),
                "status": "active",
            }
        except OSError as exc:
            result["errors"].append({"file": source_path.name, "error": str(exc)})

    for name in sorted(manifest.keys()):
        if name in seen_names:
            continue
        stale = target_dir / name
        if stale.exists():
            try:
                stale.unlink()
            except OSError as exc:
                result["errors"].append({"file": name, "error": str(exc)})
                continue
        result["deleted"].append(name)

    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(
        json.dumps({"schema_version": "0.1.0", "updated_at": now.isoformat(), "files": next_manifest}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return result


def append_action_log(result: dict, refresh: dict | None = None) -> None:
    now = datetime.now(TIMEZONE)
    ACTION_LOG_DIR.mkdir(parents=True, exist_ok=True)
    record = {
        "id": f"action_log_{now.strftime('%Y%m%d_%H%M%S')}_english_gpts_import",
        "created_at": now.isoformat(),
        "agent_name": "nomad-english",
        "action_type": "import_gpts_reviews_from_icloud",
        "target_tool": "local_files",
        "reason": "Keep GPTs English review exports available for cumulative dashboard analysis.",
        "input": {"source_dir": result.get("source_dir"), "target_dir": result.get("target_dir")},
        "output": {
            "scanned_count": result.get("scanned_count", 0),
            "imported_count": len(result.get("imported", [])),
            "updated_count": len(result.get("updated", [])),
            "skipped_count": len(result.get("skipped", [])),
            "error_count": len(result.get("errors", [])),
            "refresh_date": refresh.get("date") if refresh else None,
        },
        "status": "warning" if result.get("errors") else "success",
        "approval_required": False,
        "approved_by_user": False,
        "error": result.get("errors") or None,
    }
    path = ACTION_LOG_DIR / f"{now.date().isoformat()}.jsonl"
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")


def main() -> None:
    args = parse_args()
    result = import_reviews(Path(args.source).expanduser(), Path(args.target).expanduser())
    refresh = None
    if args.refresh:
        from refresh_outputs import refresh_outputs

        refresh = refresh_outputs(args.date)
        result["refresh"] = {
            "date": refresh["date"],
            "outputs": [
                "dashboard/english.json",
                "data/english/english-notes.json",
                f"data/agent_reports/{refresh['date']}.json",
            ],
        }
    append_action_log(result, refresh=refresh)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

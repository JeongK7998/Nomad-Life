#!/usr/bin/env python3
"""Package current Nomad Life data by stay/region and create a local backup."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tarfile
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TIMEZONE = ZoneInfo("Asia/Makassar")
CURRENT_STAY_PATH = PROJECT_ROOT / "data/travel/current-stay.json"
STAYS_INDEX_PATH = PROJECT_ROOT / "data/travel/stays-index.json"
STAYS_ROOT = PROJECT_ROOT / "data/stays"
BACKUPS_ROOT = PROJECT_ROOT / "data/backups/stays"


DATA_SOURCES = [
    "data/action_logs",
    "data/captures",
    "data/activity",
    "data/agent_reports",
    "data/content",
    "data/context",
    "data/english",
    "data/expenses",
    "data/health/health-summary.json",
    "data/health/workout-sessions.jsonl",
    "data/meals",
    "data/rest",
    "data/travel",
    "data/work",
    "dashboard",
    "reports/daily",
    "reports/weekly",
    "reports/monthly",
]

EXCLUDED_NAMES = {
    ".DS_Store",
    "node_modules",
    ".git",
    "__pycache__",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a region/stay package and backup from local Nomad Life data.")
    parser.add_argument("--stay-id", default="bali-2026-05", help="Stable stay id, e.g. bali-2026-05.")
    parser.add_argument("--region", default="Bali", help="Human-readable region name.")
    parser.add_argument("--country", default="Indonesia", help="Country name.")
    parser.add_argument("--start-date", default="2026-05-19", help="Stay start date in YYYY-MM-DD.")
    parser.add_argument("--end-date", default=None, help="Optional stay end date in YYYY-MM-DD.")
    parser.add_argument("--timezone", default="Asia/Makassar", help="IANA timezone for this stay.")
    parser.add_argument("--dataset-scope", default="current", choices=["current", "all"], help="Dashboard dataset scope for this stay.")
    parser.add_argument("--note", default="Bali real-use data package.", help="Short package note.")
    parser.add_argument("--no-backup", action="store_true", help="Only update the stay package without creating a tar.gz backup.")
    return parser.parse_args()


def read_json(path: Path, fallback: dict | None = None) -> dict:
    if not path.exists():
        return fallback or {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return fallback or {}


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def append_jsonl(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def should_copy(path: Path) -> bool:
    return not any(part in EXCLUDED_NAMES for part in path.parts)


def copy_source(source: Path, target_root: Path) -> list[str]:
    copied: list[str] = []
    if not source.exists():
        return copied

    if source.is_file():
        relative = source.relative_to(PROJECT_ROOT)
        target = target_root / "snapshot" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        copied.append(str(relative))
        return copied

    for path in sorted(source.rglob("*")):
        if not path.is_file() or not should_copy(path):
            continue
        relative = path.relative_to(PROJECT_ROOT)
        target = target_root / "snapshot" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        copied.append(str(relative))
    return copied


def build_current_stay(args: argparse.Namespace, now: datetime) -> dict:
    stay_id = str(args.stay_id or "").strip()
    region = str(args.region or "").strip()
    country = str(args.country or "").strip()
    timezone = str(args.timezone or "").strip()
    start_date = str(args.start_date or "").strip()
    if not stay_id:
        raise ValueError("stay_id is required.")
    if not region:
        raise ValueError("region is required.")
    if not timezone:
        raise ValueError("timezone is required.")
    ZoneInfo(timezone)
    return {
        "schema_version": "0.1.0",
        "updated_at": now.isoformat(),
        "stay_id": stay_id,
        "region": region,
        "country": country,
        "timezone": timezone,
        "start_date": start_date,
        "end_date": args.end_date,
        "status": "active" if not args.end_date else "closed",
        "dataset_scope": getattr(args, "dataset_scope", "current") or "current",
        "local_package_path": f"data/stays/{stay_id}",
        "backup_root": f"data/backups/stays/{stay_id}",
        "notes": [
            args.note,
            "Canonical working data remains in data/, dashboard/, and reports/.",
            "This stay package is a local-first grouped snapshot for review, migration, and backup.",
        ],
    }


def stay_index_item(stay: dict) -> dict:
    return {
        "stay_id": stay.get("stay_id"),
        "region": stay.get("region"),
        "country": stay.get("country"),
        "timezone": stay.get("timezone"),
        "start_date": stay.get("start_date"),
        "end_date": stay.get("end_date"),
        "status": stay.get("status"),
        "dataset_scope": stay.get("dataset_scope", "current"),
        "local_package_path": stay.get("local_package_path"),
        "backup_root": stay.get("backup_root"),
        "updated_at": stay.get("updated_at"),
        "note": (stay.get("notes") or [""])[0],
    }


def update_stays_index(current_stay: dict, previous_stay: dict | None = None) -> dict:
    index = read_json(
        STAYS_INDEX_PATH,
        {
            "schema_version": "0.1.0",
            "updated_at": current_stay.get("updated_at"),
            "active_stay_id": None,
            "stays": [],
        },
    )
    stays = [item for item in index.get("stays", []) if item.get("stay_id")]

    if previous_stay and previous_stay.get("stay_id") and previous_stay.get("stay_id") != current_stay.get("stay_id"):
        closed_previous = dict(previous_stay)
        closed_previous["status"] = "closed"
        closed_previous["end_date"] = closed_previous.get("end_date") or current_stay.get("start_date")
        closed_previous["updated_at"] = current_stay.get("updated_at")
        stays = [item for item in stays if item.get("stay_id") != closed_previous.get("stay_id")]
        stays.append(stay_index_item(closed_previous))

    stays = [item for item in stays if item.get("stay_id") != current_stay.get("stay_id")]
    stays.append(stay_index_item(current_stay))
    stays.sort(key=lambda item: (item.get("start_date") or "", item.get("stay_id") or ""), reverse=True)

    index = {
        "schema_version": "0.1.0",
        "updated_at": current_stay.get("updated_at"),
        "active_stay_id": current_stay.get("stay_id") if current_stay.get("status") == "active" else None,
        "stays": stays,
    }
    write_json(STAYS_INDEX_PATH, index)
    return index


def package_stay(args: argparse.Namespace) -> dict:
    tz = ZoneInfo(args.timezone)
    now = datetime.now(tz)
    stay_dir = STAYS_ROOT / args.stay_id
    snapshot_dir = stay_dir / "snapshot"
    if snapshot_dir.exists():
        shutil.rmtree(snapshot_dir)
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    current_stay = build_current_stay(args, now)
    write_json(CURRENT_STAY_PATH, current_stay)
    stays_index = update_stays_index(current_stay)

    copied_files: list[str] = []
    for source in DATA_SOURCES:
        copied_files.extend(copy_source(PROJECT_ROOT / source, stay_dir))

    backup_path = None
    if not args.no_backup:
        backup_dir = BACKUPS_ROOT / args.stay_id
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_path = backup_dir / f"{args.stay_id}-{now.strftime('%Y%m%d-%H%M%S')}.tar.gz"

    action = {
        "id": f"action_log_{now.strftime('%Y%m%d_%H%M%S')}_stay_package",
        "created_at": now.isoformat(),
        "agent_name": "nomad-travel-guide",
        "action_type": "package_stay_data",
        "target_tool": "local_files",
        "reason": "Group Nomad Life data by active stay/region and create a local backup.",
        "input": {
            "stay_id": args.stay_id,
            "region": args.region,
            "country": args.country,
            "start_date": args.start_date,
            "end_date": args.end_date,
            "dataset_scope": getattr(args, "dataset_scope", "current") or "current",
        },
        "output": {
            "current_stay_path": "data/travel/current-stay.json",
            "package_path": f"data/stays/{args.stay_id}",
            "manifest_path": f"data/stays/{args.stay_id}/manifest.json",
            "backup_path": str(backup_path.relative_to(PROJECT_ROOT)) if backup_path else None,
            "file_count": len(copied_files),
        },
        "status": "success",
        "approval_required": False,
        "approved_by_user": False,
        "error": None,
    }
    append_jsonl(PROJECT_ROOT / f"data/action_logs/{now.date().isoformat()}.jsonl", action)
    for path in copy_source(PROJECT_ROOT / "data/action_logs", stay_dir):
        if path not in copied_files:
            copied_files.append(path)

    manifest = {
        "schema_version": "0.1.0",
        "generated_at": now.isoformat(),
        "stay": current_stay,
        "stays_index": {
            "path": "data/travel/stays-index.json",
            "active_stay_id": stays_index.get("active_stay_id"),
            "stay_count": len(stays_index.get("stays") or []),
        },
        "source_roots": DATA_SOURCES,
        "excluded_names": sorted(EXCLUDED_NAMES),
        "file_count": len(copied_files),
        "files": copied_files,
        "privacy": {
            "local_first": True,
            "contains_personal_data": True,
            "cloud_upload_allowed": False,
            "secrets_excluded_by_scope": True,
        },
        "restore_notes": [
            "This package is a point-in-time copy. Restore manually by copying selected files from snapshot/ back to the project root.",
            "Do not restore over newer canonical data without reviewing diffs first.",
        ],
        "retention_policy": "Keep at least the latest backup per active stay during MVP validation.",
    }
    write_json(stay_dir / "manifest.json", manifest)

    if not args.no_backup:
        with tarfile.open(backup_path, "w:gz") as archive:
            archive.add(stay_dir, arcname=f"stays/{args.stay_id}")
        manifest["backup"] = {
            "path": str(backup_path.relative_to(PROJECT_ROOT)),
            "sha256": file_sha256(backup_path),
        }
        write_json(stay_dir / "manifest.json", manifest)

    return {
        "schema_version": "0.1.0",
        "generated_at": now.isoformat(),
        "stay_id": args.stay_id,
        "package_path": f"data/stays/{args.stay_id}",
        "manifest_path": f"data/stays/{args.stay_id}/manifest.json",
        "backup_path": str(backup_path.relative_to(PROJECT_ROOT)) if backup_path else None,
        "backup_sha256": file_sha256(backup_path) if backup_path else None,
        "file_count": len(copied_files),
    }


def package_current_stay() -> dict:
    current = read_json(CURRENT_STAY_PATH, {})
    args = argparse.Namespace(
        stay_id=current.get("stay_id") or "bali-2026-05",
        region=current.get("region") or "Bali",
        country=current.get("country") or "Indonesia",
        start_date=current.get("start_date") or datetime.now(ZoneInfo(current.get("timezone") or "Asia/Makassar")).date().isoformat(),
        end_date=current.get("end_date"),
        timezone=current.get("timezone") or "Asia/Makassar",
        dataset_scope=current.get("dataset_scope") or "current",
        note="Manual current stay package from dashboard/local runner.",
        no_backup=False,
    )
    return package_stay(args)


def update_current_stay(payload: dict) -> dict:
    previous = read_json(CURRENT_STAY_PATH, {})
    timezone = str(payload.get("timezone") or previous.get("timezone") or "Asia/Makassar").strip()
    now = datetime.now(ZoneInfo(timezone))
    previous_note = (previous.get("notes") or [""])[0]
    args = argparse.Namespace(
        stay_id=str(payload.get("stay_id") or previous.get("stay_id") or "").strip(),
        region=str(payload.get("region") or previous.get("region") or "").strip(),
        country=str(payload.get("country") or previous.get("country") or "").strip(),
        start_date=str(payload.get("start_date") or previous.get("start_date") or now.date().isoformat()).strip(),
        end_date=str(payload.get("end_date") or "").strip() or None,
        timezone=timezone,
        dataset_scope=str(payload.get("dataset_scope") or previous.get("dataset_scope") or "current"),
        note=str(payload.get("note") or previous_note or "User configured stay from Settings.").strip(),
    )
    current_stay = build_current_stay(args, now)
    write_json(CURRENT_STAY_PATH, current_stay)
    stays_index = update_stays_index(current_stay, previous_stay=previous)
    action = {
        "id": f"action_log_{now.strftime('%Y%m%d_%H%M%S')}_current_stay_update",
        "created_at": now.isoformat(),
        "agent_name": "nomad-travel-guide",
        "action_type": "update_current_stay",
        "target_tool": "local_files",
        "reason": "User updated current stay settings from the Dashboard.",
        "input": {
            "stay_id": current_stay["stay_id"],
            "region": current_stay["region"],
            "country": current_stay["country"],
            "timezone": current_stay["timezone"],
            "start_date": current_stay["start_date"],
            "end_date": current_stay["end_date"],
            "dataset_scope": current_stay["dataset_scope"],
        },
        "output": {
            "current_stay_path": "data/travel/current-stay.json",
            "stays_index_path": "data/travel/stays-index.json",
        },
        "status": "success",
        "approval_required": False,
        "approved_by_user": False,
        "error": None,
    }
    append_jsonl(PROJECT_ROOT / f"data/action_logs/{now.date().isoformat()}.jsonl", action)
    current_stay["stays_index"] = {
        "active_stay_id": stays_index.get("active_stay_id"),
        "stay_count": len(stays_index.get("stays") or []),
    }
    return current_stay


def main() -> None:
    args = parse_args()
    print(json.dumps(package_stay(args), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

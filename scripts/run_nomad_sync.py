#!/usr/bin/env python3
"""Run the Nomad Life cloud-light sync loop safely from the Mac."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterator
from zoneinfo import ZoneInfo


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TIMEZONE = ZoneInfo("Asia/Seoul")
LOCK_PATH = PROJECT_ROOT / "data/sync/nomad-sync.lock"
RUN_LOG_PATH = PROJECT_ROOT / "data/action_logs/nomad-sync-runs.jsonl"
ENV_PATH = PROJECT_ROOT / ".env"
STALE_LOCK_SECONDS = 60 * 60


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Nomad Life Supabase sync with env loading, locking, and run logs.")
    parser.add_argument("--dry-run", action="store_true", help="Preview pending queue work and publishable snapshots.")
    parser.add_argument("--skip-process", action="store_true", help="Do not process pending Supabase queue rows.")
    parser.add_argument("--skip-publish", action="store_true", help="Do not publish dashboard snapshots.")
    parser.add_argument("--limit", type=int, default=20, help="Maximum pending rows to process per queue table.")
    parser.add_argument("--watch", action="store_true", help="Repeat sync until stopped.")
    parser.add_argument("--interval", type=int, default=300, help="Seconds between watch runs. Defaults to 300.")
    parser.add_argument("--iterations", type=int, help="Stop watch mode after this many runs.")
    return parser.parse_args()


def load_env_file(path: Path = ENV_PATH) -> dict[str, str]:
    loaded: dict[str, str] = {}
    if not path.exists():
        return loaded
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if not key or key in os.environ:
            continue
        os.environ[key] = value
        loaded[key] = value
    return loaded


def required_env_present(dry_run: bool) -> tuple[bool, list[str]]:
    if dry_run:
        return True, []
    missing = [name for name in ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY") if not os.environ.get(name)]
    return not missing, missing


@contextmanager
def sync_lock() -> Iterator[None]:
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    if LOCK_PATH.exists():
        lock_age = time.time() - LOCK_PATH.stat().st_mtime
        if lock_age > STALE_LOCK_SECONDS:
            LOCK_PATH.unlink()
    try:
        fd = os.open(str(LOCK_PATH), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise RuntimeError(f"Sync already appears to be running: {LOCK_PATH}") from exc
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(json.dumps({"pid": os.getpid(), "started_at": datetime.now(TIMEZONE).isoformat()}) + "\n")
        yield
    finally:
        try:
            LOCK_PATH.unlink()
        except FileNotFoundError:
            pass


def worker_command(args: argparse.Namespace) -> list[str]:
    command = [sys.executable, str(PROJECT_ROOT / "scripts/supabase_worker.py"), "--limit", str(args.limit)]
    if not args.skip_process:
        command.append("--process")
    if not args.skip_publish:
        command.append("--publish-snapshots")
    if args.dry_run:
        command.append("--dry-run")
    return command


def append_run_log(record: dict) -> None:
    RUN_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with RUN_LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def run_once(args: argparse.Namespace) -> dict:
    started_at = datetime.now(TIMEZONE)
    load_env_file()
    env_ok, missing = required_env_present(args.dry_run)
    if not env_ok:
        raise RuntimeError(f"Missing required environment values: {', '.join(missing)}")

    command = worker_command(args)
    completed = subprocess.run(  # noqa: S603 - command is built from this repository's Python script.
        command,
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    finished_at = datetime.now(TIMEZONE)
    parsed_stdout = None
    if completed.stdout.strip():
        try:
            parsed_stdout = json.loads(completed.stdout)
        except json.JSONDecodeError:
            parsed_stdout = {"raw": completed.stdout.strip()}
    record = {
        "schema_version": "0.1.0",
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "duration_seconds": round((finished_at - started_at).total_seconds(), 3),
        "status": "success" if completed.returncode == 0 else "failed",
        "dry_run": args.dry_run,
        "process": not args.skip_process,
        "publish_snapshots": not args.skip_publish,
        "limit": args.limit,
        "returncode": completed.returncode,
        "worker_result": parsed_stdout,
        "stderr": completed.stderr.strip() or None,
    }
    append_run_log(record)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or "Supabase worker failed.")
    return record


def public_result(record: dict) -> dict:
    worker_result = record.get("worker_result") or {}
    return {
        "schema_version": record["schema_version"],
        "started_at": record["started_at"],
        "finished_at": record["finished_at"],
        "duration_seconds": record["duration_seconds"],
        "status": record["status"],
        "dry_run": record["dry_run"],
        "processed_count": len(worker_result.get("processed") or []),
        "failed_count": len(worker_result.get("failed") or []),
        "snapshot_count": len(worker_result.get("snapshots") or []),
        "worker_result": worker_result,
        "run_log_path": str(RUN_LOG_PATH.relative_to(PROJECT_ROOT)),
    }


def main() -> None:
    args = parse_args()
    if args.skip_process and args.skip_publish:
        raise SystemExit("Nothing to do: both --skip-process and --skip-publish were provided.")
    if args.interval < 30:
        raise SystemExit("--interval must be at least 30 seconds.")

    runs = 0
    while True:
        with sync_lock():
            result = public_result(run_once(args))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        runs += 1
        if not args.watch or (args.iterations and runs >= args.iterations):
            break
        time.sleep(args.interval)


if __name__ == "__main__":
    main()

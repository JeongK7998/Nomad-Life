#!/usr/bin/env python3
"""Process Nomad Life Supabase queues from the Mac Hermes worker."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from quick_capture import save_capture  # noqa: E402
from refresh_outputs import refresh_outputs  # noqa: E402
from workout_store import read_workout_sessions, save_workout_session, summarize_strength_entries  # noqa: E402


TIMEZONE = ZoneInfo("Asia/Seoul")
WORKER_NAME = "mac_hermes_worker"
DASHBOARD_FILES = {
    "today": PROJECT_ROOT / "dashboard/today.json",
    "health": PROJECT_ROOT / "dashboard/health.json",
    "life-balance": PROJECT_ROOT / "dashboard/life-balance.json",
    "activity-allocation": PROJECT_ROOT / "dashboard/activity-allocation.json",
    "notifications": PROJECT_ROOT / "dashboard/notifications.json",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Process Supabase queue records for Nomad Life.")
    parser.add_argument("--process", action="store_true", help="Process pending capture/workout queue rows.")
    parser.add_argument("--publish-snapshots", action="store_true", help="Publish local dashboard JSON snapshots.")
    parser.add_argument("--dry-run", action="store_true", help="Read and print pending work without mutating Supabase/local data.")
    parser.add_argument("--limit", type=int, default=20)
    return parser.parse_args()


def env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"{name} is required.")
    return value.rstrip("/")


class SupabaseClient:
    def __init__(self) -> None:
        self.url = env("SUPABASE_URL")
        self.key = env("SUPABASE_SERVICE_ROLE_KEY")

    def request(self, method: str, path: str, body: Any | None = None) -> Any:
        data = None
        headers = {
            "apikey": self.key,
            "authorization": f"Bearer {self.key}",
            "content-type": "application/json",
            "accept": "application/json",
            "prefer": "return=representation",
        }
        if body is not None:
            data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        request = Request(f"{self.url}/rest/v1/{path}", data=data, headers=headers, method=method)
        try:
            with urlopen(request, timeout=30) as response:  # noqa: S310 - controlled Supabase URL from env.
                raw = response.read().decode("utf-8")
                return json.loads(raw) if raw else None
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Supabase {method} {path} failed: {exc.code} {detail}") from exc

    def pending_rows(self, table: str, limit: int) -> list[dict]:
        path = f"{table}?status=eq.pending&order=created_at.asc&limit={limit}"
        return self.request("GET", path) or []

    def rows(self, path: str) -> list[dict]:
        return self.request("GET", path) or []

    def patch(self, table: str, row_id: str, payload: dict) -> dict | None:
        rows = self.request("PATCH", f"{table}?id=eq.{quote(row_id)}", payload)
        return rows[0] if rows else None

    def insert(self, table: str, payload: dict) -> dict | None:
        rows = self.request("POST", table, payload)
        return rows[0] if rows else None

    def log_sync(
        self,
        *,
        action: str,
        status: str,
        target_table: str | None = None,
        target_id: str | None = None,
        details: dict | None = None,
    ) -> None:
        self.insert(
            "sync_logs",
            {
                "worker": WORKER_NAME,
                "action": action,
                "target_table": target_table,
                "target_id": target_id,
                "status": status,
                "details": details or {},
            },
        )


def process_capture(row: dict, client: SupabaseClient, dry_run: bool = False) -> dict:
    payload = row.get("payload") or {}
    text = str(payload.get("text") or payload.get("raw_content") or "").strip()
    if not text:
        raise ValueError("capture_queue payload.text is required.")
    capture_type = str(payload.get("type") or "text")
    media_url = payload.get("media_url")
    if dry_run:
        return {"capture_id": None, "date": None, "summary": text[:80]}
    client.patch("capture_queue", row["id"], {"status": "processing", "updated_at": datetime.now(TIMEZONE).isoformat()})
    capture = save_capture(text, capture_type, media_url)
    refresh_outputs(capture["date"])
    client.patch(
        "capture_queue",
        row["id"],
        {
            "status": "processed",
            "processed_at": datetime.now(TIMEZONE).isoformat(),
            "updated_at": datetime.now(TIMEZONE).isoformat(),
            "local_capture_id": capture["id"],
            "error": None,
        },
    )
    return {"capture_id": capture["id"], "date": capture["date"]}


def process_workout(row: dict, client: SupabaseClient, dry_run: bool = False) -> dict:
    payload = row.get("payload") or {}
    entries = payload.get("entries") or []
    if not entries:
        raise ValueError("workout_queue payload.entries is required.")
    if dry_run:
        return {"session_id": None, "summary": summarize_strength_entries(entries)}
    client.patch("workout_queue", row["id"], {"status": "processing", "updated_at": datetime.now(TIMEZONE).isoformat()})
    capture = save_capture(f"근력운동 기록: {summarize_strength_entries(entries)}", "checkin")
    payload["source"] = "supabase_workout_queue"
    payload["source_capture_id"] = capture["id"]
    session = save_workout_session(payload)
    refresh_outputs(session["date"])
    client.patch(
        "workout_queue",
        row["id"],
        {
            "status": "processed",
            "processed_at": datetime.now(TIMEZONE).isoformat(),
            "updated_at": datetime.now(TIMEZONE).isoformat(),
            "local_workout_session_id": session["id"],
            "error": None,
        },
    )
    return {"session_id": session["id"], "date": session["date"]}


def mark_failed(client: SupabaseClient, table: str, row_id: str, error: Exception, dry_run: bool) -> None:
    if dry_run:
        return
    client.patch(
        table,
        row_id,
        {
            "status": "failed",
            "updated_at": datetime.now(TIMEZONE).isoformat(),
            "error": str(error),
        },
    )


def try_log_sync(client: SupabaseClient | None, **payload: Any) -> str | None:
    if client is None:
        return None
    try:
        client.log_sync(**payload)
    except Exception as exc:  # noqa: BLE001 - logging should not undo queue processing.
        return str(exc)
    return None


def latest_action(logs: list[dict], action: str, target_table: str | None = None) -> dict | None:
    for log in logs:
        if log.get("action") != action:
            continue
        if target_table and log.get("target_table") != target_table:
            continue
        return log
    return None


def build_sync_status(client: SupabaseClient | None, now: datetime) -> dict:
    if client is None:
        return {
            "schema_version": "0.1.0",
            "generated_at": now.isoformat(),
            "date": now.date().isoformat(),
            "data_quality": {
                "status": "partial",
                "notes": ["Dry run snapshot. Supabase queue counts are unavailable without a client."],
            },
            "summary": {
                "pending_captures": None,
                "pending_workouts": None,
                "last_pull_at": None,
                "last_publish_at": None,
                "last_failure_at": None,
                "health": "unknown",
            },
            "recent_events": [],
        }

    capture_pending = client.rows("capture_queue?select=id&status=eq.pending&limit=1000")
    workout_pending = client.rows("workout_queue?select=id&status=eq.pending&limit=1000")
    logs = client.rows(
        "sync_logs?select=created_at,action,target_table,status,details"
        "&order=created_at.desc&limit=20"
    )
    last_pull = latest_action(logs, "pull_queue")
    last_publish = latest_action(logs, "publish_snapshot", "dashboard_snapshots")
    failures = [log for log in logs if log.get("status") == "failed"]
    last_failure = failures[0] if failures else None
    health = "attention" if last_failure else "pending" if capture_pending or workout_pending else "ok"
    recent_events = [
        {
            "created_at": log.get("created_at"),
            "action": log.get("action"),
            "target_table": log.get("target_table"),
            "status": log.get("status"),
            "details": {
                key: value
                for key, value in (log.get("details") or {}).items()
                if key in {"pending_count", "snapshot_key", "snapshot_date", "path", "session_count", "error"}
            },
        }
        for log in logs[:8]
    ]
    return {
        "schema_version": "0.1.0",
        "generated_at": now.isoformat(),
        "date": now.date().isoformat(),
        "data_quality": {
            "status": "partial",
            "notes": [
                "Sanitized sync status snapshot generated by the Mac worker.",
                "Service role keys and raw private payloads are not included.",
            ],
        },
        "summary": {
            "pending_captures": len(capture_pending),
            "pending_workouts": len(workout_pending),
            "last_pull_at": last_pull.get("created_at") if last_pull else None,
            "last_publish_at": last_publish.get("created_at") if last_publish else None,
            "last_failure_at": last_failure.get("created_at") if last_failure else None,
            "health": health,
        },
        "recent_events": recent_events,
    }


def publish_snapshot_record(
    client: SupabaseClient | None,
    *,
    key: str,
    payload: dict,
    path: str,
    dry_run: bool,
    log_warnings: list[dict],
) -> dict:
    record = {
        "snapshot_key": key,
        "snapshot_date": payload.get("date"),
        "schema_version": payload.get("schema_version") or "0.1.0",
        "payload": payload,
        "source": WORKER_NAME,
    }
    inserted = None
    if not dry_run and client:
        inserted = client.insert("dashboard_snapshots", record)
        warning = try_log_sync(
            client,
            action="publish_snapshot",
            status="success",
            target_table="dashboard_snapshots",
            target_id=inserted.get("id") if inserted else None,
            details={
                "snapshot_key": key,
                "snapshot_date": record["snapshot_date"],
                "path": path,
            },
        )
        if warning:
            log_warnings.append({"snapshot_key": key, "warning": warning})
    return {
        "snapshot_key": key,
        "path": path,
        "snapshot_id": inserted.get("id") if inserted else None,
    }


def publish_snapshots(client: SupabaseClient | None, dry_run: bool = False) -> list[dict]:
    published = []
    log_warnings = []
    for key, path in DASHBOARD_FILES.items():
        if not path.exists():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        published.append(
            publish_snapshot_record(
                client,
                key=key,
                payload=payload,
                path=str(path.relative_to(PROJECT_ROOT)),
                dry_run=dry_run,
                log_warnings=log_warnings,
            )
        )
    workout_history = {
        "schema_version": "0.1.0",
        "generated_at": datetime.now(TIMEZONE).isoformat(),
        "date": datetime.now(TIMEZONE).date().isoformat(),
        "sessions": read_workout_sessions(),
    }
    published.append(
        publish_snapshot_record(
            client,
            key="workout-history",
            payload=workout_history,
            path="data/health/workout-sessions.jsonl",
            dry_run=dry_run,
            log_warnings=log_warnings,
        )
    )
    now = datetime.now(TIMEZONE)
    sync_status = build_sync_status(client, now)
    sync_status_path = PROJECT_ROOT / "dashboard/sync-status.json"
    sync_status_path.write_text(json.dumps(sync_status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    published.append(
        publish_snapshot_record(
            client,
            key="sync-status",
            payload=sync_status,
            path="dashboard/sync-status.json",
            dry_run=dry_run,
            log_warnings=log_warnings,
        )
    )
    if log_warnings:
        published.append({"snapshot_key": "_sync_log_warnings", "warnings": log_warnings})
    return published


def main() -> None:
    args = parse_args()
    if not args.process and not args.publish_snapshots and not args.dry_run:
        args.process = True

    should_process = args.process or (args.dry_run and not args.publish_snapshots)
    publish_only_dry_run = args.dry_run and args.publish_snapshots and not should_process
    client = None if publish_only_dry_run else SupabaseClient()
    result: dict[str, Any] = {"processed": [], "failed": [], "snapshots": []}

    if should_process:
        if client is None:
            client = SupabaseClient()
        for table, handler in [("capture_queue", process_capture), ("workout_queue", process_workout)]:
            rows = client.pending_rows(table, args.limit)
            if not args.dry_run:
                warning = try_log_sync(
                    client,
                    action="pull_queue",
                    status="success",
                    target_table=table,
                    details={"pending_count": len(rows), "limit": args.limit},
                )
                if warning:
                    result["failed"].append({"table": "sync_logs", "id": None, "error": warning})
            for row in rows:
                try:
                    output = handler(row, client, args.dry_run)
                    result["processed"].append({"table": table, "id": row["id"], "output": output})
                    if not args.dry_run:
                        warning = try_log_sync(
                            client,
                            action="process_queue_item",
                            status="success",
                            target_table=table,
                            target_id=row["id"],
                            details=output,
                        )
                        if warning:
                            result["failed"].append({"table": "sync_logs", "id": row["id"], "error": warning})
                except Exception as exc:  # noqa: BLE001 - worker should mark rows failed and continue.
                    mark_failed(client, table, row["id"], exc, args.dry_run)
                    result["failed"].append({"table": table, "id": row.get("id"), "error": str(exc)})
                    if not args.dry_run:
                        warning = try_log_sync(
                            client,
                            action="process_queue_item",
                            status="failed",
                            target_table=table,
                            target_id=row.get("id"),
                            details={"error": str(exc)},
                        )
                        if warning:
                            result["failed"].append({"table": "sync_logs", "id": row.get("id"), "error": warning})

    if args.publish_snapshots:
        result["snapshots"] = publish_snapshots(client, args.dry_run)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

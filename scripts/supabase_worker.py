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
from activity_store import delete_activity_session, read_activity_sessions, save_activity_session, update_activity_session  # noqa: E402
from capture_store import delete_capture, read_all_captures  # noqa: E402
from exercise_library import add_custom_exercise, delete_exercise, merged_exercises, reorder_exercises, set_archived, update_exercise  # noqa: E402
from refresh_outputs import refresh_outputs  # noqa: E402
from workout_store import delete_workout_session, read_workout_sessions, save_workout_session, summarize_strength_entries, update_workout_session  # noqa: E402
from import_finance_exports import ICLOUD_FINANCE_DIR, LOCAL_INBOX_DIR as FINANCE_LOCAL_INBOX_DIR  # noqa: E402
from import_finance_exports import append_action_log as log_finance_import  # noqa: E402
from import_finance_exports import import_exports as import_finance_exports  # noqa: E402
from import_finance_exports import normalize_exports as normalize_finance_exports  # noqa: E402
from import_finance_exports import write_finance_review_snapshot  # noqa: E402


TIMEZONE = ZoneInfo("Asia/Seoul")
WORKER_NAME = "mac_hermes_worker"
DASHBOARD_FILES = {
    "today": PROJECT_ROOT / "dashboard/today.json",
    "health": PROJECT_ROOT / "dashboard/health.json",
    "english": PROJECT_ROOT / "dashboard/english.json",
    "work": PROJECT_ROOT / "dashboard/work.json",
    "life-balance": PROJECT_ROOT / "dashboard/life-balance.json",
    "activity-allocation": PROJECT_ROOT / "dashboard/activity-allocation.json",
    "notifications": PROJECT_ROOT / "dashboard/notifications.json",
    "finance-review": PROJECT_ROOT / "dashboard/finance-review.json",
}
WORK_PROJECTS_PATH = PROJECT_ROOT / "data/work/projects.json"
WORK_PROGRESS_PATH = PROJECT_ROOT / "data/work/project-progress.json"
WORK_ACTIVITY_PATH = PROJECT_ROOT / "data/work/codex-activity.jsonl"


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


def optional_env(name: str) -> str | None:
    value = os.environ.get(name)
    return value.rstrip("/") if value else None


class SupabaseClient:
    def __init__(self) -> None:
        self.url = env("SUPABASE_URL")
        self.key = env("SUPABASE_SERVICE_ROLE_KEY")
        self.owner_user_id = optional_env("NOMAD_SUPABASE_OWNER_USER_ID")

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
        try:
            rows = self.request("POST", table, payload)
        except RuntimeError as exc:
            message = str(exc)
            if "PGRST204" not in message or "user_id" not in message or "schema cache" not in message:
                raise
            legacy_payload = {key: value for key, value in payload.items() if key != "user_id"}
            rows = self.request("POST", table, legacy_payload)
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
                "user_id": self.owner_user_id,
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
    if payload.get("kind") == "input_history_delete":
        history_kind = str(payload.get("history_kind") or "").strip()
        history_id = str(payload.get("history_id") or payload.get("id") or "").strip()
        if not history_id:
            raise ValueError("input_history_delete history_id is required.")
        if dry_run:
            return {"deleted": history_kind or "unknown", "history_id": history_id}
        client.patch("capture_queue", row["id"], {"status": "processing", "updated_at": datetime.now(TIMEZONE).isoformat()})
        if history_kind == "activity" or history_id.startswith("activity_"):
            deleted = delete_activity_session(history_id)
        elif history_kind == "workout" or history_id.startswith("workout_session_"):
            deleted = delete_workout_session(history_id)
        elif history_kind == "capture" or history_id.startswith("capture_"):
            deleted = delete_capture(history_id)
        else:
            raise ValueError(f"Unsupported input history delete target: {history_kind or history_id}")
        refresh_outputs(deleted.get("date"))
        client.patch(
            "capture_queue",
            row["id"],
            {
                "status": "processed",
                "processed_at": datetime.now(TIMEZONE).isoformat(),
                "updated_at": datetime.now(TIMEZONE).isoformat(),
                "local_capture_id": history_id,
                "error": None,
            },
        )
        return {"deleted": history_kind, "history_id": history_id, "date": deleted.get("date")}

    if payload.get("kind") == "finance_sync_request":
        if dry_run:
            return {"finance_sync": "requested"}
        client.patch("capture_queue", row["id"], {"status": "processing", "updated_at": datetime.now(TIMEZONE).isoformat()})
        result = sync_finance_exports()
        client.patch(
            "capture_queue",
            row["id"],
            {
                "status": "processed",
                "processed_at": datetime.now(TIMEZONE).isoformat(),
                "updated_at": datetime.now(TIMEZONE).isoformat(),
                "local_capture_id": "finance_sync",
                "error": None,
            },
        )
        return result

    if payload.get("kind") == "exercise_library_mutation":
        action = str(payload.get("action") or "").strip()
        if dry_run:
            return {"exercise_library_action": action, "summary": action or "mutation"}
        client.patch("capture_queue", row["id"], {"status": "processing", "updated_at": datetime.now(TIMEZONE).isoformat()})
        if action == "add":
            result = {"exercise": add_custom_exercise(payload.get("exercise") or {})}
        elif action == "update":
            result = {"exercise": update_exercise(str(payload.get("exercise_id") or ""), payload.get("updates") or {})}
        elif action == "archive":
            result = {"preference": set_archived(str(payload.get("exercise_id") or ""), bool(payload.get("archived")))}
        elif action == "delete":
            result = delete_exercise(str(payload.get("exercise_id") or ""))
        elif action == "reorder":
            result = reorder_exercises(payload.get("ordered_ids") or [])
        else:
            raise ValueError(f"Unsupported exercise library mutation: {action}")
        client.patch(
            "capture_queue",
            row["id"],
            {
                "status": "processed",
                "processed_at": datetime.now(TIMEZONE).isoformat(),
                "updated_at": datetime.now(TIMEZONE).isoformat(),
                "local_capture_id": result.get("exercise", {}).get("id") or result.get("exercise_id"),
                "error": None,
            },
        )
        return {"exercise_library_action": action, **result}

    if payload.get("kind") == "activity_session":
        if dry_run:
            return {
                "activity_id": None,
                "date": None,
                "summary": f"{payload.get('area') or 'activity'} · {payload.get('detail') or payload.get('memo') or ''}"[:80],
            }
        client.patch("capture_queue", row["id"], {"status": "processing", "updated_at": datetime.now(TIMEZONE).isoformat()})
        payload["source"] = "nomad_quick"
        payload["source_id"] = row["id"]
        if payload.get("edit_mode") == "update_requested" and payload.get("edit_source_id"):
            activity = update_activity_session(str(payload["edit_source_id"]), payload)
        else:
            activity = save_activity_session(payload)
        refresh_outputs(activity["date"])
        client.patch(
            "capture_queue",
            row["id"],
            {
                "status": "processed",
                "processed_at": datetime.now(TIMEZONE).isoformat(),
                "updated_at": datetime.now(TIMEZONE).isoformat(),
                "local_capture_id": activity["id"],
                "error": None,
            },
        )
        return {"activity_id": activity["id"], "date": activity["date"]}

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
    if payload.get("edit_mode") == "update_requested" and payload.get("edit_source_id"):
        session = update_workout_session(str(payload["edit_source_id"]), payload)
    else:
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


def sync_finance_exports() -> dict:
    now = datetime.now(TIMEZONE)
    import_result = import_finance_exports(ICLOUD_FINANCE_DIR, FINANCE_LOCAL_INBOX_DIR)
    normalized = normalize_finance_exports(FINANCE_LOCAL_INBOX_DIR, latest_only=True, now=now)
    finance_review = write_finance_review_snapshot(normalized, now=now)
    refresh_outputs(now.date().isoformat(), now=now)
    log_finance_import(import_result, normalized)
    return {
        "finance_sync": "completed",
        "selected_file": finance_review.get("source", {}).get("selected_file"),
        "expense_count": normalized.get("summary", {}).get("expense_count", 0),
        "latest_trade_date": finance_review.get("analysis", {}).get("latest_trade_date"),
    }


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
        "user_id": client.owner_user_id if client else optional_env("NOMAD_SUPABASE_OWNER_USER_ID"),
        "snapshot_key": key,
        "snapshot_date": payload.get("date"),
        "schema_version": payload.get("schema_version") or "0.1.0",
        "payload": payload,
        "source": WORKER_NAME,
    }
    inserted = None
    if not dry_run and client:
        if not client.owner_user_id:
            raise RuntimeError("NOMAD_SUPABASE_OWNER_USER_ID is required when publishing authenticated dashboard snapshots.")
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


def read_json_file(path: Path, fallback: dict) -> dict:
    if not path.exists():
        return fallback
    return json.loads(path.read_text(encoding="utf-8"))


def read_recent_work_events(limit: int = 30) -> list[dict]:
    if not WORK_ACTIVITY_PATH.exists():
        return []
    events = []
    lines = [line for line in WORK_ACTIVITY_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    for line in lines[-limit:]:
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def build_work_projects_snapshot() -> dict:
    payload = read_json_file(WORK_PROJECTS_PATH, {"schema_version": "0.1.0", "projects": []})
    progress = read_json_file(WORK_PROGRESS_PATH, {"projects": []})
    events = read_recent_work_events()
    projects = []
    for project in payload.get("projects") or []:
        project_events = [event for event in events if event.get("project_id") == project.get("project_id")]
        decisions = [item for event in project_events for item in (event.get("decisions") or [])]
        blockers = [item for event in project_events for item in (event.get("blockers") or [])]
        next_actions = [item for event in project_events for item in (event.get("next_actions") or [])]
        latest_event = project_events[-1] if project_events else {}
        tracking = {
            "signal": "blocked" if blockers else "active" if project_events else "idle",
            "event_count": len(project_events),
            "latest_event_at": latest_event.get("captured_at"),
            "changed_file_count": sum(len(event.get("changed_files") or []) for event in project_events[-5:]),
            "decision_count": len(decisions),
            "blocker_count": len(blockers),
            "next_action_count": len(next_actions),
            "recent_decisions": decisions[:5],
            "recent_blockers": blockers[:5],
            "recent_next_actions": next_actions[:5],
            "recent_events": list(reversed(project_events[-5:])),
            "git": {"available": False},
            "outputs": [],
        }
        latest_change = latest_event.get("evidence_summary") or latest_event.get("goal") or project.get("current_focus")
        enriched = {
            **project,
            "folder_status": "available" if Path(str(project.get("path") or "")).expanduser().exists() else "missing",
            "tracking": tracking,
            "experience": {
                "stage": "Direction" if project_events else "Idea",
                "signal": "Blocked" if blockers else "Moving" if project_events else "Quiet",
                "output_state": "Concept" if project_events else "None",
                "direction": "Clear" if project.get("next_action") or next_actions else "Forming",
                "review_need": "Decision needed" if blockers else "Low",
                "next_open": project.get("next_action") or (next_actions[0] if next_actions else "다음 행동이 아직 정리되지 않았습니다."),
                "latest_change": latest_change or "아직 의미 있는 변화가 없습니다.",
                "pulse": {
                    "direction": 1.0 if project.get("next_action") or next_actions else 0.6,
                    "output": 0.35 if project_events else 0.1,
                    "review": 0.9 if blockers else 0.15,
                    "next": 1.0 if project.get("next_action") or next_actions else 0.15,
                },
            },
        }
        projects.append(enriched)
    active = [project for project in projects if project.get("status") not in {"paused", "shipped"}]
    blocked = [project for project in projects if project.get("tracking", {}).get("blocker_count")]
    return {
        "schema_version": "0.1.0",
        "generated_at": datetime.now(TIMEZONE).isoformat(),
        "date": datetime.now(TIMEZONE).date().isoformat(),
        "summary": {
            "project_count": len(projects),
            "active_count": len(active),
            "event_count": len(events),
            "blocked_count": len(blocked),
            "status_map": {
                "Moving": [project.get("project_id") for project in projects if project.get("tracking", {}).get("signal") == "active"],
                "Blocked": [project.get("project_id") for project in projects if project.get("tracking", {}).get("signal") == "blocked"],
                "Quiet": [project.get("project_id") for project in projects if project.get("tracking", {}).get("signal") == "idle"],
            },
        },
        "projects": projects,
        "progress": progress,
        "recent_events": events,
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
    exercise_library = {
        "schema_version": "0.1.0",
        "generated_at": datetime.now(TIMEZONE).isoformat(),
        "date": datetime.now(TIMEZONE).date().isoformat(),
        "exercises": merged_exercises(),
    }
    published.append(
        publish_snapshot_record(
            client,
            key="exercise-library",
            payload=exercise_library,
            path="data/health/exercise-library.json",
            dry_run=dry_run,
            log_warnings=log_warnings,
        )
    )
    input_history = {
        "schema_version": "0.1.0",
        "generated_at": datetime.now(TIMEZONE).isoformat(),
        "date": datetime.now(TIMEZONE).date().isoformat(),
        "captures": read_all_captures(include_ignored=True),
        "activity_sessions": read_activity_sessions(include_ignored=True),
    }
    published.append(
        publish_snapshot_record(
            client,
            key="input-history",
            payload=input_history,
            path="data/captures/*.jsonl + data/activity/activity-sessions.jsonl",
            dry_run=dry_run,
            log_warnings=log_warnings,
        )
    )
    work_projects = build_work_projects_snapshot()
    published.append(
        publish_snapshot_record(
            client,
            key="work-projects",
            payload=work_projects,
            path="data/work/projects.json + data/work/codex-activity.jsonl",
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
        if not args.dry_run:
            try:
                result["processed"].append({"table": "local_files", "id": "finance_import", "output": sync_finance_exports()})
            except Exception as exc:  # noqa: BLE001 - dashboard publishing can continue without Finance.
                result["failed"].append({"table": "local_files", "id": "finance_import", "error": str(exc)})
                if client is not None:
                    warning = try_log_sync(
                        client,
                        action="import_finance_exports",
                        status="failed",
                        target_table="local_files",
                        target_id="finance_import",
                        details={"error": str(exc)},
                    )
                    if warning:
                        result["failed"].append({"table": "sync_logs", "id": "finance_import", "error": warning})
        result["snapshots"] = publish_snapshots(client, args.dry_run)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

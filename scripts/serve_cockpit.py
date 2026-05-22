#!/usr/bin/env python3
"""Serve the local Nomad Dashboard files."""

from __future__ import annotations

import json
import os
import socket
import sys
import argparse
import subprocess
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from process_inbox import process_inbox  # noqa: E402
from quick_capture import save_capture  # noqa: E402
from capture_store import delete_capture, read_captures, read_captures_for_month, update_capture, update_capture_status  # noqa: E402
from activity_store import delete_activity_session, read_activity_sessions, save_activity_session, update_activity_session  # noqa: E402
from refresh_outputs import refresh_outputs  # noqa: E402
from read_calendar_context import build_context as build_calendar_context  # noqa: E402
from read_calendar_context import log_action as log_calendar_action  # noqa: E402
from read_calendar_context import write_json as write_calendar_json  # noqa: E402
from read_notes_context import build_context as build_notes_context  # noqa: E402
from read_notes_context import log_action as log_notes_action  # noqa: E402
from read_notes_context import write_json as write_notes_json  # noqa: E402
from workout_store import delete_workout_session, read_workout_sessions, save_workout_session, summarize_strength_entries, update_workout_session  # noqa: E402
from exercise_library import active_exercises, add_custom_exercise, delete_exercise, mark_used, merged_exercises, reorder_exercises, set_archived, set_favorite, update_exercise  # noqa: E402
from import_exercise_library import apply_preview, read_preview, write_preview  # noqa: E402
from import_english_gpts_reviews import import_reviews as import_english_reviews  # noqa: E402
from import_english_gpts_reviews import append_action_log as log_english_review_import  # noqa: E402
from import_english_gpts_reviews import ICLOUD_ENGLISH_DIR, LOCAL_INBOX_DIR  # noqa: E402
from import_finance_exports import ICLOUD_FINANCE_DIR, LOCAL_INBOX_DIR as FINANCE_LOCAL_INBOX_DIR  # noqa: E402
from import_finance_exports import append_action_log as log_finance_import  # noqa: E402
from import_finance_exports import import_exports as import_finance_exports  # noqa: E402
from import_finance_exports import normalize_exports as normalize_finance_exports  # noqa: E402
from import_finance_exports import write_finance_review_snapshot  # noqa: E402
from package_stay_data import CURRENT_STAY_PATH, STAYS_INDEX_PATH, package_current_stay, update_current_stay  # noqa: E402
from time_utils import local_timezone  # noqa: E402


WORK_PROJECTS_PATH = PROJECT_ROOT / "data/work/projects.json"
WORK_PROGRESS_PATH = PROJECT_ROOT / "data/work/project-progress.json"
WORK_ACTIVITY_PATH = PROJECT_ROOT / "data/work/codex-activity.jsonl"
ENGLISH_DASHBOARD_PATH = PROJECT_ROOT / "dashboard/english.json"
VALIDATION_MODE = os.environ.get("NOMAD_VALIDATION_MODE") == "1"
VALIDATION_ROOT = Path(os.environ.get("NOMAD_VALIDATION_ROOT", PROJECT_ROOT / "data/_validation_sandbox")).expanduser()


def validation_path(*parts: str) -> Path:
    return VALIDATION_ROOT.joinpath(*parts)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return records


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")


def write_validation_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class CockpitHandler(SimpleHTTPRequestHandler):
    def validation_record(self, kind: str, payload: dict[str, Any]) -> dict[str, Any]:
        from datetime import datetime  # noqa: PLC0415

        now = datetime.now(local_timezone())
        record = {
            "id": f"validation_{kind}_{int(now.timestamp() * 1000)}",
            "schema_version": "0.1.0",
            "created_at": now.isoformat(timespec="seconds"),
            "date": payload.get("date") or now.date().isoformat(),
            "status": payload.get("status") or "saved",
            "validation_sandbox": True,
            **payload,
        }
        return record

    def validation_refresh_stub(self, date: str | None = None) -> dict[str, Any]:
        return {
            "validation_sandbox": True,
            "date": date,
            "dashboard": {"paths": ["dashboard/today.json", "dashboard/activity-allocation.json"]},
            "expenses": {"candidate_count": 0},
            "notifications": {"candidate_count": 0},
        }

    def handle_validation_capture(self) -> None:
        length = int(self.headers.get("content-length", "0"))
        payload = json.loads(self.rfile.read(length).decode("utf-8"))
        text = str(payload.get("text") or payload.get("raw_content") or "").strip()
        if not text:
            raise ValueError("text is required.")
        capture = self.validation_record(
            "capture",
            {
                "type": payload.get("type") or "text",
                "raw_content": text,
                "linked_agents": payload.get("linked_agents") or ["nomad-quick-capture"],
                "confidence": 0.8,
            },
        )
        append_jsonl(validation_path("data", "captures", f"{capture['date']}.jsonl"), capture)
        self.send_json(HTTPStatus.CREATED, {"capture": capture, "refresh": self.validation_refresh_stub(capture["date"])})

    def handle_validation_activity_session(self) -> None:
        length = int(self.headers.get("content-length", "0"))
        payload = json.loads(self.rfile.read(length).decode("utf-8"))
        area = str(payload.get("area") or "work")
        activity = self.validation_record(
            "activity",
            {
                "kind": "activity_session",
                "area": area,
                "duration_minutes": int(payload.get("duration_minutes") or 60),
                "place": payload.get("place") or "validation_sandbox",
                "subcategory": payload.get("subcategory") or area,
                "detail": payload.get("detail") or "Validation dummy activity",
                "review_required": bool(payload.get("review_required")),
                "review_reason": payload.get("review_reason"),
                "metadata": {"validation_sandbox": True, **(payload.get("metadata") or {})},
            },
        )
        append_jsonl(validation_path("data", "activity", "activity-sessions.jsonl"), activity)
        self.send_json(HTTPStatus.CREATED, {"activity": activity, "refresh": self.validation_refresh_stub(activity["date"])})

    def handle_validation_workout_session(self) -> None:
        length = int(self.headers.get("content-length", "0"))
        payload = json.loads(self.rfile.read(length).decode("utf-8"))
        session = self.validation_record(
            "workout",
            {
                "kind": "workout_session",
                "activity_type": payload.get("activity_type") or "strength",
                "duration_minutes": int(payload.get("duration_minutes") or 45),
                "entries": payload.get("entries") or [],
                "note": payload.get("note") or "",
                "metadata": {"validation_sandbox": True, **(payload.get("metadata") or {})},
            },
        )
        append_jsonl(validation_path("data", "health", "workout-sessions.jsonl"), session)
        capture = self.validation_record("capture", {"type": "checkin", "raw_content": "Validation workout detail", "linked_agents": ["nomad-health"]})
        append_jsonl(validation_path("data", "captures", f"{session['date']}.jsonl"), capture)
        self.send_json(HTTPStatus.CREATED, {"session": session, "capture": capture, "refresh": self.validation_refresh_stub(session["date"])})

    def handle_validation_update(self, history_kind: str) -> None:
        length = int(self.headers.get("content-length", "0"))
        payload = json.loads(self.rfile.read(length).decode("utf-8"))
        self.send_json(
            HTTPStatus.OK,
            {
                history_kind: self.validation_record(history_kind, payload.get("updates") or payload),
                "refresh": self.validation_refresh_stub(),
            },
        )

    def handle_validation_delete(self, history_kind: str) -> None:
        length = int(self.headers.get("content-length", "0"))
        payload = json.loads(self.rfile.read(length).decode("utf-8"))
        self.send_json(HTTPStatus.OK, {"deleted": {"id": payload.get(f"{history_kind}_id") or payload.get("id"), "validation_sandbox": True}})

    def do_POST(self) -> None:
        if VALIDATION_MODE:
            try:
                if self.path == "/api/capture":
                    self.handle_validation_capture()
                    return
                if self.path == "/api/activity-session":
                    self.handle_validation_activity_session()
                    return
                if self.path == "/api/workout-session":
                    self.handle_validation_workout_session()
                    return
                if self.path in {"/api/activity-session/update", "/api/workout-session/update", "/api/captures/update"}:
                    self.handle_validation_update("activity")
                    return
                if self.path in {"/api/activity-session/delete", "/api/workout-session/delete", "/api/captures/delete"}:
                    self.handle_validation_delete("activity")
                    return
                if self.path in {"/api/sync-inbox", "/api/sync-local-apps", "/api/sync-english-reviews", "/api/sync-finance-exports", "/api/work-import", "/api/stay-package"}:
                    self.send_json(HTTPStatus.OK, {"validation_sandbox": True, "status": "skipped_external_or_local_write"})
                    return
                if self.path in {"/api/exercises/custom", "/api/exercises/update", "/api/exercises/archive", "/api/exercises/delete", "/api/exercises/reorder", "/api/exercises/favorite"}:
                    self.send_json(HTTPStatus.OK, {"validation_sandbox": True, "status": "ok"})
                    return
                if self.path == "/api/work-projects":
                    self.send_json(HTTPStatus.OK, {"validation_sandbox": True, "status": "ok"})
                    return
                if self.path == "/api/current-stay":
                    self.send_json(HTTPStatus.OK, {"validation_sandbox": True, "stay": json.loads(validation_path("data", "travel", "current-stay.json").read_text(encoding="utf-8"))})
                    return
            except Exception as exc:  # noqa: BLE001 - validation errors should be visible to the runner.
                self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc), "validation_sandbox": True})
                return

        if self.path == "/api/capture":
            self.handle_capture()
            return

        if self.path == "/api/sync-inbox":
            self.handle_sync_inbox()
            return

        if self.path == "/api/captures/ignore":
            self.handle_ignore_capture()
            return

        if self.path == "/api/captures/update":
            self.handle_update_capture()
            return

        if self.path == "/api/captures/delete":
            self.handle_delete_capture()
            return

        if self.path == "/api/sync-local-apps":
            self.handle_sync_local_apps()
            return

        if self.path == "/api/sync-english-reviews":
            self.handle_sync_english_reviews()
            return

        if self.path == "/api/sync-finance-exports":
            self.handle_sync_finance_exports()
            return

        if self.path == "/api/workout-session":
            self.handle_workout_session()
            return

        if self.path == "/api/workout-session/update":
            self.handle_workout_session_update()
            return
        if self.path == "/api/workout-session/delete":
            self.handle_workout_session_delete()
            return

        if self.path == "/api/activity-session":
            self.handle_activity_session()
            return

        if self.path == "/api/activity-session/update":
            self.handle_activity_session_update()
            return

        if self.path == "/api/activity-session/delete":
            self.handle_activity_session_delete()
            return

        if self.path == "/api/exercises/favorite":
            self.handle_exercise_favorite()
            return

        if self.path == "/api/exercises/custom":
            self.handle_exercise_custom()
            return

        if self.path == "/api/exercises/update":
            self.handle_exercise_update()
            return

        if self.path == "/api/exercises/archive":
            self.handle_exercise_archive()
            return

        if self.path == "/api/exercises/delete":
            self.handle_exercise_delete()
            return

        if self.path == "/api/exercises/reorder":
            self.handle_exercise_reorder()
            return

        if self.path == "/api/exercises/import-preview":
            self.handle_exercise_import_preview()
            return

        if self.path == "/api/exercises/import-apply":
            self.handle_exercise_import_apply()
            return

        if self.path == "/api/work-projects":
            self.handle_work_project_create()
            return

        if self.path == "/api/work-import":
            self.handle_work_import()
            return

        if self.path == "/api/choose-folder":
            self.handle_choose_folder()
            return

        if self.path == "/api/stay-package":
            self.handle_stay_package()
            return

        if self.path == "/api/current-stay":
            self.handle_current_stay_update()
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Unknown endpoint")

    def handle_capture(self) -> None:
        try:
            length = int(self.headers.get("content-length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            text = str(payload.get("text") or "").strip()
            capture_type = str(payload.get("type") or "text")
            media_url = payload.get("media_url")
            capture = save_capture(text, capture_type, media_url)
            refresh = refresh_outputs(capture["date"])
            self.send_json(
                HTTPStatus.CREATED,
                {
                    "capture": capture,
                    "refresh": refresh,
                },
            )
        except Exception as exc:  # noqa: BLE001 - return useful local API errors.
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})

    def handle_sync_inbox(self) -> None:
        try:
            result = process_inbox(regenerate_dashboard=True)
            from datetime import datetime  # noqa: PLC0415

            date = datetime.now(local_timezone()).date().isoformat()
            result["refresh"] = refresh_outputs(date)
            self.send_json(HTTPStatus.OK, result)
        except Exception as exc:  # noqa: BLE001 - return useful local API errors.
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})

    def handle_sync_english_reviews(self) -> None:
        try:
            from datetime import datetime  # noqa: PLC0415

            now = datetime.now(local_timezone())
            phases = [{"phase": "icloud_sync", "status": "running"}]
            result = import_english_reviews(ICLOUD_ENGLISH_DIR, LOCAL_INBOX_DIR)
            phases[0]["status"] = "done"
            phases.append({"phase": "analysis_refresh", "status": "running"})
            refresh = refresh_outputs(now.date().isoformat(), now=now)
            phases[1]["status"] = "done"
            result["refresh"] = refresh
            log_english_review_import(result, refresh=refresh)
            pending_reviews = None
            analyzed_reviews = None
            if ENGLISH_DASHBOARD_PATH.exists():
                payload = json.loads(ENGLISH_DASHBOARD_PATH.read_text(encoding="utf-8"))
                stats = payload.get("review_file_stats") or {}
                pending_reviews = int(stats.get("pending_files") or 0)
                analyzed_reviews = int(stats.get("analyzed_files") or 0)
            guidance = (
                "맥 에이전트가 실행되면 리뷰가 완료됩니다."
                if pending_reviews and pending_reviews > 0
                else ""
            )
            self.send_json(
                HTTPStatus.OK,
                {
                    **result,
                    "phases": phases,
                    "review_status": {
                        "pending_count": pending_reviews,
                        "analyzed_count": analyzed_reviews,
                        "guidance": guidance,
                    },
                },
            )
        except Exception as exc:  # noqa: BLE001 - return useful local API errors.
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})

    def handle_sync_finance_exports(self) -> None:
        try:
            from datetime import datetime  # noqa: PLC0415

            now = datetime.now(local_timezone())
            result = import_finance_exports(ICLOUD_FINANCE_DIR, FINANCE_LOCAL_INBOX_DIR)
            normalized = normalize_finance_exports(FINANCE_LOCAL_INBOX_DIR, latest_only=True, now=now)
            finance_review = write_finance_review_snapshot(normalized, now=now)
            refresh = refresh_outputs(now.date().isoformat(), now=now)
            log_finance_import(result, normalized)
            self.send_json(
                HTTPStatus.OK,
                {
                    "import": result,
                    "refresh": refresh,
                    "normalized": {
                        "output": "data/expenses/normalized-expenses.json",
                        "summary": normalized.get("summary", {}),
                        "data_quality": normalized.get("data_quality", {}),
                        "dashboard": {
                            "output": "dashboard/finance-review.json",
                            "analysis": finance_review.get("analysis", {}),
                        },
                    },
                },
            )
        except Exception as exc:  # noqa: BLE001 - return useful local API errors.
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})

    def handle_stay_package(self) -> None:
        try:
            result = package_current_stay()
            self.send_json(HTTPStatus.OK, result)
        except Exception as exc:  # noqa: BLE001 - return useful local API errors.
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})

    def handle_current_stay_update(self) -> None:
        try:
            length = int(self.headers.get("content-length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            stay = update_current_stay(payload)
            refresh = refresh_outputs()
            self.send_json(HTTPStatus.OK, {"stay": stay, "refresh": refresh})
        except Exception as exc:  # noqa: BLE001 - return useful local API errors.
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})

    def handle_workout_session(self) -> None:
        try:
            length = int(self.headers.get("content-length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            summary = summarize_strength_entries(payload.get("entries") or [])
            capture = save_capture(f"근력운동 기록: {summary}", "checkin")
            payload["source_capture_id"] = capture["id"]
            session = save_workout_session(payload)
            for entry in session.get("entries") or []:
                exercise_id = entry.get("exercise")
                if exercise_id:
                    mark_used(exercise_id)
            refresh = refresh_outputs(session["date"])
            self.send_json(
                HTTPStatus.CREATED,
                {
                    "session": session,
                    "capture": capture,
                    "refresh": refresh,
                },
            )
        except Exception as exc:  # noqa: BLE001 - return useful local API errors.
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})

    def handle_workout_session_update(self) -> None:
        try:
            length = int(self.headers.get("content-length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            session_id = str(payload.get("session_id") or "").strip()
            if not session_id:
                raise ValueError("session_id is required.")
            updates = payload.get("updates") or {}
            session = update_workout_session(session_id, updates)
            for entry in session.get("entries") or []:
                exercise_id = entry.get("exercise")
                if exercise_id:
                    mark_used(exercise_id)
            refresh = refresh_outputs(session["date"])
            self.send_json(HTTPStatus.OK, {"session": session, "refresh": refresh})
        except Exception as exc:  # noqa: BLE001 - return useful local API errors.
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})

    def handle_workout_session_delete(self) -> None:
        try:
            length = int(self.headers.get("content-length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            session_id = str(payload.get("session_id") or "").strip()
            if not session_id:
                raise ValueError("session_id is required.")
            session = delete_workout_session(session_id)
            refresh = refresh_outputs(session.get("date"))
            self.send_json(HTTPStatus.OK, {"deleted": session, "refresh": refresh})
        except Exception as exc:  # noqa: BLE001 - return useful local API errors.
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})

    def handle_activity_session(self) -> None:
        try:
            length = int(self.headers.get("content-length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            activity = save_activity_session(payload)
            refresh = refresh_outputs(activity["date"])
            self.send_json(
                HTTPStatus.CREATED,
                {
                    "activity": activity,
                    "refresh": refresh,
                },
            )
        except Exception as exc:  # noqa: BLE001 - return useful local API errors.
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})

    def handle_activity_session_update(self) -> None:
        try:
            length = int(self.headers.get("content-length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            activity_id = str(payload.get("activity_id") or "").strip()
            if not activity_id:
                raise ValueError("activity_id is required.")
            activity = update_activity_session(activity_id, payload.get("updates") or {})
            refresh = refresh_outputs(activity["date"])
            self.send_json(HTTPStatus.OK, {"activity": activity, "refresh": refresh})
        except Exception as exc:  # noqa: BLE001 - return useful local API errors.
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})

    def handle_activity_session_delete(self) -> None:
        try:
            length = int(self.headers.get("content-length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            activity_id = str(payload.get("activity_id") or "").strip()
            if not activity_id:
                raise ValueError("activity_id is required.")
            activity = delete_activity_session(activity_id)
            refresh = refresh_outputs(activity.get("date"))
            self.send_json(HTTPStatus.OK, {"deleted": activity, "refresh": refresh})
        except Exception as exc:  # noqa: BLE001 - return useful local API errors.
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if VALIDATION_MODE:
            if parsed.path == "/api/config":
                self.send_json(HTTPStatus.OK, {"mode": "local", "validation_sandbox": True})
                return
            if parsed.path == "/api/current-stay":
                self.handle_validation_current_stay()
                return
            if parsed.path == "/api/captures":
                self.handle_validation_captures(parsed.query)
                return
            if parsed.path == "/api/activity-history":
                self.handle_validation_activity_history(parsed.query)
                return
            if parsed.path == "/api/workout-history":
                self.handle_validation_workout_history()
                return
            if parsed.path == "/api/work-projects":
                self.handle_validation_work_projects()
                return
            if parsed.path == "/api/exercises":
                self.handle_validation_exercises()
                return
            if parsed.path == "/api/hermes-draft":
                self.send_json(HTTPStatus.OK, {"date": "", "exists": False, "content": "", "validation_sandbox": True})
                return
            if parsed.path == "/api/inbox-status":
                self.send_json(HTTPStatus.OK, {"pending": 0, "files": [], "validation_sandbox": True})
                return
            if parsed.path.startswith("/dashboard/") or parsed.path.startswith("/data/"):
                if self.serve_validation_file(parsed.path):
                    return

        if parsed.path == "/api/inbox-status":
            self.handle_inbox_status()
            return

        if parsed.path == "/api/config":
            self.handle_config()
            return

        if parsed.path == "/api/captures":
            self.handle_captures(parsed.query)
            return

        if parsed.path == "/api/activity-history":
            self.handle_activity_history(parsed.query)
            return

        if parsed.path == "/api/hermes-draft":
            self.handle_hermes_draft(parsed.query)
            return

        if parsed.path == "/api/exercises":
            self.handle_exercises(parsed.query)
            return

        if parsed.path == "/api/exercises/import-preview":
            self.handle_get_exercise_import_preview()
            return

        if parsed.path == "/api/workout-history":
            self.handle_workout_history()
            return

        if parsed.path == "/api/work-projects":
            self.handle_work_projects()
            return

        if parsed.path == "/api/current-stay":
            self.handle_current_stay()
            return

        super().do_GET()

    def serve_validation_file(self, request_path: str) -> bool:
        relative_path = request_path.lstrip("/")
        path = validation_path(relative_path)
        if not path.exists() or not path.is_file():
            return False
        content_type = "application/json; charset=utf-8" if path.suffix == ".json" else "text/plain; charset=utf-8"
        body = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("content-type", content_type)
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
        return True

    def handle_validation_current_stay(self) -> None:
        path = validation_path("data", "travel", "current-stay.json")
        if not path.exists():
            self.send_json(HTTPStatus.OK, {"exists": False, "index": {"stays": []}, "validation_sandbox": True})
            return
        stay = json.loads(path.read_text(encoding="utf-8"))
        index_path = validation_path("data", "travel", "stays-index.json")
        index = json.loads(index_path.read_text(encoding="utf-8")) if index_path.exists() else {"stays": []}
        self.send_json(HTTPStatus.OK, {"exists": True, "stay": stay, "index": index, "validation_sandbox": True})

    def handle_validation_captures(self, query: str) -> None:
        params = parse_qs(query)
        month = (params.get("month") or [""])[0]
        captures = []
        for path in sorted(validation_path("data", "captures").glob("*.jsonl")):
            captures.extend(read_jsonl(path))
        if month:
            captures = [item for item in captures if str(item.get("date") or "").startswith(month)]
        self.send_json(HTTPStatus.OK, {"captures": captures, "validation_sandbox": True})

    def handle_validation_activity_history(self, query: str) -> None:
        params = parse_qs(query)
        month = (params.get("month") or [""])[0]
        sessions = read_jsonl(validation_path("data", "activity", "activity-sessions.jsonl"))
        if month:
            sessions = [item for item in sessions if str(item.get("date") or "").startswith(month)]
        self.send_json(HTTPStatus.OK, {"sessions": sessions, "validation_sandbox": True})

    def handle_validation_workout_history(self) -> None:
        self.send_json(
            HTTPStatus.OK,
            {
                "sessions": read_jsonl(validation_path("data", "health", "workout-sessions.jsonl")),
                "validation_sandbox": True,
            },
        )

    def handle_validation_work_projects(self) -> None:
        projects_path = validation_path("data", "work", "projects.json")
        progress_path = validation_path("data", "work", "project-progress.json")
        payload = json.loads(projects_path.read_text(encoding="utf-8")) if projects_path.exists() else {"projects": []}
        payload["progress"] = json.loads(progress_path.read_text(encoding="utf-8")) if progress_path.exists() else {"projects": []}
        payload["recent_events"] = read_jsonl(validation_path("data", "work", "codex-activity.jsonl"))[-20:]
        payload["validation_sandbox"] = True
        self.send_json(HTTPStatus.OK, payload)

    def handle_validation_exercises(self) -> None:
        self.send_json(
            HTTPStatus.OK,
            {
                "exercises": [
                    {"id": "validation_push_up", "name_ko": "푸시업", "name_en": "Push-up", "primary_muscle": "chest", "equipment": "bodyweight"},
                    {"id": "validation_squat", "name_ko": "스쿼트", "name_en": "Squat", "primary_muscle": "legs", "equipment": "bodyweight"},
                ],
                "validation_sandbox": True,
            },
        )

    def handle_current_stay(self) -> None:
        try:
            if not CURRENT_STAY_PATH.exists():
                self.send_json(HTTPStatus.OK, {"exists": False, "index": {"stays": []}})
                return
            stay = json.loads(CURRENT_STAY_PATH.read_text(encoding="utf-8"))
            index = json.loads(STAYS_INDEX_PATH.read_text(encoding="utf-8")) if STAYS_INDEX_PATH.exists() else {"stays": []}
            self.send_json(HTTPStatus.OK, {"exists": True, "stay": stay, "index": index})
        except Exception as exc:  # noqa: BLE001 - return useful local API errors.
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})

    def read_work_projects_payload(self) -> dict:
        if not WORK_PROJECTS_PATH.exists():
            return {"schema_version": "0.1.0", "projects": []}
        return json.loads(WORK_PROJECTS_PATH.read_text(encoding="utf-8"))

    def write_work_projects_payload(self, payload: dict) -> None:
        WORK_PROJECTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        WORK_PROJECTS_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def read_json_file(self, path: Path, fallback: dict) -> dict:
        if not path.exists():
            return fallback
        return json.loads(path.read_text(encoding="utf-8"))

    def read_recent_activity_events(self, limit: int = 30) -> list[dict]:
        if not WORK_ACTIVITY_PATH.exists():
            return []
        lines = [line for line in WORK_ACTIVITY_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
        events = []
        for line in lines[-limit:]:
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return events

    def run_project_git(self, path: Path, args: list[str]) -> str:
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

    def git_tracking_summary(self, path: Path) -> dict:
        if not path.exists() or not (path / ".git").exists():
            return {"available": False}
        status = self.run_project_git(path, ["status", "--short"])
        branch = self.run_project_git(path, ["branch", "--show-current"])
        last_commit = self.run_project_git(path, ["log", "-1", "--format=%h%x09%cs%x09%s"])
        diff_stat = self.run_project_git(path, ["diff", "--stat"])
        staged = modified = untracked = deleted = renamed = 0
        changed_files: list[str] = []
        for line in status.splitlines():
            if not line:
                continue
            code = line[:2]
            if code == "??":
                untracked += 1
                file_path = line[3:].strip()
            else:
                if code[0] != " ":
                    staged += 1
                if code[1] == "M" or code[0] == "M":
                    modified += 1
                if "D" in code:
                    deleted += 1
                if "R" in code:
                    renamed += 1
                file_path = line[3:].strip() if len(line) > 3 and line[2] == " " else line[2:].strip()
            if " -> " in file_path:
                file_path = file_path.split(" -> ", 1)[1].strip()
            changed_files.append(file_path)
        commit_payload = {}
        if last_commit:
            parts = last_commit.split("\t", 2)
            commit_payload = {
                "hash": parts[0] if len(parts) > 0 else "",
                "date": parts[1] if len(parts) > 1 else "",
                "subject": parts[2] if len(parts) > 2 else "",
            }
        return {
            "available": True,
            "branch": branch or "unknown",
            "dirty": bool(status),
            "changed_file_count": len(changed_files),
            "staged_count": staged,
            "modified_count": modified,
            "untracked_count": untracked,
            "deleted_count": deleted,
            "renamed_count": renamed,
            "changed_files": changed_files[:20],
            "last_commit": commit_payload,
            "diff_stat": diff_stat,
        }

    def output_folder_summary(self, source: dict) -> dict:
        path_value = str(source.get("path") or "").strip()
        if not path_value:
            return {"available": False}
        path = Path(path_value).expanduser()
        if not path.exists():
            return {"available": False, "path": str(path), "file_count": 0}
        files = [item for item in path.rglob("*") if item.is_file()]
        latest = max((item.stat().st_mtime for item in files), default=None)
        from datetime import datetime  # noqa: PLC0415

        latest_at = datetime.fromtimestamp(latest, local_timezone()).isoformat(timespec="seconds") if latest else None
        recent_files = sorted(files, key=lambda item: item.stat().st_mtime, reverse=True)[:8]
        return {
            "available": True,
            "path": str(path),
            "file_count": len(files),
            "latest_modified_at": latest_at,
            "recent_files": [str(item.relative_to(path)) for item in recent_files],
        }

    def project_experience_summary(self, project: dict, tracking: dict) -> dict:
        git = tracking.get("git") or {}
        outputs = tracking.get("outputs") or []
        has_outputs = any(output.get("available") and output.get("file_count", 0) for output in outputs)
        has_events = bool(tracking.get("event_count"))
        has_changes = bool(tracking.get("changed_file_count"))
        has_decisions = bool(tracking.get("decision_count"))
        has_next = bool(tracking.get("next_action_count"))
        has_blockers = bool(tracking.get("blocker_count"))
        status = project.get("status")

        if status == "paused":
            stage = "Paused"
        elif has_outputs:
            stage = "Review"
        elif has_changes and has_events:
            stage = "Build"
        elif has_events or has_decisions:
            stage = "Direction"
        else:
            stage = "Idea"

        if has_blockers:
            signal = "Blocked"
        elif status == "paused":
            signal = "Quiet"
        elif git.get("dirty") or has_events:
            signal = "Moving"
        else:
            signal = "Quiet"

        if has_outputs:
            output_state = "Reviewable"
        elif has_changes:
            output_state = "In progress"
        elif has_events:
            output_state = "Concept"
        else:
            output_state = "None"

        if has_decisions and has_next:
            direction = "Clear"
        elif has_decisions or has_next:
            direction = "Forming"
        else:
            direction = "Foggy"

        if has_blockers:
            review_need = "Decision needed"
        elif has_outputs:
            review_need = "Review ready"
        elif has_changes and not tracking.get("recent_next_actions"):
            review_need = "Self review"
        else:
            review_need = "Low"

        next_open = (
            project.get("next_action")
            or (tracking.get("recent_next_actions") or ["다음 행동이 아직 정리되지 않았습니다."])[0]
        )
        latest_change = "아직 의미 있는 변화가 없습니다."
        latest_events = tracking.get("recent_events") or []
        if latest_events:
            latest_change = latest_events[0].get("evidence_summary") or latest_events[0].get("goal") or latest_change
        elif git.get("dirty"):
            latest_change = f"Local work in progress: {tracking.get('changed_file_count', 0)} file(s) changed"

        return {
            "stage": stage,
            "signal": signal,
            "output_state": output_state,
            "direction": direction,
            "review_need": review_need,
            "next_open": next_open,
            "latest_change": latest_change,
            "pulse": {
                "direction": 1.0 if direction == "Clear" else 0.6 if direction == "Forming" else 0.25,
                "output": 1.0 if output_state == "Reviewable" else 0.6 if output_state == "In progress" else 0.35 if output_state == "Concept" else 0.1,
                "review": 0.9 if review_need in {"Review ready", "Decision needed"} else 0.45 if review_need == "Self review" else 0.15,
                "next": 1.0 if project.get("next_action") or has_next else 0.15,
            },
        }

    def enrich_work_project(self, project: dict, events: list[dict]) -> dict:
        project_path = Path(str(project.get("path") or "")).expanduser()
        project_events = [event for event in events if event.get("project_id") == project.get("project_id")]
        evidence_sources = project.get("evidence_sources") or []
        git_source = next((source for source in evidence_sources if source.get("type") == "git" and source.get("enabled", True)), None)
        output_sources = [source for source in evidence_sources if source.get("type") == "output_folder" and source.get("enabled", True)]
        git_summary = self.git_tracking_summary(Path(git_source.get("path") or project_path).expanduser()) if git_source else {"available": False}
        output_summaries = [self.output_folder_summary(source) for source in output_sources]
        decisions = []
        blockers = []
        next_actions = []
        changed_from_events = 0
        for event in project_events:
            decisions.extend(event.get("decisions") or [])
            blockers.extend(event.get("blockers") or [])
            next_actions.extend(event.get("next_actions") or [])
            changed_from_events += len(event.get("changed_files") or [])
        latest_event = max((event.get("captured_at") or "" for event in project_events), default=None)
        changed_file_count = git_summary.get("changed_file_count", 0)
        signal = "idle"
        if blockers:
            signal = "blocked"
        elif changed_file_count or project_events:
            signal = "active"
        elif project.get("status") == "paused":
            signal = "paused"
        tracking = {
            "signal": signal,
            "event_count": len(project_events),
            "latest_event_at": latest_event,
            "changed_file_count": changed_file_count,
            "changed_file_evidence_count": changed_from_events,
            "decision_count": len(decisions),
            "blocker_count": len(blockers),
            "next_action_count": len(next_actions),
            "recent_decisions": decisions[:5],
            "recent_blockers": blockers[:5],
            "recent_next_actions": next_actions[:5],
            "recent_events": list(reversed(project_events[-5:])),
            "git": git_summary,
            "outputs": output_summaries,
        }
        enriched = {
            **project,
            "folder_status": "available" if project_path.exists() else "missing",
            "tracking": tracking,
        }
        enriched["experience"] = self.project_experience_summary(enriched, tracking)
        return enriched

    def work_dashboard_summary(self, projects: list[dict], events: list[dict]) -> dict:
        active = [project for project in projects if project.get("status") not in {"paused", "shipped"}]
        dirty = [project for project in projects if project.get("tracking", {}).get("git", {}).get("dirty")]
        blocked = [project for project in projects if project.get("tracking", {}).get("blocker_count")]
        missing = [project for project in projects if project.get("folder_status") == "missing"]
        experience_statuses = ["Moving", "Needs Decision", "Needs Review", "Quiet", "Blocked"]
        status_map = {key: [] for key in experience_statuses}
        for project in projects:
            experience = project.get("experience", {})
            if experience.get("signal") == "Blocked" or experience.get("review_need") == "Decision needed":
                bucket = "Blocked" if experience.get("signal") == "Blocked" else "Needs Decision"
            elif experience.get("review_need") == "Review ready":
                bucket = "Needs Review"
            elif experience.get("signal") == "Moving":
                bucket = "Moving"
            else:
                bucket = "Quiet"
            status_map[bucket].append(project.get("project_id"))
        return {
            "project_count": len(projects),
            "active_count": len(active),
            "event_count": len(events),
            "dirty_count": len(dirty),
            "blocked_count": len(blocked),
            "missing_path_count": len(missing),
            "total_changed_files": sum(project.get("tracking", {}).get("changed_file_count", 0) for project in projects),
            "status_counts": {
                status: sum(1 for project in projects if project.get("status") == status)
                for status in sorted({project.get("status", "unknown") for project in projects})
            },
            "status_map": status_map,
        }

    def handle_work_projects(self) -> None:
        try:
            payload = self.read_work_projects_payload()
            progress = self.read_json_file(WORK_PROGRESS_PATH, {"projects": []})
            events = self.read_recent_activity_events()
            projects = [self.enrich_work_project(project, events) for project in payload.get("projects") or []]
            self.send_json(
                HTTPStatus.OK,
                {
                    "summary": self.work_dashboard_summary(projects, events),
                    "projects": projects,
                    "progress": progress,
                    "recent_events": events,
                },
            )
        except Exception as exc:  # noqa: BLE001 - return useful local API errors.
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})

    def handle_work_project_create(self) -> None:
        try:
            length = int(self.headers.get("content-length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            project = self.normalize_work_project(payload)
            projects_payload = self.read_work_projects_payload()
            projects = projects_payload.setdefault("projects", [])
            project_index = next((index for index, item in enumerate(projects) if item.get("project_id") == project["project_id"]), None)
            if payload.get("mode") == "update":
                if project_index is None:
                    raise ValueError("project_id not found.")
                existing = projects[project_index]
                projects[project_index] = {
                    **existing,
                    **project,
                    "kpis": existing.get("kpis", project.get("kpis", [])),
                }
                project = projects[project_index]
            else:
                if project_index is not None:
                    raise ValueError("project_id already exists.")
                projects.append(project)
            from datetime import datetime  # noqa: PLC0415

            projects_payload["updated_at"] = datetime.now(local_timezone()).isoformat(timespec="seconds")
            self.write_work_projects_payload(projects_payload)
            self.send_json(HTTPStatus.CREATED, {"project": project, "projects": projects})
        except Exception as exc:  # noqa: BLE001 - return useful local API errors.
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})

    def string_list(self, value: Any) -> list[str]:
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        return [item.strip() for item in str(value or "").replace("\n", ",").split(",") if item.strip()]

    def normalize_work_project(self, payload: dict) -> dict:
        name = str(payload.get("name") or "").strip()
        path_value = str(payload.get("path") or "").strip()
        if not name:
            raise ValueError("Project name is required.")
        if not path_value:
            raise ValueError("Project folder path is required.")
        project_path = Path(path_value).expanduser()
        if not project_path.is_absolute():
            raise ValueError("Project folder path must be absolute.")
        project_id = str(payload.get("project_id") or self.slugify(name)).strip()
        if not project_id:
            raise ValueError("project_id is required.")
        source_types = set(payload.get("evidence_sources") or ["git", "codex"])
        evidence_sources = []
        if "git" in source_types:
            evidence_sources.append({"type": "git", "enabled": True, "path": str(project_path)})
        if "codex" in source_types:
            evidence_sources.append({"type": "codex", "enabled": True})
        output_path = str(payload.get("output_path") or "").strip()
        if output_path:
            evidence_sources.append({"type": "output_folder", "enabled": True, "path": str(Path(output_path).expanduser())})
        aliases = self.string_list(payload.get("aliases", []))
        return {
            "project_id": project_id,
            "name": name,
            "type": str(payload.get("type") or "ai-work").strip() or "ai-work",
            "status": str(payload.get("status") or "in_progress").strip() or "in_progress",
            "priority": str(payload.get("priority") or "P2").strip() or "P2",
            "active_weight": payload.get("active_weight", 1),
            "sensitivity": str(payload.get("sensitivity") or "personal-private").strip() or "personal-private",
            "publish_to_dashboard": bool(payload.get("publish_to_dashboard", True)),
            "evidence_mode": str(payload.get("evidence_mode") or "codex_and_git").strip() or "codex_and_git",
            "path": str(project_path),
            "current_focus": str(payload.get("current_focus") or "").strip(),
            "next_action": str(payload.get("next_action") or "").strip(),
            "success_criteria": self.string_list(payload.get("success_criteria", [])),
            "review_cadence": str(payload.get("review_cadence") or "daily").strip() or "daily",
            "stale_after_days": int(payload.get("stale_after_days") or 2),
            "exclude_paths": self.string_list(payload.get("exclude_paths", [])),
            "kpis": [],
            "evidence_sources": evidence_sources,
            "aliases": aliases or [name, project_id],
            "folder_status": "available" if project_path.exists() else "missing",
        }

    def slugify(self, value: str) -> str:
        normalized = "".join(char.lower() if char.isalnum() else "-" for char in value.strip())
        return "-".join(part for part in normalized.split("-") if part)

    def handle_work_import(self) -> None:
        try:
            length = int(self.headers.get("content-length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            command = [sys.executable, str(PROJECT_ROOT / "scripts/import_codex_activity.py")]
            if payload.get("dry_run", True):
                command.append("--dry-run")
            if payload.get("include_clean"):
                command.append("--include-clean")
            project_id = str(payload.get("project_id") or "").strip()
            if project_id:
                command.extend(["--project-id", project_id])
            completed = subprocess.run(  # noqa: S603 - command targets this repository script.
                command,
                cwd=PROJECT_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            result = json.loads(completed.stdout) if completed.stdout.strip() else {}
            status = HTTPStatus.OK if completed.returncode == 0 else HTTPStatus.BAD_REQUEST
            self.send_json(status, {**result, "stderr": completed.stderr.strip() or None})
        except Exception as exc:  # noqa: BLE001 - return useful local API errors.
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})

    def handle_choose_folder(self) -> None:
        try:
            script = (
                'POSIX path of (choose folder with prompt '
                '"Select a project folder for Nomad Life AI Work")'
            )
            completed = subprocess.run(  # noqa: S603 - fixed macOS folder picker command.
                ["osascript", "-e", script],
                cwd=PROJECT_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            if completed.returncode != 0:
                error = completed.stderr.strip() or completed.stdout.strip() or "Folder selection cancelled."
                if "User canceled" in error or "(-128)" in error:
                    self.send_json(HTTPStatus.OK, {"cancelled": True, "path": None})
                    return
                raise ValueError(error)
            selected_path = completed.stdout.strip()
            self.send_json(HTTPStatus.OK, {"cancelled": False, "path": selected_path})
        except Exception as exc:  # noqa: BLE001 - return useful local API errors.
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})

    def handle_exercises(self, query: str = "") -> None:
        try:
            params = parse_qs(query)
            include_archived = params.get("include_archived", ["0"])[0] in {"1", "true", "yes"}
            exercises = merged_exercises() if include_archived else active_exercises()
            self.send_json(HTTPStatus.OK, {"exercises": exercises})
        except Exception as exc:  # noqa: BLE001 - return useful local API errors.
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})

    def handle_config(self) -> None:
        self.send_json(
            HTTPStatus.OK,
            {
                "mode": os.environ.get("NOMAD_DASHBOARD_MODE", "local"),
                "supabaseUrl": os.environ.get("VITE_SUPABASE_URL", ""),
                "supabaseAnonKey": os.environ.get("VITE_SUPABASE_ANON_KEY", ""),
            },
        )

    def handle_workout_history(self) -> None:
        try:
            self.send_json(HTTPStatus.OK, {"sessions": read_workout_sessions()})
        except Exception as exc:  # noqa: BLE001 - return useful local API errors.
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})

    def handle_exercise_favorite(self) -> None:
        try:
            length = int(self.headers.get("content-length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            exercise_id = str(payload.get("exercise_id") or "").strip()
            if not exercise_id:
                raise ValueError("exercise_id is required.")
            preference = set_favorite(exercise_id, bool(payload.get("favorite")))
            self.send_json(HTTPStatus.OK, {"exercise_id": exercise_id, "preference": preference})
        except Exception as exc:  # noqa: BLE001 - return useful local API errors.
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})

    def handle_exercise_custom(self) -> None:
        try:
            length = int(self.headers.get("content-length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            exercise = add_custom_exercise(payload)
            self.send_json(HTTPStatus.CREATED, {"exercise": exercise, "exercises": merged_exercises()})
        except Exception as exc:  # noqa: BLE001 - return useful local API errors.
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})

    def handle_exercise_update(self) -> None:
        try:
            length = int(self.headers.get("content-length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            exercise_id = str(payload.get("exercise_id") or "").strip()
            if not exercise_id:
                raise ValueError("exercise_id is required.")
            exercise = update_exercise(exercise_id, payload.get("updates") or {})
            self.send_json(HTTPStatus.OK, {"exercise": exercise, "exercises": merged_exercises()})
        except Exception as exc:  # noqa: BLE001 - return useful local API errors.
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})

    def handle_exercise_archive(self) -> None:
        try:
            length = int(self.headers.get("content-length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            exercise_id = str(payload.get("exercise_id") or "").strip()
            if not exercise_id:
                raise ValueError("exercise_id is required.")
            preference = set_archived(exercise_id, bool(payload.get("archived")))
            self.send_json(HTTPStatus.OK, {"exercise_id": exercise_id, "preference": preference, "exercises": merged_exercises()})
        except Exception as exc:  # noqa: BLE001 - return useful local API errors.
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})

    def handle_exercise_delete(self) -> None:
        try:
            length = int(self.headers.get("content-length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            exercise_id = str(payload.get("exercise_id") or "").strip()
            if not exercise_id:
                raise ValueError("exercise_id is required.")
            result = delete_exercise(exercise_id)
            self.send_json(HTTPStatus.OK, {**result, "exercises": merged_exercises()})
        except Exception as exc:  # noqa: BLE001 - return useful local API errors.
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})

    def handle_exercise_reorder(self) -> None:
        try:
            length = int(self.headers.get("content-length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            result = reorder_exercises(payload.get("ordered_ids") or [])
            self.send_json(HTTPStatus.OK, {**result, "exercises": merged_exercises()})
        except Exception as exc:  # noqa: BLE001 - return useful local API errors.
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})

    def preview_summary(self, preview: dict) -> dict:
        return {
            "exists": bool(preview),
            "generated_at": preview.get("generated_at"),
            "source": preview.get("source"),
            "limit": preview.get("limit"),
            "stats": preview.get("stats", {}),
            "license_policy": preview.get("license_policy", {}),
            "incoming": (preview.get("incoming") or [])[:30],
        }

    def handle_get_exercise_import_preview(self) -> None:
        try:
            self.send_json(HTTPStatus.OK, self.preview_summary(read_preview()))
        except Exception as exc:  # noqa: BLE001 - return useful local API errors.
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})

    def handle_exercise_import_preview(self) -> None:
        try:
            length = int(self.headers.get("content-length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            source = str(payload.get("source") or "wger")
            limit = int(payload.get("limit") or 10)
            if source not in {"local-demo", "wger"}:
                raise ValueError("Unsupported exercise import source.")
            if limit < 1 or limit > 300:
                raise ValueError("limit must be between 1 and 300.")
            preview = write_preview(source, limit, images_only=bool(payload.get("images_only")))
            self.send_json(HTTPStatus.OK, self.preview_summary(preview))
        except Exception as exc:  # noqa: BLE001 - return useful local API errors.
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})

    def handle_exercise_import_apply(self) -> None:
        try:
            preview = read_preview()
            if not preview:
                raise ValueError("No exercise import preview exists.")
            backup_path = apply_preview(preview)
            self.send_json(
                HTTPStatus.OK,
                {
                    "applied": True,
                    "backup_path": str(backup_path.relative_to(PROJECT_ROOT)),
                    "stats": preview.get("stats", {}),
                    "exercises": merged_exercises(),
                },
            )
        except Exception as exc:  # noqa: BLE001 - return useful local API errors.
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})

    def handle_captures(self, query: str) -> None:
        try:
            from datetime import datetime  # noqa: PLC0415

            params = parse_qs(query)
            month = params.get("month", [None])[0]
            if month:
                captures = read_captures_for_month(month, include_ignored=True)
                self.send_json(HTTPStatus.OK, {"month": month, "captures": captures})
                return
            date = params.get("date", [datetime.now(local_timezone()).date().isoformat()])[0]
            captures = read_captures(date, include_ignored=True)
            self.send_json(HTTPStatus.OK, {"date": date, "captures": captures})
        except Exception as exc:  # noqa: BLE001 - return useful local API errors.
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})

    def handle_activity_history(self, query: str) -> None:
        try:
            from datetime import datetime  # noqa: PLC0415

            params = parse_qs(query)
            month = params.get("month", [None])[0]
            if month:
                sessions = [
                    session
                    for session in read_activity_sessions(include_ignored=True)
                    if str(session.get("date") or "").startswith(month)
                ]
                self.send_json(HTTPStatus.OK, {"month": month, "sessions": sessions})
                return
            date = params.get("date", [datetime.now(local_timezone()).date().isoformat()])[0]
            sessions = read_activity_sessions(date, include_ignored=True)
            self.send_json(HTTPStatus.OK, {"date": date, "sessions": sessions})
        except Exception as exc:  # noqa: BLE001 - return useful local API errors.
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})

    def handle_ignore_capture(self) -> None:
        try:
            length = int(self.headers.get("content-length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            capture_id = str(payload.get("capture_id") or "").strip()
            if not capture_id:
                raise ValueError("capture_id is required.")

            capture = update_capture_status(capture_id, "ignored")
            refresh = refresh_outputs(capture["date"])
            self.send_json(HTTPStatus.OK, {"capture": capture, "refresh": refresh})
        except Exception as exc:  # noqa: BLE001 - return useful local API errors.
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})

    def handle_update_capture(self) -> None:
        try:
            length = int(self.headers.get("content-length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            capture_id = str(payload.get("capture_id") or "").strip()
            if not capture_id:
                raise ValueError("capture_id is required.")

            capture = update_capture(capture_id, payload.get("updates") or {})
            refresh = refresh_outputs(capture["date"])
            self.send_json(HTTPStatus.OK, {"capture": capture, "refresh": refresh})
        except Exception as exc:  # noqa: BLE001 - return useful local API errors.
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})

    def handle_delete_capture(self) -> None:
        try:
            length = int(self.headers.get("content-length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            capture_id = str(payload.get("capture_id") or "").strip()
            if not capture_id:
                raise ValueError("capture_id is required.")

            capture = delete_capture(capture_id)
            refresh = refresh_outputs(capture.get("date"))
            self.send_json(HTTPStatus.OK, {"deleted": capture, "refresh": refresh})
        except Exception as exc:  # noqa: BLE001 - return useful local API errors.
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})

    def handle_sync_local_apps(self) -> None:
        try:
            from datetime import datetime  # noqa: PLC0415

            now = datetime.now(local_timezone())

            calendar_path = PROJECT_ROOT / "data/context/calendar-context.json"
            calendar_context = build_calendar_context(days=2)
            write_calendar_json(calendar_path, calendar_context)
            log_calendar_action(
                now,
                calendar_path,
                calendar_context["data_quality"]["status"],
                calendar_context["summary"]["event_count"],
            )

            notes_path = PROJECT_ROOT / "data/context/notes-context.json"
            notes_context = build_notes_context(folder="Nomad Life", max_notes=10, include_body=False)
            write_notes_json(notes_path, notes_context)
            log_notes_action(
                now,
                notes_path,
                notes_context["data_quality"]["status"],
                notes_context["summary"]["note_count"],
                "Nomad Life",
            )

            refresh = refresh_outputs(now.date().isoformat(), now=now)
            self.send_json(
                HTTPStatus.OK,
                {
                    "calendar": {
                        "data_quality": calendar_context["data_quality"],
                        "summary": calendar_context["summary"],
                    },
                    "notes": {
                        "data_quality": notes_context["data_quality"],
                        "summary": notes_context["summary"],
                    },
                    "refresh": refresh,
                },
            )
        except Exception as exc:  # noqa: BLE001 - return useful local API errors.
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})

    def handle_hermes_draft(self, query: str) -> None:
        try:
            from datetime import datetime  # noqa: PLC0415

            params = parse_qs(query)
            date = params.get("date", [datetime.now(local_timezone()).date().isoformat()])[0]
            path = PROJECT_ROOT / f"reports/daily/{date}-hermes-draft.md"
            if not path.exists():
                self.send_json(HTTPStatus.OK, {"date": date, "exists": False, "content": ""})
                return
            self.send_json(
                HTTPStatus.OK,
                {
                    "date": date,
                    "exists": True,
                    "path": str(path.relative_to(PROJECT_ROOT)),
                    "content": path.read_text(encoding="utf-8"),
                },
            )
        except Exception as exc:  # noqa: BLE001 - return useful local API errors.
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})

    def handle_inbox_status(self) -> None:
        try:
            from process_inbox import inbox_files  # noqa: PLC0415

            files = [
                str(path.relative_to(PROJECT_ROOT))
                for path in inbox_files()
            ]
            self.send_json(HTTPStatus.OK, {"pending": len(files), "files": files})
        except Exception as exc:  # noqa: BLE001 - return useful local API errors.
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})

    def send_json(self, status: HTTPStatus, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", "application/json; charset=utf-8")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def next_available_address(host: str, preferred_port: int, attempts: int = 20) -> tuple[str, int]:
    for port in range(preferred_port, preferred_port + attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                probe.bind((host, port))
            except OSError:
                continue
            return host, port
    raise OSError(f"No available local port from {preferred_port} to {preferred_port + attempts - 1}.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Serve the local Nomad Dashboard files.")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host. Use 0.0.0.0 for same-Wi-Fi mobile testing.")
    parser.add_argument("--port", type=int, default=4174, help="Preferred port. Defaults to 4174.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    os.chdir(PROJECT_ROOT)
    address = next_available_address(args.host, args.port)
    server = ThreadingHTTPServer(address, CockpitHandler)
    print(f"Nomad Dashboard: http://{address[0]}:{address[1]}/web/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

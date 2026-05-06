#!/usr/bin/env python3
"""Serve the local Nomad Dashboard files."""

from __future__ import annotations

import json
import os
import socket
import sys
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from process_inbox import process_inbox  # noqa: E402
from quick_capture import save_capture  # noqa: E402
from capture_store import read_captures, update_capture_status  # noqa: E402
from refresh_outputs import refresh_outputs  # noqa: E402
from read_calendar_context import build_context as build_calendar_context  # noqa: E402
from read_calendar_context import log_action as log_calendar_action  # noqa: E402
from read_calendar_context import write_json as write_calendar_json  # noqa: E402
from read_notes_context import build_context as build_notes_context  # noqa: E402
from read_notes_context import log_action as log_notes_action  # noqa: E402
from read_notes_context import write_json as write_notes_json  # noqa: E402
from workout_store import read_workout_sessions, save_workout_session, summarize_strength_entries  # noqa: E402
from exercise_library import mark_used, merged_exercises, set_favorite  # noqa: E402
from import_exercise_library import apply_preview, read_preview, write_preview  # noqa: E402


class CockpitHandler(SimpleHTTPRequestHandler):
    def do_POST(self) -> None:
        if self.path == "/api/capture":
            self.handle_capture()
            return

        if self.path == "/api/sync-inbox":
            self.handle_sync_inbox()
            return

        if self.path == "/api/captures/ignore":
            self.handle_ignore_capture()
            return

        if self.path == "/api/sync-local-apps":
            self.handle_sync_local_apps()
            return

        if self.path == "/api/workout-session":
            self.handle_workout_session()
            return

        if self.path == "/api/exercises/favorite":
            self.handle_exercise_favorite()
            return

        if self.path == "/api/exercises/import-preview":
            self.handle_exercise_import_preview()
            return

        if self.path == "/api/exercises/import-apply":
            self.handle_exercise_import_apply()
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
            from zoneinfo import ZoneInfo  # noqa: PLC0415

            date = datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat()
            result["refresh"] = refresh_outputs(date)
            self.send_json(HTTPStatus.OK, result)
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

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/inbox-status":
            self.handle_inbox_status()
            return

        if parsed.path == "/api/config":
            self.handle_config()
            return

        if parsed.path == "/api/captures":
            self.handle_captures(parsed.query)
            return

        if parsed.path == "/api/hermes-draft":
            self.handle_hermes_draft(parsed.query)
            return

        if parsed.path == "/api/exercises":
            self.handle_exercises()
            return

        if parsed.path == "/api/exercises/import-preview":
            self.handle_get_exercise_import_preview()
            return

        if parsed.path == "/api/workout-history":
            self.handle_workout_history()
            return

        super().do_GET()

    def handle_exercises(self) -> None:
        try:
            self.send_json(HTTPStatus.OK, {"exercises": merged_exercises()})
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
            from zoneinfo import ZoneInfo  # noqa: PLC0415

            params = parse_qs(query)
            date = params.get("date", [datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat()])[0]
            captures = read_captures(date, include_ignored=True)
            self.send_json(HTTPStatus.OK, {"date": date, "captures": captures})
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

    def handle_sync_local_apps(self) -> None:
        try:
            from datetime import datetime  # noqa: PLC0415
            from zoneinfo import ZoneInfo  # noqa: PLC0415

            now = datetime.now(ZoneInfo("Asia/Seoul"))

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
            from zoneinfo import ZoneInfo  # noqa: PLC0415

            params = parse_qs(query)
            date = params.get("date", [datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat()])[0]
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


def main() -> None:
    os.chdir(PROJECT_ROOT)
    address = next_available_address("127.0.0.1", 4174)
    server = ThreadingHTTPServer(address, CockpitHandler)
    print(f"Nomad Dashboard: http://{address[0]}:{address[1]}/web/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

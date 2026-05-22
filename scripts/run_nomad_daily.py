#!/usr/bin/env python3
"""Run the local deterministic Nomad Life daily pipeline."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from time_utils import local_timezone

from process_inbox import process_inbox
from quick_capture import PROJECT_ROOT
from read_calendar_context import build_context as build_calendar_context
from read_calendar_context import log_action as log_calendar_action
from read_calendar_context import write_json as write_calendar_json
from read_notes_context import build_context as build_notes_context
from read_notes_context import log_action as log_notes_action
from read_notes_context import write_json as write_notes_json
from refresh_outputs import refresh_outputs
from package_stay_data import package_current_stay


TIMEZONE = local_timezone()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Nomad Life daily local pipeline.")
    parser.add_argument("--date", help="Date to generate in YYYY-MM-DD. Defaults to today in configured local timezone.")
    parser.add_argument("--skip-inbox", action="store_true", help="Do not process inbox files.")
    parser.add_argument("--include-local-apps", action="store_true", help="Read approved local app context snapshots.")
    parser.add_argument("--skip-calendar", action="store_true", help="Skip Apple Calendar context when local apps are included.")
    parser.add_argument("--skip-notes", action="store_true", help="Skip Apple Notes context when local apps are included.")
    parser.add_argument("--notes-folder", default="Nomad Life", help="Exact Apple Notes folder to read.")
    parser.add_argument("--package-stay", action="store_true", help="Create a current stay package and local backup after refresh.")
    return parser.parse_args()


def run_daily(
    date: str | None = None,
    skip_inbox: bool = False,
    include_local_apps: bool = False,
    skip_calendar: bool = False,
    skip_notes: bool = False,
    notes_folder: str = "Nomad Life",
    package_stay: bool = False,
) -> dict:
    now = datetime.now(TIMEZONE)
    target_date = date or now.date().isoformat()

    inbox = None
    if not skip_inbox:
        inbox = process_inbox(regenerate_dashboard=False)

    local_apps = None
    if include_local_apps:
        local_apps = {}
        if not skip_calendar:
            calendar_path = PROJECT_ROOT / "data/context/calendar-context.json"
            calendar_context = build_calendar_context(days=2)
            write_calendar_json(calendar_path, calendar_context)
            log_calendar_action(now, calendar_path, calendar_context["data_quality"]["status"], calendar_context["summary"]["event_count"])
            local_apps["calendar"] = {
                "data_quality": calendar_context["data_quality"],
                "summary": calendar_context["summary"],
            }
        if not skip_notes:
            notes_path = PROJECT_ROOT / "data/context/notes-context.json"
            notes_context = build_notes_context(folder=notes_folder, max_notes=10, include_body=False)
            write_notes_json(notes_path, notes_context)
            log_notes_action(now, notes_path, notes_context["data_quality"]["status"], notes_context["summary"]["note_count"], notes_folder)
            local_apps["notes"] = {
                "data_quality": notes_context["data_quality"],
                "summary": notes_context["summary"],
            }

    refresh = refresh_outputs(target_date, now=now)
    stay_package = package_current_stay() if package_stay else None
    return {
        "schema_version": "0.1.0",
        "generated_at": now.isoformat(),
        "project_root": str(PROJECT_ROOT),
        "date": target_date,
        "inbox": inbox,
        "local_apps": local_apps,
        "dashboard": refresh["dashboard"],
        "expenses": refresh["expenses"],
        "notifications": refresh["notifications"],
        "stay_package": stay_package,
        "next_steps": [
            "Review dashboard/today.json",
            "Review dashboard/notifications.json",
            "Review reports/daily/{date}-brief.md".format(date=target_date),
            "Use Hermes coordinator enrichment only after local output is stable",
        ],
    }


def main() -> None:
    args = parse_args()
    print(
        json.dumps(
            run_daily(
                date=args.date,
                skip_inbox=args.skip_inbox,
                include_local_apps=args.include_local_apps,
                skip_calendar=args.skip_calendar,
                skip_notes=args.skip_notes,
                notes_folder=args.notes_folder,
                package_stay=args.package_stay,
            ),
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

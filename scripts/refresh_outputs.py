#!/usr/bin/env python3
"""Refresh derived Nomad Life outputs after local data changes."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from time_utils import local_timezone

from generate_activity_allocation import generate_activity_allocation
from generate_agent_reports import generate_agent_reports
from generate_daily_brief import generate_daily_brief
from generate_expense_candidates import generate_expense_candidates
from generate_notifications import generate_notifications


TIMEZONE = local_timezone()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Refresh Nomad Life derived outputs.")
    parser.add_argument("--date", help="Date to refresh in YYYY-MM-DD. Defaults to today in configured local timezone.")
    return parser.parse_args()


def refresh_outputs(date: str | None = None, now: datetime | None = None) -> dict:
    now = now or datetime.now(TIMEZONE)
    target_date = date or now.date().isoformat()
    activity = generate_activity_allocation(target_date, now=now)
    agent_reports = generate_agent_reports(target_date, now=now)
    expenses = generate_expense_candidates(target_date, now=now)
    dashboard = generate_daily_brief(target_date, now=now)
    notifications = generate_notifications(target_date, now=now)
    return {
        "schema_version": "0.1.0",
        "generated_at": now.isoformat(),
        "date": target_date,
        "activity": activity,
        "agent_reports": agent_reports,
        "expenses": expenses,
        "dashboard": dashboard,
        "notifications": notifications,
    }


def main() -> None:
    args = parse_args()
    print(json.dumps(refresh_outputs(args.date), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

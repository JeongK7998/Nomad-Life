"""Shared local time helpers for Nomad Life scripts."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TIMEZONE = "Asia/Makassar"


def configured_timezone_name() -> str:
    path = PROJECT_ROOT / "data/travel/current-stay.json"
    if not path.exists():
        return DEFAULT_TIMEZONE
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return DEFAULT_TIMEZONE
    return str(payload.get("timezone") or DEFAULT_TIMEZONE)


def local_timezone() -> ZoneInfo:
    try:
        return ZoneInfo(configured_timezone_name())
    except Exception:
        return ZoneInfo(DEFAULT_TIMEZONE)


def local_now() -> datetime:
    return datetime.now(local_timezone())

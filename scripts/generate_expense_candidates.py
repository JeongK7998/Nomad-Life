#!/usr/bin/env python3
"""Generate reviewable expense candidates from finance-linked captures."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from capture_store import read_captures


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TIMEZONE = ZoneInfo("Asia/Seoul")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Nomad Life expense candidates.")
    parser.add_argument("--date", help="Date to process in YYYY-MM-DD. Defaults to all capture dates.")
    return parser.parse_args()


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def append_jsonl(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")


def capture_dates() -> list[str]:
    captures_dir = PROJECT_ROOT / "data/captures"
    return sorted(path.stem for path in captures_dir.glob("*.jsonl"))


def infer_category(text: str) -> tuple[str | None, str | None]:
    lowered = text.lower()
    if any(word in text for word in ["택시", "버스", "지하철", "기차", "교통"]):
        return "transport", "taxi" if "택시" in text else None
    if any(word in text for word in ["점심", "아침", "저녁", "식사", "밥", "카페", "커피"]):
        return "food", "cafe" if "카페" in text or "커피" in text else None
    if any(word in text for word in ["숙소", "호텔", "에어비앤비"]):
        return "lodging", None
    if any(word in lowered for word in ["subscription", "saas"]) or any(word in text for word in ["구독", "결제"]):
        return "tools", None
    return None, None


def candidate_from_capture(capture: dict) -> dict | None:
    finance = capture.get("parsed_result", {}).get("finance")
    if not finance:
        return None

    category, subcategory = infer_category(capture.get("raw_content", ""))
    return {
        "id": f"expense_candidate_{capture['id'].replace('capture_', '')}",
        "date": capture["date"],
        "created_at": capture["created_at"],
        "amount": finance.get("amount"),
        "currency": finance.get("currency"),
        "exchange_rate": None,
        "category": category,
        "subcategory": subcategory,
        "place": None,
        "payment_method": None,
        "satisfaction": None,
        "required_or_optional": None,
        "note": capture.get("raw_content", ""),
        "source": capture["id"],
        "status": "candidate",
        "confidence": capture.get("confidence", 0.0),
        "review": {
            "required": True,
            "reason": "Generated from Quick Capture. Category and metadata need user review before normalization.",
        },
    }


def generate_expense_candidates(date: str | None = None, now: datetime | None = None) -> dict:
    now = now or datetime.now(TIMEZONE)
    dates = [date] if date else capture_dates()
    candidates = []

    for capture_date in dates:
        for capture in read_captures(capture_date, include_ignored=False):
            candidate = candidate_from_capture(capture)
            if candidate:
                candidates.append(candidate)

    candidates.sort(key=lambda item: (item["date"], item["created_at"], item["id"]))
    payload = {
        "schema_version": "0.1.0",
        "generated_at": now.isoformat(),
        "date": date,
        "data_quality": {
            "status": "partial" if candidates else "empty",
            "notes": [
                "Expense candidates are generated from captures and are not normalized expenses yet.",
                "User review is required before moving candidates into normalized-expenses.json.",
            ],
        },
        "policy": {
            "auto_confirm": False,
            "review_required": True,
        },
        "candidates": candidates,
    }
    write_json(PROJECT_ROOT / "data/expenses/expense-candidates.json", payload)

    record = {
        "id": f"action_log_{now.strftime('%Y%m%d_%H%M%S')}_expense_candidates",
        "created_at": now.isoformat(),
        "agent_name": "nomad-finance",
        "action_type": "generate_expense_candidates",
        "target_tool": "local_files",
        "reason": "Create reviewable expense candidates from finance captures",
        "input": {"date": date},
        "output": {
            "path": "data/expenses/expense-candidates.json",
            "candidate_count": len(candidates),
        },
        "status": "success",
        "approval_required": False,
        "approved_by_user": False,
        "error": None,
    }
    append_jsonl(PROJECT_ROOT / f"data/action_logs/{now.date().isoformat()}.jsonl", record)
    return {
        "date": date,
        "candidates": len(candidates),
        "outputs": ["data/expenses/expense-candidates.json"],
    }


def main() -> None:
    args = parse_args()
    print(json.dumps(generate_expense_candidates(args.date), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

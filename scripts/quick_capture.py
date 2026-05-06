#!/usr/bin/env python3
"""Append a Nomad Life quick capture to local JSONL storage."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TIMEZONE = ZoneInfo("Asia/Seoul")


AGENT_KEYWORDS = {
    "nomad-finance": [
        "원",
        "달러",
        "루피아",
        "엔",
        "유로",
        "썼",
        "결제",
        "비용",
        "예산",
        "지출",
        "카드",
        "현금",
    ],
    "nomad-food": [
        "아침",
        "점심",
        "식사",
        "밥",
        "카페",
        "커피",
        "맛",
        "무거",
        "가벼",
        "단백질",
        "채소",
        "술",
    ],
    "nomad-health": [
        "운동",
        "수영",
        "서핑",
        "헬스",
        "산책",
        "걸음",
        "아팠",
        "통증",
        "컨디션",
    ],
    "nomad-work": [
        "작업",
        "코딩",
        "AI",
        "미팅",
        "회의",
        "프로젝트",
        "집중",
        "완료",
        "막혔",
    ],
    "nomad-travel-guide": [
        "이동",
        "숙소",
        "비행",
        "공항",
        "예약",
        "여행",
        "체험",
        "날씨",
        "비자",
    ],
    "nomad-creator": [
        "콘텐츠",
        "블로그",
        "인스타",
        "스레드",
        "영상",
        "사진",
        "글",
        "소재",
    ],
    "nomad-english": [
        "영어",
        "표현",
        "회화",
        "말",
        "복습",
        "단어",
        "롤플레이",
    ],
    "nomad-rest": [
        "피곤",
        "휴식",
        "회복",
        "잠",
        "수면",
        "번아웃",
        "쉬",
        "무리",
    ],
}


CURRENCY_ALIASES = {
    "원": "KRW",
    "달러": "USD",
    "루피아": "IDR",
    "엔": "JPY",
    "유로": "EUR",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Save a Nomad Life quick capture.")
    parser.add_argument("content", nargs="*", help="Capture text. If omitted, --text is used.")
    parser.add_argument("--text", help="Capture text.")
    parser.add_argument("--type", default="text", choices=["text", "voice", "photo", "expense", "checkin"])
    parser.add_argument("--media-url", default=None)
    parser.add_argument("--no-refresh", action="store_true", help="Do not refresh derived dashboard outputs.")
    return parser.parse_args()


def slugify(text: str) -> str:
    words = re.findall(r"[A-Za-z0-9가-힣]+", text)
    return "_".join(words[:4])[:40] or "capture"


def detect_agents(text: str) -> list[str]:
    linked = []
    lowered = text.lower()
    for agent, keywords in AGENT_KEYWORDS.items():
        if any(keyword.lower() in lowered for keyword in keywords):
            linked.append(agent)
    return linked or ["nomad-coordinator"]


def extract_amount(text: str) -> dict | None:
    pattern = re.compile(r"(?P<amount>\d[\d,\.]*|\d+\s*만)\s*(?P<currency>원|달러|루피아|엔|유로)")
    match = pattern.search(text)
    if not match:
        return None

    raw_amount = match.group("amount").replace(",", "").replace(" ", "")
    if raw_amount.endswith("만"):
        amount = int(raw_amount[:-1]) * 10000
    elif "." in raw_amount:
        amount = float(raw_amount)
    else:
        amount = int(raw_amount)

    currency_label = match.group("currency")
    return {
        "amount": amount,
        "currency": CURRENCY_ALIASES[currency_label],
        "raw": match.group(0),
    }


def extract_duration_hours(text: str) -> float | None:
    match = re.search(r"(\d+(?:\.\d+)?)\s*시간", text)
    if not match:
        return None
    return float(match.group(1))


def build_parsed_result(text: str, linked_agents: list[str]) -> dict:
    parsed: dict[str, object] = {}

    amount = extract_amount(text)
    if amount:
        parsed["finance"] = amount

    duration = extract_duration_hours(text)
    if duration is not None:
        parsed.setdefault("activity", {})
        parsed["activity"]["duration_hours"] = duration

    if "카페" in text:
        parsed.setdefault("work", {})
        parsed["work"]["place_hint"] = "카페"

    if any(word in text for word in ["점심", "아침", "식사", "밥"]) or (
        "저녁" in text and any(word in text for word in ["먹", "식사", "밥", "메뉴"])
    ):
        parsed.setdefault("food", {})
        for meal_type in ["아침", "점심", "저녁"]:
            if meal_type in text:
                parsed["food"]["meal_type_hint"] = meal_type
        if "무거" in text:
            parsed["food"]["fullness_hint"] = "heavy"
        if "맛" in text and "좋" in text:
            parsed["food"]["satisfaction_hint"] = "high"

    if "수영" in text and any(word in text for word in ["못", "안 "]):
        parsed.setdefault("health", {})
        parsed["health"]["missed_activity"] = "swimming"

    if "영어" in text and any(word in text for word in ["못", "거의"]):
        parsed.setdefault("english", {})
        parsed["english"]["status_hint"] = "missed_or_light"

    parsed["linked_agents"] = linked_agents
    return parsed


def confidence_for(parsed: dict, linked_agents: list[str]) -> float:
    score = 0.35 + min(len(linked_agents), 5) * 0.06 + min(len(parsed), 5) * 0.04
    return round(min(score, 0.82), 2)


def append_jsonl(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")


def load_recent_captures(captures_dir: Path, limit: int = 20) -> list[dict]:
    records: list[dict] = []
    for path in sorted(captures_dir.glob("*.jsonl"), reverse=True):
        with path.open(encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
        if len(records) >= limit:
            break
    return sorted(records[-limit:], key=lambda item: item["created_at"])


def write_latest_context(now: datetime) -> None:
    captures = load_recent_captures(PROJECT_ROOT / "data/captures")
    context = {
        "schema_version": "0.1.0",
        "updated_at": now.isoformat(),
        "date_range": {
            "start": captures[0]["date"] if captures else None,
            "end": captures[-1]["date"] if captures else None,
        },
        "captures": [
            {
                "id": capture["id"],
                "date": capture["date"],
                "type": capture["type"],
                "raw_content": capture["raw_content"],
                "linked_agents": capture["linked_agents"],
                "confidence": capture["confidence"],
                "status": capture["status"],
            }
            for capture in captures
        ],
    }
    path = PROJECT_ROOT / "data/context/latest-captures.json"
    path.write_text(json.dumps(context, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def log_action(now: datetime, capture_id: str) -> None:
    record = {
        "id": f"action_log_{now.strftime('%Y%m%d_%H%M%S')}_quick_capture",
        "created_at": now.isoformat(),
        "agent_name": "nomad-quick-capture",
        "action_type": "write_capture",
        "target_tool": "local_files",
        "reason": "Save user quick capture",
        "input": {"capture_id": capture_id},
        "output": {
            "captures_path": f"data/captures/{now.date().isoformat()}.jsonl",
            "context_path": "data/context/latest-captures.json",
        },
        "status": "success",
        "approval_required": False,
        "approved_by_user": False,
        "error": None,
    }
    append_jsonl(PROJECT_ROOT / f"data/action_logs/{now.date().isoformat()}.jsonl", record)


def save_capture(text: str, capture_type: str = "text", media_url: str | None = None, now: datetime | None = None) -> dict:
    text = text.strip()
    if not text:
        raise ValueError("Capture text is required.")

    now = now or datetime.now(TIMEZONE)
    linked_agents = detect_agents(text)
    parsed = build_parsed_result(text, linked_agents)
    capture_id = f"capture_{now.strftime('%Y%m%d_%H%M%S')}_{slugify(text)}"
    record = {
        "id": capture_id,
        "created_at": now.isoformat(),
        "date": now.date().isoformat(),
        "type": capture_type,
        "raw_content": text,
        "media_url": media_url,
        "parsed_result": parsed,
        "linked_agents": linked_agents,
        "confidence": confidence_for(parsed, linked_agents),
        "status": "parsed",
    }

    append_jsonl(PROJECT_ROOT / f"data/captures/{record['date']}.jsonl", record)
    write_latest_context(now)
    log_action(now, capture_id)
    return record


def main() -> None:
    args = parse_args()
    text = args.text or " ".join(args.content)
    record = save_capture(text, args.type, args.media_url)
    output = {"capture": record}
    if not args.no_refresh:
        from refresh_outputs import refresh_outputs  # noqa: PLC0415

        output["refresh"] = refresh_outputs(record["date"])
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

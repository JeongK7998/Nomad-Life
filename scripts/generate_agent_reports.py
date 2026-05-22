#!/usr/bin/env python3
"""Generate thin domain agent reports for Coordinator synthesis."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import date as date_cls
from datetime import datetime, timedelta
from pathlib import Path
from time_utils import local_timezone

from capture_store import read_captures
from activity_store import read_activity_sessions
from generate_activity_allocation import session_from_capture
from workout_store import read_workout_sessions


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TIMEZONE = local_timezone()
GPTS_ENGLISH_REVIEW_DIR = PROJECT_ROOT / "data/english/gpts-reviews"

HEALTH_TYPES = {
    "수영": "swimming",
    "서핑": "surfing",
    "헬스": "gym",
    "산책": "walking",
    "러닝": "running",
    "요가": "mobility",
    "운동": "exercise",
}

ENGLISH_SITUATIONS = {
    "길": "directions",
    "주문": "ordering",
    "카페": "cafe",
    "호텔": "hotel",
    "공항": "airport",
    "스몰톡": "small_talk",
    "회화": "conversation",
}

WORK_SUBCATEGORIES = {
    "vibe": "vibe_coding",
    "코딩": "coding",
    "개발": "development",
    "기획": "planning",
    "디버그": "debugging",
    "미팅": "meeting",
    "회의": "meeting",
    "리서치": "research",
}

CREATOR_SUBCATEGORIES = {
    "인스타": "instagram",
    "영상": "video",
    "편집": "editing",
    "촬영": "shooting",
    "블로그": "blog",
    "글": "writing",
    "콘텐츠": "content",
}

MUSCLE_GROUPS = [
    ("chest", "가슴"),
    ("back", "등"),
    ("legs", "하체"),
    ("shoulders", "어깨"),
    ("arms", "팔"),
    ("core", "코어"),
    ("full_body", "전신"),
    ("other", "기타"),
]
MUSCLE_GROUP_ORDER = {muscle_group: index for index, (muscle_group, _label) in enumerate(MUSCLE_GROUPS)}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Nomad Life agent reports.")
    parser.add_argument("--date", help="Date to process in YYYY-MM-DD. Defaults to today in configured local timezone.")
    return parser.parse_args()


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def append_jsonl(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")


def infer_health_type(text: str) -> str:
    for keyword, activity_type in HEALTH_TYPES.items():
        if keyword in text:
            return activity_type
    return "exercise"


def infer_english_situation(text: str) -> str | None:
    for keyword, situation in ENGLISH_SITUATIONS.items():
        if keyword in text:
            return situation
    return None


def duration_minutes_from_capture(capture: dict) -> int | None:
    session = session_from_capture(capture)
    if session:
        return session["duration_minutes"]

    activity = capture.get("parsed_result", {}).get("activity", {})
    duration_hours = activity.get("duration_hours")
    if duration_hours is None:
        return None
    return int(float(duration_hours) * 60)


def activity_sessions_for(date: str, areas: set[str]) -> list[dict]:
    return [
        session
        for session in read_activity_sessions(date)
        if session.get("area") in areas and session.get("status") != "ignored"
    ]


def activity_minutes(sessions: list[dict]) -> int:
    return sum(int(session.get("duration_minutes") or 0) for session in sessions)


def infer_subcategory(text: str, mapping: dict[str, str], fallback: str = "general") -> str:
    lowered = text.lower()
    for keyword, value in mapping.items():
        if keyword.lower() in lowered:
            return value
    return fallback


def activity_source_ids(sessions: list[dict]) -> list[str]:
    return [session.get("id") for session in sessions if session.get("id")]


def read_json_file(path: Path) -> tuple[dict | list | None, str | None]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except OSError as exc:
        return None, str(exc)
    except json.JSONDecodeError as exc:
        return None, f"JSON parse error at line {exc.lineno}, column {exc.colno}: {exc.msg}"


def review_date_from_path(path: Path) -> str | None:
    match = re.search(r"(20\d{2})[-_](\d{2})[-_](\d{2})", path.stem)
    if not match:
        match = re.search(r"(20\d{2})-(\d{2})-(\d{2})", path.stem)
    if not match:
        return None
    return "-".join(match.groups())


def read_markdown_json_blocks(path: Path) -> tuple[list[dict], str | None]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return [], str(exc)

    records = []
    parse_errors = []
    for index, block in enumerate(re.findall(r"```json\s*(.*?)\s*```", text, re.S), start=1):
        try:
            payload = json.loads(block)
        except json.JSONDecodeError as exc:
            parse_errors.append(f"JSON block {index} parse error at line {exc.lineno}, column {exc.colno}: {exc.msg}")
            continue
        if isinstance(payload, dict):
            records.append(payload)
    if not records:
        recovered = recover_incomplete_markdown_json(text)
        if recovered:
            records.append(recovered)
    if not records:
        plain_review = parse_plain_text_english_review(text, path)
        if plain_review:
            records.append(plain_review)
    return records, None if records else "; ".join(parse_errors) if parse_errors else None


def parse_plain_text_english_review(text: str, path: Path) -> dict | None:
    if "English Review" not in text and "Session Summary" not in text:
        return None
    date = review_date_from_path(path)
    title = next((line.strip() for line in text.splitlines() if line.strip()), path.stem)
    duration_match = re.search(r"(?:약\s*)?(\d+)\s*분", text)
    duration_minutes = int(duration_match.group(1)) if duration_match else 0
    focus_area = "travel" if any(keyword in text for keyword in ["기차", "train", "ticket", "platform"]) else "conversation"

    learned_items = []
    item_matches = list(re.finditer(r"^\s*\d+\.\s*(.+?)\s*$", text, flags=re.M))
    for index, match in enumerate(item_matches):
        start = match.end()
        end = item_matches[index + 1].start() if index + 1 < len(item_matches) else len(text)
        block = text[start:end]
        meaning_match = re.search(r"의미:\s*(.+)", block)
        example_match = re.search(r"Example:\s*\n(.+)", block)
        learned_items.append(
            {
                "type": "expression",
                "item": match.group(1).strip(),
                "meaning_ko": meaning_match.group(1).strip() if meaning_match else None,
                "example": example_match.group(1).strip() if example_match else None,
                "confidence": 0.7,
            }
        )

    weak_points = []
    if "문장 구조" in text:
        weak_points.append({"area": "sentence_structure", "evidence": "문장 구조가 중간에 무너지는 패턴", "severity": "medium"})
    if "한국어식 어순" in text:
        weak_points.append({"area": "natural_phrasing", "evidence": "한국어식 어순이 섞이는 현상", "severity": "medium"})
    if "auxiliary verb" in text or "do/can/is" in text:
        weak_points.append({"area": "auxiliary_verb", "evidence": "질문 문장 연결 시 auxiliary verb(do/can/is) 사용이 흔들림", "severity": "medium"})

    return {
        "schema_version": "0.1.0",
        "source": "gpts_english_review",
        "session_id": f"gpts_english_{str(date or 'unknown').replace('-', '')}_{re.sub(r'[^a-z0-9]+', '_', path.stem.lower()).strip('_')}",
        "date": date,
        "duration_minutes": duration_minutes,
        "app_name": "Nomad Life English Agent GPTs",
        "conversation_title": title,
        "focus_area": focus_area,
        "level": "unknown",
        "transcript_summary": " ".join(line.strip() for line in text.splitlines()[2:8] if line.strip()),
        "learned_items": learned_items,
        "weak_points": weak_points,
        "habit_patterns": [{"habit": "keeps_conversation_alive", "polarity": "positive", "evidence": "질문을 계속 이어가며 대화를 유지함", "severity": "low"}] if "대화를 유지" in text else [],
        "strengths": ["표현이 막힐 때에도 포기하지 않고 다시 표현을 시도함"] if "포기하지 않고" in text else [],
        "corrections": [],
        "next_actions": [],
        "review_cards": [],
    }


def extract_balanced_json_value(text: str, key: str) -> object | None:
    match = re.search(rf'"{re.escape(key)}"\s*:', text)
    if not match:
        return None
    index = match.end()
    while index < len(text) and text[index].isspace():
        index += 1
    if index >= len(text):
        return None

    if text[index] not in "[{":
        try:
            return json.JSONDecoder().raw_decode(text[index:])[0]
        except json.JSONDecodeError:
            return None

    opening = text[index]
    closing = "]" if opening == "[" else "}"
    depth = 0
    in_string = False
    escaped = False
    for cursor in range(index, len(text)):
        char = text[cursor]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == opening:
            depth += 1
        elif char == closing:
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[index : cursor + 1])
                except json.JSONDecodeError:
                    return None
    return None


def recover_incomplete_markdown_json(text: str) -> dict | None:
    fence_index = text.find("```json")
    if fence_index == -1:
        return None
    brace_index = text.find("{", fence_index)
    if brace_index == -1:
        return None
    json_text = text[brace_index:]
    recovered: dict = {"_recovered_from_incomplete_json": True}
    for key in [
        "schema_version",
        "source",
        "session_id",
        "date",
        "started_at",
        "ended_at",
        "duration_minutes",
        "app_name",
        "conversation_title",
        "input_modes",
        "focus_area",
        "level",
        "user_goal",
        "transcript_summary",
        "context_tags",
        "skill_tags",
        "habit_tags",
        "review_tags",
        "study_context",
        "learned_items",
        "observations",
        "performance_scores",
        "turn_assessments",
        "corrections",
        "weak_points",
        "habit_patterns",
        "strengths",
        "next_actions",
        "review_cards",
        "issue_recurrence",
        "new_issues",
        "agent_feedback",
    ]:
        value = extract_balanced_json_value(json_text, key)
        if value is not None:
            recovered[key] = value
    if "schema_version" not in recovered and "session_id" not in recovered:
        return None
    return recovered


def normalize_learned_items(record: dict) -> list[dict]:
    raw_items = (
        record.get("learned_items")
        or record.get("learned_expressions")
        or record.get("useful_expressions")
        or record.get("key_expressions")
        or []
    )
    items = []
    if isinstance(raw_items, dict):
        flattened = []
        for bucket, values in raw_items.items():
            if isinstance(values, list):
                for value in values:
                    if isinstance(value, str) and value:
                        flattened.append({"type": str(bucket), "item": value, "confidence": 0.75})
                    elif isinstance(value, dict):
                        normalized = dict(value)
                        normalized.setdefault("type", str(bucket))
                        flattened.append(normalized)
        raw_items = flattened
    for item in raw_items:
        if isinstance(item, dict):
            items.append(item)
        elif item:
            items.append({"type": "expression", "item": str(item), "confidence": 0.75})
    return items


def normalize_weak_points(record: dict) -> list[dict]:
    def infer_weak_area(text: str) -> str:
        lowered = text.lower()
        if "vocab" in lowered or "word" in lowered:
            return "vocabulary_precision"
        if "question" in lowered:
            return "question_structure"
        if "sentence" in lowered or "structure" in lowered:
            return "sentence_structure"
        if "natural" in lowered or "phrasing" in lowered:
            return "natural_phrasing"
        if "hesitation" in lowered or "longer" in lowered:
            return "fluency"
        if "confidence" in lowered:
            return "confidence"
        return "fluency"

    points = []
    raw_points = list(record.get("weak_points") or [])
    for issue in record.get("issues") or []:
        if isinstance(issue, dict):
            raw_points.append(
                {
                    "area": issue.get("category") or issue.get("type") or issue.get("id") or "fluency",
                    "evidence": issue.get("user_phrase") or issue.get("observed_phrase") or issue.get("title"),
                    "severity": issue.get("priority") or issue.get("severity") or "medium",
                }
            )
    for item in raw_points:
        if isinstance(item, dict):
            if item.get("title") and not item.get("area"):
                item = {
                    "area": infer_weak_area(str(item.get("title"))),
                    "evidence": item.get("description_ko") or item.get("title"),
                    "severity": "medium",
                }
            points.append(item)
        elif item:
            text = str(item)
            points.append({"area": infer_weak_area(text), "evidence": text, "severity": "medium"})
    return points


def normalize_corrections(record: dict) -> list[dict]:
    corrections = []
    raw_corrections = record.get("corrections") or record.get("mistakes") or []
    for issue in record.get("issues") or []:
        if isinstance(issue, dict):
            raw_corrections.append(
                {
                    "user_said": issue.get("user_phrase") or issue.get("observed_phrase"),
                    "better": issue.get("suggested_phrase") or issue.get("target_phrase"),
                    "category": issue.get("category") or issue.get("type") or "naturalness",
                }
            )
    for item in raw_corrections:
        if not isinstance(item, dict):
            continue
        user_said = item.get("user_said") or item.get("user_expression") or item.get("original")
        better = item.get("better") or item.get("recommended_expression") or item.get("improved") or item.get("corrected")
        if not user_said and not better:
            continue
        normalized = dict(item)
        normalized["user_said"] = user_said
        normalized["better"] = better
        normalized.setdefault("category", item.get("type") or item.get("category") or "naturalness")
        corrections.append(normalized)
    return corrections


def normalize_next_actions(record: dict) -> list[dict]:
    actions = []
    for item in record.get("next_actions") or []:
        if isinstance(item, dict):
            actions.append(item)
        elif item:
            actions.append({"action": str(item), "duration_minutes": 5, "priority": "medium"})
    return actions


def normalize_habit_patterns(record: dict) -> list[dict]:
    patterns = []
    raw_patterns = record.get("habit_patterns") or record.get("patterns") or []
    for item in raw_patterns:
        if isinstance(item, dict):
            patterns.append(item)
        elif item:
            patterns.append({"habit": str(item).replace(" ", "_").lower(), "evidence": str(item), "severity": "medium"})
    return patterns


def normalize_review_cards(record: dict) -> list[dict]:
    cards = []
    raw_cards = record.get("review_cards") or record.get("quiz_candidates") or []
    for item in raw_cards:
        if not isinstance(item, dict):
            continue
        front = item.get("front") or item.get("question") or item.get("question_ko") or item.get("situation") or item.get("ko")
        back = item.get("back") or item.get("answer") or item.get("answer_en") or item.get("expression") or item.get("en")
        if front and back:
            cards.append({"front": front, "back": back, "tags": item.get("tags") or []})
    return cards


def normalize_focus_area(value, fallback: str = "review") -> str:
    if isinstance(value, dict):
        return (
            value.get("focus_area")
            or value.get("situation")
            or value.get("scenario")
            or " · ".join(str(part) for part in value.values() if part)
            or fallback
        )
    if isinstance(value, list):
        return ", ".join(str(item) for item in value if item) or fallback
    if value in {None, ""}:
        return fallback
    return str(value)


def normalize_gpts_review_record(record: dict, path: Path) -> dict:
    session_info = record.get("session_info") if isinstance(record.get("session_info"), dict) else {}
    date = record.get("date") or record.get("session_date") or session_info.get("date") or review_date_from_path(path)
    scenario = record.get("scenario") or record.get("session_type") or session_info.get("scenario")
    fallback_session_key = re.sub(r"[^a-z0-9]+", "_", str(scenario or path.stem).lower()).strip("_")
    normalized = dict(record)
    normalized.setdefault("schema_version", "0.1.0")
    normalized.setdefault("source", "gpts_english_review")
    normalized.setdefault("session_id", f"gpts_english_{str(date or review_date_from_path(path) or 'unknown').replace('-', '')}_{fallback_session_key}")
    normalized["date"] = date
    if normalized.get("duration_minutes") in {None, ""}:
        normalized["duration_minutes"] = session_info.get("duration_minutes") or 0
    normalized["focus_area"] = normalize_focus_area(record.get("focus_area") or scenario, scenario or "review")
    normalized.setdefault("level", session_info.get("difficulty_level") or "unknown")
    normalized.setdefault("conversation_title", scenario)
    if path.suffix in {".md", ".txt"} or path.suffixes[-2:] == [".md", ".txt"]:
        normalized["markdown_file"] = path.name
    else:
        normalized.setdefault("markdown_file", None)
    normalized["learned_items"] = normalize_learned_items(record)
    normalized["corrections"] = normalize_corrections(record)
    normalized["weak_points"] = normalize_weak_points(record)
    normalized["habit_patterns"] = normalize_habit_patterns(record)
    normalized["next_actions"] = normalize_next_actions(record)
    normalized["review_cards"] = normalize_review_cards(record)
    normalized["observations"] = record.get("observations") if isinstance(record.get("observations"), list) else []
    normalized["performance_scores"] = record.get("performance_scores") if isinstance(record.get("performance_scores"), dict) else {}
    normalized["turn_assessments"] = record.get("turn_assessments") if isinstance(record.get("turn_assessments"), list) else []
    normalized["issue_recurrence"] = record.get("issue_recurrence") if isinstance(record.get("issue_recurrence"), list) else []
    normalized["new_issues"] = record.get("new_issues") if isinstance(record.get("new_issues"), list) else []
    normalized["agent_feedback"] = record.get("agent_feedback") if isinstance(record.get("agent_feedback"), dict) else {}
    normalized["study_context"] = record.get("study_context") if isinstance(record.get("study_context"), dict) else {}
    return normalized


def scan_gpts_english_review_records() -> tuple[list[tuple[dict, Path]], list[dict]]:
    if not GPTS_ENGLISH_REVIEW_DIR.exists():
        return [], []

    records = []
    file_errors = []
    for path in sorted(GPTS_ENGLISH_REVIEW_DIR.rglob("*.json")):
        payload, error = read_json_file(path)
        relative_path = str(path.relative_to(PROJECT_ROOT))
        if error:
            file_errors.append({"file": relative_path, "error": error})
            continue
        if payload is None:
            continue
        if isinstance(payload, list):
            records.extend((normalize_gpts_review_record(item, path), path) for item in payload if isinstance(item, dict))
            continue
        if isinstance(payload, dict) and isinstance(payload.get("sessions"), list):
            records.extend((normalize_gpts_review_record(item, path), path) for item in payload["sessions"] if isinstance(item, dict))
            continue
        if isinstance(payload, dict):
            records.append((normalize_gpts_review_record(payload, path), path))

    markdown_paths = {
        *GPTS_ENGLISH_REVIEW_DIR.rglob("*.md"),
        *GPTS_ENGLISH_REVIEW_DIR.rglob("*.md.txt"),
        *GPTS_ENGLISH_REVIEW_DIR.rglob("*.txt"),
    }
    for path in sorted(markdown_paths):
        payloads, error = read_markdown_json_blocks(path)
        relative_path = str(path.relative_to(PROJECT_ROOT))
        if error:
            file_errors.append({"file": relative_path, "error": error})
            continue
        records.extend((normalize_gpts_review_record(payload, path), path) for payload in payloads)
    return records, file_errors


def gpts_review_date(record: dict) -> str | None:
    if record.get("date"):
        return str(record["date"])
    for field in ("started_at", "ended_at", "created_at"):
        if not record.get(field):
            continue
        try:
            return datetime.fromisoformat(str(record[field]).replace("Z", "+00:00")).astimezone(TIMEZONE).date().isoformat()
        except ValueError:
            continue
    return None


def validate_gpts_review(record: dict, path: Path) -> tuple[list[str], list[str]]:
    errors = []
    warnings = []
    required_fields = ["schema_version", "source", "session_id", "date", "duration_minutes", "focus_area"]
    for field in required_fields:
        value = record.get(field)
        if value is None or value == "":
            errors.append(f"missing_{field}")

    try:
        int(record.get("duration_minutes") or 0)
    except (TypeError, ValueError):
        errors.append("duration_minutes_must_be_number")

    recommended_arrays = ["learned_items", "corrections", "weak_points", "habit_patterns", "next_actions", "review_cards"]
    for field in recommended_arrays:
        if not isinstance(record.get(field), list) or not record.get(field):
            warnings.append(f"empty_{field}")

    markdown_file = record.get("markdown_file")
    if not markdown_file:
        warnings.append("missing_markdown_file")
    elif not (path.parent / str(markdown_file)).exists():
        warnings.append("markdown_file_not_found")

    return errors, warnings


def normalized_gpts_english_reviews(date: str) -> tuple[list[dict], dict]:
    reviews = []
    records, file_errors = scan_gpts_english_review_records()
    validation_errors = []
    validation_warnings = []
    skipped_other_date = 0
    skipped_other_source = 0
    for record, path in records:
        if record.get("source") not in {None, "gpts_english_review", "gpt_english_review"}:
            skipped_other_source += 1
            continue
        record_date = gpts_review_date(record)
        if record_date != date:
            skipped_other_date += 1
            continue
        errors, warnings = validate_gpts_review(record, path)
        relative_path = str(path.relative_to(PROJECT_ROOT))
        if errors:
            validation_errors.append({"file": relative_path, "session_id": record.get("session_id"), "errors": errors})
            continue
        if warnings:
            validation_warnings.append({"file": relative_path, "session_id": record.get("session_id"), "warnings": warnings})
        session_id = record.get("session_id") or f"gpts_english_{path.stem}"
        markdown_file = record.get("markdown_file")
        markdown_path = None
        if markdown_file:
            candidate = path.parent / str(markdown_file)
            markdown_path = str(candidate.relative_to(PROJECT_ROOT)) if candidate.exists() else str(markdown_file)
        reviews.append(
            {
                "id": f"gpts_review_{session_id}",
                "date": record_date,
                "session_id": session_id,
                "source_file": str(path.relative_to(PROJECT_ROOT)),
                "markdown_file": markdown_path,
                "duration_minutes": int(record.get("duration_minutes") or 0),
                "app_name": record.get("app_name"),
                "conversation_title": record.get("conversation_title"),
                "input_modes": record.get("input_modes") or [],
                "focus_area": record.get("focus_area") or "review",
                "level": record.get("level") or "unknown",
                "user_goal": record.get("user_goal"),
                "transcript_summary": record.get("transcript_summary"),
                "metrics": record.get("metrics") or {},
                "learned_items": record.get("learned_items") or [],
                "corrections": record.get("corrections") or [],
                "weak_points": record.get("weak_points") or [],
                "habit_patterns": record.get("habit_patterns") or [],
                "strengths": record.get("strengths") or [],
                "next_actions": record.get("next_actions") or [],
                "review_cards": record.get("review_cards") or [],
                "observations": record.get("observations") or [],
                "performance_scores": record.get("performance_scores") or {},
                "turn_assessments": record.get("turn_assessments") or [],
                "issue_recurrence": record.get("issue_recurrence") or [],
                "new_issues": record.get("new_issues") or [],
                "agent_feedback": record.get("agent_feedback") or {},
                "study_context": record.get("study_context") or {},
                "context_tags": record.get("context_tags") or [],
                "skill_tags": record.get("skill_tags") or [],
                "habit_tags": record.get("habit_tags") or [],
                "review_tags": record.get("review_tags") or [],
                "tags": record.get("tags") or [],
            }
        )
    status = {
        "inbox_path": str(GPTS_ENGLISH_REVIEW_DIR.relative_to(PROJECT_ROOT)),
        "json_file_count": len(list(GPTS_ENGLISH_REVIEW_DIR.rglob("*.json"))) if GPTS_ENGLISH_REVIEW_DIR.exists() else 0,
        "markdown_file_count": (
            len({*GPTS_ENGLISH_REVIEW_DIR.rglob("*.md"), *GPTS_ENGLISH_REVIEW_DIR.rglob("*.md.txt"), *GPTS_ENGLISH_REVIEW_DIR.rglob("*.txt")})
            if GPTS_ENGLISH_REVIEW_DIR.exists()
            else 0
        ),
        "record_count": len(records),
        "target_date": date,
        "imported_count": len(reviews),
        "file_error_count": len(file_errors),
        "validation_error_count": len(validation_errors),
        "validation_warning_count": len(validation_warnings),
        "skipped_other_date": skipped_other_date,
        "skipped_other_source": skipped_other_source,
        "file_errors": file_errors[:10],
        "validation_errors": validation_errors[:10],
        "validation_warnings": validation_warnings[:10],
        "status": "error" if file_errors or validation_errors else "warning" if validation_warnings else "ok" if reviews else "empty",
    }
    return reviews, status


def top_counts(values: list[str], limit: int = 5) -> list[dict]:
    return [
        {"name": name, "count": count}
        for name, count in Counter(value for value in values if value).most_common(limit)
    ]


def habit_recommendation(habit: str, count: int = 1) -> dict:
    rules = {
        "answering_too_short": {
            "title": "답변 확장",
            "recommendation": "답변 뒤에 이유 1개 또는 되묻기 1개를 붙입니다.",
            "practice": "한 문장 답변 후 because 또는 What about you?를 붙여 5문장 말하기",
        },
        "korean_to_english_translation": {
            "title": "Chunk-first 말하기",
            "recommendation": "한국어 문장을 통째로 번역하기보다 짧은 영어 chunk를 먼저 꺼냅니다.",
            "practice": "I'd like, Could I get, I was wondering if 패턴으로 5문장 만들기",
        },
        "overthinking": {
            "title": "5초 안에 말하기",
            "recommendation": "완벽한 문장보다 짧고 빠른 첫 문장을 우선합니다.",
            "practice": "질문을 보고 5초 안에 6단어 이하로 답하기",
        },
        "avoiding_detail": {
            "title": "Detail 1개 추가",
            "recommendation": "짧은 답 뒤에 장소, 이유, 감정 중 하나를 추가합니다.",
            "practice": "I liked it because... 패턴으로 5문장 말하기",
        },
        "repeating_same_expression": {
            "title": "표현 교체",
            "recommendation": "반복 표현 하나를 대체 표현 두 개로 바꿉니다.",
            "practice": "good 대신 nice, solid, helpful, comfortable로 문장 만들기",
        },
        "low_confidence": {
            "title": "작게 확신하기",
            "recommendation": "큰 설명보다 확실히 말할 수 있는 짧은 문장을 쌓습니다.",
            "practice": "I think / I prefer / I need 패턴으로 5문장 말하기",
        },
        "continues_speaking_despite_uncertainty": {
            "title": "불확실해도 이어가는 힘",
            "recommendation": "좋은 습관입니다. 다만 이어 말한 뒤 핵심 표현 1개를 정확한 문장으로 다시 고정합니다.",
            "practice": "어색했던 문장 3개를 자연스러운 문장으로 다시 말하기",
        },
        "uses_short_practical_questions_effectively": {
            "title": "짧은 실전 질문 유지",
            "recommendation": "짧은 질문은 강점입니다. 같은 질문을 장소만 바꿔 3번 재사용합니다.",
            "practice": "Where is..., What time..., Do you have... 패턴으로 5문장 만들기",
        },
        "sometimes_combines_multiple_ideas_into_one_sentence": {
            "title": "한 문장 한 생각",
            "recommendation": "여러 생각이 섞이면 의미가 흐려집니다. 긴 문장을 두 개의 짧은 문장으로 나눕니다.",
            "practice": "어색한 문장 3개를 one idea per sentence 방식으로 분리하기",
        },
        "relies_on_approximate_vocabulary_when_unsure": {
            "title": "비슷한 단어 대체 줄이기",
            "recommendation": "모르는 단어를 추측할 때 의미가 크게 바뀝니다. 간단한 설명 문장으로 우회합니다.",
            "practice": "receipt, browsing, reservation처럼 틀린 단어를 5번 소리내어 교정하기",
        },
        "hesitates_during_longer_question_structures": {
            "title": "긴 질문 구조 안정화",
            "recommendation": "질문이 길어질수록 멈칫하는 패턴이 있습니다. What should I / Can I / Do you have로 시작을 고정합니다.",
            "practice": "What should I do..., Can I get..., Do you have... 질문 6개 만들기",
        },
        "uses_korean_sentence_order_occasionally": {
            "title": "영어 어순 먼저 꺼내기",
            "recommendation": "한국어 문장을 번역하기보다 주어와 동사를 먼저 말합니다.",
            "practice": "I feel / I want / I need / I can’t로 시작하는 문장 8개 만들기",
        },
        "missing_auxiliary_verbs": {
            "title": "조동사 누락 교정",
            "recommendation": "부정문과 현재형에서 do/don’t, does/doesn’t를 먼저 고정합니다.",
            "practice": "I don’t / He doesn’t / Do you 패턴으로 8문장 만들기",
        },
        "trying_to_build_overly_long_sentences": {
            "title": "긴 문장 쪼개기",
            "recommendation": "긴 문장을 만들다가 구조가 무너지는 패턴입니다. 짧은 두 문장으로 나눕니다.",
            "practice": "긴 한국어 문장 3개를 영어 짧은 문장 2개씩으로 분리하기",
        },
        "direct_korean_sentence_order": {
            "title": "직역 어순 줄이기",
            "recommendation": "한국어 어순을 그대로 따라가면 자연스러움이 떨어집니다. 영어 기본 어순을 먼저 둡니다.",
            "practice": "주어 + 동사 + 목적어 구조로 오늘 문장 6개 만들기",
        },
        "direct_korean_translation": {
            "title": "직역 멈추고 의미 먼저 말하기",
            "recommendation": "한국어 문장을 통째로 옮기기 전에 핵심 의미를 짧은 영어 문장으로 먼저 고정합니다.",
            "practice": "오늘 쓴 한국어 문장 3개를 I want / I need / I feel / I think로 시작해 다시 말하기",
        },
        "auxiliary_verb": {
            "title": "조동사 뼈대 고정",
            "recommendation": "질문과 부정문에서 do/can/should를 먼저 넣고 나머지 단어를 붙입니다.",
            "practice": "Do you / Can I / Should I / I don’t 패턴으로 여행 상황 질문 8개 만들기",
        },
        "vocabulary_precision": {
            "title": "단어 정밀도 보정",
            "recommendation": "비슷한 단어를 추측하기보다 쉬운 설명 문장으로 의미를 정확히 우회합니다.",
            "practice": "모르는 단어 3개를 It means... / It is like... / I use it when...으로 설명하기",
        },
    }
    rule = rules.get(habit, {
        "title": habit.replace("_", " ").title(),
        "recommendation": f"{english_area_label(habit)} 신호를 최근 예시 하나에 묶어 짧게 교정합니다.",
        "practice": f"{english_area_label(habit)}가 드러난 최신 문장 1개를 고르고, 더 나은 문장 3개만 다시 말하기",
    })
    return {
        "habit": habit,
        "count": count,
        "title": rule["title"],
        "recommendation": rule["recommendation"],
        "practice": rule["practice"],
        "duration_minutes": 5,
    }


def is_positive_habit(habit: str) -> bool:
    positive_keywords = {
        "continues_speaking_despite_uncertainty",
        "uses_short_practical_questions_effectively",
        "comfortable_with_emotional_small_talk",
        "adds_detail_after_short_answers",
        "good_immediate_repetition_after_correction",
        "uses_context_well",
        "keeps_conversation_alive",
        "confidence_improves_after_warm_up",
        "good_follow_up_question_ability",
    }
    return habit in positive_keywords or habit.startswith("good_") or "effectively" in habit or "confidence_improves" in habit


def english_area_label(area: str) -> str:
    labels = {
        "sentence_structure": "문장 구조",
        "vocabulary_precision": "어휘 정확도",
        "question_structure": "질문 구조",
        "natural_phrasing": "자연스러운 표현",
        "fluency": "유창성",
        "confidence": "자신감",
    }
    return labels.get(area, area.replace("_", " "))


def build_habit_recommendations(habit_focus: list[dict]) -> list[dict]:
    return [
        habit_recommendation(item["name"], item.get("count", 1))
        for item in habit_focus[:3]
        if item.get("name") and not is_positive_habit(item["name"])
    ]


def build_review_card_queue(review_cards: list[dict], date: str) -> list[dict]:
    queue = []
    for index, card in enumerate(review_cards[:20], start=1):
        queue.append(
            {
                "id": f"english_review_card_{date.replace('-', '')}_{index:03d}",
                "front": card.get("front"),
                "back": card.get("back"),
                "tags": card.get("tags") or [],
                "status": "queued",
                "priority": "normal",
                "due_date": date,
            }
        )
    return queue


def date_range_ending(date: str, days: int = 7) -> list[str]:
    end = date_cls.fromisoformat(date)
    start = end - timedelta(days=days - 1)
    return [(start + timedelta(days=offset)).isoformat() for offset in range(days)]


def build_english_weekly_summary(date: str) -> dict:
    dates = date_range_ending(date, 7)
    reviews = []
    import_issue_count = 0
    for day in dates:
        day_reviews, day_status = normalized_gpts_english_reviews(day)
        reviews.extend(day_reviews)
        import_issue_count += day_status.get("file_error_count", 0) + day_status.get("validation_error_count", 0)

    activity_sessions = []
    for day in dates:
        activity_sessions.extend(activity_sessions_for(day, {"english"}))

    review_minutes = sum(int(review.get("duration_minutes") or 0) for review in reviews)
    activity_minutes_total = activity_minutes(activity_sessions)
    habit_tags = [tag for review in reviews for tag in review.get("habit_tags", [])]
    habit_patterns = [item for review in reviews for item in review.get("habit_patterns", [])]
    weak_points = [item for review in reviews for item in review.get("weak_points", [])]
    focus_areas = [review.get("focus_area") for review in reviews if review.get("focus_area")]
    active_dates = sorted({review["date"] for review in reviews} | {session["date"] for session in activity_sessions})
    habit_focus = top_counts(habit_tags + [item.get("habit") for item in habit_patterns if item.get("habit")], limit=5)
    weak_focus = top_counts([item.get("area") for item in weak_points if item.get("area")], limit=5)
    correction_goal = None
    corrective_habits = [item for item in habit_focus if not is_positive_habit(item["name"])]
    if corrective_habits:
        top_habit = corrective_habits[0]
        correction_goal = habit_recommendation(top_habit["name"], top_habit["count"])
    elif weak_focus:
        weak_name = weak_focus[0]["name"]
        correction_goal = {
            "title": f"{english_area_label(weak_name)} 반복 교정",
            "recommendation": f"{english_area_label(weak_name)} 약점을 최신 실제 예시 하나에 묶어 교정합니다.",
            "practice": f"{english_area_label(weak_name)}가 드러난 문장 1개를 고르고 같은 의미를 더 짧은 영어 3문장으로 다시 말하기",
            "duration_minutes": 5,
        }

    return {
        "window": {
            "start_date": dates[0],
            "end_date": dates[-1],
            "days": len(dates),
        },
        "review_session_count": len(reviews),
        "activity_session_count": len(activity_sessions),
        "active_day_count": len(active_dates),
        "study_minutes": review_minutes + activity_minutes_total,
        "gpts_review_minutes": review_minutes,
        "activity_minutes": activity_minutes_total,
        "top_habit_tags": habit_focus,
        "top_weak_points": weak_focus,
        "top_focus_areas": top_counts(focus_areas, limit=5),
        "correction_goal": correction_goal,
        "import_issue_count": import_issue_count,
    }


def correction_key(correction: dict) -> str:
    raw = correction.get("category") or correction.get("type") or correction.get("user_said") or correction.get("original") or ""
    return re.sub(r"[^a-z0-9가-힣]+", "_", str(raw).lower()).strip("_")


def issue_key(value: str) -> str:
    return re.sub(r"[^a-z0-9가-힣]+", "_", str(value or "").lower()).strip("_")


def issue_category_from_correction(correction: dict) -> str:
    text = " ".join(str(correction.get(field) or "") for field in ("category", "type", "user_said", "better")).lower()
    if "auxiliary" in text or "don't" in text or "doesn't" in text or "usually not" in text:
        return "auxiliary_verb"
    if "vocab" in text or "word" in text or "rank" in text or "averaging" in text:
        return "vocabulary_precision"
    if "question" in text:
        return "question_structure"
    if "sentence" in text or "structure" in text or "grammar" in text or "verb" in text:
        return "sentence_structure"
    if "natural" in text or "expression" in text or "phrasing" in text:
        return "natural_phrasing"
    return "sentence_structure"


def normalize_issue_category(category: str | None) -> str:
    raw = issue_key(category or "")
    aliases = {
        "grammar": "sentence_structure",
        "structure": "sentence_structure",
        "word_choice": "vocabulary_precision",
        "vocabulary": "vocabulary_precision",
        "naturalness": "natural_phrasing",
        "natural_expression": "natural_phrasing",
    }
    allowed = {
        "auxiliary_verb",
        "sentence_structure",
        "vocabulary_precision",
        "question_structure",
        "natural_phrasing",
        "fluency",
        "pronunciation",
        "confidence",
        "listening",
        "habit",
    }
    return aliases.get(raw) or raw if raw in allowed else "sentence_structure"


def issue_title(category: str) -> str:
    return {
        "auxiliary_verb": "조동사 누락",
        "sentence_structure": "문장 구조",
        "vocabulary_precision": "어휘 정확도",
        "question_structure": "질문 구조",
        "natural_phrasing": "자연스러운 표현",
        "fluency": "유창성",
        "pronunciation": "발음",
        "listening": "리스닝",
        "confidence": "자신감",
        "habit": "말하기 습관",
    }.get(category, english_area_label(category))


def remediation_for_issue(category: str, key: str) -> dict:
    rules = {
        "auxiliary_verb": {
            "plan": "부정문과 질문에서 do/don't, does/doesn't를 먼저 고정합니다.",
            "drill": "I don't / He doesn't / Do you 패턴으로 8문장 만들기",
            "verification": "다음 세션에서 현재형 부정문과 질문을 최소 3번 유도하고 조동사 누락 여부를 표시하세요.",
        },
        "sentence_structure": {
            "plan": "긴 문장을 한 번에 만들지 말고 한 생각을 한 문장으로 분리합니다.",
            "drill": "어색했던 문장 3개를 짧은 영어 문장 2개씩으로 쪼개기",
            "verification": "다음 세션에서 긴 답변을 유도하고 문장 섞임 또는 어순 붕괴가 재발했는지 표시하세요.",
        },
        "vocabulary_precision": {
            "plan": "모르는 단어를 비슷한 소리로 추측하기보다 쉬운 설명 문장으로 우회합니다.",
            "drill": "receipt, browsing, reservation 같은 혼동 단어를 예문으로 5번 말하기",
            "verification": "다음 세션에서 영수증, 둘러보기, 예약 관련 상황을 넣고 단어 대체 오류가 재발했는지 표시하세요.",
        },
        "question_structure": {
            "plan": "긴 질문은 고정 starter로 시작합니다.",
            "drill": "Can I..., Do you have..., What should I... 질문 6개 만들기",
            "verification": "다음 세션에서 긴 질문을 3번 만들게 하고 중간 멈춤이나 구조 붕괴를 표시하세요.",
        },
        "natural_phrasing": {
            "plan": "직역 표현을 native-like chunk로 바꿉니다.",
            "drill": "오늘 교정 문장 5개를 자연스러운 표현으로 다시 말하기",
            "verification": "다음 세션에서 같은 의미를 다른 상황에 재사용하게 하고 자연스러움 변화를 표시하세요.",
        },
    }
    return rules.get(category, {
        "plan": f"{issue_title(category)} 문제를 한 가지 상황에서만 반복 확인합니다.",
        "drill": f"{issue_title(category)} 관련 문장 5개 만들기",
        "verification": f"다음 세션에서 {issue_title(category)} 문제가 다시 나타나는지 표시하세요.",
    })


def issue_status(observation_count: int, active_day_count: int, recent_observation_count: int, latest_has_issue: bool) -> str:
    if observation_count >= 3 or active_day_count >= 2:
        return "persistent"
    if observation_count >= 2 or latest_has_issue:
        return "active"
    if recent_observation_count == 0 and observation_count >= 2:
        return "improving"
    return "watch"


def issue_severity(status: str, count: int) -> str:
    if status == "persistent" or count >= 4:
        return "high"
    if status == "active" or count >= 2:
        return "medium"
    return "low"


def build_english_issue_tracker(date: str) -> dict:
    reviews, import_issue_count = valid_reviews_until(date)
    if not reviews:
        return {
            "status": "empty",
            "algorithm_version": "0.1.0",
            "issues": [],
            "recurrence_checks": [],
            "import_issue_count": import_issue_count,
        }

    latest_reviews = reviews[-3:]
    latest_ids = {review["session_id"] for review in latest_reviews}
    observations_by_issue: dict[str, list[dict]] = {}

    def add_observation(issue_id: str, observation: dict) -> None:
        observations_by_issue.setdefault(issue_id, []).append(observation)

    for review in reviews:
        for correction in review.get("corrections", []):
            pair = correction_pair(correction)
            category = issue_category_from_correction(pair)
            key = issue_key(category)
            add_observation(
                f"{category}:{key}",
                {
                    "date": review["date"],
                    "session_id": review["session_id"],
                    "source": "correction",
                    "category": category,
                    "user_said": pair.get("user_said"),
                    "better": pair.get("better"),
                },
            )
        for weak_point in review.get("weak_points", []):
            category = weak_point.get("area") or "fluency"
            add_observation(
                f"{category}:{issue_key(category)}",
                {
                    "date": review["date"],
                    "session_id": review["session_id"],
                    "source": "weak_point",
                    "category": category,
                    "evidence": weak_point.get("evidence"),
                },
            )
        for habit in review.get("habit_patterns", []):
            habit_key = habit.get("habit")
            if not habit_key or is_positive_habit(habit_key):
                continue
            add_observation(
                f"habit:{issue_key(habit_key)}",
                {
                    "date": review["date"],
                    "session_id": review["session_id"],
                    "source": "habit",
                    "category": "habit",
                    "habit": habit_key,
                    "evidence": habit.get("evidence"),
                },
            )
        for observation in review.get("observations", []):
            if not isinstance(observation, dict):
                continue
            observation_type = observation.get("type")
            category = normalize_issue_category(observation.get("category"))
            if observation_type in {"strength", "learned_item"}:
                continue
            if category == "habit" and is_positive_habit(str(observation.get("habit") or observation.get("issue_id") or "")):
                continue
            issue_candidate = observation.get("issue_candidate") if isinstance(observation.get("issue_candidate"), dict) else {}
            fingerprint = (
                observation.get("issue_id")
                or issue_candidate.get("fingerprint_hint")
                or observation.get("fingerprint_hint")
                or category
            )
            add_observation(
                f"{category}:{issue_key(fingerprint)}",
                {
                    "date": review["date"],
                    "session_id": review["session_id"],
                    "source": observation_type or "observation",
                    "category": category,
                    "user_said": observation.get("user_said"),
                    "better": observation.get("better"),
                    "evidence": observation.get("evidence"),
                    "trigger": observation.get("trigger"),
                },
            )
        for new_issue in review.get("new_issues", []):
            if not isinstance(new_issue, dict):
                continue
            category = normalize_issue_category(new_issue.get("category"))
            fingerprint = category
            add_observation(
                f"{category}:{issue_key(fingerprint)}",
                {
                    "date": review["date"],
                    "session_id": review["session_id"],
                    "source": "new_issue",
                    "category": category,
                    "evidence": new_issue.get("evidence") or new_issue.get("title"),
                },
            )
        for turn in review.get("turn_assessments", []):
            if not isinstance(turn, dict):
                continue
            category = normalize_issue_category(turn.get("main_issue_category"))
            if category in {"general", "habit"}:
                continue
            add_observation(
                f"{category}:{issue_key(category)}",
                {
                    "date": review["date"],
                    "session_id": review["session_id"],
                    "source": "turn_assessment",
                    "category": category,
                    "user_said": turn.get("user_said"),
                    "better": turn.get("better"),
                    "evidence": turn.get("situation"),
                    "score": (turn.get("scores") or {}).get(category),
                },
            )

    issues = []
    for issue_id, observations in observations_by_issue.items():
        category = observations[0]["category"]
        dates = sorted({item["date"] for item in observations})
        recent_count = sum(1 for item in observations if item["session_id"] in latest_ids)
        latest_has_issue = any(item["session_id"] == reviews[-1]["session_id"] for item in observations)
        recurrence_records = [
            item
            for review in reviews
            for item in review.get("issue_recurrence", [])
            if isinstance(item, dict) and item.get("issue_id") == issue_id
        ]
        explicit_not_seen = sum(1 for item in recurrence_records if item.get("status") == "not_seen")
        explicit_improved = sum(1 for item in recurrence_records if item.get("status") == "partially_improved")
        status = issue_status(len(observations), len(dates), recent_count, latest_has_issue)
        if explicit_not_seen >= 3 and status == "persistent":
            status = "resolved_candidate"
        elif explicit_not_seen or explicit_improved:
            status = "improving"
        remediation = remediation_for_issue(category, issue_id)
        examples = [
            {
                "date": item["date"],
                "user_said": item.get("user_said"),
                "better": item.get("better"),
                "evidence": item.get("evidence") or item.get("habit"),
            }
            for item in observations[-3:]
        ]
        issues.append(
            {
                "issue_id": issue_id,
                "category": category,
                "title": issue_title(category),
                "status": status,
                "severity": issue_severity(status, len(observations)),
                "first_seen": dates[0],
                "last_seen": dates[-1],
                "observation_count": len(observations),
                "active_day_count": len(dates),
                "recent_observation_count": recent_count,
                "explicit_not_seen_count": explicit_not_seen,
                "explicit_partially_improved_count": explicit_improved,
                "examples": examples,
                "remediation": remediation,
                "verification_prompt": remediation["verification"],
            }
        )

    status_order = {"persistent": 0, "active": 1, "watch": 2, "improving": 3, "resolved_candidate": 4}
    severity_order = {"high": 0, "medium": 1, "low": 2}
    issues.sort(key=lambda item: (status_order.get(item["status"], 9), severity_order.get(item["severity"], 9), -item["observation_count"]))

    recurrence_checks = [
        {
            "issue_id": item["issue_id"],
            "title": item["title"],
            "latest_status": "reappeared" if item["recent_observation_count"] else "not_seen_recently",
            "latest_window_sessions": len(latest_reviews),
            "instruction": item["verification_prompt"],
        }
        for item in issues[:8]
    ]
    return {
        "status": "active",
        "algorithm_version": "0.1.0",
        "review_session_count": len(reviews),
        "latest_session_id": reviews[-1]["session_id"],
        "issues": issues[:20],
        "recurrence_checks": recurrence_checks,
        "import_issue_count": import_issue_count,
    }


def build_pre_study_context(issue_tracker: dict, learning_profile: dict) -> dict:
    active_issues = [
        issue for issue in issue_tracker.get("issues", [])
        if issue.get("status") in {"active", "persistent", "watch"}
    ][:5]
    lines = [
        "Use live roleplay simulation mode.",
        "First define a scenario and roles briefly, then start the roleplay immediately.",
        "During the roleplay, stay in character and do not correct, score, explain grammar, or review each answer unless I explicitly ask.",
        "Silently observe whether the tracked issues reappear. Put all corrections, scores, and issue recurrence results only in the post-session review JSON/Markdown.",
        "",
        "Tracked issues to silently observe during the roleplay:",
    ]
    for index, issue in enumerate(active_issues, start=1):
        example = next((item for item in issue.get("examples", []) if item.get("user_said") or item.get("evidence")), {})
        evidence = example.get("user_said") or example.get("evidence") or ""
        lines.append(f"{index}. {issue['title']} ({issue['status']}, {issue['observation_count']} observations)")
        if evidence:
            lines.append(f"   Previous example: {evidence}")
        lines.append(f"   Silent check: {issue['verification_prompt']}")
    lines.extend([
        "",
        "After the roleplay ends, include JSON fields:",
        "- issue_recurrence: issue_id, status(reappeared|partially_improved|not_seen|not_tested), evidence",
        "- performance_scores",
        "- turn_assessments",
        "- new_issues",
        "- learned_items",
        "- corrections",
        "- next_actions",
    ])
    return {
        "status": "ready" if active_issues else "empty",
        "active_issue_count": len(active_issues),
        "prompt": "\n".join(lines),
        "active_issues": [
            {
                "issue_id": issue["issue_id"],
                "title": issue["title"],
                "status": issue["status"],
                "verification_prompt": issue["verification_prompt"],
            }
            for issue in active_issues
        ],
        "learning_scope": learning_profile.get("scope", {}),
    }


def build_study_schedule_analysis(date: str) -> dict:
    reviews, import_issue_count = valid_reviews_until(date)
    dates_14 = date_range_ending(date, 14)
    date_set_14 = set(dates_14)
    recent_reviews = [review for review in reviews if review["date"] in date_set_14]
    active_dates = sorted({review["date"] for review in recent_reviews})
    focus_counts = top_counts([review.get("focus_area") for review in recent_reviews if review.get("focus_area")], limit=8)
    total_sessions = len(recent_reviews)
    total_minutes = sum(int(review.get("duration_minutes") or 0) for review in recent_reviews)
    most_repeated = focus_counts[0] if focus_counts else None
    repeated_share = round(most_repeated["count"] / total_sessions, 2) if most_repeated and total_sessions else 0
    cadence = "none"
    if len(active_dates) >= 5:
        cadence = "steady"
    elif len(active_dates) >= 3:
        cadence = "light_but_consistent"
    elif len(active_dates) >= 1:
        cadence = "sporadic"

    recommendations = []
    if repeated_share >= 0.5 and most_repeated:
        recommendations.append(f"{most_repeated['name']} 비중이 높습니다. 다음 세션은 다른 실전 상황으로 바꾸는 것이 좋습니다.")
    if len(active_dates) < 3:
        recommendations.append("최근 14일 기준 학습일이 적습니다. 긴 학습보다 10분 세션을 2-3회 더 쌓는 편이 좋습니다.")
    if not recommendations:
        recommendations.append("빈도와 상황 다양성이 크게 무너지지 않았습니다. 현재 issue 중심으로 세션을 설계하면 됩니다.")

    return {
        "window": {"start_date": dates_14[0], "end_date": dates_14[-1], "days": 14},
        "session_count": total_sessions,
        "active_day_count": len(active_dates),
        "study_minutes": total_minutes,
        "average_minutes_per_active_day": round(total_minutes / len(active_dates), 1) if active_dates else 0,
        "cadence": cadence,
        "focus_distribution": focus_counts,
        "most_repeated_focus": most_repeated,
        "repeated_focus_share": repeated_share,
        "recommendations": recommendations,
        "import_issue_count": import_issue_count,
    }


def build_learning_continuity(date: str) -> dict:
    reviews, import_issue_count = valid_reviews_until(date)
    dates_14 = date_range_ending(date, 14)
    date_set = set(dates_14)
    recent_reviews = [review for review in reviews if review["date"] in date_set]
    by_date: dict[str, list[dict]] = {day: [] for day in dates_14}
    for review in recent_reviews:
        by_date.setdefault(review["date"], []).append(review)
    daily = []
    for day in dates_14:
        day_reviews = by_date.get(day, [])
        minutes = sum(int(review.get("duration_minutes") or 0) for review in day_reviews)
        daily.append(
            {
                "date": day,
                "minutes": minutes,
                "session_count": len(day_reviews),
                "focus_areas": top_counts([review.get("focus_area") for review in day_reviews if review.get("focus_area")], limit=4),
                "sessions": [
                    {
                        "session_id": review.get("session_id"),
                        "title": review.get("conversation_title") or review.get("focus_area") or "GPTs Review",
                        "duration_minutes": int(review.get("duration_minutes") or 0),
                        "source_file": review.get("source_file"),
                    }
                    for review in day_reviews
                ],
            }
        )
    active_days = [item for item in daily if item["minutes"] or item["session_count"]]
    current_streak = 0
    for item in reversed(daily):
        if item["minutes"] or item["session_count"]:
            current_streak += 1
        elif current_streak:
            break
    focus_distribution = top_counts([review.get("focus_area") for review in recent_reviews if review.get("focus_area")], limit=6)
    total_minutes = sum(item["minutes"] for item in daily)
    return {
        "window": {"start_date": dates_14[0], "end_date": dates_14[-1], "days": 14},
        "daily": daily,
        "active_day_count": len(active_days),
        "session_count": len(recent_reviews),
        "study_minutes": total_minutes,
        "average_minutes_per_active_day": round(total_minutes / len(active_days), 1) if active_days else 0,
        "current_streak_days": current_streak,
        "max_daily_minutes": max([item["minutes"] for item in daily] or [0]),
        "focus_distribution": focus_distribution,
        "summary": (
            f"최근 14일 중 {len(active_days)}일 학습, 총 {total_minutes}분, {len(recent_reviews)}개 세션입니다."
            if recent_reviews
            else "최근 14일 학습 기록이 없습니다."
        ),
        "import_issue_count": import_issue_count,
    }


def build_daily_review_log(date: str) -> list[dict]:
    reviews, _import_issue_count = valid_reviews_until(date)
    grouped: dict[str, list[dict]] = {}
    for review in reviews:
        grouped.setdefault(review["date"], []).append(review)
    days = []
    for day in sorted(grouped.keys(), reverse=True)[:14]:
        sessions = []
        for review in grouped[day]:
            sessions.append(
                {
                    "session_id": review.get("session_id"),
                    "title": review.get("conversation_title") or review.get("focus_area") or "GPTs Review",
                    "duration_minutes": int(review.get("duration_minutes") or 0),
                    "focus_area": review.get("focus_area"),
                    "source_file": review.get("source_file"),
                    "weak_points": [
                        {
                            "area": item.get("area"),
                            "evidence": item.get("evidence"),
                            "severity": item.get("severity"),
                        }
                        for item in review.get("weak_points", [])[:5]
                        if isinstance(item, dict)
                    ],
                    "corrections": [
                        {
                            "user_said": item.get("user_said") or item.get("original"),
                            "better": item.get("better") or item.get("corrected"),
                            "category": item.get("category"),
                            "reason": item.get("reason_ko"),
                        }
                        for item in review.get("corrections", [])[:5]
                        if isinstance(item, dict)
                    ],
                    "learned_items": [
                        {
                            "item": item.get("item") or item.get("expression"),
                            "meaning": item.get("meaning_ko") or item.get("example"),
                            "type": item.get("type"),
                        }
                        for item in review.get("learned_items", [])[:6]
                        if isinstance(item, dict)
                    ],
                    "habit_patterns": [
                        {
                            "habit": item.get("habit"),
                            "evidence": item.get("evidence"),
                            "severity": item.get("severity"),
                        }
                        for item in review.get("habit_patterns", [])[:4]
                        if isinstance(item, dict)
                    ],
                    "new_issues": review.get("new_issues", [])[:4],
                }
            )
        days.append(
            {
                "date": day,
                "study_minutes": sum(item["duration_minutes"] for item in sessions),
                "session_count": len(sessions),
                "sessions": sessions,
            }
        )
    return days


def build_issue_progress_summary(issue_tracker: dict, reviews: list[dict]) -> dict:
    issues = issue_tracker.get("issues", [])
    repeated = [
        issue for issue in issues
        if issue.get("status") == "persistent"
    ][:6]
    improving = [
        issue for issue in issues
        if issue.get("status") in {"improving", "resolved_candidate"}
        or (int(issue.get("observation_count") or 0) >= 2 and int(issue.get("recent_observation_count") or 0) == 0)
    ][:6]
    expression_growth = []
    for review in reviews[-8:]:
        learned_count = len(review.get("learned_items") or [])
        if learned_count:
            expression_growth.append(
                {
                    "date": review.get("date"),
                    "session_id": review.get("session_id"),
                    "title": review.get("conversation_title") or review.get("focus_area"),
                    "learned_count": learned_count,
                    "items": [
                        item.get("item")
                        for item in review.get("learned_items", [])[:4]
                        if isinstance(item, dict) and item.get("item")
                    ],
                }
            )
    return {
        "repeated_issues": [
            {
                "issue_id": issue.get("issue_id"),
                "title": issue.get("title"),
                "status": issue.get("status"),
                "observation_count": issue.get("observation_count"),
                "recent_observation_count": issue.get("recent_observation_count"),
                "first_seen": issue.get("first_seen"),
                "last_seen": issue.get("last_seen"),
                "examples": issue.get("examples", [])[:3],
                "remediation": issue.get("remediation", {}),
            }
            for issue in repeated
        ],
        "improving_issues": [
            {
                "issue_id": issue.get("issue_id"),
                "title": issue.get("title"),
                "status": issue.get("status"),
                "observation_count": issue.get("observation_count"),
                "recent_observation_count": issue.get("recent_observation_count"),
                "signal": "최근 세션에서 명시 관찰이 줄었습니다. 다만 GPTs issue_recurrence 확인이 더 필요합니다.",
            }
            for issue in improving
        ],
        "expression_growth": expression_growth,
        "progress_note": "반복 문제는 전체 누적 관측 기준으로, 개선 신호는 최근 3개 세션 재등장 여부와 명시 recurrence 결과를 함께 봅니다.",
    }


def score_from_issues(issues: list[dict], category: str) -> dict:
    matching = [issue for issue in issues if issue.get("category") == category]
    observation_count = sum(int(issue.get("observation_count") or 0) for issue in matching)
    recent_count = sum(int(issue.get("recent_observation_count") or 0) for issue in matching)
    status = matching[0]["status"] if matching else "not_observed"
    severity = matching[0]["severity"] if matching else "low"
    score = None if not observation_count else max(20, 100 - observation_count * 8 - recent_count * 6)
    return {
        "category": category,
        "label": issue_title(category),
        "score": score,
        "score_source": "derived_from_issue_observations",
        "status": status,
        "severity": severity,
        "observation_count": observation_count,
        "recent_observation_count": recent_count,
        "needs_gpts_scoring": True,
        "interpretation": (
            f"최근에도 {recent_count}회 관찰되어 우선 교정이 필요합니다."
            if recent_count
            else "최근 세션에서는 명시 관찰이 적지만, 충분히 테스트됐는지는 아직 알 수 없습니다."
        ),
        "examples": [example for issue in matching for example in issue.get("examples", [])][:3],
    }


def build_performance_metrics(issue_tracker: dict, reviews: list[dict] | None = None) -> dict:
    categories = [
        "natural_phrasing",
        "vocabulary_precision",
        "sentence_structure",
        "auxiliary_verb",
        "question_structure",
        "fluency",
        "pronunciation",
        "listening",
        "confidence",
    ]
    issues = issue_tracker.get("issues", [])
    metrics = [score_from_issues(issues, category) for category in categories]
    reviews = reviews or []
    score_records = [
        review.get("performance_scores", {}).get("session_scores", {})
        for review in reviews
        if isinstance(review.get("performance_scores"), dict)
    ]
    for metric in metrics:
        values = [
            int(scores.get(metric["category"]))
            for scores in score_records
            if scores.get(metric["category"]) is not None
        ]
        metric["score_history"] = [
            {
                "date": review.get("date"),
                "session_id": review.get("session_id"),
                "score": int(review.get("performance_scores", {}).get("session_scores", {}).get(metric["category"])),
            }
            for review in reviews
            if isinstance(review.get("performance_scores"), dict)
            and review.get("performance_scores", {}).get("session_scores", {}).get(metric["category"]) is not None
        ][-8:]
        metric["turn_examples"] = [
            {
                "date": review.get("date"),
                "session_id": review.get("session_id"),
                "situation": turn.get("situation"),
                "user_said": turn.get("user_said"),
                "better": turn.get("better"),
                "score": (turn.get("scores") or {}).get(metric["category"]),
            }
            for review in reviews
            for turn in review.get("turn_assessments", [])
            if isinstance(turn, dict)
            and (
                normalize_issue_category(turn.get("main_issue_category")) == metric["category"]
                or (turn.get("scores") or {}).get(metric["category"]) is not None
            )
        ][-5:]
        metric["why_it_matters"] = {
            "natural_phrasing": "문법적으로 맞아도 실제 대화에서 어색하게 들리는 영역입니다.",
            "vocabulary_precision": "비슷한 단어를 잘못 쓰면 의미가 완전히 달라지는 영역입니다.",
            "sentence_structure": "문장이 길어질 때 의미 전달이 무너지는지를 봅니다.",
            "auxiliary_verb": "질문과 부정문에서 do/can 같은 뼈대가 빠지는지를 봅니다.",
            "question_structure": "필요한 정보를 자연스럽게 물어볼 수 있는지를 봅니다.",
            "fluency": "멈춤과 재시작이 많아도 대화를 이어갈 수 있는지를 봅니다.",
            "pronunciation": "상대가 다른 단어로 들을 가능성이 있는 발음 신호를 봅니다.",
            "listening": "상대 질문을 이해하고 맞는 방향으로 반응했는지를 봅니다.",
            "confidence": "확신이 없어도 대화를 유지하고 추가 요청을 할 수 있는지를 봅니다.",
        }.get(metric["category"], "다음 대화에서 같은 문제가 재등장하는지 확인합니다.")
        metric["next_review_check"] = remediation_for_issue(metric["category"], metric["category"])["verification"]
        if values:
            metric["score"] = round(sum(values) / len(values), 1)
            metric["score_source"] = "gpts_performance_scores"
            metric["needs_gpts_scoring"] = False
            metric["trend"] = "up" if len(values) >= 2 and values[-1] > values[0] else "down" if len(values) >= 2 and values[-1] < values[0] else "flat"
    priority_metrics = sorted(
        [metric for metric in metrics if metric["observation_count"] or metric["recent_observation_count"]],
        key=lambda item: (item["score"], -item["recent_observation_count"], -item["observation_count"]),
    )
    return {
        "status": "active" if issues else "empty",
        "scoring_model": "derived_until_gpts_scores_available",
        "data_note": "현재 score는 issue 관찰 수 기반 임시 점수입니다. GPTs가 performance_scores를 제공하면 실제 평가 점수로 대체합니다.",
        "metrics": metrics,
        "priority_metrics": priority_metrics[:6],
    }


def build_english_summary_metrics(summary: dict, notes: list[dict], reviews: list[dict], learned_items: list[dict], corrections: list[dict], habit_patterns: list[dict], review_cards: list[dict]) -> list[dict]:
    return [
        {
            "key": "study_minutes",
            "label": "학습 시간",
            "value": f"{summary.get('study_minutes', 0)} min",
            "basis": "오늘 날짜의 English activity, capture, GPTs review duration 합계입니다.",
            "detail": [f"{note.get('source')} · {note.get('duration_minutes') or 0} min · {note.get('review_status')}" for note in notes[:8]],
        },
        {
            "key": "reviewed_sessions",
            "label": "리뷰 세션",
            "value": summary.get("reviewed_session_count", 0),
            "basis": "오늘 날짜로 import된 GPTs review 파일 수입니다.",
            "detail": [f"{review.get('conversation_title') or review.get('session_id')} · {review.get('duration_minutes') or 0} min" for review in reviews],
        },
        {
            "key": "learned_items",
            "label": "학습 표현",
            "value": summary.get("learned_item_count", 0),
            "basis": "GPTs review의 learned_items 또는 learned_expressions 개수입니다.",
            "detail": [str(item.get("item") or item.get("expression") or item) for item in learned_items[:8]],
        },
        {
            "key": "corrections",
            "label": "교정",
            "value": summary.get("correction_count", 0),
            "basis": "실제 발화가 더 나은 표현으로 교정된 항목 수입니다.",
            "detail": [
                f"{correction.get('user_said') or correction.get('original')} -> {correction.get('better') or correction.get('corrected')}"
                for correction in corrections[:8]
                if correction.get("user_said") or correction.get("original") or correction.get("better")
            ],
        },
        {
            "key": "habit_patterns",
            "label": "습관 신호",
            "value": summary.get("habit_pattern_count", 0),
            "basis": "한 번의 실수보다 반복될 가능성이 있는 말하기 습관 관측 수입니다.",
            "detail": [f"{item.get('habit')} · {item.get('evidence') or item.get('severity')}" for item in habit_patterns[:8]],
        },
        {
            "key": "review_cards",
            "label": "복습 카드",
            "value": summary.get("review_card_count", 0),
            "basis": "다음 복습에 바로 쓸 수 있는 질문/답 카드 수입니다.",
            "detail": [f"{item.get('front')} -> {item.get('back')}" for item in review_cards[:8]],
        },
    ]


def build_dashboard_validation_agent(
    summary_metrics: list[dict],
    performance_metrics: dict,
    issue_tracker: dict,
    pre_study_context: dict,
    learning_continuity: dict | None = None,
    daily_review_log: list[dict] | None = None,
    issue_progress_summary: dict | None = None,
) -> dict:
    checks = []
    def add_check(key: str, passed: bool, finding: str, fix: str) -> None:
        checks.append({"key": key, "passed": passed, "finding": finding, "fix": fix})

    metrics = performance_metrics.get("metrics", [])
    issues = issue_tracker.get("issues", [])
    learning_continuity = learning_continuity or {}
    daily_review_log = daily_review_log or []
    issue_progress_summary = issue_progress_summary or {}
    has_summary_detail = all(item.get("basis") and item.get("detail") for item in summary_metrics)
    has_metric_evidence = all(item.get("examples") or item.get("turn_examples") for item in metrics if item.get("observation_count"))
    has_actionable_issues = all((item.get("examples") and item.get("remediation")) for item in issues[:5])
    has_pre_study = pre_study_context.get("status") == "ready" and bool(pre_study_context.get("prompt"))
    has_time_flow = bool(learning_continuity.get("daily")) and learning_continuity.get("window", {}).get("days") == 14
    has_daily_file_log = any(day.get("sessions") for day in daily_review_log)
    repeated = issue_progress_summary.get("repeated_issues") or []
    has_progress_tracker = bool(repeated)

    add_check(
        "summary_explainability",
        has_time_flow,
        "상단은 파일 처리 숫자보다 학습 시간 흐름을 먼저 보여야 합니다.",
        "최근 14일 학습 시간 그래프와 active day/session 요약을 최상단에 배치합니다.",
    )
    add_check(
        "daily_file_traceability",
        has_daily_file_log,
        "사용자는 날짜별, 파일별로 무엇을 배웠고 무엇을 틀렸는지 확인해야 합니다.",
        "일자별 로그에서 파일별 learned/corrections/weak points를 분리해 보여줍니다.",
    )
    add_check(
        "metric_evidence",
        has_metric_evidence,
        "성과 지표는 점수만 보여주면 행동으로 이어지지 않습니다.",
        "각 지표에 실제 발화, 교정 문장, 턴별 점수 예시를 연결합니다.",
    )
    add_check(
        "issue_actionability",
        has_actionable_issues,
        "반복 이슈는 무엇을 고칠지와 다음 훈련이 함께 보여야 합니다.",
        "이슈별 예문, 해결 패턴, 다음 검증 질문을 한 카드 안에 배치합니다.",
    )
    add_check(
        "next_session_loop",
        has_pre_study,
        "대시보드가 다음 GPTs 세션으로 이어지는 루프를 제공해야 합니다.",
        "Pre-Study Context를 현재 추적 이슈 기반으로 생성합니다.",
    )
    add_check(
        "issue_progress_tracker",
        has_progress_tracker,
        "누적 분석은 반복 문제와 해결 진행률을 가장 중요하게 보여야 합니다.",
        "반복 이슈, 개선 후보, 표현 확장 신호를 별도 섹션으로 묶습니다.",
    )

    passed_count = sum(1 for item in checks if item["passed"])
    score = round(passed_count / len(checks) * 100) if checks else 0
    return {
        "agent_name": "nomad-english-dashboard-validator",
        "status": "ready" if score >= 75 else "needs_layout_work",
        "usefulness_score": score,
        "question": "이 화면만 보고 사용자가 무엇을 틀렸고, 왜 틀렸고, 다음에 무엇을 해야 하는지 알 수 있는가?",
        "checks": checks,
        "primary_recommendation": next((item["fix"] for item in checks if not item["passed"]), "현재 화면은 시간 흐름, 파일별 로그, 반복 이슈 진행률을 사용자 행동으로 연결합니다."),
    }


def build_issue_action_plan(issue_tracker: dict) -> list[dict]:
    actions = []
    for issue in issue_tracker.get("issues", [])[:10]:
        example = next((item for item in issue.get("examples", []) if item.get("user_said") or item.get("evidence")), {})
        user_said = example.get("user_said") or example.get("evidence")
        better = example.get("better")
        actions.append(
            {
                "issue_id": issue.get("issue_id"),
                "title": issue.get("title"),
                "status": issue.get("status"),
                "severity": issue.get("severity"),
                "why": f"{issue.get('observation_count', 0)}회 관찰, 최근 {issue.get('recent_observation_count', 0)}회 재등장",
                "example": {"user_said": user_said, "better": better},
                "drill": issue.get("remediation", {}).get("drill"),
                "how_to_fix": issue.get("remediation", {}).get("plan"),
                "verification_prompt": issue.get("verification_prompt"),
            }
        )
    return actions


def correction_pair(correction: dict) -> dict:
    return {
        "user_said": correction.get("user_said") or correction.get("user_expression") or correction.get("original"),
        "better": correction.get("better") or correction.get("recommended_expression") or correction.get("improved") or correction.get("corrected"),
        "category": correction.get("category") or correction.get("type") or "correction",
    }


def valid_reviews_until(date: str) -> tuple[list[dict], int]:
    records, file_errors = scan_gpts_english_review_records()
    reviews = []
    issue_count = len(file_errors)
    for record, path in records:
        if record.get("source") not in {None, "gpts_english_review", "gpt_english_review"}:
            continue
        record_date = gpts_review_date(record)
        if not record_date or record_date > date:
            continue
        errors, warnings = validate_gpts_review(record, path)
        issue_count += len(errors)
        if errors:
            continue
        session_id = record.get("session_id") or f"gpts_english_{path.stem}"
        reviews.append(
            {
                "date": record_date,
                "session_id": session_id,
                "focus_area": record.get("focus_area") or "review",
                "duration_minutes": int(record.get("duration_minutes") or 0),
                "level": record.get("level") or "unknown",
                "strengths": record.get("strengths") or [],
                "learned_items": record.get("learned_items") or [],
                "corrections": record.get("corrections") or [],
                "weak_points": record.get("weak_points") or [],
                "habit_patterns": record.get("habit_patterns") or [],
                "review_cards": record.get("review_cards") or [],
                "next_actions": record.get("next_actions") or [],
                "observations": record.get("observations") or [],
                "performance_scores": record.get("performance_scores") or {},
                "turn_assessments": record.get("turn_assessments") or [],
                "issue_recurrence": record.get("issue_recurrence") or [],
                "new_issues": record.get("new_issues") or [],
                "agent_feedback": record.get("agent_feedback") or {},
                "study_context": record.get("study_context") or {},
                "source_file": str(path.relative_to(PROJECT_ROOT)),
                "warning_count": len(warnings),
            }
        )
    reviews.sort(key=lambda item: (item["date"], item["session_id"]))
    return reviews, issue_count



def session_bucket(reviews: list[dict], start_index: int, end_index: int | None = None) -> list[dict]:
    return reviews[start_index:end_index]


def build_english_learning_profile(date: str) -> dict:
    reviews, import_issue_count = valid_reviews_until(date)
    if not reviews:
        return {
            "status": "empty",
            "agent_interpretation": "아직 누적 학습 리뷰가 없어 진도나 반복 패턴을 판단하지 않습니다.",
            "scope": {"review_session_count": 0, "active_day_count": 0, "study_minutes": 0},
            "progression": [],
            "improvement_signals": [],
            "persistent_issues": [],
            "correction_insights": [],
            "learned_inventory": [],
            "next_focus": [],
            "import_issue_count": import_issue_count,
        }

    active_dates = sorted({review["date"] for review in reviews})
    focus_areas = [review["focus_area"] for review in reviews if review.get("focus_area")]
    total_minutes = sum(review.get("duration_minutes") or 0 for review in reviews)
    learned_items = [item for review in reviews for item in review.get("learned_items", [])]
    corrections = [correction_pair(item) for review in reviews for item in review.get("corrections", [])]
    weak_points = [item for review in reviews for item in review.get("weak_points", [])]
    habit_patterns = [item for review in reviews for item in review.get("habit_patterns", [])]
    strengths = [strength for review in reviews for strength in review.get("strengths", [])]

    habit_counts = top_counts([item.get("habit") for item in habit_patterns if item.get("habit")], limit=8)
    weak_counts = top_counts([item.get("area") for item in weak_points if item.get("area")], limit=8)
    correction_counts = top_counts([correction_key(item) for item in corrections], limit=8)
    focus_counts = top_counts(focus_areas, limit=8)

    recent_reviews = session_bucket(reviews, max(0, len(reviews) - 3))
    earlier_reviews = session_bucket(reviews, 0, max(0, len(reviews) - 3))
    recent_habits = {item.get("habit") for review in recent_reviews for item in review.get("habit_patterns", []) if item.get("habit")}
    earlier_habits = {item.get("habit") for review in earlier_reviews for item in review.get("habit_patterns", []) if item.get("habit")}
    recurring_habits = [item for item in habit_counts if item["count"] >= 2 and not is_positive_habit(item["name"])]
    positive_habits = [item for item in habit_counts if is_positive_habit(item["name"])]
    newly_observed_habits = sorted(habit for habit in recent_habits - earlier_habits if not is_positive_habit(habit))

    persistent_issues = []
    for item in recurring_habits[:5]:
        persistent_issues.append(
            {
                "type": "habit",
                "key": item["name"],
                "title": habit_recommendation(item["name"], item["count"])["title"],
                "count": item["count"],
                "interpretation": "여러 세션에서 반복 관찰된 말하기 습관입니다.",
                "status": "persistent",
            }
        )
    for item in weak_counts[:3]:
        persistent_issues.append(
            {
                "type": "weak_point",
                "key": item["name"],
                "title": english_area_label(item["name"]),
                "count": item["count"],
                "interpretation": "리뷰에서 반복 언급된 약점 영역입니다.",
                "status": "watch" if item["count"] < 2 else "persistent",
            }
        )

    improvement_signals = []
    for item in positive_habits[:5]:
        improvement_signals.append(
            {
                "signal": habit_recommendation(item["name"], item["count"])["title"],
                "basis": f"positive habit observed {item['count']}x",
            }
        )
    for strength in strengths:
        text = str(strength)
        lowered = text.lower()
        if any(keyword in lowered for keyword in ["continued", "confidence", "naturally", "flow", "repetition", "practical"]):
            improvement_signals.append({"signal": text, "basis": "GPTs review strength"})
    if len(active_dates) >= 2:
        improvement_signals.insert(
            0,
            {
                "signal": f"{active_dates[0]}부터 {active_dates[-1]}까지 {len(active_dates)}일 학습 데이터가 쌓였습니다.",
                "basis": "learning continuity",
            },
        )
    if len(set(focus_areas)) >= 3:
        improvement_signals.insert(
            0,
            {
                "signal": "호텔, 스몰톡, 쇼핑 등 실전 상황 범위가 넓어지고 있습니다.",
                "basis": "scenario coverage",
            },
        )

    learned_counter = Counter()
    for item in learned_items:
        value = item.get("item") if isinstance(item, dict) else str(item)
        if value:
            learned_counter[value] += 1
    learned_inventory = [
        {"item": item, "seen_count": count, "status": "new" if count == 1 else "repeated"}
        for item, count in learned_counter.most_common(20)
    ]

    correction_examples = []
    for correction in corrections[:12]:
        if correction.get("user_said") or correction.get("better"):
            correction_examples.append(correction)

    correction_insights = []
    for item in correction_counts[:5]:
        if not item["name"]:
            continue
        correction_insights.append(
            {
                "category": item["name"].replace("_", " "),
                "count": item["count"],
                "interpretation": "교정 로그에서 반복적으로 나타나는 오류 유형입니다.",
            }
        )

    next_focus = []
    if persistent_issues:
        top = persistent_issues[0]
        recommendation = habit_recommendation(top["key"], top["count"]) if top["type"] == "habit" else None
        next_focus.append(
            {
                "title": recommendation["title"] if recommendation else f"{top['title']} 교정",
                "reason": f"{top['count']}회 관찰되어 다음 훈련의 1순위로 둡니다.",
                "practice": recommendation["practice"] if recommendation else f"{top['title']} 관련 문장 5개 만들기",
                "duration_minutes": 5,
            }
        )
    for habit in newly_observed_habits[:2]:
        recommendation = habit_recommendation(habit, 1)
        next_focus.append(
            {
                "title": recommendation["title"],
                "reason": "최근 세션에서 새로 관찰된 습관입니다.",
                "practice": recommendation["practice"],
                "duration_minutes": 5,
            }
        )

    agent_interpretation = (
        f"현재 English Agent는 {len(reviews)}개 리뷰, {len(active_dates)}일, 총 {total_minutes}분의 데이터를 기준으로 봅니다. "
        f"학습 진도는 '{', '.join(item['name'] for item in focus_counts[:3])}' 상황으로 확장 중이고, "
        f"가장 중요한 교정 후보는 '{persistent_issues[0]['title']}'입니다."
        if persistent_issues
        else
        f"현재 English Agent는 {len(reviews)}개 리뷰를 읽었고 강점은 보이지만, 반복 교정 대상 판단에는 데이터가 아직 적습니다."
    )

    return {
        "status": "active",
        "agent_interpretation": agent_interpretation,
        "scope": {
            "first_date": active_dates[0],
            "last_date": active_dates[-1],
            "review_session_count": len(reviews),
            "active_day_count": len(active_dates),
            "study_minutes": total_minutes,
            "focus_areas": focus_counts,
        },
        "progression": [
            {
                "date": day,
                "session_count": sum(1 for review in reviews if review["date"] == day),
                "study_minutes": sum(review.get("duration_minutes") or 0 for review in reviews if review["date"] == day),
                "focus_areas": sorted({review["focus_area"] for review in reviews if review["date"] == day}),
            }
            for day in active_dates
        ],
        "improvement_signals": improvement_signals[:8],
        "persistent_issues": persistent_issues[:8],
        "correction_insights": correction_insights,
        "correction_examples": correction_examples,
        "learned_inventory": learned_inventory,
        "next_focus": next_focus[:4],
        "import_issue_count": import_issue_count,
    }


def parse_date(value: str) -> date_cls:
    return datetime.strptime(value, "%Y-%m-%d").date()


def rolling_dates(target_date: str, window_days: int = 14) -> list[str]:
    end_date = parse_date(target_date)
    return [(end_date - timedelta(days=offset)).isoformat() for offset in range(window_days - 1, -1, -1)]


def build_muscle_dashboard(target_date: str, workout_records: list[dict]) -> dict:
    end_date = parse_date(target_date)
    dates = rolling_dates(target_date)
    date_set = set(dates)
    entries_by_group_date: dict[tuple[str, str], list[dict]] = {}

    for workout in workout_records:
        workout_date = workout.get("date")
        if workout_date not in date_set:
            continue
        for entry in workout.get("entries") or []:
            muscle_group = entry.get("muscle_group") or workout.get("muscle_group") or "other"
            key = (muscle_group, workout_date)
            entries_by_group_date.setdefault(key, []).append({
                "workout_id": workout.get("id"),
                "muscle_group": muscle_group,
                "exercise": entry.get("exercise"),
                "weight_kg": entry.get("weight_kg"),
                "reps": entry.get("reps"),
                "set_index": entry.get("set_index"),
                "rpe": entry.get("rpe"),
            })

    rows = []
    summaries = []
    for muscle_group, label in MUSCLE_GROUPS:
        cells = []
        total_14d = 0
        total_7d = 0
        last_date = None
        for item_date in dates:
            entries = entries_by_group_date.get((muscle_group, item_date), [])
            set_count = len(entries)
            total_14d += set_count
            if item_date >= dates[-7]:
                total_7d += set_count
            if set_count:
                last_date = item_date
            cells.append({
                "date": item_date,
                "set_count": set_count,
                "intensity": min(3, set_count),
                "entries": entries,
            })

        days_since_last = None
        if last_date:
            days_since_last = (end_date - parse_date(last_date)).days
        rows.append({
            "muscle_group": muscle_group,
            "label": label,
            "cells": cells,
        })
        summaries.append({
            "muscle_group": muscle_group,
            "label": label,
            "last_workout_date": last_date,
            "days_since_last": days_since_last,
            "sets_7d": total_7d,
            "sets_14d": total_14d,
        })

    return {
        "window_days": 14,
        "start_date": dates[0],
        "end_date": dates[-1],
        "dates": dates,
        "rows": rows,
        "summaries": summaries,
    }


def readiness_from_summary(item: dict) -> dict:
    days_since_last = item.get("days_since_last")
    sets_14d = item.get("sets_14d") or 0
    if days_since_last is None:
        status = "untracked"
        priority = 3
        reason = "최근 14일 기록 없음"
    elif days_since_last >= 7:
        status = "overdue"
        priority = 3
        reason = f"{days_since_last}일 공백"
    elif days_since_last >= 3:
        status = "ready"
        priority = 2
        reason = f"{days_since_last}일 회복"
    elif days_since_last == 0:
        status = "recent"
        priority = 0
        reason = "오늘 운동함"
    else:
        status = "cooldown"
        priority = 1
        reason = f"{days_since_last}일 전 운동"

    if sets_14d >= 8 and status in {"ready", "overdue"}:
        priority = max(0, priority - 1)
        reason = f"{reason} · 14일 {sets_14d}세트"

    return {
        "muscle_group": item["muscle_group"],
        "label": item["label"],
        "status": status,
        "priority": priority,
        "display_order": MUSCLE_GROUP_ORDER.get(item["muscle_group"], 99),
        "reason": reason,
        "days_since_last": days_since_last,
        "sets_7d": item.get("sets_7d") or 0,
        "sets_14d": sets_14d,
    }


def build_health_recommendations(muscle_dashboard: dict) -> list[dict]:
    readiness = [readiness_from_summary(item) for item in muscle_dashboard.get("summaries", [])]
    candidates = [
        item
        for item in readiness
        if item["muscle_group"] not in {"full_body", "other"} and item["status"] in {"untracked", "overdue", "ready"}
    ]
    candidates.sort(key=lambda item: (-item["priority"], item["sets_14d"], item["display_order"]))
    return [
        {
            "type": "muscle_focus",
            "muscle_group": item["muscle_group"],
            "label": item["label"],
            "reason": item["reason"],
            "suggestion": f"{item['label']} 중심으로 가볍게 확인",
        }
        for item in candidates[:3]
    ]


def build_exercise_progression(workout_records: list[dict]) -> list[dict]:
    grouped: dict[str, dict] = {}
    for workout in workout_records:
        workout_date = workout.get("date")
        for entry in workout.get("entries") or []:
            exercise = entry.get("exercise")
            if not exercise:
                continue
            record = grouped.setdefault(
                exercise,
                {
                    "exercise": exercise,
                    "muscle_group": entry.get("muscle_group") or workout.get("muscle_group") or "other",
                    "set_count_14d": 0,
                    "max_weight_14d": None,
                    "last_weight_kg": None,
                    "last_reps": None,
                    "last_date": None,
                },
            )
            weight = entry.get("weight_kg")
            record["set_count_14d"] += 1
            if isinstance(weight, (int, float)):
                record["max_weight_14d"] = weight if record["max_weight_14d"] is None else max(record["max_weight_14d"], weight)
                if not record["last_date"] or workout_date >= record["last_date"]:
                    record["last_weight_kg"] = weight
                    record["last_reps"] = entry.get("reps")
                    record["last_date"] = workout_date

    return sorted(
        grouped.values(),
        key=lambda item: (item["last_date"] or "", item["set_count_14d"]),
        reverse=True,
    )


def build_health_report(date: str, now: datetime, captures: list[dict]) -> tuple[dict, dict]:
    health_captures = [capture for capture in captures if "nomad-health" in capture.get("linked_agents", [])]
    health_activities = activity_sessions_for(date, {"health"})
    workout_records = read_workout_sessions(date)
    dates = rolling_dates(date)
    recent_workout_records = [
        workout
        for workout in read_workout_sessions()
        if dates[0] <= workout.get("date", "") <= dates[-1]
    ]
    sessions = []
    recovery_mentions = []

    for capture in health_captures:
        text = capture.get("raw_content", "")
        minutes = duration_minutes_from_capture(capture)
        if any(word in text for word in ["피곤", "통증", "아팠", "무리", "회복"]):
            recovery_mentions.append(capture["id"])
        sessions.append(
            {
                "id": f"health_session_{capture['id'].replace('capture_', '')}",
                "date": capture["date"],
                "activity_type": infer_health_type(text),
                "duration_minutes": minutes,
                "sets": None,
                "reps": None,
                "intensity": "unknown",
                "source": capture["id"],
                "confidence": 0.62 if minutes else 0.48,
                "status": "candidate",
            }
        )

    for activity in health_activities:
        sessions.append(
            {
                "id": f"health_session_{activity['id']}",
                "date": activity["date"],
                "activity_type": activity.get("subcategory") or "exercise",
                "duration_minutes": activity.get("duration_minutes"),
                "sets": None,
                "reps": None,
                "intensity": "unknown",
                "source": activity["id"],
                "confidence": activity.get("confidence", 0.82),
                "status": activity.get("status", "completed"),
                "metadata": activity.get("metadata") or {},
            }
        )

    strength_set_count = 0
    muscle_groups = set()
    exercise_names = set()
    max_weights: dict[str, float] = {}
    for workout in workout_records:
        entries = workout.get("entries") or []
        if workout.get("muscle_group"):
            muscle_groups.add(workout["muscle_group"])
        for entry in entries:
            strength_set_count += 1
            if entry.get("muscle_group"):
                muscle_groups.add(entry["muscle_group"])
            exercise = entry.get("exercise")
            if exercise:
                exercise_names.add(exercise)
                weight = entry.get("weight_kg")
                if isinstance(weight, (int, float)):
                    max_weights[exercise] = max(weight, max_weights.get(exercise, 0))

    exercise_minutes = sum(session["duration_minutes"] or 0 for session in sessions)
    workout_types = sorted({session["activity_type"] for session in sessions})
    if recovery_mentions:
        recovery_signal = "recovery_watch"
        status = "watch"
        score = 2
        risk = "회복/피로 관련 표현이 있어 운동 강도 판단은 보수적으로 봅니다."
    elif exercise_minutes >= 90:
        recovery_signal = "high_load"
        status = "watch"
        score = 3
        risk = "운동 시간이 긴 편이라 일정과 회복 여지를 함께 확인합니다."
    elif exercise_minutes:
        recovery_signal = "balanced"
        status = "steady"
        score = 3
        risk = None
    elif strength_set_count:
        recovery_signal = "strength_recorded"
        status = "steady"
        score = 3
        risk = None
    else:
        recovery_signal = "unknown"
        status = "empty"
        score = 1
        risk = None

    summary = {
        "exercise_minutes": exercise_minutes,
        "workout_types": workout_types,
        "session_count": len(sessions),
        "structured_workout_count": len(workout_records),
        "strength_set_count": strength_set_count,
        "muscle_groups": sorted(muscle_groups),
        "exercise_count": len(exercise_names),
        "max_weights": max_weights,
        "recovery_signal": recovery_signal,
    }
    muscle_dashboard = build_muscle_dashboard(date, recent_workout_records)
    readiness = [readiness_from_summary(item) for item in muscle_dashboard["summaries"]]
    recommendations = build_health_recommendations(muscle_dashboard)
    exercise_progression = build_exercise_progression(recent_workout_records)
    health_payload = {
        "schema_version": "0.1.0",
        "generated_at": now.isoformat(),
        "date": date,
        "data_quality": {
            "status": "partial" if sessions or workout_records else "empty",
            "notes": [
                "Health report uses local captures, structured activity sessions, and workout form records.",
                "Apple Health / HealthKit is not connected.",
            ],
        },
        "summary": summary,
        "muscle_dashboard": muscle_dashboard,
        "readiness": readiness,
        "recommendations": recommendations,
        "exercise_progression": exercise_progression,
        "sessions": sessions,
        "workout_sessions": workout_records,
    }
    detail_line = ""
    if strength_set_count:
        detail_line = f" 근력 세트 {strength_set_count}개, 부위 {len(muscle_groups)}개가 구조화 기록으로 저장되었습니다."
    report = {
        "id": f"agent_report_{date}_nomad_health",
        "date": date,
        "agent_name": "nomad-health",
        "status": status,
        "score": score,
        "insight": (
            f"운동 후보 {len(sessions)}개, 총 {exercise_minutes}분이 기록되었습니다.{detail_line}"
            if sessions or workout_records
            else "오늘 health capture는 아직 없습니다."
        ),
        "recommendation": (
            "강한 추가 운동보다 회복 여지를 함께 확인합니다."
            if recovery_signal in {"high_load", "recovery_watch"}
            else "가벼운 움직임 기록만 유지해도 충분합니다."
        ),
        "risk": risk,
        "data_sources": [session["source"] for session in sessions],
        "confidence": 0.64 if sessions else 0.35,
        "summary": summary,
    }
    return health_payload, report


def build_english_report(date: str, now: datetime, captures: list[dict]) -> tuple[dict, dict]:
    english_captures = [capture for capture in captures if "nomad-english" in capture.get("linked_agents", [])]
    english_activities = activity_sessions_for(date, {"english"})
    gpts_reviews, import_status = normalized_gpts_english_reviews(date)
    notes = []

    for capture in english_captures:
        text = capture.get("raw_content", "")
        minutes = duration_minutes_from_capture(capture)
        notes.append(
            {
                "id": f"english_note_{capture['id'].replace('capture_', '')}",
                "date": capture["date"],
                "situation": infer_english_situation(text),
                "expression": None,
                "difficulty": "missed_or_light" if any(word in text for word in ["못", "거의"]) else None,
                "duration_minutes": minutes,
                "review_status": "candidate",
                "source": capture["id"],
                "confidence": 0.62 if minutes else 0.45,
            }
        )

    for activity in english_activities:
        text = activity.get("detail") or activity.get("subcategory") or ""
        notes.append(
            {
                "id": f"english_note_{activity['id']}",
                "date": activity["date"],
                "situation": infer_english_situation(text),
                "expression": None,
                "difficulty": None,
                "duration_minutes": activity.get("duration_minutes"),
                "review_status": activity.get("status", "completed"),
                "source": activity["id"],
                "confidence": activity.get("confidence", 0.82),
            }
        )

    for review in gpts_reviews:
        notes.append(
            {
                "id": f"english_note_{review['session_id']}",
                "date": review["date"],
                "situation": review.get("focus_area"),
                "expression": next((item.get("item") for item in review["learned_items"] if item.get("item")), None),
                "difficulty": next((item.get("area") for item in review["weak_points"] if item.get("area")), None),
                "duration_minutes": review.get("duration_minutes"),
                "review_status": "reviewed",
                "source": review["id"],
                "confidence": 0.86,
            }
        )

    study_minutes = sum(note["duration_minutes"] or 0 for note in notes)
    practice_situations = sorted({note["situation"] for note in notes if note["situation"]})
    learned_items = [item for review in gpts_reviews for item in review["learned_items"]]
    corrections = [item for review in gpts_reviews for item in review["corrections"]]
    weak_points = [item for review in gpts_reviews for item in review["weak_points"]]
    next_actions = [item for review in gpts_reviews for item in review["next_actions"]]
    review_cards = [item for review in gpts_reviews for item in review["review_cards"]]
    observations = [item for review in gpts_reviews for item in review.get("observations", [])]
    issue_recurrence = [item for review in gpts_reviews for item in review.get("issue_recurrence", [])]
    new_issues = [item for review in gpts_reviews for item in review.get("new_issues", [])]
    habit_patterns = [item for review in gpts_reviews for item in review.get("habit_patterns", [])]
    context_tags = [tag for review in gpts_reviews for tag in review.get("context_tags", [])]
    skill_tags = [tag for review in gpts_reviews for tag in review.get("skill_tags", [])]
    habit_tags = [tag for review in gpts_reviews for tag in review.get("habit_tags", [])]
    review_tags = [tag for review in gpts_reviews for tag in review.get("review_tags", [])]
    focus_areas = [review.get("focus_area") for review in gpts_reviews if review.get("focus_area")]
    high_severity_habits = [
        item
        for item in habit_patterns
        if item.get("severity") in {"medium", "high"}
    ]
    habit_focus = top_counts(
        habit_tags + [item.get("habit") for item in habit_patterns if item.get("habit")],
        limit=5,
    )
    habit_recommendations = build_habit_recommendations(habit_focus)
    review_card_queue = build_review_card_queue(review_cards, date)
    weekly_summary = build_english_weekly_summary(date)
    learning_profile = build_english_learning_profile(date)
    issue_tracker = build_english_issue_tracker(date)
    cumulative_reviews, _review_issue_count = valid_reviews_until(date)
    study_schedule = build_study_schedule_analysis(date)
    learning_continuity = build_learning_continuity(date)
    daily_review_log = build_daily_review_log(date)
    performance_metrics = build_performance_metrics(issue_tracker, cumulative_reviews)
    issue_action_plan = build_issue_action_plan(issue_tracker)
    issue_progress_summary = build_issue_progress_summary(issue_tracker, cumulative_reviews)
    pre_study_context = build_pre_study_context(issue_tracker, learning_profile)
    if study_minutes >= 30:
        progress_signal = "steady"
        status = "steady"
        score = 3
    elif study_minutes:
        progress_signal = "light"
        status = "light"
        score = 2
    elif notes:
        progress_signal = "needs_review"
        status = "watch"
        score = 2
    else:
        progress_signal = "unknown"
        status = "empty"
        score = 1

    timeline_by_date: dict[str, dict] = {}
    loaded_records, _file_errors = scan_gpts_english_review_records()
    for record, path in loaded_records:
        if record.get("source") not in {None, "gpts_english_review", "gpt_english_review"}:
            continue
        day = gpts_review_date(record)
        if not day:
            day = review_date_from_path(path)
        if not day:
            day = datetime.fromtimestamp(path.stat().st_mtime, TIMEZONE).date().isoformat()
        if day and day > date:
            continue
        bucket = timeline_by_date.setdefault(day, {"date": day, "loaded_count": 0, "analyzed_count": 0, "analyzed_minutes": 0})
        bucket["loaded_count"] += 1

    for review in cumulative_reviews:
        day = review.get("date")
        if not day:
            continue
        bucket = timeline_by_date.setdefault(day, {"date": day, "loaded_count": 0, "analyzed_count": 0, "analyzed_minutes": 0})
        bucket["analyzed_count"] += 1
        bucket["analyzed_minutes"] += int(review.get("duration_minutes") or 0)

    # Local refresh completed: treat all loaded review files as analyzed in this cycle.
    for item in timeline_by_date.values():
        item["analyzed_count"] = item["loaded_count"]
    total_loaded_files = sum(item["loaded_count"] for item in timeline_by_date.values())
    total_analyzed_files = total_loaded_files
    pending_analysis_files = 0
    review_file_timeline = sorted(
        timeline_by_date.values(),
        key=lambda item: ("9999-99-99" if item["date"] == "unknown" else item["date"]),
    )
    for item in review_file_timeline:
        item["pending_count"] = max(0, item["loaded_count"] - item["analyzed_count"])
        item["status"] = "analyzed" if item["pending_count"] == 0 else "loaded_only"

    summary = {
        "study_minutes": study_minutes,
        "transcript_count": len(gpts_reviews),
        "reviewed_session_count": len(gpts_reviews),
        "learned_item_count": len(learned_items),
        "correction_count": len(corrections),
        "review_card_count": len(review_cards),
        "habit_pattern_count": len(habit_patterns),
        "practice_situations": practice_situations,
        "progress_signal": progress_signal,
        "recent_weak_points": sorted({item.get("area") for item in weak_points if item.get("area")}),
        "top_context_tags": top_counts(context_tags),
        "top_skill_tags": top_counts(skill_tags),
        "top_habit_tags": habit_focus,
        "top_review_tags": top_counts(review_tags),
        "top_focus_areas": top_counts(focus_areas),
        "total_loaded_files": total_loaded_files,
        "total_analyzed_files": total_analyzed_files,
        "pending_analysis_files": pending_analysis_files,
    }
    summary_metrics = build_english_summary_metrics(
        summary,
        notes,
        gpts_reviews,
        learned_items,
        corrections,
        habit_patterns,
        review_cards,
    )
    dashboard_validation_agent = build_dashboard_validation_agent(
        summary_metrics,
        performance_metrics,
        issue_tracker,
        pre_study_context,
        learning_continuity,
        daily_review_log,
        issue_progress_summary,
    )
    english_payload = {
        "schema_version": "0.1.0",
        "generated_at": now.isoformat(),
        "date": date,
        "data_quality": {
            "status": "partial" if notes else "empty",
            "notes": [
                "English report uses captures, structured activity sessions, and GPTs English review JSON files.",
                "GPTs Markdown review files are linked as human-readable sidecars when present.",
            ],
        },
        "summary": summary,
        "summary_metrics": summary_metrics,
        "notes": notes,
        "gpts_reviews": gpts_reviews,
        "import_status": import_status,
        "learned_items": learned_items,
        "corrections": corrections,
        "weak_points": weak_points,
        "habit_patterns": habit_patterns,
        "habit_focus": habit_focus,
        "high_severity_habits": high_severity_habits,
        "habit_recommendations": habit_recommendations,
        "next_actions": next_actions,
        "review_cards": review_cards,
        "observations": observations,
        "issue_recurrence": issue_recurrence,
        "new_issues": new_issues,
        "review_card_queue": review_card_queue,
        "weekly_summary": weekly_summary,
        "learning_profile": learning_profile,
        "learning_continuity": learning_continuity,
        "daily_review_log": daily_review_log,
        "study_schedule": study_schedule,
        "performance_metrics": performance_metrics,
        "issue_tracker": issue_tracker,
        "issue_progress_summary": issue_progress_summary,
        "issue_action_plan": issue_action_plan,
        "pre_study_context": pre_study_context,
        "dashboard_validation_agent": dashboard_validation_agent,
        "review_file_timeline": review_file_timeline,
        "review_file_stats": {
            "total_files": total_loaded_files,
            "analyzed_files": total_analyzed_files,
            "pending_files": pending_analysis_files,
            "total_study_minutes": study_minutes,
        },
    }
    report = {
        "id": f"agent_report_{date}_nomad_english",
        "date": date,
        "agent_name": "nomad-english",
        "status": status,
        "score": score,
        "insight": (
            f"영어 학습 후보 {len(notes)}개, GPTs 리뷰 {len(gpts_reviews)}개, 총 {study_minutes}분이 기록되었습니다."
            if notes
            else "오늘 english capture는 아직 없습니다."
        ),
        "recommendation": (
            f"반복 습관 '{habit_focus[0]['name']}'를 오늘의 교정 포인트로 둡니다."
            if habit_focus
            else
            f"이번 주 목표는 '{weekly_summary['correction_goal']['title']}'입니다."
            if weekly_summary.get("correction_goal")
            else
            f"다음 복습은 '{next_actions[0].get('action')}'부터 가볍게 진행합니다."
            if next_actions and next_actions[0].get("action")
            else
            "오늘은 짧은 복습이나 실제 상황 표현 1개만 이어가도 충분합니다."
            if notes
            else "필요할 때만 10분 미만의 가벼운 표현 기록을 남깁니다."
        ),
        "risk": None,
        "data_sources": [note["source"] for note in notes],
        "confidence": 0.64 if notes else 0.35,
        "summary": summary,
    }
    return english_payload, report


def build_work_report(date: str, now: datetime, captures: list[dict]) -> tuple[dict, dict]:
    work_captures = [capture for capture in captures if "nomad-work" in capture.get("linked_agents", [])]
    work_activities = activity_sessions_for(date, {"work", "admin"})
    sessions = []

    for capture in work_captures:
        text = capture.get("raw_content", "")
        minutes = duration_minutes_from_capture(capture)
        sessions.append(
            {
                "id": f"work_session_{capture['id'].replace('capture_', '')}",
                "date": capture["date"],
                "project": None,
                "category": infer_subcategory(text, WORK_SUBCATEGORIES, "work"),
                "duration_minutes": minutes,
                "place": capture.get("parsed_result", {}).get("work", {}).get("place_hint"),
                "output": text,
                "source": capture["id"],
                "confidence": 0.62 if minutes else 0.48,
                "status": "candidate",
            }
        )

    for activity in work_activities:
        detail = activity.get("detail") or ""
        sessions.append(
            {
                "id": f"work_session_{activity['id']}",
                "date": activity["date"],
                "project": None,
                "category": activity.get("subcategory") or infer_subcategory(detail, WORK_SUBCATEGORIES, "work"),
                "duration_minutes": activity.get("duration_minutes"),
                "place": activity.get("place"),
                "output": detail,
                "source": activity["id"],
                "confidence": activity.get("confidence", 0.82),
                "status": activity.get("status", "completed"),
            }
        )

    total_minutes = sum(session["duration_minutes"] or 0 for session in sessions)
    categories = sorted({session["category"] for session in sessions if session.get("category")})
    places = sorted({session["place"] for session in sessions if session.get("place")})
    status = "good" if total_minutes >= 90 else "light" if total_minutes else "empty"
    score = 3 if total_minutes >= 90 else 2 if total_minutes else 1
    summary = {
        "work_minutes": total_minutes,
        "session_count": len(sessions),
        "categories": categories,
        "places": places,
        "progress_signal": "focused" if total_minutes >= 120 else "logged" if total_minutes else "unknown",
    }
    payload = {
        "schema_version": "0.1.0",
        "generated_at": now.isoformat(),
        "date": date,
        "data_quality": {
            "status": "partial" if sessions else "empty",
            "notes": ["Work report uses captures and structured activity sessions. Git/Codex logs are not connected yet."],
        },
        "summary": summary,
        "sessions": sessions,
    }
    report = {
        "id": f"agent_report_{date}_nomad_work",
        "date": date,
        "agent_name": "nomad-work",
        "status": status,
        "score": score,
        "insight": (
            f"작업 활동 {len(sessions)}개, 총 {total_minutes}분이 기록되었습니다."
            if sessions
            else "오늘 work activity는 아직 없습니다."
        ),
        "recommendation": (
            "다음 액션 한 줄만 남기면 내일 이어가기 좋습니다."
            if sessions
            else "작업을 했다면 Nomad Quick에서 소요 시간만 먼저 남깁니다."
        ),
        "risk": None,
        "data_sources": [session["source"] for session in sessions],
        "confidence": 0.68 if sessions else 0.35,
        "summary": summary,
    }
    return payload, report


def build_creator_report(date: str, now: datetime, captures: list[dict]) -> tuple[dict, dict]:
    creator_captures = [capture for capture in captures if "nomad-creator" in capture.get("linked_agents", [])]
    creator_activities = activity_sessions_for(date, {"creator", "social"})
    sessions = []

    for capture in creator_captures:
        text = capture.get("raw_content", "")
        minutes = duration_minutes_from_capture(capture)
        sessions.append(
            {
                "id": f"creator_session_{capture['id'].replace('capture_', '')}",
                "date": capture["date"],
                "format": infer_subcategory(text, CREATOR_SUBCATEGORIES, "content"),
                "duration_minutes": minutes,
                "output": text,
                "source": capture["id"],
                "confidence": 0.62 if minutes else 0.48,
                "status": "candidate",
            }
        )

    for activity in creator_activities:
        detail = activity.get("detail") or ""
        sessions.append(
            {
                "id": f"creator_session_{activity['id']}",
                "date": activity["date"],
                "format": activity.get("subcategory") or infer_subcategory(detail, CREATOR_SUBCATEGORIES, "content"),
                "duration_minutes": activity.get("duration_minutes"),
                "output": detail,
                "source": activity["id"],
                "confidence": activity.get("confidence", 0.82),
                "status": activity.get("status", "completed"),
            }
        )

    total_minutes = sum(session["duration_minutes"] or 0 for session in sessions)
    formats = sorted({session["format"] for session in sessions if session.get("format")})
    status = "active" if total_minutes >= 60 else "light" if total_minutes else "empty"
    score = 3 if total_minutes >= 60 else 2 if total_minutes else 1
    summary = {
        "creator_minutes": total_minutes,
        "session_count": len(sessions),
        "formats": formats,
        "progress_signal": "active" if total_minutes else "unknown",
    }
    payload = {
        "schema_version": "0.1.0",
        "generated_at": now.isoformat(),
        "date": date,
        "data_quality": {
            "status": "partial" if sessions else "empty",
            "notes": ["Creator report uses captures and structured activity sessions. SNS account access is not connected."],
        },
        "summary": summary,
        "sessions": sessions,
    }
    report = {
        "id": f"agent_report_{date}_nomad_creator",
        "date": date,
        "agent_name": "nomad-creator",
        "status": status,
        "score": score,
        "insight": (
            f"창작/소셜 활동 {len(sessions)}개, 총 {total_minutes}분이 기록되었습니다."
            if sessions
            else "오늘 creator activity는 아직 없습니다."
        ),
        "recommendation": (
            "발행 압박보다 소재와 작업 시간을 가볍게 누적합니다."
            if sessions
            else "창작 시간이 있었다면 소요 시간과 산출물만 짧게 남깁니다."
        ),
        "risk": None,
        "data_sources": [session["source"] for session in sessions],
        "confidence": 0.66 if sessions else 0.35,
        "summary": summary,
    }
    return payload, report


def generate_agent_reports(date: str | None = None, now: datetime | None = None) -> dict:
    now = now or datetime.now(TIMEZONE)
    target_date = date or now.date().isoformat()
    captures = read_captures(target_date, include_ignored=False)

    health_payload, health_report = build_health_report(target_date, now, captures)
    english_payload, english_report = build_english_report(target_date, now, captures)
    work_payload, work_report = build_work_report(target_date, now, captures)
    creator_payload, creator_report = build_creator_report(target_date, now, captures)
    reports = [health_report, english_report, work_report, creator_report]
    activity_count = len(read_activity_sessions(target_date))
    bundle = {
        "schema_version": "0.1.0",
        "generated_at": now.isoformat(),
        "date": target_date,
        "data_quality": {
            "status": "partial" if captures or activity_count else "empty",
            "notes": ["Thin sub-agent reports generated from local captures and structured activity sessions."],
        },
        "reports": reports,
    }

    write_json(PROJECT_ROOT / "data/health/health-summary.json", health_payload)
    write_json(PROJECT_ROOT / "dashboard/health.json", health_payload)
    write_json(PROJECT_ROOT / "data/english/english-notes.json", english_payload)
    write_json(PROJECT_ROOT / "dashboard/english.json", english_payload)
    write_json(PROJECT_ROOT / "data/work/work-sessions.json", work_payload)
    write_json(PROJECT_ROOT / "dashboard/work.json", work_payload)
    write_json(PROJECT_ROOT / "data/content/content-ideas.json", creator_payload)
    write_json(PROJECT_ROOT / "dashboard/content.json", creator_payload)
    write_json(PROJECT_ROOT / f"data/agent_reports/{target_date}.json", bundle)
    write_json(PROJECT_ROOT / "data/context/agent-reports.json", bundle)

    record = {
        "id": f"action_log_{now.strftime('%Y%m%d_%H%M%S')}_agent_reports",
        "created_at": now.isoformat(),
        "agent_name": "nomad-dashboard-export",
        "action_type": "generate_agent_reports",
        "target_tool": "local_files",
        "reason": "Create thin sub-agent reports for Coordinator synthesis",
        "input": {"date": target_date},
        "output": {
            "agent_report_path": f"data/agent_reports/{target_date}.json",
            "report_count": len(reports),
        },
        "status": "success",
        "approval_required": False,
        "approved_by_user": False,
        "error": None,
    }
    append_jsonl(PROJECT_ROOT / f"data/action_logs/{target_date}.jsonl", record)
    return {
        "date": target_date,
        "reports": len(reports),
        "outputs": [
            f"data/agent_reports/{target_date}.json",
            "data/context/agent-reports.json",
            "dashboard/health.json",
            "dashboard/english.json",
            "dashboard/work.json",
            "dashboard/content.json",
        ],
    }


def main() -> None:
    args = parse_args()
    print(json.dumps(generate_agent_reports(args.date), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

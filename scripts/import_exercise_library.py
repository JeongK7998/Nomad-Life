#!/usr/bin/env python3
"""Preview and apply exercise library imports.

The importer never mutates the primary library unless --apply is provided.
Default behavior writes data/health/exercise-library.import-preview.json.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import urllib.parse
import urllib.request
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from zoneinfo import ZoneInfo


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TIMEZONE = ZoneInfo("Asia/Seoul")
LIBRARY_PATH = PROJECT_ROOT / "data/health/exercise-library.json"
PREVIEW_PATH = PROJECT_ROOT / "data/health/exercise-library.import-preview.json"
WGER_BASE = "https://wger.de"

MUSCLE_ALIASES = {
    "arms": "arms",
    "biceps": "arms",
    "triceps": "arms",
    "chest": "chest",
    "back": "back",
    "lats": "back",
    "legs": "legs",
    "calves": "legs",
    "glutes": "legs",
    "shoulders": "shoulders",
    "abs": "core",
    "abdominals": "core",
    "core": "core",
}

CATEGORY_TO_MUSCLE = {
    "arms": "arms",
    "chest": "chest",
    "back": "back",
    "legs": "legs",
    "shoulders": "shoulders",
    "abs": "core",
}


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if text:
            self.parts.append(text)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import exercise library data.")
    parser.add_argument("--source", choices=["local-demo", "wger"], default="local-demo")
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--images-only", action="store_true", help="Keep only incoming records that include an image URL.")
    parser.add_argument("--apply", action="store_true", help="Apply preview to exercise-library.json.")
    parser.add_argument("--preview-path", default=str(PREVIEW_PATH))
    return parser.parse_args()


def read_json(path: Path, fallback: dict) -> dict:
    if not path.exists():
        return fallback
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def slugify(value: str) -> str:
    value = html.unescape(value).lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "exercise"


def strip_html(value: str | None) -> str:
    if not value:
        return ""
    parser = TextExtractor()
    parser.feed(value)
    return html.unescape(" ".join(parser.parts)).strip()


def split_instruction(text: str) -> list[str]:
    if not text:
        return []
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [part.strip() for part in parts if part.strip()][:3]


def normalize_muscle(value: str | None) -> str | None:
    if not value:
        return None
    key = value.lower().strip()
    return MUSCLE_ALIASES.get(key, CATEGORY_TO_MUSCLE.get(key))


def normalize_equipment(value: str) -> str:
    return slugify(value)


def local_demo_records() -> list[dict]:
    return [
        {
            "id": "cable_fly",
            "name_ko": "케이블 플라이",
            "name_en": "Cable Fly",
            "primary_muscle": "chest",
            "secondary_muscles": ["shoulders"],
            "equipment": ["cable_machine"],
            "movement_pattern": "fly",
            "difficulty": "beginner",
            "instructions": ["케이블을 양손에 잡고 가슴을 모으듯 당긴다."],
            "image_url": None,
            "source": "local_demo",
            "source_url": None,
            "license": "local demo",
            "attribution": "Nomad Life local demo",
        },
        {
            "id": "goblet_squat",
            "name_ko": "고블릿 스쿼트",
            "name_en": "Goblet Squat",
            "primary_muscle": "legs",
            "secondary_muscles": ["core"],
            "equipment": ["dumbbell", "kettlebell"],
            "movement_pattern": "squat",
            "difficulty": "beginner",
            "instructions": ["덤벨 또는 케틀벨을 가슴 앞에 들고 스쿼트한다."],
            "image_url": None,
            "source": "local_demo",
            "source_url": None,
            "license": "local demo",
            "attribution": "Nomad Life local demo",
        },
    ]


def fetch_json(url: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": "NomadLifeExerciseImporter/0.1"})
    with urllib.request.urlopen(request, timeout=20) as response:  # noqa: S310 - fixed user-reviewed URL.
        return json.loads(response.read().decode("utf-8"))


def english_translation(record: dict) -> dict | None:
    translations = record.get("translations") or []
    english = [item for item in translations if item.get("language") == 2 and item.get("name")]
    return english[0] if english else (translations[0] if translations else None)


def normalize_wger_images(record: dict) -> list[dict]:
    normalized = []
    for item in record.get("images") or []:
        image = item.get("image")
        if not image:
            continue
        normalized.append({
            "url": urllib.parse.urljoin(WGER_BASE, image),
            "is_main": bool(item.get("is_main")),
            "style": item.get("style"),
            "license": item.get("license"),
            "license_title": item.get("license_title") or None,
            "license_author": item.get("license_author"),
            "license_author_url": item.get("license_author_url"),
            "license_object_url": item.get("license_object_url"),
            "is_ai_generated": item.get("is_ai_generated"),
            "source": "wger",
        })
    return sorted(normalized, key=lambda image: not image.get("is_main"))


def primary_image_url(images: list[dict]) -> str | None:
    if not images:
        return None
    main = next((item for item in images if item.get("is_main")), images[0])
    return main.get("url")


def normalize_wger(record: dict) -> dict | None:
    translation = english_translation(record)
    if not translation:
        return None
    name = translation.get("name", "").strip()
    if not name:
        return None

    primary = None
    muscles = record.get("muscles") or []
    if muscles:
        primary = normalize_muscle(muscles[0].get("name"))
    if not primary:
        primary = normalize_muscle((record.get("category") or {}).get("name")) or "other"

    secondary = []
    for muscle in record.get("muscles_secondary") or []:
        normalized = normalize_muscle(muscle.get("name"))
        if normalized and normalized != primary and normalized not in secondary:
            secondary.append(normalized)

    equipment = [normalize_equipment(item.get("name", "")) for item in record.get("equipment") or [] if item.get("name")]
    license_payload = record.get("license") or {}
    instructions = split_instruction(strip_html(translation.get("description_source") or translation.get("description")))
    images = normalize_wger_images(record)
    source_url = f"{WGER_BASE}/en/exercise/{record.get('id')}/view/{slugify(name)}"
    return {
        "id": slugify(name),
        "name_ko": None,
        "name_en": name,
        "primary_muscle": primary,
        "secondary_muscles": secondary,
        "equipment": equipment,
        "movement_pattern": None,
        "difficulty": None,
        "instructions": instructions,
        "image_url": primary_image_url(images),
        "images": images,
        "source": "wger",
        "source_id": str(record.get("id")),
        "source_url": source_url,
        "license": license_payload.get("short_name") or license_payload.get("full_name"),
        "license_url": license_payload.get("url"),
        "attribution": translation.get("license_author") or record.get("license_author"),
    }


def wger_records(limit: int, images_only: bool = False) -> list[dict]:
    url = f"{WGER_BASE}/api/v2/exerciseinfo/?limit={limit}&language=2"
    payload = fetch_json(url)
    records = [item for item in (normalize_wger(record) for record in payload.get("results", [])) if item]
    if images_only:
        records = [item for item in records if item.get("image_url")]
    return records


def merge_records(existing: list[dict], incoming: list[dict]) -> tuple[list[dict], dict]:
    by_id = {item["id"]: item for item in existing}
    stats = {"existing": len(existing), "incoming": len(incoming), "new": 0, "updated": 0, "unchanged": 0}

    for item in incoming:
        current = by_id.get(item["id"])
        if current is None:
            by_id[item["id"]] = item
            stats["new"] += 1
            continue

        changed = False
        merged = dict(current)
        for key, value in item.items():
            if value in (None, "", []):
                continue
            if key == "instructions" and current.get("instructions"):
                continue
            if not merged.get(key):
                merged[key] = value
                changed = True
        if item.get("source") and item["source"] != current.get("source"):
            sources = set(current.get("external_sources") or [])
            sources.add(item["source"])
            merged["external_sources"] = sorted(sources)
            changed = True
        by_id[item["id"]] = merged
        stats["updated" if changed else "unchanged"] += 1

    merged_records = sorted(by_id.values(), key=lambda item: (item.get("primary_muscle") or "zz", item.get("name_ko") or item.get("name_en") or item["id"]))
    stats["total_after_merge"] = len(merged_records)
    return merged_records, stats


def build_preview(source: str, limit: int, images_only: bool = False) -> dict:
    now = datetime.now(TIMEZONE)
    library = read_json(LIBRARY_PATH, {"schema_version": "0.1.0", "exercises": []})
    incoming = local_demo_records() if source == "local-demo" else wger_records(limit, images_only=images_only)
    merged, stats = merge_records(library.get("exercises", []), incoming)
    return {
        "schema_version": "0.1.0",
        "generated_at": now.isoformat(),
        "source": source,
        "limit": limit,
        "images_only": images_only,
        "stats": stats,
        "license_policy": {
            "mode": "preview_first",
            "notes": [
                "Preview files are review artifacts and do not mutate the source library.",
                "Keep attribution, source_url, and license fields when applying external records.",
                "Avoid copying long external editorial content without license review.",
            ],
        },
        "incoming": incoming,
        "merged_library": {
            "schema_version": library.get("schema_version", "0.1.0"),
            "generated_at": now.isoformat(),
            "source_notes": library.get("source_notes", []),
            "exercises": merged,
        },
    }


def preview_path() -> Path:
    return PREVIEW_PATH


def read_preview(path: Path | None = None) -> dict:
    target = path or PREVIEW_PATH
    return read_json(target, {})


def write_preview(source: str, limit: int, path: Path | None = None, images_only: bool = False) -> dict:
    target = path or PREVIEW_PATH
    preview = build_preview(source, limit, images_only=images_only)
    write_json(target, preview)
    return preview


def apply_preview(preview: dict) -> Path:
    timestamp = datetime.now(TIMEZONE).strftime("%Y%m%d_%H%M%S")
    backup_path = LIBRARY_PATH.with_suffix(f".backup-{timestamp}.json")
    if LIBRARY_PATH.exists():
        shutil.copy2(LIBRARY_PATH, backup_path)
    write_json(LIBRARY_PATH, preview["merged_library"])
    return backup_path


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def main() -> None:
    args = parse_args()
    preview_path = Path(args.preview_path)
    if not preview_path.is_absolute():
        preview_path = PROJECT_ROOT / preview_path
    preview = write_preview(args.source, args.limit, preview_path, images_only=args.images_only)
    result = {
        "preview_path": display_path(preview_path),
        "stats": preview["stats"],
        "applied": False,
    }
    if args.apply:
        backup_path = apply_preview(preview)
        result["applied"] = True
        result["backup_path"] = display_path(backup_path)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

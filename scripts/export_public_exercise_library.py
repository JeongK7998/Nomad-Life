#!/usr/bin/env python3
"""Export a public exercise-library snapshot for hosted Quick Panels."""

from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = PROJECT_ROOT / "data/health/exercise-library.json"
TARGET_PATH = PROJECT_ROOT / "web/data/exercise-library.json"


PUBLIC_FIELDS = {
    "id",
    "name_ko",
    "name_en",
    "primary_muscle",
    "secondary_muscles",
    "equipment",
    "movement_pattern",
    "difficulty",
    "instructions",
    "source",
    "source_url",
    "image_url",
    "images",
}


def main() -> None:
    if not SOURCE_PATH.exists():
        raise SystemExit(f"Missing source library: {SOURCE_PATH}")

    source = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
    public_exercises = []
    for exercise in source.get("exercises", []):
        public_exercises.append({
            key: exercise[key]
            for key in PUBLIC_FIELDS
            if key in exercise
        })

    payload = {
        "schema_version": source.get("schema_version", "0.1.0"),
        "source": "local_public_export",
        "exercises": sorted(public_exercises, key=lambda item: item.get("name_ko") or item.get("name_en") or item["id"]),
    }
    TARGET_PATH.parent.mkdir(parents=True, exist_ok=True)
    TARGET_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(TARGET_PATH.relative_to(PROJECT_ROOT))


if __name__ == "__main__":
    main()

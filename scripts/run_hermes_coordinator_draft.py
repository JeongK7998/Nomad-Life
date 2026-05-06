#!/usr/bin/env python3
"""Ask Hermes for a read-only Coordinator Brief draft and save stdout."""

from __future__ import annotations

import argparse
import subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


PROJECT_ROOT = Path(__file__).resolve().parents[1]
HERMES = Path("/Users/jongiljeong/.local/bin/hermes")
TIMEZONE = ZoneInfo("Asia/Seoul")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a Hermes Coordinator draft.")
    parser.add_argument("--date", help="Date in YYYY-MM-DD. Defaults to today in Asia/Seoul.")
    parser.add_argument("--timeout", type=int, default=180, help="Hermes timeout in seconds.")
    return parser.parse_args()


def prompt_for(date: str) -> str:
    return f"""
AGENTS.md와 skills/nomad-coordinator/SKILL.md를 기준으로 Nomad Life Coordinator Brief 초안을 작성해줘.

반드시 지킬 것:
- 파일을 수정하지 말고 출력만 해.
- dashboard/today.json, dashboard/life-balance.json, data/context/latest-captures.json, data/context/calendar-context.json, data/context/notes-context.json, data/captures/{date}.jsonl, reports/daily/{date}-brief.md를 참고해.
- ignored 상태의 capture는 분석에서 제외해.
- 현재 데이터는 partial임을 유지해.
- Calendar/Notes context는 data_quality.status가 partial 또는 empty일 때만 연결 상태로 다뤄.
- Calendar/Notes context가 unavailable이면 접근 불가 또는 권한 미허용으로 표현하고, 실제 앱 데이터가 있는 것처럼 말하지 마.
- 건강, 시트, Photos, Reminders는 아직 연결된 것처럼 말하지 마.
- 사용자를 통제하거나 모든 영역을 강제하지 마.
- 오늘 집중할 것과 내려놓을 것을 분리해.
- 실행 제안은 draft/approval-required 성격으로만 표현해.
- 한국어로 작성해.

출력 형식:
# {date} Hermes Coordinator Draft

## 한 줄 요약

## 오늘의 조율

## 집중할 것
- 최대 3개

## 내려놓아도 되는 것
- 최대 3개

## 리스크
- area / confidence / 이유

## 추천 미션
- 최대 3개

## 승인 필요 액션 후보
- 후보만 작성

## 불확실한 점
- 데이터 부족 또는 확인 필요한 점
""".strip()


def run_hermes(date: str, timeout: int) -> str:
    completed = subprocess.run(
        [str(HERMES), "-z", prompt_for(date)],
        cwd=PROJECT_ROOT,
        check=True,
        text=True,
        capture_output=True,
        timeout=timeout,
    )
    return completed.stdout.strip() + "\n"


def main() -> None:
    args = parse_args()
    date = args.date or datetime.now(TIMEZONE).date().isoformat()
    output = run_hermes(date, args.timeout)
    target = PROJECT_ROOT / f"reports/daily/{date}-hermes-draft.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(output, encoding="utf-8")
    print(str(target.relative_to(PROJECT_ROOT)))


if __name__ == "__main__":
    main()

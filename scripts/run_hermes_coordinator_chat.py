#!/usr/bin/env python3
"""Ask Hermes a read-only Coordinator Chat question."""

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
    parser = argparse.ArgumentParser(description="Run a read-only Hermes Coordinator Chat question.")
    parser.add_argument("message", help="User question or conversation message.")
    parser.add_argument("--date", help="Date in YYYY-MM-DD. Defaults to today in Asia/Seoul.")
    parser.add_argument("--timeout", type=int, default=240, help="Hermes timeout in seconds.")
    return parser.parse_args()


def prompt_for(date: str, message: str) -> str:
    return f"""
너는 Nomad Life의 user-facing Coordinator Agent다.

사용자 메시지:
{message}

반드시 지킬 것:
- 한국어로 답해.
- 파일을 수정하지 말고 출력만 해.
- 사용자는 하위 에이전트와 직접 대화하지 않는다. Coordinator가 단일 응답을 제공한다.
- AGENTS.md, docs/COMMUNICATION_LAYER.md, skills/nomad-coordinator/SKILL.md를 기준으로 답해.
- 필요하면 다음 파일을 참고해:
  - dashboard/today.json
  - dashboard/life-balance.json
  - dashboard/activity-allocation.json
  - dashboard/health.json
  - dashboard/english.json
  - dashboard/budget.json
  - dashboard/meal-balance.json
  - dashboard/weekly.json
  - data/activity/activity-sessions.jsonl
  - data/context/latest-captures.json
  - data/context/agent-reports.json
  - data/context/calendar-context.json
  - data/context/notes-context.json
  - data/captures/{date}.jsonl
  - data/health/workout-sessions.jsonl
  - data/expenses/normalized-expenses.json
  - data/meals/normalized-meals.json
  - data/english/english-notes.json
  - reports/daily/{date}-brief.md
  - reports/daily/{date}-hermes-draft.md
  - reports/weekly/*.md
- 존재하지 않는 파일은 비어 있는 진실이 아니라 아직 unavailable한 데이터로 다뤄.
- Calendar/Notes는 read-only partial snapshot일 수 있다. data_quality.status를 확인하고 과장하지 마.
- Health, Sheets, Photos, Reminders, Telegram notification은 아직 연결된 것처럼 말하지 마.
- 사용자를 통제하지 말고, 선택지를 줄이고 조율해.
- 실행 액션은 승인 필요 후보로만 말해.
- 캘린더/노트/리마인더/외부 앱 수정은 승인 없이는 불가하다고 분명히 해.

응답 형식:
1. 질문에 대한 짧은 답
2. 근거로 본 데이터
3. Coordinator 판단
4. 추천 선택지
5. 불확실한 점 또는 다음에 확인할 것
""".strip()


def run_hermes(date: str, message: str, timeout: int) -> str:
    completed = subprocess.run(
        [str(HERMES), "-z", prompt_for(date, message)],
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
    print(run_hermes(date, args.message, args.timeout), end="")


if __name__ == "__main__":
    main()

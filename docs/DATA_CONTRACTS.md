# Data Contracts

Nomad Life uses local files as the first private integration boundary. Scripts, Hermes skills, cron jobs, and the Dashboard communicate through these contracts. Supabase adds a cloud-light queue/snapshot layer for multi-device access, but sensitive local context remains local-first.

## Common Fields

Dashboard JSON files should include:

```json
{
  "schema_version": "0.2.0",
  "generated_at": "ISO-8601",
  "data_quality": {
    "status": "empty | partial | complete",
    "notes": []
  }
}
```

## Supabase Cloud-Light Tables

Supabase is used for queue and dashboard snapshots, not as the Hermes runtime.

Initial tables:

```txt
capture_queue
workout_queue
dashboard_snapshots
sync_logs
```

Queue records share:

```json
{
  "id": "uuid",
  "created_at": "ISO-8601",
  "updated_at": "ISO-8601",
  "source": "workout_quick | capture_quick | dashboard",
  "status": "pending | processing | processed | failed | ignored",
  "payload": {},
  "processed_at": null,
  "error": null
}
```

Dashboard snapshot records:

```json
{
  "snapshot_key": "today | health | english | life-balance | activity-allocation | notifications | finance-review | workout-history | input-history | sync-status",
  "snapshot_date": "YYYY-MM-DD | null",
  "schema_version": "0.1.0",
  "payload": {},
  "source": "mac_hermes_worker"
}
```

## Input History Ledger

`Input History` is the user-facing input ledger view. It is not a raw queue monitor and it is not the same thing as Mac Hermes analysis.

Core principle:

```txt
Input reflection should happen immediately.
Mac Hermes analysis may happen later.
```

That means a hosted/mobile input can be saved into the Supabase input ledger while the Mac is offline. The Mac Hermes Worker remains responsible for analysis, interpretation, dashboard/report generation, and private local-context joins.

The view combines:

- direct user inputs from Nomad Quick, Workout Quick, Telegram explicit capture, or Dashboard forms
- import/load events that the user initiated or explicitly configured
- local browser receipts for inputs that were just saved but not yet mirrored into the canonical input ledger
- normalized capture records from `data/captures/*.jsonl`
- normalized activity records from `data/activity/activity-sessions.jsonl`
- normalized workout records from `data/health/workout-sessions.jsonl`
- batch import summaries for files such as English GPTs reviews or finance exports

Status meaning:

```txt
입력됨: the direct user input is stored in the input ledger.
로딩됨: an external file or batch source was received/copied and is visible to Nomad Life.
정규화됨: loaded source data was converted into a Nomad Life normalized data contract.
분석 대기: the input/loading event exists, but Mac Hermes has not yet analyzed it into dashboard/report outputs.
분석됨: Mac Hermes has consumed the record and reflected it in dashboard/report outputs.
확인 필요: the user or Coordinator should review classification, date, duration, duplicate risk, parse quality, or import errors.
제외됨: the record is intentionally ignored/excluded from analysis.
```

Required fields for every Input History item:

```json
{
  "id": "input_* | import_* | source-specific id",
  "input_kind": "direct | import | context | evidence | settings",
  "domain": "work | ai_work | health | english | finance | food | travel | creator | rest | context | system",
  "method": "nomad_quick | workout_quick | telegram_explicit_capture | dashboard_form | file_import | icloud_dropbox | local_context_refresh | codex_evidence_import | settings_form",
  "created_at": "ISO-8601",
  "event_date": "YYYY-MM-DD | null",
  "title": "short user-visible title",
  "summary": "short sanitized summary",
  "input_status": "입력됨 | 로딩됨 | 정규화됨 | 확인 필요 | 제외됨",
  "analysis_status": "분석 대기 | 분석됨 | 분석 제외 | 확인 필요",
  "source_ref": "path, queue id, local id, or null",
  "canonical_ref": "normalized record id/path or null",
  "client_submission_id": "stable id for direct hosted/mobile submissions or null",
  "requires_user_review": false,
  "privacy_level": "normal | sensitive | private_local_only"
}
```

The Dashboard should reconcile local receipts with normalized results. New hosted/mobile submissions should carry a stable `client_submission_id` in the direct input payload and in the normalized result. Once a matching normalized result exists, the local receipt becomes a hidden shadow receipt in the default `현재 원장` and `대기/확인 필요` views. `모두 보기` may still show shadow receipts for debugging, but they are not separate life records.

For legacy records without `client_submission_id`, the Dashboard may hide same-date local health receipts when a matching health activity or workout result exists. This prevents duplicate health rows after the worker processes a mobile workout.

Input History inclusion rules:

| Source | Include In Input History | Display Grain | Default Status |
|---|---:|---|---|
| Nomad Quick work / AI work time input | yes | one direct activity input | 입력됨 · 분석 대기 |
| Nomad Quick health time/type input | yes | one direct activity input | 입력됨 · 분석 대기 |
| Workout Quick strength detail input | yes | one direct workout input | 입력됨 · 분석 대기 |
| Nomad Quick English study time input | yes | one direct activity input | 입력됨 · 분석 대기 |
| English GPTs review file import | yes | one batch/file import event | 로딩됨 or 정규화됨 · 분석 대기 |
| Finance app export import | yes | one batch/file import event, not every transaction row | 로딩됨 or 정규화됨 · 분석 대기 |
| Quick food/meal input | yes | one direct activity/capture input | 입력됨 · 분석 대기 |
| Telegram explicit capture | yes | one direct capture input | 입력됨 · 분석 대기 |
| Calendar context refresh | no by default | show in Data Sources | 로딩됨 · 분석됨/대기 |
| Notes context refresh | no by default | show in Data Sources | 로딩됨 · 분석됨/대기 |
| Codex/Git work evidence import | no by default | show in Work Evidence / Data Sources | 정규화됨 · 분석 대기 |
| Exercise library settings changes | no by default | show in Settings/Library log | 입력됨 |
| Dashboard snapshot publish | no | show in Sync Status | 분석됨 |

Relationship rules:

| Relationship | Rule |
|---|---|
| English study time input and English GPTs review file | Do not auto-match. Time input is an activity record. Review file is a separate import/review record. |
| Finance export rows and Quick expense-like memo | Do not auto-match by default. Finance export remains the canonical finance ledger source; Quick memo may become an expense candidate only. |
| Health quick time/type and workout detail | Match only when they originate from the same explicit user submission or share a stable source id. |
| Calendar/Notes context and direct inputs | Do not merge. Mac Hermes may use them as analysis context only. |
| Codex evidence and AI work time input | Do not merge. Time input is a manual activity record; Codex evidence is project-progress evidence. |

Recommended UI grouping:

```txt
Input History
  Direct inputs + import/load events

Data Sources
  Calendar, Notes, Finance export status, English review folder, Codex/Git evidence status

Analysis Status
  Mac Hermes analysis freshness, dashboard/report generation, snapshot publish state
```

Sync log records:

```json
{
  "worker": "mac_hermes_worker",
  "action": "pull_queue | process_queue_item | publish_snapshot",
  "target_table": "capture_queue | workout_queue | dashboard_snapshots",
  "target_id": "uuid | null",
  "status": "success | failed",
  "details": {}
}
```

`sync_logs` is an operational audit trail for the Mac worker. It records queue pulls, queue item processing, and dashboard snapshot publishing. It must not contain raw Notes, Calendar, HealthKit exports, full finance ledgers, or service credentials.

## Sync Status

Path:

```txt
dashboard/sync-status.json
```

Published snapshot key:

```txt
sync-status
```

This is a sanitized Dashboard-facing status snapshot generated by the Mac worker from queue counts and `sync_logs`. Browser clients should read this snapshot instead of reading `sync_logs` or queue tables directly.

Required shape:

```json
{
  "schema_version": "0.1.0",
  "generated_at": "ISO-8601",
  "date": "YYYY-MM-DD",
  "data_quality": {
    "status": "partial",
    "notes": []
  },
  "summary": {
    "pending_captures": 0,
    "pending_workouts": 0,
    "last_pull_at": "ISO-8601 | null",
    "last_publish_at": "ISO-8601 | null",
    "last_failure_at": "ISO-8601 | null",
    "health": "ok | pending | attention | unknown"
  },
  "recent_events": []
}
```

See:

```txt
supabase/migrations/0001_cloud_light.sql
docs/CLOUD_LIGHT_ARCHITECTURE.md
```

## Capture JSONL

Path:

```txt
data/captures/YYYY-MM-DD.jsonl
```

Each line is one capture.

Required fields:

```json
{
  "id": "capture_YYYYMMDD_HHMMSS_slug",
  "created_at": "ISO-8601",
  "date": "YYYY-MM-DD",
  "type": "text | voice | photo | expense | checkin",
  "raw_content": "",
  "media_url": null,
  "parsed_result": {},
  "linked_agents": [],
  "confidence": 0.0,
  "status": "raw | parsed | needs_review | ignored"
}
```

`ignored` captures remain in the JSONL file for auditability, but dashboard generation excludes them.

## Latest Captures Context

Path:

```txt
data/context/latest-captures.json
```

Used by downstream skills to avoid scanning every capture file.

## Activity Sessions

Path:

```txt
data/activity/activity-sessions.jsonl
```

Activity Sessions are the shared timeline spine for Nomad Life. Nomad Quick PWA should create these records for structured activity input. Domain-specific records, such as workout details or English transcript notes, should link back to activity sessions instead of replacing them.

Each line is one activity session.

Required fields:

```json
{
  "id": "activity_YYYYMMDD_HHMMSS_slug",
  "created_at": "ISO-8601",
  "updated_at": "ISO-8601",
  "date": "YYYY-MM-DD",
  "start_time": "HH:MM | null",
  "end_time": "HH:MM | null",
  "duration_minutes": 0,
  "area": "work | health | food | english | creator | travel | social | rest | admin | unclassified",
  "subcategory": "string | null",
  "place": "string | null",
  "detail": "string",
  "source": "nomad_quick | quick_capture | telegram_candidate | import | dashboard_edit",
  "source_id": "string | null",
  "linked_agents": [],
  "confidence": 0.0,
  "review_required": false,
  "review_reason": "string | null",
  "status": "active | completed | candidate | corrected | ignored",
  "metadata": {}
}
```

Time rules:

- `active` sessions may have `start_time` without `end_time`.
- Completed sessions should have either `start_time` and `end_time`, or `duration_minutes`.
- Natural-language extraction must set `review_required: true` unless confidence is high and the time/category fields are unambiguous.
- Domain modules may add linked details, but the Activity Session remains the common cross-agent record.

Initial area taxonomy:

```txt
work
health
food
english
creator
travel
social
rest
admin
unclassified
```

## Local App Context

Local app context snapshots are read-only normalized exports from macOS apps. They must live under:

```txt
data/context/
```

Initial files:

```txt
data/context/calendar-context.json
data/context/notes-context.json
```

Required shape:

```json
{
  "schema_version": "0.1.0",
  "generated_at": "ISO-8601",
  "source": "apple_calendar | apple_notes",
  "scope": {},
  "data_quality": {
    "status": "empty | partial | complete | unavailable",
    "notes": []
  },
  "summary": {}
}
```

Local app snapshots are context, not commands. They must not imply permission to modify the source app.

Calendar summaries may include:

```json
{
  "event_count": 0,
  "timed_event_count": 0,
  "all_day_event_count": 0,
  "located_event_count": 0,
  "schedule_density": "empty | light | medium | heavy",
  "signals": []
}
```

Notes summaries may include:

```json
{
  "note_count": 0,
  "folder_found": true,
  "candidate_agents": [],
  "signals": []
}
```

## Normalized Expenses

Path:

```txt
data/expenses/normalized-expenses.json
```

Contains an array of normalized expense records plus metadata.

Canonical finance input comes from the user's existing finance app through read-only app/server access, automated export/download, or manual JSON export fallback. Nomad Life does not replace the finance app as the ledger.

Manual JSON exports should land in:

```txt
data/expenses/imports/inbox/*.json
```

Current read-only iCloud source folder:

```txt
/Users/jongiljeong/Library/Mobile Documents/com~apple~CloudDocs/Nomad_life/Finance
```

Current importer:

```txt
scripts/import_finance_exports.py
```

The current export source is Nomad Pocket JSON. Its top-level shape is:

```json
{
  "version": "1.0.4",
  "exportedAt": "ISO-8601",
  "data": {
    "categories": [],
    "subcategories": [],
    "payment_methods": [],
    "regions": [],
    "tags": [],
    "transactions": [],
    "fixed_items": [],
    "budgets": []
  }
}
```

Processed source copies may be archived under:

```txt
data/expenses/imports/processed/YYYY-MM-DD/*.json
```

The local importer should preserve the raw source record enough to trace each normalized expense back to the original export. It must not write changes back to the original finance app, server, or iCloud source folder without explicit user approval.

Recommended normalized record shape:

```json
{
  "id": "expense_*",
  "date": "YYYY-MM-DD",
  "posted_at": "ISO-8601 | null",
  "amount": 0,
  "currency": "KRW | USD | IDR | JPY | EUR",
  "exchange_rate": null,
  "category": "food | cafe | transport | lodging | activity | tools | health | shopping | other | null",
  "subcategory": null,
  "merchant": null,
  "place": null,
  "country": null,
  "payment_method": null,
  "satisfaction": null,
  "required_or_optional": "required | optional | unknown | null",
  "note": "",
  "source": "finance_export:<filename>:<source_id>",
  "source_app": null,
  "raw_hash": "sha256"
}
```

Finance analysis outputs should focus on spend status, category mix, recurring patterns, budget pressure, location/travel-driven spikes, missing days, duplicate risks, and practical adjustment suggestions.

```txt
dashboard/finance-review.json
```

Contains a Dashboard-safe Finance analysis snapshot generated from `normalized-expenses.json`. The Mac worker publishes this as the `finance-review` Supabase dashboard snapshot so Hosted Dashboard and mobile clients can show the same latest Finance analysis without needing direct access to the local normalized ledger file.

## Stay Packages And Backups

Canonical working files remain in:

```txt
data/
dashboard/
reports/
```

When the user changes region or starts a meaningful stay, Nomad Life should also create a local stay package.

Current active stay:

```txt
data/travel/current-stay.json
```

Shape:

```json
{
  "schema_version": "0.1.0",
  "updated_at": "ISO-8601",
  "stay_id": "bali-2026-05",
  "region": "Bali",
  "country": "Indonesia",
  "timezone": "Asia/Makassar",
  "start_date": "YYYY-MM-DD",
  "end_date": null,
  "status": "active | closed",
  "local_package_path": "data/stays/bali-2026-05",
  "backup_root": "data/backups/stays/bali-2026-05",
  "notes": []
}
```

Stay index:

```txt
data/travel/stays-index.json
```

Shape:

```json
{
  "schema_version": "0.1.0",
  "updated_at": "ISO-8601",
  "active_stay_id": "bali-2026-05",
  "stays": [
    {
      "stay_id": "bali-2026-05",
      "region": "Bali",
      "country": "Indonesia",
      "timezone": "Asia/Makassar",
      "start_date": "YYYY-MM-DD",
      "end_date": null,
      "status": "active | closed",
      "dataset_scope": "current | all",
      "local_package_path": "data/stays/bali-2026-05",
      "backup_root": "data/backups/stays/bali-2026-05",
      "updated_at": "ISO-8601",
      "note": ""
    }
  ]
}
```

The active stay is the default attribution target for new captures, activities, workouts, daily reports, and stay packages. Closed stays remain available for future review pages that compare spending, time allocation, health activity, English practice, and work signals across regions or months.

Stay package:

```txt
data/stays/{stay_id}/manifest.json
data/stays/{stay_id}/snapshot/**
```

The manifest records package metadata, copied source roots, copied file paths, and privacy flags. The snapshot is a local grouped copy for review, migration, and backup; it is not the canonical write target for day-to-day tools.

Backup:

```txt
data/backups/stays/{stay_id}/{stay_id}-YYYYMMDD-HHMMSS.tar.gz
```

Backups are local-first and may contain personal data. They must not be uploaded to cloud storage or external services without explicit user approval.

Current helper:

```txt
scripts/package_stay_data.py
npm run stay:package
```

## Expense Candidates

Path:

```txt
data/expenses/expense-candidates.json
```

Contains reviewable candidates generated from finance-linked captures. These are not final ledger entries.

Finance candidates are not the primary finance input path. The canonical finance source is the user's existing finance app export/download or read-only view. Capture-derived candidates are only contextual hints until the external ledger import contract is implemented.

Required shape:

```json
{
  "schema_version": "0.1.0",
  "generated_at": "ISO-8601",
  "date": "YYYY-MM-DD | null",
  "data_quality": {
    "status": "empty | partial",
    "notes": []
  },
  "policy": {
    "auto_confirm": false,
    "review_required": true
  },
  "candidates": [
    {
      "id": "expense_candidate_*",
      "date": "YYYY-MM-DD",
      "amount": 0,
      "currency": "KRW | USD | IDR | JPY | EUR",
      "category": null,
      "subcategory": null,
      "note": "",
      "source": "capture_*",
      "status": "candidate",
      "review": {
        "required": true,
        "reason": ""
      }
    }
  ]
}
```

Candidates require user review before they are moved into `normalized-expenses.json`.

## Normalized Meals

Path:

```txt
data/meals/normalized-meals.json
```

Contains an array of normalized meal records plus metadata.

## Activity Allocation

Path:

```txt
data/context/activity-allocation.json
dashboard/activity-allocation.json
```

Future dashboard input for understanding where the user's time is actually going.

Initial records can be inferred from captures such as:

```txt
9시부터 11시까지 코딩
오후 3시부터 1시간 수영
저녁에 영어 40분
```

Required conceptual shape:

```json
{
  "schema_version": "0.1.0",
  "generated_at": "ISO-8601",
  "date": "YYYY-MM-DD",
  "summary": {
    "total_tracked_minutes": 0,
    "capacity_minutes": 1440,
    "tracked_share_of_capacity": 0.0,
    "areas": [
      {
        "area": "AI Work | Health | English | Rest | Creator | Travel | Finance",
        "minutes": 0,
        "share": 0.0,
        "share_of_capacity": 0.0,
        "source_count": 0
      }
    ]
  },
  "month_summary": {
    "month": "YYYY-MM",
    "elapsed_days": 1,
    "capacity_minutes": 1440,
    "total_tracked_minutes": 0,
    "tracked_share_of_capacity": 0.0,
    "areas": []
  },
  "sessions": [
    {
      "id": "activity_session_*",
      "date": "YYYY-MM-DD",
      "area": "Health",
      "label": "수영",
      "start_time": "15:00",
      "end_time": null,
      "duration_minutes": 60,
      "source": "capture_*",
      "confidence": 0.0,
      "status": "candidate"
    }
  ]
}
```

## Agent Reports

Path:

```txt
data/agent_reports/YYYY-MM-DD.json
data/context/agent-reports.json
```

These reports are the first shared contract between thin sub-agents and the Coordinator. The Coordinator should read this contract before falling back to raw capture counts.

Required shape:

```json
{
  "schema_version": "0.1.0",
  "generated_at": "ISO-8601",
  "date": "YYYY-MM-DD",
  "data_quality": {
    "status": "empty | partial | complete",
    "notes": []
  },
  "reports": [
    {
      "id": "agent_report_YYYY-MM-DD_nomad_health",
      "date": "YYYY-MM-DD",
      "agent_name": "nomad-health",
      "status": "empty | light | steady | watch | protect",
      "score": 1,
      "insight": "",
      "recommendation": "",
      "risk": null,
      "data_sources": ["capture_*"],
      "confidence": 0.0,
      "summary": {}
    }
  ]
}
```

Initial thin-slice reporters:

- `nomad-health`
- `nomad-english`

Reports are interpretation candidates for Coordinator synthesis. They do not grant permission to mutate Calendar, Notes, Reminders, Health, finance apps, or external services.

Activity allocation should remain candidate-based until parsing and correction rules are agreed.

Daily activity share uses `24h = 1440 minutes` as capacity. Monthly activity share uses elapsed days in the selected month multiplied by 1440 minutes.

Initial parser scope:

- `N시간`
- `N분`
- `9시부터 11시까지`
- `오후 3시부터 1시간`

Out of initial parser scope:

- Ambiguous all-day statements
- Calendar reconciliation
- Automatic correction UI
- Multi-day time spans

## GPTs English Reviews

Path:

```txt
data/english/gpts-reviews/inbox/*.json
data/english/gpts-reviews/inbox/*.md
```

GPTs English review JSON files are structured imports from a user-created GPTs English learning app. JSON is the canonical agent input. Markdown is a human-readable sidecar.

Current source folder for the user's GPTs English review exports:

```txt
/Users/jongiljeong/Library/Mobile Documents/com~apple~CloudDocs/Nomad_life/English
```

Because macOS/iCloud permissions can block direct reads from this folder, the stable agent import path remains `data/english/gpts-reviews/inbox/`.

Instruction template:

```txt
docs/gpts/ENGLISH_REVIEW_GPTS_INSTRUCTIONS.md
```

Required JSON shape:

```json
{
  "schema_version": "0.1.0",
  "source": "gpts_english_review",
  "session_id": "gpts_english_YYYYMMDD_HHMM",
  "date": "YYYY-MM-DD",
  "started_at": "ISO-8601 | null",
  "ended_at": "ISO-8601 | null",
  "duration_minutes": 0,
  "app_name": "",
  "conversation_title": "",
  "input_modes": ["voice", "text"],
  "focus_area": "conversation | pronunciation | vocabulary | grammar | travel | small_talk | work | review",
  "level": "beginner | intermediate | advanced | unknown",
  "user_goal": "",
  "transcript_summary": "",
  "markdown_file": "english-review-YYYY-MM-DD-HHMM.md",
  "metrics": {
    "turn_count": 0,
    "user_message_count": 0,
    "assistant_message_count": 0,
    "estimated_speaking_minutes": 0
  },
  "study_context": {
    "pre_study_context_used": false,
    "target_issue_ids": [],
    "planned_scenario": "",
    "actual_scenario": "",
    "scenario_success": "completed | partial | changed | unknown"
  },
  "observations": [],
  "performance_scores": {
    "scale": "0-100",
    "session_scores": {},
    "score_evidence": []
  },
  "turn_assessments": [],
  "learned_items": [],
  "corrections": [],
  "weak_points": [],
  "habit_patterns": [],
  "strengths": [],
  "next_actions": [],
  "review_cards": [],
  "issue_recurrence": [],
  "new_issues": [],
  "agent_feedback": {
    "progress_signals": [],
    "unresolved_issues": [],
    "resolved_candidate_issues": [],
    "next_session_should_test": []
  },
  "tags": []
}
```

Import rules:

- The JSON file must not include a full sensitive transcript by default.
- Markdown review files may include a `json` codeblock as a fallback when GPTs cannot provide a separate JSON file.
- `duration_minutes` is required for frequency and workload analysis.
- `learned_items`, `corrections`, `weak_points`, `next_actions`, and `review_cards` should be structured arrays, not prose-only text.
- `observations` should contain the machine-readable event log for corrections, weak points, habits, strengths, learned items, and issue tests.
- `performance_scores` and `turn_assessments` are required for real performance trend graphs. If absent, English Agent falls back to derived issue-observation scores.
- `issue_recurrence` should be present whenever the previous `pre_study_context` was used. It must distinguish `not_seen` from `not_tested`.
- `new_issues` should list newly detected issue candidates with stable `fingerprint_hint` values.
- The English Agent reads these files into `data/english/english-notes.json` and `dashboard/english.json`.
- This import is read-only. It does not modify the source GPTs app or external files.

`dashboard/english.json` may additionally expose:

```json
{
  "import_status": {
    "status": "empty | ok | warning | error",
    "json_file_count": 0,
    "imported_count": 0,
    "validation_error_count": 0,
    "validation_warning_count": 0
  },
  "weekly_summary": {
    "window": {
      "start_date": "YYYY-MM-DD",
      "end_date": "YYYY-MM-DD",
      "days": 7
    },
    "review_session_count": 0,
    "activity_session_count": 0,
    "active_day_count": 0,
    "study_minutes": 0,
    "top_habit_tags": [],
    "top_weak_points": [],
    "correction_goal": null
  },
  "habit_recommendations": [],
  "review_card_queue": [],
  "learning_profile": {
    "status": "empty | active",
    "agent_interpretation": "",
    "scope": {
      "first_date": "YYYY-MM-DD",
      "last_date": "YYYY-MM-DD",
      "review_session_count": 0,
      "active_day_count": 0,
      "study_minutes": 0,
      "focus_areas": []
    },
    "progression": [],
    "improvement_signals": [],
    "persistent_issues": [],
    "correction_insights": [],
    "correction_examples": [],
    "learned_inventory": [],
    "next_focus": []
  },
  "issue_tracker": {
    "status": "empty | active",
    "algorithm_version": "0.1.0",
    "review_session_count": 0,
    "latest_session_id": "",
    "issues": [],
    "recurrence_checks": []
  },
  "pre_study_context": {
    "status": "empty | ready",
    "active_issue_count": 0,
    "prompt": "",
    "active_issues": []
  }
}
```

`habit_recommendations` are deterministic coaching suggestions generated from repeated `habit_tags` and `habit_patterns`. `review_card_queue` is a lightweight queue generated from GPTs `review_cards`; it is not yet a spaced-repetition scheduler.

`learning_profile` is the English Agent's cumulative interpretation layer. It should read all available GPTs review records up to the target date and surface progress, repeated unresolved issues, learned material, and the next training focus. It must not claim long-term improvement when the data window is too small.

`issue_tracker` is the specialized review loop. It detects repeated corrections, weak points, and non-positive habits as issues, assigns lifecycle status, keeps evidence examples, and creates recurrence checks for later reviews.

`pre_study_context` is a copyable prompt for the next GPTs study session. It tells GPTs which active issues to test and how to report whether each issue reappeared.

## Health Summary

Path:

```txt
data/health/health-summary.json
dashboard/health.json
```

Tracks exercise time, workout type, structured strength details, and recovery signals. Apple Health access is not part of the default contract and requires explicit approval.

`dashboard/health.json` also includes a rolling 14-day muscle schedule for Cockpit visualization:

```json
{
  "muscle_dashboard": {
    "window_days": 14,
    "start_date": "YYYY-MM-DD",
    "end_date": "YYYY-MM-DD",
    "dates": ["YYYY-MM-DD"],
    "rows": [
      {
        "muscle_group": "chest",
        "label": "가슴",
        "cells": [
          {
            "date": "YYYY-MM-DD",
            "set_count": 0,
            "intensity": 0,
            "entries": []
          }
        ]
      }
    ],
    "summaries": [
      {
        "muscle_group": "chest",
        "label": "가슴",
        "last_workout_date": null,
        "days_since_last": null,
        "sets_7d": 0,
        "sets_14d": 0
      }
    ]
  },
  "readiness": [
    {
      "muscle_group": "back",
      "label": "등",
      "status": "untracked | overdue | ready | cooldown | recent",
      "priority": 0,
      "display_order": 1,
      "reason": "최근 14일 기록 없음",
      "days_since_last": null,
      "sets_7d": 0,
      "sets_14d": 0
    }
  ],
  "recommendations": [
    {
      "type": "muscle_focus",
      "muscle_group": "back",
      "label": "등",
      "reason": "최근 14일 기록 없음",
      "suggestion": "등 중심으로 가볍게 확인"
    }
  ],
  "exercise_progression": [
    {
      "exercise": "bench_press",
      "muscle_group": "chest",
      "set_count_14d": 0,
      "max_weight_14d": null,
      "last_weight_kg": null,
      "last_reps": null,
      "last_date": null
    }
  ]
}
```

## Workout Sessions

Path:

```txt
data/health/workout-sessions.jsonl
```

Each line is one structured workout detail session. The local Cockpit form can write this file. HealthKit or workout app imports may later write compatible read-only imported records after explicit approval.

Required shape:

```json
{
  "id": "workout_session_YYYYMMDD_HHMMSS",
  "created_at": "ISO-8601",
  "date": "YYYY-MM-DD",
  "type": "strength | swimming | running | walking | surfing | mobility | other",
  "source": "local_cockpit_form | healthkit_import | workout_app_export",
  "source_capture_id": "capture_*",
  "started_at": "ISO-8601",
  "ended_at": "ISO-8601",
  "status": "active | completed | candidate",
  "muscle_group": "chest | back | legs | shoulders | arms | core | full_body | other",
  "entries": [
    {
      "muscle_group": "chest",
      "exercise": "bench_press",
      "weight_kg": 60,
      "reps": 10,
      "set_index": 1,
      "rpe": null,
      "note": null
    }
  ],
  "note": null
}
```

`capture` remains the raw/audit input. `workout_session` is the structured analysis record used by `nomad-health`.

## Exercise Library

Paths:

```txt
data/health/exercise-library.json
data/health/exercise-preferences.json
data/health/exercise-library.import-preview.json
```

`exercise-library.json` is the local normalized exercise catalog used by the Cockpit workout form. It starts as a reviewed local seed and may later be expanded from external libraries such as wger or PlainExercise after license review. External detail pages should be referenced by `source_url` when full content licensing is unclear.

```json
{
  "schema_version": "0.1.0",
  "exercises": [
    {
      "id": "bench_press",
      "name_ko": "벤치프레스",
      "name_en": "Bench Press",
      "primary_muscle": "chest",
      "secondary_muscles": ["shoulders", "arms"],
      "equipment": ["barbell", "bench"],
      "movement_pattern": "push",
      "difficulty": "intermediate",
      "instructions": ["short local/reference instruction"],
      "image_url": "https://example.com/main-image.jpg",
      "images": [
        {
          "url": "https://example.com/main-image.jpg",
          "is_main": true,
          "license": "CC-BY-SA 4.0",
          "license_author": "source contributor",
          "license_author_url": "https://example.com/author",
          "source": "wger"
        }
      ],
      "source": "local_seed | wger | plainexercise | custom",
      "source_url": null
    }
  ]
}
```

`exercise-preferences.json` stores user-specific ordering signals separately from the source catalog:

```json
{
  "schema_version": "0.1.0",
  "exercises": {
    "bench_press": {
      "favorite": true,
      "usage_count": 12,
      "last_used_at": "ISO-8601",
      "updated_at": "ISO-8601"
    }
  }
}
```

`exercise-library.import-preview.json` is a review artifact generated by `scripts/import_exercise_library.py`. It contains `incoming`, `stats`, license notes, and the proposed `merged_library`. The primary library must only be replaced after review, either by running the importer with `--apply` or by an explicit UI approval flow.

## English Summary

Path:

```txt
data/english/english-notes.json
dashboard/english.json
```

Tracks study time, transcript metadata, weak expressions, and progress signals. Transcript folder scope and retention policy must be confirmed before reading broad text content.

## Today Dashboard

Path:

```txt
dashboard/today.json
```

The Basic Nomad Dashboard should be able to render the main daily view from this file.

## Notification Candidates

Path:

```txt
dashboard/notifications.json
```

This file contains notification candidates only. Creating a candidate does not mean it was sent.

Required shape:

```json
{
  "schema_version": "0.1.0",
  "generated_at": "ISO-8601",
  "date": "YYYY-MM-DD",
  "policy": {
    "send_allowed_by_default": false,
    "approval_required_before_send": true
  },
  "notifications": [
    {
      "id": "",
      "kind": "",
      "title": "",
      "message": "",
      "priority": "low | medium | high",
      "channel": "telegram_candidate",
      "status": "candidate",
      "send_allowed": false,
      "approval_required_before_send": true
    }
  ]
}
```

## Action Logs

Path:

```txt
data/action_logs/YYYY-MM-DD.jsonl
```

Every script or skill that writes files should append a log record.

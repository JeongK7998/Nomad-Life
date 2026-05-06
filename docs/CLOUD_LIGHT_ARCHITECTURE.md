# Cloud-Light Architecture

Nomad Dashboard is the user-facing platform surface. It must be available from Mac, iPad, and iPhone. Hermes remains the execution and reasoning center on the Mac.

## Decision

Use GitHub, Vercel, and Supabase as the cloud-light layer:

- GitHub stores source code and deployment history.
- Vercel hosts Nomad Dashboard and Quick Panels.
- Supabase provides auth, input queues, dashboard snapshots, and sync logs.
- Mac Hermes Worker processes queue records, writes local data, runs skills, and publishes snapshots.

When referring to Supabase in setup or operations, always name the exact Supabase project because Nomad Life may share infrastructure with another project. If the project name has not been confirmed, say `Supabase 프로젝트명 미확인` and ask before giving project-specific steps.

Current target:

```txt
Supabase project: Nomad Life
Supabase URL: https://ikeubpdajcuqlvbvvhbq.supabase.co
```

Supabase and Vercel are not the agent brain. They are availability, queue, sync, and display infrastructure.

## Target Shape

```txt
Mac / iPad / iPhone
        ↓
Vercel-hosted Nomad Dashboard + Quick Panels
        ↓
Supabase
  - capture_queue
  - workout_queue
  - dashboard_snapshots
  - sync_logs
        ↓
Mac Hermes Worker
  - queue pull
  - local normalization
  - Hermes / skills / reports
  - dashboard refresh
        ↓
Local Data Store
        ↓
Supabase dashboard snapshot publish
        ↓
Vercel-hosted Dashboard on all devices
```

## Responsibilities

### GitHub

- Source of truth for application code, scripts, docs, and schema.
- Pull request / commit history for architecture changes.
- Vercel deployment trigger.

### Vercel

- Hosted Nomad Dashboard.
- Hosted Quick Panels such as Workout Quick.
- Static web hosting first.
- Optional thin API routes later, only when needed.

Vercel must not run Hermes or process private Mac context.

### Supabase

- Authentication and device access.
- Queue for mobile and web inputs.
- Latest dashboard snapshots.
- Sync logs and failure visibility.

Supabase should initially store only normalized queue payloads and dashboard summaries. It should not store raw private app exports, credentials, full Notes, full Calendar, finance secrets, or HealthKit raw exports.

### Mac Hermes Worker

- Pulls pending Supabase queue records.
- Converts them into local JSON/JSONL contracts.
- Runs deterministic refresh scripts and Hermes-based interpretation.
- Publishes dashboard snapshots back to Supabase.
- Logs every pull/process/publish action.
- Writes `sync_logs` rows for queue pulls, item results, failures, and snapshot publishes.
- Publishes a sanitized `sync-status` dashboard snapshot so browser clients can see pending counts and recent worker health without direct access to service-role logs or raw queues.

## Data Policy

Cloud-light allowed:

- Quick capture text intended for Nomad Life.
- Structured workout input.
- Dashboard summaries and snapshots.
- Review/action candidates.
- Queue processing status.

Local-first only:

- Full Apple Notes context.
- Full Calendar context.
- Raw HealthKit exports.
- Finance credentials and full ledger exports unless explicitly approved.
- Local files, source documents, sensitive personal logs.

iCloud Drive remains a fallback/dropbox for:

- Offline capture.
- Large photos/receipts/exports.
- Files that should be processed locally before optional summarization.

## Modes

### Local Mode

```txt
Dashboard reads /dashboard/*.json
Quick Panels POST to local /api/*
Hermes Worker reads local files
```

Used for development, debugging, and private context verification.

### Cloud Mode

```txt
Dashboard reads Supabase dashboard_snapshots
Quick Panels insert queue rows into Supabase
Mac Hermes Worker processes Supabase queue
```

Used for iPhone/iPad/Mac access outside the local Wi-Fi.

## First Implementation Slice

1. Create Supabase tables: `capture_queue`, `workout_queue`, `dashboard_snapshots`, `sync_logs`.
2. Add Mac worker script to process pending queue rows.
3. Publish local dashboard JSON files as Supabase snapshots.
4. Add frontend environment config for Supabase mode.
5. Deploy Dashboard and Quick Panels to Vercel.

Current implementation foundation:

- `api/config.js` exposes browser-safe mode and Supabase anon config.
- Local `scripts/serve_cockpit.py` also exposes `/api/config`.
- `web/app.js` can read local dashboard files in local mode or latest Supabase `dashboard_snapshots` in cloud mode.
- `web/app.js` can send Quick Capture and dashboard Workout Detail entries to Supabase queues in cloud mode.
- `web/workout-quick.js` can run in local mode or Supabase queue mode.
- `web/data/exercise-library.json` is a public dropdown snapshot generated from the local exercise library.
- `scripts/supabase_worker.py` processes pending Supabase queue rows on the Mac and publishes dashboard snapshots, including `workout-history`.
- `scripts/supabase_worker.py` writes operational audit rows to `sync_logs` for queue pulls, queue item processing, failures, and snapshot publishing.
- `scripts/supabase_worker.py` publishes `sync-status` for the Dashboard Sync Status panel.

## Guardrails

- Do not move Hermes execution to Vercel/Supabase.
- Do not make Supabase the canonical source for sensitive local context.
- Do not auto-act on external apps from queue items.
- Every cloud queue item needs a status lifecycle.
- Failed queue items must remain inspectable.
- Dashboard snapshots are derived display artifacts, not raw memory.

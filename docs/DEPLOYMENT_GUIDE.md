# Deployment Guide

This guide describes the GitHub + Vercel + Supabase path for Nomad Dashboard.

## Naming

- Product surface: Nomad Dashboard
- Mobile-first inputs: Quick Panels
- Runtime: Mac Hermes Worker
- Cloud layer: Supabase + Vercel

## Repository

GitHub should contain:

```txt
AGENTS.md
docs/
skills/
scripts/
web/
supabase/
vercel.json
```

Do not commit:

```txt
data/
dashboard/
reports/
.env
*.local
```

Generated local outputs and private data stay local unless explicitly published as a sanitized dashboard snapshot.

Current GitHub repository:

```txt
https://github.com/JeongK7998/Nomad-Life
```

Vercel project `nomad-life` is connected to this repository for push-based deployments.

## Vercel

Initial Vercel deployment is static:

```txt
/web/index.html
/web/workout-quick.html
/web/*.css
/web/*.js
/web/data/exercise-library.json
/api/config.js
```

Current Vercel project:

```txt
Project: nomad-life
Team: boss7998-5893s-projects
Project ID: prj_q6wme89RLJNQCGqHAwYsaKiODIVD
```

The Vercel output directory is `web`, so generated local folders such as `data/`, `dashboard/`, and `reports/` are not uploaded as hosted static assets. The hosted dashboard reads Supabase snapshots instead.

Recommended production URLs:

```txt
/web/                   Nomad Dashboard
/web/workout-quick.html Workout Quick Panel
/workout                Workout Quick Panel shortcut
```

Environment variables for cloud mode:

```txt
VITE_SUPABASE_URL
VITE_SUPABASE_ANON_KEY
NOMAD_DASHBOARD_MODE=supabase
```

The current static web code does not yet require a build step. If a frontend framework is introduced later, document the build output and update `vercel.json`.

Current static build command:

```bash
npm run build
```

This is intentionally a no-op. Use prebuilt deployment after local verification:

```bash
npx vercel build --prod
npx vercel deploy --prebuilt --prod --yes
```

If Vercel Authentication is enabled, the hosted URL requires a Vercel login or a temporary share link until Supabase/Auth policy is finalized.

Public exercise library export:

```bash
scripts/export_public_exercise_library.py
```

This writes:

```txt
web/data/exercise-library.json
```

Hosted Quick Panels use this public snapshot for dropdowns. User-specific preferences and workout history stay local/Supabase-backed and should not be baked into this public file.

Dashboard mode behavior:

```txt
local mode:
  /api/config -> mode local
  /dashboard/*.json
  /api/captures
  /api/hermes-draft
  /api/workout-history
  local POST APIs for capture/workout

supabase mode:
  /api/config -> mode supabase
  latest Supabase dashboard_snapshots:
    today
    health
    life-balance
    activity-allocation
    notifications
    workout-history
  Supabase REST insert into capture_queue/workout_queue
```

## Supabase

Project name:

```txt
Nomad Life
https://ikeubpdajcuqlvbvvhbq.supabase.co
```

Always include the Supabase project name in setup, deployment, and operations guidance. Nomad Life may use tables inside a Supabase project that also serves another product, so project-specific steps should not say only "Supabase" when they mean a concrete project.

Apply schema:

```bash
supabase db push
```

or paste the SQL from:

```txt
supabase/migrations/0001_cloud_light.sql
```

Required tables:

- `capture_queue`
- `workout_queue`
- `dashboard_snapshots`
- `sync_logs`

Use RLS before exposing the dashboard outside a trusted local environment.

## Mac Hermes Worker

The Mac worker uses service-role credentials and must run only on the Mac.

Required local environment variables:

```txt
SUPABASE_URL=https://ikeubpdajcuqlvbvvhbq.supabase.co
SUPABASE_SERVICE_ROLE_KEY=...
```

Smoke test:

```bash
npm run sync:dry
```

Process pending rows and publish snapshots for Supabase project "Nomad Life":

```bash
npm run sync
```

Run the same sync every five minutes while the Mac is awake:

```bash
npm run sync:watch
```

`scripts/run_nomad_sync.py` loads `.env`, prevents overlapping runs with `data/sync/nomad-sync.lock`, calls `scripts/supabase_worker.py`, and appends a local run summary to `data/action_logs/nomad-sync-runs.jsonl`.

When snapshot publishing runs, the worker first imports the latest read-only Finance JSON export from the configured iCloud Drive Finance folder and refreshes `dashboard/finance-review.json`. It then publishes that analysis as the `finance-review` dashboard snapshot for mobile and hosted Dashboard views.

The worker writes `sync_logs` rows in Supabase project "Nomad Life" for queue pulls, processed items, failures, and snapshot publishes. Review this table first when a mobile capture, Workout Quick entry, or hosted dashboard snapshot looks stale.

Preview publishable snapshots without Supabase credentials:

```bash
scripts/supabase_worker.py --publish-snapshots --dry-run
```

## Phased Rollout

### Phase 1. Contracts

- Add schema.
- Add worker.
- Keep local dashboard working.

### Phase 2. Cloud Snapshot Read

- Publish `dashboard/*.json` into Supabase `dashboard_snapshots`.
- Hosted Dashboard reads the latest snapshot.
- iPhone/iPad can view the Dashboard from Vercel.

### Phase 3. Quick Panel Queue

- Workout Quick writes to Supabase `workout_queue`.
- Capture Quick writes to Supabase `capture_queue`.
- Mac worker pulls and processes queue.

Workout Quick mode behavior:

```txt
local mode:
  /api/config -> mode local
  /api/exercises
  /api/workout-history
  /api/workout-session

supabase mode:
  /api/config -> mode supabase
  /web/data/exercise-library.json
  latest workout-history dashboard snapshot when available
  Supabase REST insert into workout_queue
  Queue inserts use Prefer: return=minimal because anon cannot read queue rows.
```

### Phase 4. Auth and Access

- Add Supabase Auth.
- Restrict dashboard snapshots and queues by user.
- Keep service role only on Mac.

### Phase 5. Automation

- Run Mac worker periodically.
- Add failure review surface.
- Keep sensitive external app mutations approval-based.

## Rollback

If cloud sync misbehaves:

1. Stop Mac worker.
2. Switch Dashboard to local mode.
3. Keep queue rows in Supabase for inspection.
4. Process only after schema/payload fixes are made.

Never delete queue records as the first response to a sync problem.

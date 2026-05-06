# Mobile Input Strategy

Nomad Life now uses Supabase queue as the primary mobile input path because Nomad Dashboard and Quick Panels must work from Mac, iPad, and iPhone without same-Wi-Fi constraints.

## Decision

Use Supabase queue first for structured mobile/web inputs. Keep iCloud Drive as fallback/dropbox for offline files, photos, receipts, and exports.

## Capture Paths

```txt
Path A: Supabase Queue
iPhone / iPad / Mac Quick Panel
  -> Supabase capture_queue or workout_queue
  -> scripts/supabase_worker.py on Mac
  -> data/captures/YYYY-MM-DD.jsonl
  -> data/health/workout-sessions.jsonl when relevant
  -> dashboard/*.json
  -> Supabase dashboard_snapshots
```

```txt
Path B: Local Dashboard / Quick Panel
Browser on Mac or same local network
  -> POST /api/capture or /api/workout-session
  -> dashboard refresh
```

```txt
Path C: iCloud Drive Fallback
iPhone / iPad Shortcut or Files app
  -> iCloud Drive file
  -> data/inbox/cloud
  -> scripts/process_inbox.py
  -> local dashboard refresh
```

Roles:

- Supabase queue: primary always-accessible structured input.
- Local Dashboard: immediate local feedback while MacBook is running.
- iCloud Drive: offline fallback/dropbox for files and large media.

## iPhone Home Screen Entry

The first mobile-first PWA entry is Workout Quick.

```txt
iPhone Home Screen
  -> /workout
  -> workout_queue in Supabase project "Nomad Life"
  -> scripts/supabase_worker.py on Mac
  -> data/health/workout-sessions.jsonl
  -> dashboard/health.json
  -> dashboard_snapshots in Supabase project "Nomad Life"
```

The hosted route is stable:

```txt
https://nomad-life-neon.vercel.app/workout
```

On iPhone, open this URL in Safari and choose Share -> Add to Home Screen. The installed icon opens the workout input form directly and shares an in-progress workout draft with the Health form in the main dashboard.

## Supabase Queue Payloads

Capture queue payload:

```json
{
  "type": "text",
  "text": "오늘 점심은 12만 루피아. 오후에는 2시간 작업.",
  "media_url": null,
  "source": "capture_quick"
}
```

Workout queue payload:

```json
{
  "type": "strength",
  "started_at": "ISO-8601",
  "ended_at": "ISO-8601",
  "muscle_group": "chest",
  "entries": [
    {
      "muscle_group": "chest",
      "exercise": "bench_press",
      "weight_kg": 60,
      "reps": 10,
      "rpe": null,
      "note": null
    }
  ],
  "note": ""
}
```

Queue status lifecycle:

```txt
pending -> processing -> processed
pending -> processing -> failed
pending -> ignored
```

## iCloud Shortcut File Format

Fallback can still use `.txt` files. Each file contains one raw capture.

Recommended filename:

```txt
nomad-capture-YYYYMMDD-HHMMSS.txt
```

Recommended content:

```txt
오늘 점심은 12만 루피아. 맛은 좋았지만 무거웠고, 오후에는 2시간 작업했어.
```

Later `.json` format:

```json
{
  "type": "text",
  "text": "오늘 점심은 12만 루피아. 맛은 좋았지만 무거웠고, 오후에는 2시간 작업했어.",
  "media_url": null,
  "source": "ios_shortcut"
}
```

## Local Processing

Run:

```bash
scripts/process_inbox.py
```

The script reads:

```txt
data/inbox/local/*.txt
data/inbox/local/*.json
data/inbox/cloud/*.txt
data/inbox/cloud/*.json
```

Then it:

- saves captures to `data/captures/YYYY-MM-DD.jsonl`
- updates `data/context/latest-captures.json`
- regenerates `dashboard/today.json`
- regenerates `dashboard/life-balance.json`
- moves processed inbox files to `data/sync/processed/YYYY-MM-DD/`

## iCloud Folder Setup

Initial simple option:

1. Create an iCloud Drive folder for Nomad Life captures.
2. Periodically copy or sync files into `data/inbox/cloud`.
3. Run `scripts/process_inbox.py`.

Later option:

- Replace `data/inbox/cloud` with a symlink to the iCloud Drive folder, if this is stable on the user's machine.

Do not make this symlink until the actual iCloud folder path is confirmed.

## Evening Review Candidate

Early manual command:

```bash
scripts/process_inbox.py && scripts/generate_daily_brief.py
```

Later automation:

- Every evening at 22:00, process inbox files and generate review.
- Keep this local-first.
- Do not create cloud actions without explicit approval.

## Open Questions To Review After Real Use

- Is iCloud sync delay acceptable?
- Are text captures enough, or are photo/receipt captures needed soon?
- Should the Shortcut write `.txt` or `.json`?
- Should the Mac process inbox files manually, on login, every few minutes, or only in the evening?
- Which capture types are safe to store in iCloud as raw text?

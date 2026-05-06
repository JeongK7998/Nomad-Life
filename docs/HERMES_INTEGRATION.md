# Hermes Integration

Hermes is installed locally and available at:

```txt
/Users/jongiljeong/.local/bin/hermes
```

Verified:

```txt
Hermes Agent v0.12.0
Provider: OpenAI Codex
Model: gpt-5.5
```

Hermes successfully reads this project's `AGENTS.md` when run from the project root.

## Runtime Boundary

Nomad Life keeps a clear split between deterministic local scripts and Hermes interpretation.

```txt
Local scripts:
- Move files
- Parse obvious fields
- Update JSONL
- Export dashboard JSON
- Keep action logs

Hermes:
- Read AGENTS.md
- Read Nomad Skills
- Interpret life context
- Generate richer briefs
- Coordinate skill outputs
- Propose actions that may require approval
```

## Cloud-Light Worker Boundary

Mac Hermes Worker is the only component that may use Supabase service-role credentials.

```txt
Vercel Dashboard / Quick Panels
  -> Supabase queue rows with anon/auth credentials
  -> Mac Hermes Worker with service role
  -> local JSON/JSONL contracts
  -> dashboard refresh
  -> Supabase dashboard snapshots
```

Worker command:

```bash
scripts/supabase_worker.py --process --publish-snapshots
```

Rules:

- Do not place `SUPABASE_SERVICE_ROLE_KEY` in Vercel or browser code.
- Do not run Hermes inside Vercel.
- Do not process private Mac app context in Supabase.
- Queue rows are input requests; they are not approved external app actions.
- Failed queue rows remain inspectable.

## Local App Boundary

Hermes does not currently have dedicated Calendar, Notes, or Reminders MCP servers configured.

Local app access therefore starts through project-owned read-only bridge scripts:

```bash
scripts/read_calendar_context.py
scripts/read_notes_context.py --folder "Nomad Life"
```

The daily runner can include these snapshots explicitly:

```bash
scripts/run_nomad_daily.py --include-local-apps
```

These scripts write normalized context files under `data/context/` and append action logs. Hermes should read those JSON files instead of directly scraping personal apps.

## Coordinator Chat

Nomad Dashboard is not the main conversation surface. It is the dashboard, input, and approval UI.

The user-facing conversational surface should be Coordinator-only:

```txt
User chat message
  ↓
Hermes Coordinator
  ↓
read dashboard/context/reports
  ↓
single response
```

Local test command:

```bash
scripts/run_hermes_coordinator_chat.py "오늘 캘린더와 노트 기준으로 뭐부터 하면 좋을까?"
```

Rules:

- Read local context only.
- Do not modify files, calendars, notes, reminders, or external apps.
- Do not talk as separate domain agents.
- Preserve uncertainty from partial snapshots.
- Treat Telegram as conversation/notification, not durable storage.

See:

```txt
docs/COMMUNICATION_LAYER.md
```

## Command Contract

The main local entrypoint is:

```bash
scripts/run_nomad_daily.py
```

It should be safe to run repeatedly. It performs local deterministic work and prints a JSON summary.

Initial behavior:

```txt
1. Process local and fallback iCloud inbox files
2. Generate daily brief
3. Export dashboard/today.json
4. Export dashboard/life-balance.json
5. Print machine-readable summary
```

## Hermes One-Shot Smoke Test

```bash
/Users/jongiljeong/.local/bin/hermes -z "Nomad Life 프로젝트의 AGENTS.md를 기준으로, 한 문장으로 이 프로젝트의 핵심을 말해줘."
```

Expected behavior:

- Hermes responds using this project's AGENTS.md
- It identifies Hermes Runtime as the center
- It describes the web app as cockpit, not the agent itself

## Future Hermes Daily Brief

Once the local runner is stable, Hermes can be asked to enrich the brief:

```bash
/Users/jongiljeong/.local/bin/hermes -z "AGENTS.md와 skills/nomad-coordinator/SKILL.md를 기준으로 dashboard/today.json과 data/context/latest-captures.json을 읽고 오늘의 Coordinator Brief를 더 자연스럽게 개선해줘. 파일 수정은 하지 말고 개선 제안만 출력해줘."
```

File writing by Hermes should be added only after the output contract is stable.

## Hermes Coordinator Enrichment Draft

The first Hermes interpretation step is read-only from the agent's point of view. Hermes reads project files and prints a draft. The wrapper script stores that stdout as a draft artifact.

Command:

```bash
scripts/run_hermes_coordinator_draft.py --date YYYY-MM-DD
```

Output:

```txt
reports/daily/YYYY-MM-DD-hermes-draft.md
```

Rules:

- Hermes must not modify files directly in this step.
- The draft is review material, not the canonical daily brief.
- The deterministic local dashboard remains the source of truth until the draft format is approved.
- The draft must preserve uncertainty from partial data.
- The draft must not suggest sensitive actions as already approved.

## Cron Candidate

Do not enable this until manual runs are stable.

Example command shape:

```bash
/Users/jongiljeong/.local/bin/hermes cron create \
  --name "Nomad Morning Brief" \
  --workdir "/Users/jongiljeong/Projects/Nomad_Life" \
  --script "scripts/run_nomad_daily.py" \
  "0 8 * * *" \
  "Review the script output and produce a concise Nomad Life morning brief."
```

The project currently keeps cron manual/off by default.

## Open Questions

- Should Hermes write final reports directly, or only propose improved text first?
- Which actions are allowed in Hermes cron without user confirmation?
- Should Hermes use custom Nomad Skills through its `--skills` flag, or only project files at first?
- When should morning/evening schedules be activated?

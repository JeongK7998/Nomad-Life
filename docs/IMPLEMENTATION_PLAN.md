# Nomad Life Implementation Plan

This plan follows AGENTS.md. The project should remain Hermes-first, local-first for sensitive context, privacy-aware, and Dashboard-oriented.

## 2026 Cloud-Light Route Update

Nomad Dashboard must be visible from Mac, iPad, and iPhone. Same-Wi-Fi local hosting is too restrictive for the product direction.

Current route:

```txt
GitHub source
  -> Vercel-hosted Nomad Dashboard / Quick Panels
  -> Supabase queue + dashboard snapshots
  -> Mac Hermes Worker
  -> local data / skills / reports
  -> Supabase snapshot publish
  -> Dashboard on all devices
```

This updates the previous iCloud-first mobile inbox route:

- Supabase queue is the primary path for structured mobile/web inputs.
- iCloud Drive remains fallback/dropbox for offline files, photos, receipts, and exports.
- Hermes stays on the Mac and remains the runtime center.
- Vercel hosts the UI but does not run Hermes.

## Planning Posture

Before adding detailed workflow features, Nomad Life should define and validate the large system blocks first.

Current priority:

1. Clarify the responsibility of each major block.
2. Confirm the boundary between capture, conversation, analysis, dashboard, notification, and approval.
3. Keep detailed domain features as candidates until their scope is agreed.
4. Prefer thin vertical tests that prove block-to-block communication over polished feature depth.

Detailed behaviors such as expense confirmation, meal review, action approval flows, and notification sending should be specified only after the relevant block boundary is confirmed with the user.

## Macro Architecture Blocks

```txt
Mobile / Web / Telegram Inputs
        ↓
Supabase Queue / Local Capture Boundary
        ↓
Local Data Contracts
        ↓
Hermes Runtime + Coordinator
        ↓
Domain Skills / Context Agents
        ↓
Reports / Dashboard / Candidates
        ↓
Nomad Dashboard / Quick Panels / Telegram Response / Future Notifications
```

### A. Input Block

Purpose: receive user input from iPhone, iPad, web cockpit, Telegram, and local files.

Scope:

- Quick capture
- Explicit Telegram capture
- Supabase capture queue
- Supabase workout queue
- iCloud Drive fallback inbox
- Local web capture

Out of scope until confirmed:

- Rich photo/OCR workflows
- Voice transcription pipeline
- Hosted capture API
- Dedicated finance/expense entry UI. Finance uses external finance app exports or read-only imports.

### B. Data Contract Block

Purpose: make all intermediate artifacts explicit and inspectable.

Scope:

- `data/captures/*.jsonl`
- `data/context/*.json`
- `dashboard/*.json`
- `reports/**/*.md`
- `data/*/*-candidates.json`
- `data/action_logs/*.jsonl`

Out of scope until confirmed:

- Database migration
- Multi-user schema
- External hosted storage as source of truth

### C. Hermes Runtime Block

Purpose: keep Hermes as the central reasoning and orchestration runtime.

Scope:

- Read AGENTS.md and project docs
- Use local scripts as deterministic tools
- Coordinate domain Skills
- Produce drafts, summaries, and recommendations

Out of scope until confirmed:

- Direct write access to external apps
- Autonomous sensitive actions
- Replacing local file contracts with opaque agent memory

### D. Local Context Block

Purpose: bring personal Mac context into the system safely.

Scope:

- Apple Calendar read-only context
- Apple Notes limited-folder read-only context
- Future Reminders read-only context

Out of scope until confirmed:

- Calendar creation/editing
- Notes body-wide scanning
- Health, Photos, Mail, or financial app access

### E. Skill Council Block

Purpose: define the domain agents conceptually before deep automation.

Initial domains:

- Coordinator
- Quick Capture
- Calendar Context
- Notes Context
- Finance
- Health
- English

Future domains:

- Food
- Work
- Rest
- Travel Guide
- Creator
- Social
- Weekly Review

Out of scope until confirmed:

- Fully autonomous sub-agent execution
- Cross-agent debate UI
- Domain-specific action execution

### F. Dashboard Block

Purpose: show state, reports, candidates, and approval surfaces.

Scope:

- Today Dashboard
- Captures
- Local Context
- Agent Council
- Candidate lists
- Action Center placeholder

Out of scope until confirmed:

- Complex editing workflows
- Final approval UX for money/calendar/reminders
- Hermes execution inside Vercel

### G. Communication Block

Purpose: give the user one coherent conversational surface through Coordinator.

Scope:

- Telegram conversation
- Telegram explicit capture
- Local Hermes chat simulation

Out of scope until confirmed:

- Proactive Telegram notifications
- Voice conversation
- Multi-agent direct chat

### H. Automation Block

Purpose: run repeated local tasks only after manual flows are stable.

Scope:

- Manual daily runner
- Candidate morning/evening/weekly jobs
- Logs for every run

Out of scope until confirmed:

- Always-on background service as default
- Cron sending notifications
- Auto-actions that mutate external apps

### I. Cloud-Light Block

Purpose: improve availability without moving private reasoning away from the Mac.

Scope:

- Supabase queue
- Supabase dashboard snapshots
- Vercel-hosted Dashboard and Quick Panels
- GitHub deployment flow
- Future cron trigger

Out of scope until confirmed:

- VPS as primary personal data brain
- Cloud processing of sensitive personal context by default
- Cloud-hosted source of truth
- Service-role keys in browser/Vercel

## MVP Block Scope Review

This section is the working boundary for the next phase. It should be reviewed with the user before adding detailed domain workflows.

| Block | MVP Status | Current Implementation | MVP Decision |
| --- | --- | --- | --- |
| A. Input | include | Web capture, Workout Quick, iCloud fallback, Telegram explicit capture | move primary mobile structured input to Supabase queue |
| B. Data Contract | include | captures, context, dashboard, reports, action logs, candidates | keep local JSON/JSONL as source of truth |
| C. Hermes Runtime | include | Hermes installed, Telegram gateway connected, local runner available | Hermes coordinates and interprets; deterministic scripts keep contracts stable |
| D. Local Context | include thin | Apple Calendar read-only, Apple Notes folder metadata read-only | keep read-only; Reminders later |
| E. Skill Council | include conceptual | Coordinator, Quick Capture, Finance, Health, English, Calendar, Notes skill docs | define skill roles before deep automation |
| F. Dashboard | include thin | Today, Captures, Health, Local Context, Council, Notifications, Candidates | Dashboard shows state on all devices |
| G. Communication | include | Telegram Coordinator chat and explicit capture | no proactive sends yet |
| H. Automation | manual only | `run_nomad_daily.py`, gateway manual run | no cron/service until manual flows settle |
| I. Cloud-Light | include foundation | Vercel config, Supabase schema, worker skeleton | use Supabase as queue/snapshot layer, not brain |

### MVP Shape

The near-term MVP is not a feature-rich app. It is a stable operating loop:

```txt
Input
  -> Local data contract
  -> Local context snapshot
  -> Hermes Coordinator interpretation
  -> Dashboard/report/candidate output
  -> User review through cockpit or Telegram
```

The MVP should answer:

- Can the user capture life context from the devices they actually use?
- Can Hermes read that context through stable local files?
- Can the Coordinator explain the day/week without overreaching?
- Can the cockpit show enough state to make the system trustworthy?
- Can sensitive actions remain clearly outside automation until approved?

### Thin Vertical Slices

Use thin slices to validate block connections:

1. Capture slice
   - Telegram/Web/iCloud input
   - `data/captures/*.jsonl`
   - `data/context/latest-captures.json`
   - Today dashboard update

2. Local context slice
   - Calendar/Notes read-only scripts
   - `data/context/*.json`
   - Coordinator/cockpit context display

3. Conversation slice
   - Telegram question
   - Hermes Coordinator
   - Local files/context
   - Unified Korean response

4. Report slice
   - Manual daily runner
   - dashboard JSON
   - report markdown
   - action log

5. Candidate slice
   - Derived candidate files
   - Cockpit visibility
   - No confirmation or external mutation yet

6. Sample sub-agent slice
   - Health reads exercise captures and produces health dashboard signals
   - English reads study captures or transcript metadata and produces english dashboard signals
   - Calendar Context provides schedule density to Coordinator
   - Coordinator explains how these signals should appear on the final dashboard

7. Activity allocation dashboard slice
   - Parse clear time expressions from captures
   - Generate `data/context/activity-allocation.json`
   - Generate `dashboard/activity-allocation.json`
   - Show today's tracked time, area shares, and candidate sessions in the Dashboard
   - Keep all sessions as candidates until correction/confirmation rules are agreed

### Confirm Before Implementing

Ask the user before implementing:

- Any workflow that mutates Calendar, Notes, Reminders, files outside the project, or external apps.
- Any automatic Telegram notification send.
- Any background service, cron, or always-on gateway installation.
- Any new cloud provider beyond the agreed GitHub/Vercel/Supabase path.
- Any detailed confirmation/editing flow for finance, food, health, or actions.
- Any expansion from limited Notes metadata to broad Notes body access.
- Any move from candidates to canonical domain records.

No confirmation is needed for:

- Documentation updates that clarify already agreed principles.
- Read-only local script checks.
- Local JSON/dashboard/report regeneration.
- Non-destructive Dashboard display of existing local files.

## Block 1. Local-First Project Skeleton

Goal: create the durable filesystem boundaries that Hermes, scripts, future cron jobs, and the Dashboard can share.

Deliverables:

- Standard data folders
- Local/cloud inbox folders
- Sync queue folders
- Reports and dashboard folders
- MVP skill folders
- Initial documentation

Status: in progress

## Block 2. MVP 1 Skill Documents

Goal: define the first skills before implementing behavior.

Skills:

- nomad-quick-capture
- nomad-finance
- nomad-food
- nomad-coordinator
- nomad-dashboard-export

Each skill must define purpose, input data, files read, tools, procedure, output format, forbidden actions, and examples.

## Block 3. Data Contracts And Sample Outputs

Goal: make the file contracts visible before adding automation.

Deliverables:

- Sample capture JSONL
- Sample normalized expense and meal JSON
- Sample today dashboard JSON
- Sample life balance JSON
- JSON schema notes

## Block 4. Quick Capture Script

Goal: accept a simple text capture and write a structured record.

Initial behavior:

- Save raw input
- Tag likely agents
- Extract obvious amount, currency, food, work, health, rest, English, and content hints
- Mark uncertainty explicitly
- Write `data/captures/YYYY-MM-DD.jsonl`
- Update `data/context/latest-captures.json`

## Block 5. Daily Brief And Dashboard Export

Goal: convert local records into a useful daily operating brief.

Initial behavior:

- Read recent captures
- Generate simple agent council summaries
- Generate coordinator brief markdown
- Export `dashboard/today.json`
- Export `dashboard/life-balance.json`

## Block 6. Basic Nomad Dashboard

Goal: provide a UI that reads generated files instead of acting as the primary agent runtime.

Screens:

- Quick Capture
- Today Dashboard
- Agent Council
- Life Dashboard
- Action Center placeholder

Design direction:

- Use the Nomad Life Design System documented in `docs/DESIGN_SYSTEM.md`.
- Keep the Dashboard dense, calm, and operational.
- Do not use Wanted logos or career-product-specific brand patterns.
- Use local dashboard JSON as the UI data source.

## Block 7. Mobile Input And Cloud-Light Sync

Goal: support iPhone/iPad capture and Dashboard access without requiring same-Wi-Fi MacBook access.

Decision:

- Use Supabase queue first for structured Quick Panel inputs.
- Use Local Dashboard for immediate feedback while MacBook is running.
- Keep iCloud Drive as fallback/dropbox for files, photos, receipts, and exports.

Deliverables:

- `docs/MOBILE_INBOX.md`
- `docs/CLOUD_LIGHT_ARCHITECTURE.md`
- `docs/DEPLOYMENT_GUIDE.md`
- `supabase/migrations/0001_cloud_light.sql`
- `scripts/supabase_worker.py`
- `scripts/process_inbox.py`
- Local web `POST /api/capture`
- Supabase capture/workout queue payloads
- Dashboard snapshot publish
- Evening review automation candidate after worker is stable

Status: in progress

## Block 8. Cron And Approve-To-Act

Goal: add repeated workflows and user-approved actions only after the local flow proves useful.

Initial automations:

- Morning brief
- Evening capture review
- Budget watch
- Weekly strategy review

Sensitive actions must remain approval-based.

## Block H1. Hermes Runtime Connection

Goal: connect the local filesystem harness to Hermes without handing over unstable behavior too early.

Status: in progress

Deliverables:

- Verify Hermes installation
- Verify Hermes reads project `AGENTS.md`
- Define command contract in `docs/HERMES_INTEGRATION.md`
- Add deterministic local runner `scripts/run_nomad_daily.py`
- Keep Hermes cron disabled until manual runs are stable

## Block H2. Hermes Coordinator Enrichment

Goal: let Hermes improve the Coordinator Brief without directly modifying canonical dashboard or report files.

Status: in progress

Deliverables:

- `scripts/run_hermes_coordinator_draft.py`
- `reports/daily/YYYY-MM-DD-hermes-draft.md`
- Read-only Hermes prompt contract
- Manual review before adopting Hermes output as canonical

## Block H3. Coordinator Conversation Layer

Goal: add a user-facing conversation path that preserves the Coordinator single-channel rule.

Status: in progress

Deliverables:

- `docs/COMMUNICATION_LAYER.md`
- `scripts/run_hermes_coordinator_chat.py`
- Local CLI simulation for Telegram-style chat
- Read-only context contract for chat responses
- Notification policy before enabling Telegram alerts
- `scripts/generate_notifications.py`
- `dashboard/notifications.json`
- Dashboard Notification Candidates section

Conversation sources:

- `dashboard/today.json`
- `dashboard/life-balance.json`
- `data/context/latest-captures.json`
- `data/context/calendar-context.json`
- `data/context/notes-context.json`
- daily reports

Next steps:

- Add Telegram configuration only after local chat behavior is stable.
- Add sparse notification candidates.
- Keep Telegram as conversation/notification, not durable storage.

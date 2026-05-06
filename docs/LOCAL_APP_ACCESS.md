# Local App Access

Nomad Life treats macOS app data as sensitive local context. Hermes should not reach into personal apps directly until a small read-only bridge has a stable contract.

## Current Hermes Capability

Hermes currently has local runtime tools such as file access, terminal execution, code execution, cron jobs, skills, memory, browser automation, vision, and delegation.

No dedicated MCP server is currently configured for Calendar, Notes, Reminders, Photos, or Health.

This means local app access starts through project-owned scripts that Hermes can run or inspect. Later, the same contracts can be moved behind MCP without changing the rest of the system.

## Access Principles

- Start with read-only access.
- Store normalized snapshots under `data/context/`.
- Do not write back to Calendar, Notes, Reminders, or other personal apps in MVP tests.
- Prefer narrow scopes over whole-app reads.
- Log every local app read.
- Preserve uncertainty and partial failures in output JSON.
- Keep app-derived data out of the web app unless it has first been normalized.

## Sample Context Agents

### Calendar Context Agent

Purpose:

- Read today's and tomorrow's Apple Calendar events.
- Estimate schedule density, travel pressure, and recovery windows.
- Feed `nomad-travel-guide`, `nomad-rest`, and `nomad-coordinator`.

Output:

```txt
data/context/calendar-context.json
```

Script:

```bash
scripts/read_calendar_context.py
```

### Notes Context Agent

Purpose:

- Read only a constrained Apple Notes scope.
- Start with a dedicated folder such as `Nomad Life`.
- Feed `nomad-quick-capture`, `nomad-work`, `nomad-creator`, and `nomad-coordinator`.

Output:

```txt
data/context/notes-context.json
```

Script:

```bash
scripts/read_notes_context.py --folder "Nomad Life"
```

By default, the Notes bridge stores note metadata and short previews only. Full note body ingestion should be enabled later only after the folder rule feels safe.

## Pipeline

```txt
macOS app
  ↓
read-only bridge script
  ↓
data/context/*.json
  ↓
deterministic daily pipeline
  ↓
Hermes Coordinator draft
  ↓
web cockpit
```

## Permission Notes

The first run may trigger macOS Automation or app data permission prompts. The user should approve only the minimum app requested for the test being run.

If permissions are denied, scripts must still write a JSON file with `data_quality.status = "unavailable"` and a human-readable error.

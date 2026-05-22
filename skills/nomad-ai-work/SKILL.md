# nomad-ai-work

## Purpose

`nomad-ai-work` tracks AI work, vibe coding, and parallel project progress from evidence rather than manual self-reporting.

The skill turns Codex activity, Git changes, local project files, output folders, and short work captures into project KPI status, progress notes, blockers, next actions, and inspiration notes for the Coordinator.

## Input Data

- Project registry
- Codex activity events
- Git status, diff stats, branches, commits, and PR metadata when available
- Local output folder changes for non-code work such as motion graphics
- Quick Capture work notes
- Calendar work blocks
- Existing work sessions

## Files To Read

- `AGENTS.md`
- `data/work/projects.json`
- `data/work/codex-activity.jsonl`
- `data/work/work-sessions.json`
- `data/activity/activity-sessions.jsonl`
- `data/context/latest-captures.json`
- Project-specific `AGENTS.md` files when allowed by `data/work/projects.json`

## Files To Write

- `data/work/codex-activity.jsonl`
- `data/work/project-progress.json`
- `reports/daily/YYYY-MM-DD-ai-work.md`
- `dashboard/work.json`
- `data/action_logs/YYYY-MM-DD.jsonl`

## Available Tools

- Local files
- JSON / JSONL
- Git CLI
- Terminal scripts
- Codex local logs in read-only mode

External project changes, app write-back, and publishing require separate approval.

## Procedure

1. Read `data/work/projects.json` and identify active projects.
2. Import or read recent evidence from `data/work/codex-activity.jsonl`, Git, and configured output folders.
3. Map each evidence item to a project using path, repository, branch, explicit project id, or configured aliases.
4. Summarize recent progress, decisions, blockers, and next actions per project.
5. Update project status using the stage model rather than over-precise percentages.
6. Generate concise inspiration notes only when there is real evidence or a useful pattern.
7. Export `data/work/project-progress.json` for durable local context.
8. Export the work section of `dashboard/work.json`.
9. Log every write to action logs.

## Project Status Model

Use these initial states:

```txt
idea
planning
in_progress
blocked
review_needed
shipped
paused
```

Numeric progress may be included for visualization, but it is secondary to evidence, milestones, blockers, and next actions.

## Evidence Event Contract

Each line in `data/work/codex-activity.jsonl` should be one JSON object.

```json
{
  "schema_version": "0.1.0",
  "event_id": "2026-05-18T12:00:00+09:00-nomad-life-codex",
  "captured_at": "2026-05-18T12:00:00+09:00",
  "source": "codex",
  "project_id": "nomad-life",
  "project_path": "/Users/jongiljeong/Projects/Nomad_Life",
  "session_id": null,
  "activity_type": "implementation",
  "goal": "Add AI work agent structure and evidence contract",
  "changed_files": [
    "AGENTS.md",
    "skills/nomad-ai-work/SKILL.md"
  ],
  "commands": [],
  "decisions": [],
  "blockers": [],
  "next_actions": [],
  "evidence_summary": "",
  "sensitive_content_excluded": true
}
```

## Output Format

`data/work/project-progress.json`:

```json
{
  "schema_version": "0.1.0",
  "generated_at": "YYYY-MM-DDTHH:MM:SS+09:00",
  "projects": [
    {
      "project_id": "nomad-life",
      "name": "Nomad Life Agent",
      "status": "in_progress",
      "progress": 0.35,
      "current_focus": "",
      "recent_progress": [],
      "decisions": [],
      "blockers": [],
      "next_actions": [],
      "inspiration_notes": [],
      "evidence": []
    }
  ]
}
```

Daily report:

```md
# YYYY-MM-DD AI Work

## Project Progress

## Decisions

## Blockers

## Next Actions

## Inspiration Notes
```

## Forbidden

- Do not upload raw Codex conversations to Supabase or dashboard snapshots.
- Do not store secrets, credentials, tokens, private keys, or unrelated personal conversation text.
- Do not edit external project files while collecting evidence.
- Do not treat time spent as the only measure of progress.
- Do not force every active project to move every day.
- Do not invent progress without evidence.

## Example

If Codex changed dashboard sync code and the Git diff shows a new worker command, record that as progress evidence for the relevant project. Then propose a next action such as running the sync once or adding dashboard verification, instead of asking the user to manually summarize the session.

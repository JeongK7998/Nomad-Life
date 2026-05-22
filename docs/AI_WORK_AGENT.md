# AI Work Agent

## Goal

The AI Work Agent tracks parallel AI, coding, and creative work from automatic evidence instead of manual daily summaries.

## Source Of Truth

- `data/work/projects.json` registers projects, paths, aliases, KPIs, and evidence sources.
- `data/work/codex-activity.jsonl` stores sanitized Codex activity events.
- `data/work/project-progress.json` stores interpreted progress.
- `dashboard/work.json` is the UI-facing snapshot.

## Automation Order

1. Keep global Codex instructions lightweight and privacy-first.
2. Register each tracked project in `data/work/projects.json`.
3. Let Codex append sanitized activity events after meaningful work.
4. Add `scripts/import_codex_activity.py` to read Codex/Git evidence in read-only mode.
5. Connect the importer to Hermes daily runs or `npm run sync`.
6. Generate `project-progress.json`, daily AI work reports, and `dashboard/work.json`.
7. Publish only dashboard snapshots, not raw Codex conversations.

## Global Codex Instruction Needed

The global Codex instruction should tell Codex to leave sanitized work evidence for Nomad Life after meaningful project work. It should not require copying raw conversations or secrets.

Recommended text is now stored in `/Users/jongiljeong/.codex/AGENTS.md`.

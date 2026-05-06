export const WORKOUT_DRAFT_STORAGE_KEY = "nomad_life_workout_draft_v1";

export function reindexStrengthEntries(entries = []) {
  const counts = {};
  return entries.map((entry) => {
    const key = entry.exercise || "exercise";
    counts[key] = (counts[key] || 0) + 1;
    return {
      ...entry,
      set_index: counts[key],
    };
  });
}

export function nextSetIndex(entries = [], exercise) {
  return entries.filter((entry) => entry.exercise === exercise).length + 1;
}

export function buildStrengthWorkoutPayload({ startedAt, muscleGroup, entries, note }) {
  return {
    type: "strength",
    started_at: startedAt,
    ended_at: new Date().toISOString(),
    muscle_group: muscleGroup,
    entries: reindexStrengthEntries(entries),
    note: (note || "").trim(),
  };
}

export function readWorkoutDraft() {
  try {
    const raw = localStorage.getItem(WORKOUT_DRAFT_STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function writeWorkoutDraft(draft) {
  const entries = reindexStrengthEntries(draft.entries || []);
  const normalized = {
    schema_version: "0.1.0",
    updated_at: new Date().toISOString(),
    started_at: draft.started_at || new Date().toISOString(),
    entries,
    note: draft.note || "",
    form_state: draft.form_state || {},
    source: draft.source || "workout_form",
  };
  localStorage.setItem(WORKOUT_DRAFT_STORAGE_KEY, JSON.stringify(normalized));
  return normalized;
}

export function clearWorkoutDraft() {
  localStorage.removeItem(WORKOUT_DRAFT_STORAGE_KEY);
}

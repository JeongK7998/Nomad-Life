import {
  buildStrengthWorkoutPayload,
  clearWorkoutDraft,
  nextSetIndex,
  readWorkoutDraft,
  reindexStrengthEntries,
  writeWorkoutDraft,
  WORKOUT_DRAFT_STORAGE_KEY,
} from "./workout-shared.js?v=20260506-workout-shared";
import {
  getNomadAuthToken,
  getNomadUserId,
  initNomadAuth,
  isNomadCloudMode,
  requireNomadSession,
} from "./nomad-auth.js?v=20260520-auth";

const muscleSelect = document.querySelector("#muscle-select");
const exerciseSelect = document.querySelector("#exercise-select");
const favoriteButton = document.querySelector("#favorite-button");
const infoButton = document.querySelector("#info-button");
const resetButton = document.querySelector("#reset-button");
const recentButton = document.querySelector("#recent-button");
const manageButton = document.querySelector("#manage-button");
const latestGuide = document.querySelector("#latest-guide");
const weightInput = document.querySelector("#weight-input");
const repsInput = document.querySelector("#reps-input");
const rpeInput = document.querySelector("#rpe-input");
const addSetButton = document.querySelector("#add-set");
const saveWorkoutButton = document.querySelector("#save-workout");
const draftList = document.querySelector("#draft-list");
const quickStatus = document.querySelector("#quick-status");
const noteInput = document.querySelector("#note-input");
const timeButton = document.querySelector("#time-button");
const timeButtonValue = document.querySelector("#time-button-value");
const timeStatus = document.querySelector("#time-status");
const timePanel = document.querySelector("#time-panel");
const startDate = document.querySelector("#start-date");
const startTime = document.querySelector("#start-time");
const applyTime = document.querySelector("#apply-time");
const quickForm = document.querySelector("#quick-form");
const workoutCategoryPanel = document.querySelector("#workout-category-panel");
const workoutDetailPanel = document.querySelector("#workout-detail-panel");
const backToCategory = document.querySelector("#back-to-category");
const selectedCategoryLabel = document.querySelector("#selected-category-label");
const dialog = document.querySelector("#exercise-dialog");
const dialogTitle = document.querySelector("#dialog-title");
const dialogContent = document.querySelector("#dialog-content");

const MUSCLE_LABELS = {
  chest: "가슴",
  back: "등",
  legs: "하체",
  shoulders: "어깨",
  arms: "팔",
  core: "코어",
  full_body: "전신",
  other: "기타",
};

const QUICK_AREA_PREFILL_KEY = "nomad_quick_prefill_area";
const QUICK_ACTIVITY_AREAS = new Set(["work", "health", "food", "english", "creator", "travel", "social", "rest"]);
const LOCAL_EXERCISE_MUTATIONS_KEY = "nomad.exerciseLibraryMutations.v1";
const NOMAD_CURRENT_STAY_STORAGE_KEY = "nomad.currentStay.v1";
const NOMAD_INPUT_HISTORY_STORAGE_KEY = "nomad.inputHistory.v1";
const NOMAD_PENDING_HEALTH_STORAGE_KEY = "nomad.pendingHealth.v1";
const NOMAD_CLOUD_QUEUE_FALLBACK_KEY = "nomad.cloudQueueFallback.v1";
const DEFAULT_CURRENT_STAY = {
  stay_id: "bali-2026-05",
  region: "Bali",
  country: "Indonesia",
  timezone: "Asia/Makassar",
  dataset_scope: "current",
};

let exerciseLibrary = [];
let allExerciseLibrary = [];
let managerEditingExerciseId = null;
let managerMuscleFilter = "all";
let workoutHistorySessions = [];
let workoutEntries = [];
let workoutStartedAt = new Date().toISOString();
let editingIndex = null;
let editingReturnState = null;
let appConfig = {
  mode: "local",
  supabaseUrl: "",
  supabaseAnonKey: "",
};

function isSupabaseMode() {
  return isNomadCloudMode(appConfig);
}

function normalizeCurrentStay(stay = {}) {
  const merged = { ...DEFAULT_CURRENT_STAY, ...(stay || {}) };
  return {
    stay_id: String(merged.stay_id || DEFAULT_CURRENT_STAY.stay_id).trim(),
    region: String(merged.region || DEFAULT_CURRENT_STAY.region).trim(),
    country: String(merged.country || DEFAULT_CURRENT_STAY.country).trim(),
    timezone: String(merged.timezone || DEFAULT_CURRENT_STAY.timezone).trim(),
    dataset_scope: String(merged.dataset_scope || DEFAULT_CURRENT_STAY.dataset_scope).trim(),
  };
}

function currentStayContext() {
  try {
    return normalizeCurrentStay(JSON.parse(localStorage.getItem(NOMAD_CURRENT_STAY_STORAGE_KEY) || "null") || DEFAULT_CURRENT_STAY);
  } catch {
    return normalizeCurrentStay(DEFAULT_CURRENT_STAY);
  }
}

function appendInputHistory(record = {}) {
  try {
    const records = JSON.parse(localStorage.getItem(NOMAD_INPUT_HISTORY_STORAGE_KEY) || "[]");
    const next = Array.isArray(records) ? records : [];
    next.push({
      id: `input_${Date.now().toString(36)}`,
      captured_at: new Date().toISOString(),
      status: "saved",
      raw_content: record.raw_content || "Workout saved",
      linked_agents: ["nomad-health"],
      stay: currentStayContext(),
      ...record,
    });
    localStorage.setItem(NOMAD_INPUT_HISTORY_STORAGE_KEY, JSON.stringify(next.slice(-80)));
  } catch {
    // Saving workout should not fail because local display history is unavailable.
  }
}

function workoutFingerprint(session = {}) {
  const entries = (session.entries || [])
    .map((entry) => [
      entry.exercise || "",
      entry.muscle_group || "",
      Number(entry.set_index || 0),
      Number(entry.weight_kg || 0),
      Number(entry.reps || 0),
      Number(entry.rpe || 0),
    ].join(":"))
    .sort()
    .join("|");
  const date = String(session.date || session.started_at || "").slice(0, 10);
  return [date, Number(session.duration_minutes || 0), String(session.note || "").trim(), entries].join("::");
}

function appendPendingHealthWorkout(payload = {}) {
  try {
    const records = JSON.parse(localStorage.getItem(NOMAD_PENDING_HEALTH_STORAGE_KEY) || "{}");
    const workouts = Array.isArray(records.workouts) ? records.workouts : [];
    const item = {
      id: `pending_workout_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 7)}`,
      source: "pending_quick_save",
      status: "completed",
      date: String(payload.started_at || new Date().toISOString()).slice(0, 10),
      started_at: payload.started_at || new Date().toISOString(),
      duration_minutes: Number(payload.duration_minutes || 0),
      activity_type: "strength",
      muscle_group: payload.muscle_group || payload.entries?.[0]?.muscle_group || "full_body",
      entries: payload.entries || [],
      note: payload.note || "",
      pending_analysis: true,
      stay: payload.stay || currentStayContext(),
    };
    const next = [...workouts, item];
    const seen = new Set();
    const unique = next.filter((workout) => {
      const key = workoutFingerprint(workout);
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
    localStorage.setItem(NOMAD_PENDING_HEALTH_STORAGE_KEY, JSON.stringify({
      ...records,
      workouts: unique.slice(-80),
      activities: Array.isArray(records.activities) ? records.activities.slice(-80) : [],
    }));
  } catch {
    // Saving workout should not fail because local pending display is unavailable.
  }
}

function installInputFocusMode() {
  const focusSelector = 'input:not([type="hidden"]), select, textarea';
  let activeSurface = null;
  const surfaceSelector = [
    "dialog[open]",
    ".quick-card",
    ".quick-dialog form",
    ".quick-add-dialog",
    ".auth-panel",
    "form",
  ].join(", ");

  const clear = () => {
    activeSurface?.classList.remove("input-focus-surface");
    activeSurface = null;
    document.body.classList.remove("input-focus-active");
  };

  document.addEventListener("focusin", (event) => {
    const target = event.target.closest?.(focusSelector);
    if (!target) return;
    activeSurface?.classList.remove("input-focus-surface");
    activeSurface = target.closest(surfaceSelector) || target.parentElement;
    activeSurface?.classList.add("input-focus-surface");
    document.body.classList.add("input-focus-active");
    window.requestAnimationFrame(() => {
      target.scrollIntoView({ block: "center", inline: "nearest", behavior: "smooth" });
    });
  });

  document.addEventListener("focusout", () => {
    window.setTimeout(() => {
      if (!document.activeElement?.closest?.(focusSelector)) {
        clear();
      }
    }, 80);
  });
}

function showCategoryPanel() {
  workoutCategoryPanel.hidden = false;
  workoutDetailPanel.hidden = true;
}

function showDetailPanel(category = muscleSelect.value) {
  muscleSelect.value = category || "chest";
  refreshExerciseOptions();
  selectedCategoryLabel.textContent = "운동";
  workoutCategoryPanel.hidden = true;
  workoutDetailPanel.hidden = false;
  persistDraft();
}

function openNomadQuick(area) {
  if (QUICK_ACTIVITY_AREAS.has(area)) {
    localStorage.setItem(QUICK_AREA_PREFILL_KEY, area);
  }
  window.location.href = "/web/#quick";
}

function escapeHtml(value = "") {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function toLocalDateTimeValue(date = new Date()) {
  const localDate = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
  return localDate.toISOString().slice(0, 16);
}

function setTimeFields(date = new Date()) {
  const [datePart, timePart] = toLocalDateTimeValue(date).split("T");
  startDate.value = datePart;
  startTime.value = timePart;
}

function formatTime(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "시간 확인 필요";
  }
  return new Intl.DateTimeFormat("ko-KR", {
    month: "numeric",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(date);
}

function setWorkoutStartedAt(value = new Date(), persist = true) {
  workoutStartedAt = value.toISOString();
  setTimeFields(value);
  const label = `${formatTime(workoutStartedAt)} 적용`;
  timeButtonValue.textContent = label;
  timeStatus.textContent = label;
  if (persist) {
    persistDraft();
  }
}

async function loadJson(path) {
  const response = await fetch(path, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`${path} 로드 실패`);
  }
  return response.json();
}

async function loadAppConfig() {
  appConfig = await loadJson("/api/config").catch(() => appConfig);
  if (!appConfig.mode) {
    appConfig.mode = "local";
  }
}

async function supabaseRequest(path, options = {}) {
  await requireNomadSession();
  const authToken = getNomadAuthToken();
  const response = await fetch(`${appConfig.supabaseUrl.replace(/\/$/, "")}/rest/v1/${path}`, {
    ...options,
    headers: {
      apikey: appConfig.supabaseAnonKey,
      authorization: `Bearer ${authToken}`,
      "content-type": "application/json",
      accept: "application/json",
      prefer: "return=representation",
      ...(options.headers || {}),
    },
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Supabase ${path} failed`);
  }
  const raw = await response.text();
  return raw ? JSON.parse(raw) : null;
}

async function supabasePublicRequest(path, options = {}) {
  const response = await fetch(`${appConfig.supabaseUrl.replace(/\/$/, "")}/rest/v1/${path}`, {
    ...options,
    headers: {
      apikey: appConfig.supabaseAnonKey,
      authorization: `Bearer ${appConfig.supabaseAnonKey}`,
      "content-type": "application/json",
      accept: "application/json",
      prefer: "return=representation",
      ...(options.headers || {}),
    },
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Supabase ${path} failed`);
  }
  const raw = await response.text();
  return raw ? JSON.parse(raw) : null;
}

function isMissingUserIdSchemaError(error) {
  const message = String(error?.message || error || "");
  return message.includes("PGRST204")
    && message.includes("user_id")
    && message.includes("schema cache");
}

function omitUserId(record) {
  const { user_id: _userId, ...legacyRecord } = record;
  return legacyRecord;
}

function readCloudQueueFallback() {
  try {
    const records = JSON.parse(localStorage.getItem(NOMAD_CLOUD_QUEUE_FALLBACK_KEY) || "[]");
    return Array.isArray(records) ? records : [];
  } catch {
    return [];
  }
}

function writeCloudQueueFallback(records = []) {
  localStorage.setItem(NOMAD_CLOUD_QUEUE_FALLBACK_KEY, JSON.stringify(records.slice(-80)));
}

function storeCloudQueueFallback(table, record, error = null) {
  const item = {
    id: `cloud_fallback_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 7)}`,
    table,
    record,
    created_at: new Date().toISOString(),
    error: String(error?.message || error || "cloud queue unavailable").slice(0, 240),
  };
  writeCloudQueueFallback([...readCloudQueueFallback(), item]);
  return { localPending: true, queuedLocally: true, fallback_id: item.id };
}

async function flushCloudQueueFallback() {
  if (!isSupabaseMode() || !getNomadAuthToken()) return { flushed: 0, remaining: readCloudQueueFallback().length };
  const pending = readCloudQueueFallback();
  if (!pending.length) return { flushed: 0, remaining: 0 };
  const remaining = [];
  let flushed = 0;
  for (const item of pending) {
    const record = {
      ...(item.record || {}),
      user_id: item.record?.user_id || getNomadUserId(),
    };
    try {
      await supabaseRequest(item.table, {
        method: "POST",
        headers: { prefer: "return=minimal" },
        body: JSON.stringify(record),
      });
      flushed += 1;
    } catch (error) {
      remaining.push({ ...item, error: String(error.message || error).slice(0, 240) });
    }
  }
  writeCloudQueueFallback(remaining);
  return { flushed, remaining: remaining.length };
}

async function supabaseQueueInsert(table, record) {
  const requestOptions = {
    method: "POST",
    headers: {
      prefer: "return=minimal",
    },
    body: JSON.stringify(record),
  };
  if (!getNomadAuthToken()) {
    try {
      return await supabasePublicRequest(table, {
        ...requestOptions,
        body: JSON.stringify(omitUserId(record)),
      });
    } catch (error) {
      return storeCloudQueueFallback(table, record, error);
    }
  }
  try {
    return await supabaseRequest(table, requestOptions);
  } catch (error) {
    if (!isMissingUserIdSchemaError(error)) {
      return storeCloudQueueFallback(table, record, error);
    }
    console.warn(`Retrying ${table} insert as legacy anon queue write because the remote schema is still legacy.`);
    try {
      return await supabasePublicRequest(table, {
        method: "POST",
        headers: {
          prefer: "return=minimal",
        },
        body: JSON.stringify(omitUserId(record)),
      });
    } catch (fallbackError) {
      return storeCloudQueueFallback(table, record, fallbackError);
    }
  }
}

async function loadLegacyDashboardSnapshot(snapshotKey) {
  const query = `dashboard_snapshots?select=payload&snapshot_key=eq.${encodeURIComponent(snapshotKey)}&order=created_at.desc&limit=1`;
  const rows = await supabasePublicRequest(query, { method: "GET" });
  if (!rows?.[0]?.payload) {
    throw new Error(`${snapshotKey} legacy snapshot이 아직 없습니다.`);
  }
  return rows[0].payload;
}

async function loadDashboardSnapshot(snapshotKey) {
  const userId = getNomadUserId();
  const query = `dashboard_snapshots?select=payload,user_id&snapshot_key=eq.${encodeURIComponent(snapshotKey)}&user_id=eq.${encodeURIComponent(userId)}&order=created_at.desc&limit=1`;
  try {
    const rows = await supabaseRequest(query, { method: "GET" });
    if (rows?.[0]?.payload) {
      return rows[0].payload;
    }
  } catch (error) {
    console.warn(`Falling back to legacy dashboard snapshot for ${snapshotKey}:`, error.message);
  }
  return loadLegacyDashboardSnapshot(snapshotKey);
}

function exerciseName(exerciseId) {
  const item = exerciseLibrary.find((exercise) => exercise.id === exerciseId);
  return item?.name_ko || item?.name_en || exerciseId;
}

function selectedExercise() {
  return exerciseLibrary.find((exercise) => exercise.id === exerciseSelect.value) || null;
}

function splitCsv(value = "") {
  return value.split(",").map((item) => item.trim()).filter(Boolean);
}

function sortedExerciseItems(items = []) {
  return items.slice().sort((a, b) => {
    const orderA = a.display_order ?? 9999;
    const orderB = b.display_order ?? 9999;
    return Number(orderA) - Number(orderB)
      || Number(b.favorite) - Number(a.favorite)
      || (b.usage_count || 0) - (a.usage_count || 0)
      || (a.name_ko || a.name_en || a.id).localeCompare(b.name_ko || b.name_en || b.id, "ko");
  });
}

function exerciseSlug(value = "") {
  return String(value)
    .trim()
    .toLowerCase()
    .replaceAll("&", "and")
    .replace(/[^a-z0-9가-힣]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function readLocalExerciseMutations() {
  try {
    return JSON.parse(window.localStorage.getItem(LOCAL_EXERCISE_MUTATIONS_KEY) || "[]");
  } catch {
    return [];
  }
}

function writeLocalExerciseMutations(items = []) {
  window.localStorage.setItem(LOCAL_EXERCISE_MUTATIONS_KEY, JSON.stringify(items));
}

function localExerciseId(exercise = {}) {
  const base = exerciseSlug(exercise.name_en || exercise.name_ko || exercise.id) || "custom-exercise";
  return `${base}_${Date.now().toString(36)}`;
}

function normalizeExerciseMutation(action, payload = {}) {
  const normalizedPayload = action === "add" && !payload.exercise ? { exercise: payload } : payload;
  if (action === "add") {
    normalizedPayload.exercise = {
      ...(normalizedPayload.exercise || {}),
      id: normalizedPayload.exercise?.id || localExerciseId(normalizedPayload.exercise),
      source: normalizedPayload.exercise?.source || "custom_pending",
      pending_sync: true,
    };
  }
  return normalizedPayload;
}

function applyLocalExerciseMutations(items = []) {
  const localMutations = readLocalExerciseMutations();
  if (!localMutations.length) {
    return items;
  }
  let next = items.slice();
  localMutations.forEach((mutation) => {
    if (mutation.action === "add" && mutation.exercise) {
      if (!next.some((item) => item.id === mutation.exercise.id)) {
        next.push(mutation.exercise);
      }
      return;
    }
    if (mutation.action === "update" && mutation.exercise_id) {
      next = next.map((item) => item.id === mutation.exercise_id ? { ...item, ...(mutation.updates || {}), pending_sync: true } : item);
      return;
    }
    if (mutation.action === "archive" && mutation.exercise_id) {
      next = next.map((item) => item.id === mutation.exercise_id ? { ...item, archived: Boolean(mutation.archived), pending_sync: true } : item);
      return;
    }
    if (mutation.action === "delete" && mutation.exercise_id) {
      next = next.filter((item) => item.id !== mutation.exercise_id);
      return;
    }
    if (mutation.action === "reorder" && Array.isArray(mutation.ordered_ids)) {
      next = next.map((item) => {
        const order = mutation.ordered_ids.indexOf(item.id);
        return order >= 0 ? { ...item, display_order: order, pending_sync: true } : item;
      });
    }
  });
  return next;
}

function storeLocalExerciseMutation(action, payload = {}) {
  const normalizedPayload = normalizeExerciseMutation(action, payload);
  const mutation = {
    id: `local_mutation_${Date.now().toString(36)}`,
    created_at: new Date().toISOString(),
    action,
    ...normalizedPayload,
  };
  writeLocalExerciseMutations([...readLocalExerciseMutations(), mutation]);
  return { localPending: true, ...normalizedPayload };
}

function isQueuePolicyError(error) {
  return String(error?.message || error || "").includes("row-level security policy")
    || String(error?.message || error || "").includes("42501");
}

function managerMuscleOptions(selectedValue = "other") {
  return Object.entries(MUSCLE_LABELS)
    .map(([value, label]) => `<option value="${value}" ${selectedValue === value ? "selected" : ""}>${label}</option>`)
    .join("");
}

function managerCurrentQuery() {
  return dialogContent.querySelector("#manager-search")?.value || "";
}

function sortedSessions() {
  return workoutHistorySessions.slice().sort((a, b) => (b.started_at || b.created_at || "").localeCompare(a.started_at || a.created_at || ""));
}

function exerciseHistoryItems(exerciseId) {
  const items = [];
  sortedSessions().forEach((session) => {
    const entries = (session.entries || []).filter((entry) => entry.exercise === exerciseId);
    if (!entries.length) {
      return;
    }
    items.push({ session, entries });
  });
  return items;
}

function formatSetLine(entry = {}) {
  const weight = entry.weight_kg ?? "-";
  const reps = entry.reps ?? "-";
  const rpe = entry.rpe ? ` · RPE ${entry.rpe}` : "";
  return `${weight}kg X ${reps}${rpe}`;
}

function updateLatestGuide() {
  const exerciseId = exerciseSelect.value;
  const latestEntries = exerciseHistoryItems(exerciseId)[0]?.entries || [];
  if (!latestEntries.length) {
    latestGuide.textContent = "이전 운동 기록이 있으면 여기에 표시됩니다.";
    weightInput.placeholder = "예: 60";
    repsInput.placeholder = "예: 10";
    return;
  }
  const latest = latestEntries.at(-1);
  weightInput.placeholder = latest.weight_kg ? `${latest.weight_kg}` : "예: 60";
  repsInput.placeholder = latest.reps ? `${latest.reps}` : "예: 10";
  latestGuide.textContent = `최근 ${exerciseName(exerciseId)}: ${latestEntries.map(formatSetLine).join(" · ")}`;
}

function latestEntriesForSelectedExercise() {
  return exerciseHistoryItems(exerciseSelect.value)[0]?.entries || [];
}

function refreshExerciseActions() {
  const item = selectedExercise();
  favoriteButton.classList.toggle("active", Boolean(item?.favorite));
  favoriteButton.disabled = !item;
  infoButton.disabled = !item;
  resetButton.disabled = !item;
  recentButton.disabled = !item;
  updateLatestGuide();
}

function refreshExerciseOptions() {
  const current = exerciseSelect.value;
  const selectedMuscle = muscleSelect.value;
  const options = exerciseLibrary
    .filter((item) => {
      if (selectedMuscle === "other") {
        return true;
      }
      return item.primary_muscle === selectedMuscle || (item.secondary_muscles || []).includes(selectedMuscle);
    })
    .sort((a, b) => Number(b.favorite) - Number(a.favorite) || (b.usage_count || 0) - (a.usage_count || 0) || (a.name_ko || a.name_en).localeCompare(b.name_ko || b.name_en, "ko"));

  exerciseSelect.replaceChildren(
    ...options.map((item) => {
      const option = document.createElement("option");
      option.value = item.id;
      option.textContent = `${item.favorite ? "★ " : ""}${item.name_ko || item.name_en}`;
      return option;
    }),
  );
  if (options.some((item) => item.id === current)) {
    exerciseSelect.value = current;
  }
  if (!exerciseSelect.value && options[0]) {
    exerciseSelect.value = options[0].id;
  }
  refreshExerciseActions();
}

function reindexEntries() {
  workoutEntries = reindexStrengthEntries(workoutEntries);
}

function currentFormState() {
  return {
    muscle: muscleSelect.value,
    exercise: exerciseSelect.value,
    weight: weightInput.value,
    reps: repsInput.value,
    rpe: rpeInput.value,
  };
}

function applyFormState(state) {
  if (!state) {
    return;
  }
  muscleSelect.value = state.muscle || muscleSelect.value;
  refreshExerciseOptions();
  if ([...exerciseSelect.options].some((option) => option.value === state.exercise)) {
    exerciseSelect.value = state.exercise;
  }
  weightInput.value = state.weight ?? weightInput.value;
  repsInput.value = state.reps ?? repsInput.value;
  rpeInput.value = state.rpe ?? "";
  refreshExerciseActions();
}

function loadEntryIntoForm(entry) {
  muscleSelect.value = entry.muscle_group || muscleSelect.value;
  refreshExerciseOptions();
  if ([...exerciseSelect.options].some((option) => option.value === entry.exercise)) {
    exerciseSelect.value = entry.exercise;
  }
  weightInput.value = entry.weight_kg ?? "";
  repsInput.value = entry.reps ?? "";
  rpeInput.value = entry.rpe ?? "";
  refreshExerciseActions();
}

function resetEditMode() {
  editingIndex = null;
  editingReturnState = null;
  addSetButton.textContent = "세트 추가";
}

function persistDraft() {
  writeWorkoutDraft({
    source: "workout_quick",
    started_at: workoutStartedAt,
    entries: workoutEntries,
    note: noteInput.value,
    form_state: currentFormState(),
  });
}

function restoreDraft() {
  const draft = readWorkoutDraft();
  if (!draft || (!(draft.entries || []).length && !draft.note)) {
    return;
  }
  workoutStartedAt = draft.started_at || workoutStartedAt;
  setTimeFields(new Date(workoutStartedAt));
  workoutEntries = reindexStrengthEntries(draft.entries || []);
  noteInput.value = draft.note || "";
  applyFormState(draft.form_state);
  renderDraft();
  const label = `${formatTime(workoutStartedAt)} draft`;
  timeButtonValue.textContent = label;
  timeStatus.textContent = label;
  showDetailPanel(draft.form_state?.muscle || muscleSelect.value);
}

function groupedEntries() {
  const groups = [];
  workoutEntries.forEach((entry, index) => {
    const last = groups.at(-1);
    if (last && last.exercise === entry.exercise) {
      last.items.push({ entry, index });
      return;
    }
    groups.push({
      exercise: entry.exercise,
      muscle: entry.muscle_group,
      items: [{ entry, index }],
    });
  });
  return groups;
}

function newestFirstDraftGroups() {
  return groupedEntries()
    .map((group) => ({
      ...group,
      items: group.items.slice().reverse(),
    }))
    .reverse();
}

function renderDraft() {
  if (!workoutEntries.length) {
    draftList.innerHTML = '<p class="empty">아직 추가된 세트가 없습니다.</p>';
    return;
  }
  draftList.innerHTML = newestFirstDraftGroups().map((group) => `
    <article class="draft-card">
      <header>
        <strong>${escapeHtml(exerciseName(group.exercise))}</strong>
        <span>${escapeHtml(MUSCLE_LABELS[group.muscle] || group.muscle)} · ${group.items.length}set</span>
      </header>
      ${group.items.map(({ entry, index }) => {
        const rpe = entry.rpe ? ` · RPE ${entry.rpe}` : "";
        return `
          <div class="draft-set">
            <span>${entry.set_index}. ${entry.weight_kg}kg X ${entry.reps}${escapeHtml(rpe)}</span>
            <div>
              <button class="ghost-button edit-set" type="button" data-index="${index}">Edit</button>
              <button class="ghost-button remove-set" type="button" data-index="${index}">Remove</button>
            </div>
          </div>
        `;
      }).join("")}
    </article>
  `).join("");
}

function addOrEditSet() {
  const weight = Number(weightInput.value);
  const reps = Number.parseInt(repsInput.value, 10);
  const rpe = rpeInput.value ? Number(rpeInput.value) : null;
  if (!Number.isFinite(weight) || weight < 0 || !Number.isFinite(reps) || reps <= 0) {
    quickStatus.textContent = "무게와 반복 수를 확인하세요.";
    return;
  }
  const entry = {
    muscle_group: muscleSelect.value,
    exercise: exerciseSelect.value,
    weight_kg: weight,
    reps,
    rpe,
    note: null,
  };

  if (editingIndex !== null) {
    workoutEntries[editingIndex] = { ...workoutEntries[editingIndex], ...entry };
    reindexEntries();
    renderDraft();
    quickStatus.textContent = `${exerciseName(entry.exercise)} 세트를 수정했습니다.`;
    const returnState = editingReturnState;
    resetEditMode();
    applyFormState(returnState);
    persistDraft();
    return;
  }

  workoutEntries.push({ ...entry, set_index: nextSetIndex(workoutEntries, entry.exercise) });
  renderDraft();
  persistDraft();
  quickStatus.textContent = `${exerciseName(entry.exercise)} 세트를 추가했습니다.`;
}

function renderDialog(item) {
  if (!item) {
    return;
  }
  dialogTitle.textContent = item.name_ko || item.name_en || item.id;
  const imageUrl = item.image_url || (item.images || [])[0]?.url;
  const imageBlock = imageUrl
    ? `<img src="${escapeHtml(imageUrl)}" alt="${escapeHtml(item.name_ko || item.name_en || item.id)}" />`
    : "";
  const muscles = [
    MUSCLE_LABELS[item.primary_muscle] || item.primary_muscle,
    ...(item.secondary_muscles || []).map((muscle) => MUSCLE_LABELS[muscle] || muscle),
  ].filter(Boolean).join(", ");
  dialogContent.innerHTML = `
    ${imageBlock}
    <p><strong>부위</strong> ${escapeHtml(muscles || "-")}</p>
    <p><strong>장비</strong> ${escapeHtml((item.equipment || []).join(", ") || "-")}</p>
    <p><strong>패턴</strong> ${escapeHtml(item.movement_pattern || "-")}</p>
  `;
  dialog.showModal();
}

function renderRecentDialog(item) {
  if (!item) {
    return;
  }
  const items = exerciseHistoryItems(item.id);
  dialogTitle.textContent = `${item.name_ko || item.name_en || item.id} 최근 기록`;
  if (!items.length) {
    dialogContent.innerHTML = '<p class="empty">아직 이 운동의 과거 세트 기록이 없습니다.</p>';
    dialog.showModal();
    return;
  }
  dialogContent.innerHTML = `
    <div class="recent-session-list">
      ${items.slice(0, 3).map(({ session, entries }, index) => {
        const started = session.started_at || session.created_at || session.date || "";
        const date = started ? formatTime(started) : "날짜 확인 필요";
        return `
          <article class="recent-session">
            <header>
              <strong>${index === 0 ? "최신 운동" : `${index + 1}회 전`}</strong>
              <small>${date}</small>
            </header>
            <div class="recent-set-list">
              ${entries.map((entry) => `<span>${entry.set_index || ""}. ${formatSetLine(entry)}</span>`).join("")}
            </div>
            ${session.note ? `<span>${escapeHtml(session.note)}</span>` : ""}
          </article>
        `;
      }).join("")}
    </div>
  `;
  dialog.showModal();
}

function renderQuickAddDialog() {
  const muscle = muscleSelect.value || "other";
  dialogTitle.textContent = "운동 추가";
  dialogContent.innerHTML = `
    <div class="quick-add-dialog">
      <p class="dialog-note">선택된 부위: ${escapeHtml(MUSCLE_LABELS[muscle] || muscle)}</p>
      <label>
        <span>운동명</span>
        <input id="dialog-exercise-name" type="text" placeholder="예: 케이블 플라이" autofocus />
      </label>
      <button id="dialog-add-exercise" class="dark-button" type="button">추가</button>
    </div>
  `;
  dialog.showModal();
  dialogContent.querySelector("#dialog-exercise-name")?.focus();
}

async function quickAddSelectedMuscleExercise(rawName = "") {
  const name = rawName.trim();
  if (!name) {
    quickStatus.textContent = "추가할 운동명을 입력하세요.";
    return;
  }
  const normalizedName = name.toLowerCase();
  const existing = exerciseLibrary.find((item) => [
    item.name_ko,
    item.name_en,
    item.id,
  ].filter(Boolean).some((value) => String(value).toLowerCase() === normalizedName));
  if (existing) {
    muscleSelect.value = existing.primary_muscle || muscleSelect.value;
    refreshExerciseOptions();
    exerciseSelect.value = existing.id;
    refreshExerciseActions();
    quickStatus.textContent = `${existing.name_ko || existing.name_en} 선택됨.`;
    return;
  }
  manageButton.disabled = true;
  quickStatus.textContent = "운동을 추가하는 중...";
  try {
    const result = await queueExerciseLibraryMutation("add", {
      name_ko: name,
      name_en: name,
      primary_muscle: muscleSelect.value || "other",
      equipment: [],
      favorite: true,
    });
    await reloadExercisesKeeping(result.exercise?.id);
    quickStatus.textContent = "운동을 추가했습니다.";
  } finally {
    manageButton.disabled = false;
  }
}

async function postJson(path, payload) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(payload),
  });
  const responsePayload = await response.json();
  if (!response.ok) {
    throw new Error(responsePayload.error || `${path} failed.`);
  }
  return responsePayload;
}

async function queueExerciseLibraryMutation(action, payload = {}) {
  const normalizedPayload = normalizeExerciseMutation(action, payload);
  if (isSupabaseMode()) {
    try {
      await supabaseQueueInsert("capture_queue", {
        user_id: getNomadUserId(),
        source: "workout_quick",
        status: "pending",
        payload: {
          kind: "exercise_library_mutation",
          origin: "workout_quick_library_manager",
          action,
          ...normalizedPayload,
        },
      });
      quickStatus.textContent = "Saved. Library analysis and dashboard update pending.";
      return { queued: true };
    } catch (error) {
      if (!isQueuePolicyError(error)) {
        throw error;
      }
      const result = storeLocalExerciseMutation(action, normalizedPayload);
      quickStatus.textContent = "Supabase 정책이 막혀 이 기기에 임시 저장했습니다.";
      return result;
    }
  }
  const endpoint = {
    add: "/api/exercises/custom",
    update: "/api/exercises/update",
    archive: "/api/exercises/archive",
    delete: "/api/exercises/delete",
    reorder: "/api/exercises/reorder",
  }[action];
  if (!endpoint) {
    throw new Error(`Unsupported exercise action: ${action}`);
  }
  return postJson(endpoint, action === "add" ? normalizedPayload.exercise : normalizedPayload);
}

async function loadAllExerciseLibrary() {
  const payload = isSupabaseMode()
    ? await loadDashboardSnapshot("exercise-library").catch(() => ({ exercises: exerciseLibrary }))
    : await loadJson("/api/exercises?include_archived=1").catch(() => ({ exercises: exerciseLibrary }));
  allExerciseLibrary = sortedExerciseItems(applyLocalExerciseMutations(payload.exercises || []));
  return allExerciseLibrary;
}

function managerVisibleItems(query = "") {
  const normalizedQuery = query.trim().toLowerCase();
  return sortedExerciseItems(allExerciseLibrary)
    .filter((item) => {
      if (managerMuscleFilter !== "all" && item.primary_muscle !== managerMuscleFilter && !(item.secondary_muscles || []).includes(managerMuscleFilter)) {
        return false;
      }
      const haystack = [item.name_ko, item.name_en, item.id, item.primary_muscle, ...(item.equipment || [])].filter(Boolean).join(" ").toLowerCase();
      return !normalizedQuery || haystack.includes(normalizedQuery);
    })
    .slice(0, 40);
}

function renderManagerList(query = "") {
  const list = dialogContent.querySelector("#manager-list");
  if (!list) {
    return;
  }
  const items = managerVisibleItems(query);
  if (!items.length) {
    list.innerHTML = '<p class="empty">검색 결과가 없습니다. 아래에서 새 운동으로 추가하세요.</p>';
    return;
  }
  list.innerHTML = items.map((item, index) => {
    const isEditing = managerEditingExerciseId === item.id;
    return `
      <article class="manager-item ${item.archived ? "archived" : ""}">
        <div class="manager-item-summary">
          <div>
            <strong>${escapeHtml(item.name_ko || item.name_en || item.id)}</strong>
            <small>${escapeHtml(MUSCLE_LABELS[item.primary_muscle] || item.primary_muscle || "기타")} · ${item.archived ? "숨김" : "드롭다운 표시"} · ${item.source || "local"}</small>
          </div>
          <div class="manager-row-actions">
            <button class="ghost-button manager-move-up" type="button" data-exercise-id="${escapeHtml(item.id)}" ${index === 0 ? "disabled" : ""}>↑</button>
            <button class="ghost-button manager-move-down" type="button" data-exercise-id="${escapeHtml(item.id)}" ${index === items.length - 1 ? "disabled" : ""}>↓</button>
            <button class="ghost-button manager-edit" type="button" data-exercise-id="${escapeHtml(item.id)}">${isEditing ? "닫기" : "수정"}</button>
            <button class="ghost-button manager-archive" type="button" data-exercise-id="${escapeHtml(item.id)}" data-archived="${item.archived ? "0" : "1"}">
              ${item.archived ? "복구" : "숨김"}
            </button>
            <button class="ghost-button danger manager-delete" type="button" data-exercise-id="${escapeHtml(item.id)}">삭제</button>
          </div>
        </div>
        ${isEditing ? `
          <div class="manager-edit-panel">
            <div class="manager-grid">
              <label>한글명 <input id="manager-edit-ko-${escapeHtml(item.id)}" value="${escapeHtml(item.name_ko || "")}" /></label>
              <label>영문명 <input id="manager-edit-en-${escapeHtml(item.id)}" value="${escapeHtml(item.name_en || "")}" /></label>
              <label>부위
                <select id="manager-edit-muscle-${escapeHtml(item.id)}">
                  ${managerMuscleOptions(item.primary_muscle || "other")}
                </select>
              </label>
              <label>장비 <input id="manager-edit-equipment-${escapeHtml(item.id)}" value="${escapeHtml((item.equipment || []).join(", "))}" placeholder="dumbbell, bench" /></label>
            </div>
            <div class="manager-actions">
              <button class="dark-button manager-save-edit" type="button" data-exercise-id="${escapeHtml(item.id)}">수정 저장</button>
            </div>
          </div>
        ` : ""}
      </article>
    `;
  }).join("");
}

async function renderLibraryManager() {
  await loadAllExerciseLibrary();
  dialogTitle.textContent = "운동 목록 관리";
  dialogContent.innerHTML = `
    <div class="library-manager">
      <section class="manager-section">
        <h3>새 운동 추가</h3>
        <div class="manager-grid">
          <label>한글명 <input id="manager-new-ko" placeholder="예: 케이블 플라이" /></label>
          <label>영문명 <input id="manager-new-en" placeholder="Cable Fly" /></label>
          <label>부위
            <select id="manager-new-muscle">
              ${managerMuscleOptions("chest")}
            </select>
          </label>
          <label>장비 <input id="manager-new-equipment" placeholder="cable_machine" /></label>
        </div>
        <div class="manager-actions">
          <button id="manager-add-custom" class="dark-button" type="button">새 운동 추가</button>
        </div>
      </section>
      <section class="manager-section">
        <h3>전체 운동 리스트</h3>
        <div class="manager-filter-row">
          <select id="manager-muscle-filter" aria-label="부위 필터">
            <option value="all">전체 부위</option>
            ${Object.entries(MUSCLE_LABELS).map(([value, label]) => `<option value="${value}" ${managerMuscleFilter === value ? "selected" : ""}>${label}</option>`).join("")}
          </select>
          <input id="manager-search" placeholder="운동명, 부위, 장비 검색" />
        </div>
        <div id="manager-list" class="manager-list"></div>
      </section>
    </div>
  `;
  renderManagerList();
  if (!dialog.open) {
    dialog.showModal();
  }
}

async function reloadExercisesKeeping(exerciseId) {
  await loadInitialData();
  if (exerciseId) {
    const item = exerciseLibrary.find((exercise) => exercise.id === exerciseId);
    if (item) {
      muscleSelect.value = item.primary_muscle || muscleSelect.value;
      refreshExerciseOptions();
      exerciseSelect.value = item.id;
      refreshExerciseActions();
    }
  }
  await loadAllExerciseLibrary();
}

async function loadInitialData() {
  const historyLoader = isSupabaseMode()
    ? loadDashboardSnapshot("workout-history").catch(() => ({ sessions: [] }))
    : loadJson("/api/workout-history").catch(() => ({ sessions: [] }));
  const exerciseLoader = isSupabaseMode()
    ? loadDashboardSnapshot("exercise-library").catch(() => loadJson("/data/exercise-library.json").catch(() => ({ exercises: [] })))
    : loadJson("/api/exercises").catch(() => ({ exercises: [] }));
  const [exercisePayload, historyPayload] = await Promise.all([
    exerciseLoader,
    historyLoader,
  ]);
  exerciseLibrary = sortedExerciseItems(applyLocalExerciseMutations(exercisePayload.exercises || [])).filter((item) => !item.archived);
  workoutHistorySessions = historyPayload.sessions || [];
  refreshExerciseOptions();
  renderDraft();
}

timeButton.addEventListener("click", () => {
  timePanel.hidden = !timePanel.hidden;
});

applyTime.addEventListener("click", () => {
  if (!startDate.value || !startTime.value) {
    timeStatus.textContent = "날짜와 시간을 선택하세요.";
    return;
  }
  setWorkoutStartedAt(new Date(`${startDate.value}T${startTime.value}`));
  timePanel.hidden = true;
});

workoutCategoryPanel.addEventListener("click", (event) => {
  const button = event.target.closest("[data-activity-category]");
  if (!button) {
    return;
  }
  workoutCategoryPanel.querySelectorAll("[data-activity-category]").forEach((item) => {
    item.setAttribute("aria-pressed", item === button ? "true" : "false");
  });
  if (button.dataset.activityCategory === "health") {
    showDetailPanel("chest");
    return;
  }
  openNomadQuick(button.dataset.activityCategory);
});

backToCategory.addEventListener("click", showCategoryPanel);

muscleSelect.addEventListener("change", () => {
  refreshExerciseOptions();
  selectedCategoryLabel.textContent = "운동";
});
exerciseSelect.addEventListener("change", refreshExerciseActions);
addSetButton.addEventListener("click", addOrEditSet);

favoriteButton.addEventListener("click", () => {
  const item = selectedExercise();
  if (!item) {
    return;
  }
  if (isSupabaseMode()) {
    quickStatus.textContent = "Cloud mode에서는 Like 저장을 다음 단계에서 연결합니다.";
    return;
  }
  favoriteButton.disabled = true;
  fetch("/api/exercises/favorite", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ exercise_id: item.id, favorite: !item.favorite }),
  })
    .then(async (response) => {
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.error || "Like update failed.");
      }
      await loadInitialData();
      quickStatus.textContent = "운동 선호도를 저장했습니다.";
    })
    .catch((error) => {
      quickStatus.textContent = error.message;
    })
    .finally(() => {
      favoriteButton.disabled = false;
    });
});

infoButton.addEventListener("click", () => {
  renderDialog(selectedExercise());
});

resetButton.addEventListener("click", () => {
  const latestEntries = latestEntriesForSelectedExercise();
  const latest = latestEntries.at(-1);
  weightInput.value = latest?.weight_kg ?? 60;
  repsInput.value = latest?.reps ?? 10;
  rpeInput.value = "";
  persistDraft();
  quickStatus.textContent = "선택 운동 입력값을 리셋했습니다.";
});

recentButton.addEventListener("click", () => {
  renderRecentDialog(selectedExercise());
});

manageButton.addEventListener("click", renderQuickAddDialog);

dialogContent.addEventListener("click", (event) => {
  const button = event.target.closest("#dialog-add-exercise");
  if (!button) return;
  const input = dialogContent.querySelector("#dialog-exercise-name");
  button.disabled = true;
  quickAddSelectedMuscleExercise(input?.value.trim() || "")
    .then(() => {
      dialog.close();
    })
    .catch((error) => {
      quickStatus.textContent = error.message;
    })
    .finally(() => {
      button.disabled = false;
    });
});

dialogContent.addEventListener("keydown", (event) => {
  if (event.key !== "Enter" || event.target.id !== "dialog-exercise-name") return;
  event.preventDefault();
  dialogContent.querySelector("#dialog-add-exercise")?.click();
});

dialogContent.addEventListener("input", (event) => {
  if (event.target.id === "manager-search") {
    renderManagerList(event.target.value);
  }
});

dialogContent.addEventListener("change", (event) => {
  if (event.target.id === "manager-muscle-filter") {
    managerMuscleFilter = event.target.value || "all";
    renderManagerList(managerCurrentQuery());
  }
});

dialogContent.addEventListener("click", (event) => {
  const editButton = event.target.closest(".manager-edit");
  const saveEdit = event.target.closest(".manager-save-edit");
  const addCustom = event.target.closest("#manager-add-custom");
  const archiveButton = event.target.closest(".manager-archive");
  const deleteButton = event.target.closest(".manager-delete");
  const moveUp = event.target.closest(".manager-move-up");
  const moveDown = event.target.closest(".manager-move-down");
  if (!editButton && !saveEdit && !addCustom && !archiveButton && !deleteButton && !moveUp && !moveDown) {
    return;
  }
  const work = async () => {
    if (editButton) {
      const exerciseId = editButton.dataset.exerciseId;
      managerEditingExerciseId = managerEditingExerciseId === exerciseId ? null : exerciseId;
      renderManagerList(managerCurrentQuery());
      return;
    }
    if (saveEdit) {
      const exerciseId = saveEdit.dataset.exerciseId;
      await queueExerciseLibraryMutation("update", {
        exercise_id: exerciseId,
        updates: {
          name_ko: dialogContent.querySelector(`#manager-edit-ko-${CSS.escape(exerciseId)}`).value,
          name_en: dialogContent.querySelector(`#manager-edit-en-${CSS.escape(exerciseId)}`).value,
          primary_muscle: dialogContent.querySelector(`#manager-edit-muscle-${CSS.escape(exerciseId)}`).value,
          equipment: splitCsv(dialogContent.querySelector(`#manager-edit-equipment-${CSS.escape(exerciseId)}`).value),
        },
      });
      await reloadExercisesKeeping(exerciseId);
      quickStatus.textContent = "운동 정보를 수정했습니다.";
      renderManagerList(managerCurrentQuery());
      return;
    }
    if (archiveButton) {
      const exerciseId = archiveButton.dataset.exerciseId;
      await queueExerciseLibraryMutation("archive", { exercise_id: exerciseId, archived: archiveButton.dataset.archived === "1" });
      await reloadExercisesKeeping(exerciseSelect.value);
      renderManagerList(managerCurrentQuery());
      quickStatus.textContent = "운동 목록을 업데이트했습니다.";
      return;
    }
    if (deleteButton) {
      const exerciseId = deleteButton.dataset.exerciseId;
      const item = allExerciseLibrary.find((exercise) => exercise.id === exerciseId);
      const label = item?.name_ko || item?.name_en || exerciseId;
      if (!window.confirm(`${label} 운동을 삭제할까요? 과거 기록에는 운동 ID만 남을 수 있습니다.`)) {
        return;
      }
      await queueExerciseLibraryMutation("delete", { exercise_id: exerciseId });
      if (managerEditingExerciseId === exerciseId) {
        managerEditingExerciseId = null;
      }
      await reloadExercisesKeeping(exerciseSelect.value === exerciseId ? null : exerciseSelect.value);
      renderManagerList(managerCurrentQuery());
      quickStatus.textContent = "운동을 삭제했습니다.";
      return;
    }
    if (addCustom) {
      const payload = {
        name_ko: dialogContent.querySelector("#manager-new-ko").value,
        name_en: dialogContent.querySelector("#manager-new-en").value,
        primary_muscle: dialogContent.querySelector("#manager-new-muscle").value,
        equipment: splitCsv(dialogContent.querySelector("#manager-new-equipment").value),
        favorite: true,
      };
      const result = await queueExerciseLibraryMutation("add", payload);
      await reloadExercisesKeeping(result.exercise?.id);
      quickStatus.textContent = result.queued ? quickStatus.textContent : `${result.exercise.name_ko || result.exercise.name_en} 운동을 추가했습니다.`;
      dialog.close();
      return;
    }
    const moveButton = moveUp || moveDown;
    if (moveButton) {
      const exerciseId = moveButton.dataset.exerciseId;
      const direction = moveUp ? -1 : 1;
      const currentItems = managerVisibleItems(managerCurrentQuery()).filter((item) => !item.archived);
      const index = currentItems.findIndex((item) => item.id === exerciseId);
      const targetIndex = index + direction;
      if (index < 0 || targetIndex < 0 || targetIndex >= currentItems.length) {
        return;
      }
      const activeItems = sortedExerciseItems(allExerciseLibrary.filter((item) => !item.archived));
      const targetId = currentItems[targetIndex].id;
      const activeIndex = activeItems.findIndex((item) => item.id === exerciseId);
      const activeTargetIndex = activeItems.findIndex((item) => item.id === targetId);
      if (activeIndex < 0 || activeTargetIndex < 0) {
        return;
      }
      const next = activeItems.slice();
      [next[activeIndex], next[activeTargetIndex]] = [next[activeTargetIndex], next[activeIndex]];
      allExerciseLibrary = allExerciseLibrary.map((item) => {
        const nextOrder = next.findIndex((exercise) => exercise.id === item.id);
        return nextOrder >= 0 ? { ...item, display_order: nextOrder } : item;
      });
      exerciseLibrary = exerciseLibrary.map((item) => {
        const nextOrder = next.findIndex((exercise) => exercise.id === item.id);
        return nextOrder >= 0 ? { ...item, display_order: nextOrder } : item;
      });
      renderManagerList(managerCurrentQuery());
      await queueExerciseLibraryMutation("reorder", { ordered_ids: next.map((item) => item.id) });
      await reloadExercisesKeeping(exerciseSelect.value);
      renderManagerList(managerCurrentQuery());
      quickStatus.textContent = isSupabaseMode() ? quickStatus.textContent : "운동 순서를 저장했습니다.";
    }
  };
  event.target.disabled = true;
  work().catch((error) => {
    quickStatus.textContent = error.message;
  }).finally(() => {
    event.target.disabled = false;
  });
});

draftList.addEventListener("click", (event) => {
  const editButton = event.target.closest(".edit-set");
  const removeButton = event.target.closest(".remove-set");
  if (!editButton && !removeButton) {
    return;
  }
  const button = editButton || removeButton;
  const index = Number(button.dataset.index);
  if (!Number.isInteger(index) || !workoutEntries[index]) {
    return;
  }
  if (editButton) {
    if (editingIndex === null) {
      editingReturnState = currentFormState();
    }
    editingIndex = index;
    loadEntryIntoForm(workoutEntries[index]);
    addSetButton.textContent = "Edit Set";
    quickStatus.textContent = `${exerciseName(workoutEntries[index].exercise)} 세트를 수정 중입니다.`;
    return;
  }
  workoutEntries.splice(index, 1);
  reindexEntries();
  if (editingIndex !== null) {
    const returnState = editingReturnState;
    resetEditMode();
    applyFormState(returnState);
  }
  renderDraft();
  persistDraft();
  quickStatus.textContent = "세트를 삭제했습니다.";
});

quickForm.addEventListener("submit", (event) => {
  event.preventDefault();
  if (!workoutEntries.length) {
    quickStatus.textContent = "최소 1개 세트를 추가하세요.";
    return;
  }
  saveWorkoutButton.disabled = true;
  quickStatus.textContent = "운동을 저장하는 중...";
  const payload = buildStrengthWorkoutPayload({
    startedAt: workoutStartedAt,
    muscleGroup: muscleSelect.value,
    entries: workoutEntries,
    note: noteInput.value,
  });
  payload.stay = currentStayContext();
  const savePromise = isSupabaseMode()
    ? supabaseQueueInsert("workout_queue", {
      user_id: getNomadUserId(),
      source: "workout_quick",
      status: "pending",
      payload,
    })
    : fetch("/api/workout-session", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(payload),
  });
  let queuedLocally = false;
  savePromise
    .then(async (response) => {
      if (isSupabaseMode()) {
        queuedLocally = Boolean(response?.localPending || response?.queuedLocally);
        return response;
      }
      const responsePayload = await response.json();
      if (!response.ok) {
        throw new Error(responsePayload.error || "운동 저장에 실패했습니다.");
      }
      return responsePayload;
    })
    .then(async () => {
      workoutEntries = [];
      noteInput.value = "";
      resetEditMode();
      setWorkoutStartedAt(new Date(), false);
      clearWorkoutDraft();
      renderDraft();
      await loadInitialData();
      showCategoryPanel();
      if (isSupabaseMode()) {
        appendInputHistory({ raw_content: `Workout: ${payload.entries?.length || 0} set(s)` });
        appendPendingHealthWorkout(payload);
      }
      quickStatus.textContent = isSupabaseMode()
        ? queuedLocally
          ? "이 기기에 임시 저장했습니다. 모바일 로그인/네트워크가 복구되면 cloud queue로 다시 보냅니다."
          : "Saved. Analysis and dashboard update pending."
        : "운동을 저장했습니다.";
    })
    .catch((error) => {
      quickStatus.textContent = error.message;
    })
    .finally(() => {
      saveWorkoutButton.disabled = false;
    });
});

[muscleSelect, exerciseSelect, weightInput, repsInput, rpeInput, noteInput].forEach((element) => {
  element.addEventListener("change", persistDraft);
  element.addEventListener("input", persistDraft);
});

window.addEventListener("storage", (event) => {
  if (event.key !== WORKOUT_DRAFT_STORAGE_KEY) {
    return;
  }
  if (!event.newValue) {
    workoutEntries = [];
    noteInput.value = "";
    resetEditMode();
    renderDraft();
    return;
  }
  restoreDraft();
});

setWorkoutStartedAt(new Date(), false);
installInputFocusMode();
showCategoryPanel();
loadAppConfig()
  .then(() => initNomadAuth(appConfig, {
    onStateChange: (session) => {
      if (isSupabaseMode() && session) {
        flushCloudQueueFallback()
          .then((result) => {
            if (result.flushed) {
              quickStatus.textContent = `모바일 임시 저장 ${result.flushed}개를 cloud queue로 보냈습니다.`;
            }
          })
          .then(loadInitialData)
          .catch((error) => {
            quickStatus.textContent = error.message;
          });
      }
    },
  }))
  .then(() => {
    if (isSupabaseMode()) {
      return requireNomadSession();
    }
    return null;
  })
  .then(() => flushCloudQueueFallback())
  .then(loadInitialData)
  .then(restoreDraft)
  .then(() => {
    if (isSupabaseMode()) {
      quickStatus.textContent = "Cloud mode: Save is immediate. Analysis updates follow.";
    }
  })
  .catch((error) => {
    quickStatus.textContent = error.message;
  });

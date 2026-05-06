import {
  buildStrengthWorkoutPayload,
  clearWorkoutDraft,
  nextSetIndex,
  readWorkoutDraft,
  reindexStrengthEntries,
  writeWorkoutDraft,
  WORKOUT_DRAFT_STORAGE_KEY,
} from "./workout-shared.js?v=20260506-workout-shared";

const todayDate = document.querySelector("#today-date");
const summary = document.querySelector("#summary");
const focusList = document.querySelector("#focus-list");
const letGoList = document.querySelector("#let-go-list");
const missionsList = document.querySelector("#missions-list");
const council = document.querySelector("#agent-council");
const notificationsList = document.querySelector("#notifications-list");
const lifeBars = document.querySelector("#life-bars");
const activitySummary = document.querySelector("#activity-summary");
const activityBars = document.querySelector("#activity-bars");
const activityMonthBars = document.querySelector("#activity-month-bars");
const activityCumulative = document.querySelector("#activity-cumulative");
const activitySessions = document.querySelector("#activity-sessions");
const healthSummary = document.querySelector("#health-summary");
const healthReadiness = document.querySelector("#health-readiness");
const healthRecommendations = document.querySelector("#health-recommendations");
const routineFilters = document.querySelector("#routine-filters");
const routineTrack = document.querySelector("#routine-track");
const routinePrev = document.querySelector("#routine-prev");
const routineNext = document.querySelector("#routine-next");
const exerciseHistoryTitle = document.querySelector("#exercise-history-title");
const exerciseHistory = document.querySelector("#exercise-history");
const muscleHeatmap = document.querySelector("#muscle-heatmap");
const muscleSummary = document.querySelector("#muscle-summary");
const muscleDetail = document.querySelector("#muscle-detail");
const actionsList = document.querySelector("#actions-list");
const capturesList = document.querySelector("#captures-list");
const expenseCandidatesList = document.querySelector("#expense-candidates-list");
const hermesDraft = document.querySelector("#hermes-draft");
const localContextList = document.querySelector("#local-context-list");
const syncStatusList = document.querySelector("#sync-status-list");
const captureForm = document.querySelector("#capture-form");
const captureText = document.querySelector("#capture-text");
const captureStatus = document.querySelector("#capture-status");
const syncInboxButton = document.querySelector("#sync-inbox-button");
const syncLocalAppsButton = document.querySelector("#sync-local-apps-button");
const workoutForm = document.querySelector("#workout-form");
const openWorkoutTime = document.querySelector("#open-workout-time");
const workoutTimePopover = document.querySelector("#workout-time-popover");
const workoutStartDate = document.querySelector("#workout-start-date");
const workoutStartTime = document.querySelector("#workout-start-time");
const applyWorkoutTime = document.querySelector("#apply-workout-time");
const workoutTimeStatus = document.querySelector("#workout-time-status");
const workoutMuscle = document.querySelector("#workout-muscle");
const workoutExercise = document.querySelector("#workout-exercise");
const exerciseSearch = document.querySelector("#exercise-search");
const favoriteExercise = document.querySelector("#favorite-exercise");
const exerciseDetail = document.querySelector("#exercise-detail");
const latestExerciseGuide = document.querySelector("#latest-exercise-guide");
const exerciseDialog = document.querySelector("#exercise-dialog");
const exerciseDialogTitle = document.querySelector("#exercise-dialog-title");
const exerciseDialogContent = document.querySelector("#exercise-dialog-content");
const workoutWeight = document.querySelector("#workout-weight");
const workoutReps = document.querySelector("#workout-reps");
const workoutRpe = document.querySelector("#workout-rpe");
const addWorkoutSet = document.querySelector("#add-workout-set");
const workoutStatus = document.querySelector("#workout-status");
const workoutSetList = document.querySelector("#workout-set-list");
const workoutNote = document.querySelector("#workout-note");
const workspaceViews = [...document.querySelectorAll(".workspace-view")];
const workspaceLinks = [...document.querySelectorAll("[data-view-link]")];
const workspaceOverview = document.querySelector("#workspace-overview");
const VIEW_ALIASES = {
  captures: "capture",
  workout: "health",
  "health-dashboard": "health",
  life: "today",
  "expense-candidates": "finance",
  hermes: "reports",
  "local-context": "context",
  notifications: "council",
  actions: "council",
};

const ACTIVITY_COLORS = {
  "AI Work": "#0066ff",
  Health: "#00a86b",
  English: "#7c3aed",
  "Creator/Social": "#f97316",
  "Travel/Experience": "#0ea5e9",
  Rest: "#64748b",
  Finance: "#eab308",
  Unclassified: "#989ba2",
};

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

let workoutStartedAt = new Date().toISOString();
let workoutEntries = [];
let exerciseLibrary = [];
let workoutHistorySessions = [];
let selectedRoutineFilter = "all";
let editingWorkoutIndex = null;
let editingReturnState = null;
let appConfig = {
  mode: "local",
  supabaseUrl: "",
  supabaseAnonKey: "",
};

function isSupabaseMode() {
  return appConfig.mode === "supabase" && appConfig.supabaseUrl && appConfig.supabaseAnonKey;
}

async function loadAppConfig() {
  appConfig = await loadJson("/api/config").catch(() => appConfig);
  if (!appConfig.mode) {
    appConfig.mode = "local";
  }
}

async function supabaseRequest(path, options = {}) {
  const baseUrl = appConfig.supabaseUrl.replace(/\/$/, "");
  const response = await fetch(`${baseUrl}/rest/v1/${path}`, {
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

async function loadDashboardSnapshot(snapshotKey) {
  const query = `dashboard_snapshots?select=payload&snapshot_key=eq.${encodeURIComponent(snapshotKey)}&order=created_at.desc&limit=1`;
  const rows = await supabaseRequest(query, { method: "GET" });
  if (!rows?.[0]?.payload) {
    throw new Error(`${snapshotKey} snapshot이 아직 없습니다.`);
  }
  return rows[0].payload;
}

async function loadDashboardJson(snapshotKey, localPath, fallback) {
  if (isSupabaseMode()) {
    return loadDashboardSnapshot(snapshotKey).catch(() => fallback);
  }
  return loadJson(localPath).catch(() => fallback);
}

function setCloudModeUi() {
  const cloud = isSupabaseMode();
  syncInboxButton.disabled = cloud;
  syncLocalAppsButton.disabled = cloud;
  if (cloud && captureStatus) {
    captureStatus.textContent = "Cloud mode: 입력은 Supabase queue에 저장됩니다.";
  }
}

function toLocalDateTimeValue(date = new Date()) {
  const localDate = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
  return localDate.toISOString().slice(0, 16);
}

function resetWorkoutStartedAt() {
  workoutStartedAt = new Date().toISOString();
  setTimePickerValue(new Date());
  workoutTimeStatus.textContent = "현재 시간 적용됨";
}

function setTimePickerValue(date) {
  const value = toLocalDateTimeValue(date);
  const [datePart, timePart] = value.split("T");
  workoutStartDate.value = datePart;
  workoutStartTime.value = timePart;
}

function formatAppliedTime(value) {
  return new Intl.DateTimeFormat("ko-KR", {
    month: "numeric",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date(value));
}

function formatRoutineTime(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value || "";
  }
  return new Intl.DateTimeFormat("ko-KR", {
    month: "numeric",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(date);
}

function applyWorkoutStartedAt() {
  if (!workoutStartDate.value || !workoutStartTime.value) {
    workoutTimeStatus.textContent = "날짜와 시간을 선택하세요.";
    return;
  }
  workoutStartedAt = new Date(`${workoutStartDate.value}T${workoutStartTime.value}`).toISOString();
  workoutTimeStatus.textContent = `${formatAppliedTime(workoutStartedAt)} 적용 완료`;
  workoutTimePopover.hidden = true;
  persistWorkoutDraft();
}

function reindexWorkoutEntries() {
  workoutEntries = reindexStrengthEntries(workoutEntries);
}

function addWorkoutEntry(entry) {
  workoutEntries.push({
    ...entry,
    set_index: nextSetIndex(workoutEntries, entry.exercise),
  });
  renderWorkoutSets();
  persistWorkoutDraft();
}

function currentWorkoutFormState() {
  return {
    muscle: workoutMuscle.value,
    exercise: workoutExercise.value,
    search: exerciseSearch.value,
    weight: workoutWeight.value,
    reps: workoutReps.value,
    rpe: workoutRpe.value,
  };
}

function applyWorkoutFormState(state) {
  if (!state) {
    return;
  }
  workoutMuscle.value = state.muscle || workoutMuscle.value;
  exerciseSearch.value = state.search || "";
  refreshExerciseOptions();
  if ([...workoutExercise.options].some((option) => option.value === state.exercise)) {
    workoutExercise.value = state.exercise;
  }
  workoutWeight.value = state.weight ?? workoutWeight.value;
  workoutReps.value = state.reps ?? workoutReps.value;
  workoutRpe.value = state.rpe ?? "";
  refreshExerciseActions();
  renderExerciseHistory(workoutExercise.value);
}

function loadWorkoutEntryIntoForm(entry) {
  workoutMuscle.value = entry.muscle_group || workoutMuscle.value;
  exerciseSearch.value = "";
  refreshExerciseOptions();
  if ([...workoutExercise.options].some((option) => option.value === entry.exercise)) {
    workoutExercise.value = entry.exercise;
  }
  workoutWeight.value = entry.weight_kg ?? "";
  workoutReps.value = entry.reps ?? "";
  workoutRpe.value = entry.rpe ?? "";
  refreshExerciseActions();
  renderExerciseHistory(workoutExercise.value);
}

function resetWorkoutEditMode() {
  editingWorkoutIndex = null;
  editingReturnState = null;
  addWorkoutSet.textContent = "Add Set";
}

function persistWorkoutDraft() {
  writeWorkoutDraft({
    source: "dashboard_workout_form",
    started_at: workoutStartedAt,
    entries: workoutEntries,
    note: workoutNote.value,
    form_state: currentWorkoutFormState(),
  });
}

function restoreWorkoutDraft() {
  const draft = readWorkoutDraft();
  if (!draft || (!(draft.entries || []).length && !draft.note)) {
    return;
  }
  workoutStartedAt = draft.started_at || workoutStartedAt;
  setTimePickerValue(new Date(workoutStartedAt));
  workoutEntries = reindexStrengthEntries(draft.entries || []);
  workoutNote.value = draft.note || "";
  applyWorkoutFormState(draft.form_state);
  renderWorkoutSets();
  workoutTimeStatus.textContent = `${formatAppliedTime(workoutStartedAt)} draft restored`;
}

function setActiveView(viewName, updateHash = true) {
  const normalizedView = VIEW_ALIASES[viewName] || viewName;
  const knownView = workspaceViews.some((view) => view.dataset.view === normalizedView);
  const nextView = knownView ? normalizedView : "today";
  workspaceViews.forEach((view) => {
    view.classList.toggle("active", view.dataset.view === nextView);
  });
  workspaceLinks.forEach((link) => {
    link.classList.toggle("active", link.dataset.viewLink === nextView);
  });
  if (updateHash && window.location.hash !== `#${nextView}`) {
    history.replaceState(null, "", `#${nextView}`);
  }
}

function renderList(element, items = []) {
  element.replaceChildren(
    ...items.map((item) => {
      const li = document.createElement("li");
      li.textContent = item;
      return li;
    }),
  );
}

function renderWorkspaceOverview({ today, health, activityAllocation, captures, expenseCandidates, notifications, syncStatus }) {
  const healthRecommendation = (health.recommendations || [])
    .map((item) => item.label)
    .slice(0, 2)
    .join(", ");
  const activityMinutes = activityAllocation.summary?.tracked_minutes || activityAllocation.summary?.total_minutes || 0;
  const syncSummary = syncStatus.summary || {};
  const pendingTotal = Number(syncSummary.pending_captures || 0) + Number(syncSummary.pending_workouts || 0);
  const syncFreshness = syncFreshnessStatus(syncSummary);
  const cards = [
    {
      view: "today",
      label: "Today",
      value: `${(today.focus_today || []).length} focus`,
      detail: today.summary || "Coordinator summary",
    },
    {
      view: "capture",
      label: "Capture",
      value: `${(captures.captures || []).length} items`,
      detail: "Recent captures and inbox",
    },
    {
      view: "health",
      label: "Health",
      value: `${health.summary?.strength_set_count || 0} sets`,
      detail: healthRecommendation ? `Candidates: ${healthRecommendation}` : "Workout readiness",
    },
    {
      view: "activity",
      label: "Activity",
      value: `${Math.round(activityMinutes)} min`,
      detail: "Time allocation candidates",
    },
    {
      view: "finance",
      label: "Finance",
      value: `${(expenseCandidates.candidates || []).length} review`,
      detail: "Expense candidates",
    },
    {
      view: "council",
      label: "Council",
      value: `${(today.agent_council || []).length} agents`,
      detail: `${(notifications.notifications || []).length} notification candidates`,
    },
    {
      view: "context",
      label: "Sync",
      value: syncFreshness.label,
      detail: `${pendingTotal} pending · ${syncFreshness.detail}`,
      status: syncFreshness.status,
    },
  ];

  workspaceOverview.replaceChildren(
    ...cards.map((card) => {
      const button = document.createElement("button");
      button.className = ["overview-card", card.status ? `status-${card.status}` : ""].filter(Boolean).join(" ");
      button.type = "button";
      button.dataset.overviewView = card.view;
      button.innerHTML = `
        <span>${card.label}</span>
        <strong>${card.value}</strong>
        <small>${card.detail}</small>
      `;
      return button;
    }),
  );
}

function exerciseLabel(muscle, value) {
  const match = exerciseLibrary.find((item) => item.id === value);
  if (match) {
    return match.name_ko || match.name_en || match.id;
  }
  return value;
}

function uniqueMuscles(entries = []) {
  return [...new Set(entries.map((entry) => entry.muscle_group).filter(Boolean))];
}

function routineTags(entries = []) {
  const muscles = uniqueMuscles(entries);
  if (muscles.length >= 4) {
    return ["전신"];
  }
  return muscles.slice(0, 3).map((muscle) => MUSCLE_LABELS[muscle] || muscle);
}

function groupEntriesByExercise(entries = []) {
  return entries.reduce((groups, entry) => {
    const exercise = entry.exercise || "exercise";
    if (!groups[exercise]) {
      groups[exercise] = [];
    }
    groups[exercise].push(entry);
    return groups;
  }, {});
}

function formatSetLine(entry = {}) {
  const weight = entry.weight_kg ?? "-";
  const reps = entry.reps ?? "-";
  return `${weight}kg X ${reps}`;
}

function sortedSessions(sessions = []) {
  return sessions.slice().sort((a, b) => (b.started_at || b.created_at || "").localeCompare(a.started_at || a.created_at || ""));
}

function exerciseHistoryItems(exerciseId) {
  const items = [];
  sortedSessions(workoutHistorySessions).forEach((session) => {
    const entries = (session.entries || []).filter((entry) => entry.exercise === exerciseId);
    if (!entries.length) {
      return;
    }
    const maxWeight = Math.max(...entries.map((entry) => Number(entry.weight_kg) || 0));
    items.push({
      session,
      entries,
      maxWeight,
      setCount: entries.length,
    });
  });
  return items;
}

function latestExerciseEntries(exerciseId) {
  return exerciseHistoryItems(exerciseId)[0]?.entries || [];
}

function updateLatestExerciseGuide() {
  const exercise = workoutExercise.value;
  const latestEntries = latestExerciseEntries(exercise);
  if (!latestEntries.length) {
    latestExerciseGuide.textContent = "이전 운동 기록이 있으면 여기에 표시됩니다.";
    workoutWeight.placeholder = "예: 60";
    workoutReps.placeholder = "예: 10";
    return;
  }
  const latest = latestEntries.at(-1);
  workoutWeight.placeholder = latest.weight_kg ? `${latest.weight_kg}` : "예: 60";
  workoutReps.placeholder = latest.reps ? `${latest.reps}` : "예: 10";
  latestExerciseGuide.textContent = `최근 ${exerciseLabel(latest.muscle_group, exercise)}: ${latestEntries.map(formatSetLine).join(" · ")}`;
}

function selectedExercise() {
  return exerciseLibrary.find((item) => item.id === workoutExercise.value) || null;
}

function refreshExerciseOptions() {
  const currentValue = workoutExercise.value;
  const query = exerciseSearch.value.trim().toLowerCase();
  const selectedMuscle = workoutMuscle.value;
  const options = exerciseLibrary
    .filter((item) => {
      const muscleMatch = selectedMuscle === "other"
        ? true
        : item.primary_muscle === selectedMuscle || (item.secondary_muscles || []).includes(selectedMuscle);
      const haystack = [
        item.name_ko,
        item.name_en,
        item.id,
        item.primary_muscle,
        ...(item.secondary_muscles || []),
        ...(item.equipment || []),
      ].filter(Boolean).join(" ").toLowerCase();
      return muscleMatch && (!query || haystack.includes(query));
    })
    .sort((a, b) => Number(b.favorite) - Number(a.favorite) || (b.usage_count || 0) - (a.usage_count || 0) || (a.name_ko || a.name_en).localeCompare(b.name_ko || b.name_en, "ko"));

  workoutExercise.replaceChildren(
    ...options.map((item) => {
      const option = document.createElement("option");
      option.value = item.id;
      const favorite = item.favorite ? "★ " : "";
      const used = item.usage_count ? ` · ${item.usage_count}` : "";
      option.textContent = `${favorite}${item.name_ko || item.name_en}${used}`;
      return option;
    }),
  );
  if (options.some((item) => item.id === currentValue)) {
    workoutExercise.value = currentValue;
  }
  if (!workoutExercise.value && options[0]) {
    workoutExercise.value = options[0].id;
  }
  refreshExerciseActions();
  updateLatestExerciseGuide();
}

function refreshExerciseActions() {
  const item = selectedExercise();
  favoriteExercise.textContent = item?.favorite ? "♥" : "♡";
  favoriteExercise.classList.toggle("active", Boolean(item?.favorite));
  favoriteExercise.disabled = !item;
  exerciseDetail.disabled = !item;
  updateLatestExerciseGuide();
}

async function loadExerciseLibrary() {
  const exercisePath = isSupabaseMode() ? "/data/exercise-library.json" : "/api/exercises";
  const payload = await loadJson(exercisePath).catch(() => ({ exercises: [] }));
  exerciseLibrary = payload.exercises || [];
  refreshExerciseOptions();
  renderRoutineCards(workoutHistorySessions);
  renderExerciseHistory(workoutExercise.value);
}

function renderExerciseDialog(item) {
  if (!item) {
    return;
  }
  exerciseDialogTitle.textContent = item.name_ko || item.name_en || item.id;
  const muscles = [
    MUSCLE_LABELS[item.primary_muscle] || item.primary_muscle,
    ...(item.secondary_muscles || []).map((muscle) => MUSCLE_LABELS[muscle] || muscle),
  ].filter(Boolean).join(", ");
  const equipment = (item.equipment || []).join(", ") || "-";
  const instructions = (item.instructions || []).map((step) => `<li>${step}</li>`).join("");
  const source = item.source_url
    ? `<a href="${item.source_url}" target="_blank" rel="noreferrer">원본 보기</a>`
    : `<span>${item.source || "local"}</span>`;
  const imageUrl = item.image_url || (item.images || [])[0]?.url;
  const imageBlock = imageUrl
    ? `<img class="exercise-image" src="${imageUrl}" alt="${item.name_ko || item.name_en || item.id}" />`
    : `<div class="exercise-image-placeholder">이미지는 외부 라이브러리 import 후 표시됩니다.</div>`;
  exerciseDialogContent.innerHTML = `
    ${imageBlock}
    <div class="exercise-detail-grid">
      <div><span>부위</span><strong>${muscles}</strong></div>
      <div><span>장비</span><strong>${equipment}</strong></div>
      <div><span>패턴</span><strong>${item.movement_pattern || "-"}</strong></div>
      <div><span>난이도</span><strong>${item.difficulty || "-"}</strong></div>
    </div>
    <h3>Instructions</h3>
    <ol>${instructions || "<li>라이브러리 상세 데이터가 아직 없습니다.</li>"}</ol>
    <p class="source-line">Source: ${source}</p>
  `;
  exerciseDialog.showModal();
}

function renderWorkoutSets() {
  if (!workoutEntries.length) {
    workoutSetList.innerHTML = '<p class="empty">아직 추가된 세트가 없습니다.</p>';
    return;
  }

  const groups = [];
  workoutEntries.forEach((entry, index) => {
    const lastGroup = groups.at(-1);
    if (lastGroup && lastGroup.exercise === entry.exercise) {
      lastGroup.items.push({ entry, index });
      return;
    }
    groups.push({
      exercise: entry.exercise,
      muscle: entry.muscle_group,
      items: [{ entry, index }],
    });
  });

  workoutSetList.replaceChildren(
    ...groups.map((group) => {
      const card = document.createElement("article");
      card.className = "workout-draft-card";
      const rows = group.items.map(({ entry, index }) => {
        const rpe = entry.rpe ? ` · RPE ${entry.rpe}` : "";
        return `
          <div class="workout-draft-set">
            <span>${entry.set_index}. ${entry.weight_kg}kg X ${entry.reps}${rpe}</span>
            <div>
              <button class="button-ghost workout-edit" type="button" data-index="${index}">Edit</button>
              <button class="button-ghost workout-remove" type="button" data-index="${index}">Remove</button>
            </div>
          </div>
        `;
      }).join("");
      card.innerHTML = `
        <header>
          <strong>[${exerciseLabel(group.muscle, group.exercise)}] ${group.items.length}set</strong>
          <span class="badge">${MUSCLE_LABELS[group.muscle] || group.muscle}</span>
        </header>
        <div class="workout-draft-sets">${rows}</div>
      `;
      return card;
    }),
  );
}

function renderExerciseHistory(exerciseId) {
  if (!exerciseId) {
    exerciseHistoryTitle.textContent = "운동을 선택하세요";
    exerciseHistory.innerHTML = '<p class="empty">루틴 카드의 운동명이나 입력 폼의 운동을 선택하면 히스토리가 표시됩니다.</p>';
    return;
  }
  const items = exerciseHistoryItems(exerciseId);
  exerciseHistoryTitle.textContent = exerciseLabel("other", exerciseId);
  if (!items.length) {
    exerciseHistory.innerHTML = '<p class="empty">아직 이 운동의 과거 기록이 없습니다.</p>';
    return;
  }
  exerciseHistory.replaceChildren(
    ...items.slice(0, 8).map((item) => {
      const row = document.createElement("article");
      row.className = "history-item";
      const sourceDate = item.session.started_at?.slice(0, 10) || item.session.date || "";
      const date = sourceDate ? shortDate(sourceDate) : "-";
      row.innerHTML = `
        <span>${date}</span>
        <strong>${item.maxWeight || "-"}kg</strong>
        <small>${item.setCount} set · ${item.entries.map(formatSetLine).join(" · ")}</small>
      `;
      return row;
    }),
  );
}

function renderRoutineFilters(sessions = []) {
  const muscles = [...new Set(sessions.flatMap((session) => uniqueMuscles(session.entries || [])))];
  if (selectedRoutineFilter !== "all" && !muscles.includes(selectedRoutineFilter)) {
    selectedRoutineFilter = "all";
  }
  const filters = [
    ["all", "전체"],
    ...muscles.map((muscle) => [muscle, MUSCLE_LABELS[muscle] || muscle]),
  ];
  routineFilters.replaceChildren(
    ...filters.map(([value, label]) => {
      const button = document.createElement("button");
      button.className = value === selectedRoutineFilter ? "filter-chip active" : "filter-chip";
      button.type = "button";
      button.dataset.routineFilter = value;
      button.textContent = label;
      return button;
    }),
  );
}

function renderRoutineCards(sessions = []) {
  renderRoutineFilters(sessions);
  const visibleSessions = sortedSessions(sessions).reverse().filter((session) => {
    if (selectedRoutineFilter === "all") {
      return true;
    }
    return uniqueMuscles(session.entries || []).includes(selectedRoutineFilter);
  });

  if (!visibleSessions.length) {
    routineTrack.innerHTML = '<p class="empty">선택한 필터에 해당하는 루틴이 없습니다.</p>';
    return;
  }

  routineTrack.replaceChildren(
    ...visibleSessions.map((session) => {
      const card = document.createElement("article");
      card.className = "routine-card";
      const tags = routineTags(session.entries || []);
      const primaryMuscle = uniqueMuscles(session.entries || [])[0] || "other";
      card.dataset.muscle = primaryMuscle;
      const groups = groupEntriesByExercise(session.entries || []);
      const started = session.started_at ? formatRoutineTime(session.started_at) : session.date || "";
      const exercises = Object.entries(groups).map(([exercise, entries]) => {
        const label = exerciseLabel(entries[0]?.muscle_group || "other", exercise);
        return `
          <button class="routine-exercise" type="button" data-exercise-id="${exercise}">
            <strong>${label}</strong>
            <small>${entries.length}set</small>
            <span>${entries.map(formatSetLine).join("</span><span>")}</span>
          </button>
        `;
      }).join("");
      card.innerHTML = `
        <header>
          <div class="routine-card-meta">
            <div class="routine-tags">
              ${(tags.length ? tags : ["미분류"]).map((tag) => `<span class="routine-tag">${tag}</span>`).join("")}
            </div>
            <time>${started}</time>
          </div>
          <small>${(session.entries || []).length} set</small>
        </header>
        <div class="routine-exercise-list">${exercises}</div>
      `;
      return card;
    }),
  );
  requestAnimationFrame(() => {
    routineTrack.scrollTo({ left: routineTrack.scrollWidth, behavior: "auto" });
  });
}

function shortDate(date = "") {
  const [, month, day] = date.split("-");
  return `${Number(month)}/${Number(day)}`;
}

function readinessLabel(status) {
  return {
    untracked: "미기록",
    overdue: "공백",
    ready: "가능",
    cooldown: "회복중",
    recent: "최근",
  }[status] || "확인";
}

function renderHealthDashboard(payload = {}) {
  const summary = payload.summary || {};
  const dashboard = payload.muscle_dashboard || {};
  const dates = dashboard.dates || [];
  const rows = dashboard.rows || [];
  const summaries = dashboard.summaries || [];
  const readiness = payload.readiness || [];
  const recommendations = payload.recommendations || [];
  healthSummary.replaceChildren(
    ...[
      ["14d Window", dates.length ? `${shortDate(dates[0])} - ${shortDate(dates.at(-1))}` : "-"],
      ["Strength Sets", summary.strength_set_count || 0],
      ["Muscle Groups", (summary.muscle_groups || []).length],
      ["Workout Sessions", summary.structured_workout_count || 0],
    ].map(([label, value]) => {
      const item = document.createElement("div");
      item.className = "metric-item";
      item.innerHTML = `<span>${label}</span><strong>${value}</strong>`;
      return item;
    }),
  );

  if (!rows.length || !dates.length) {
    muscleHeatmap.innerHTML = '<p class="empty">No muscle schedule data yet.</p>';
    healthReadiness.innerHTML = '<p class="empty">No readiness data yet.</p>';
    healthRecommendations.innerHTML = '<p class="empty">No recommendation candidates yet.</p>';
    muscleSummary.innerHTML = '<p class="empty">No muscle summary yet.</p>';
    muscleDetail.innerHTML = '<p class="empty">Select a muscle/date cell after workout records exist.</p>';
    return;
  }

  const readinessItems = readiness
    .filter((item) => !["full_body", "other"].includes(item.muscle_group))
    .sort((a, b) => b.priority - a.priority || a.sets_14d - b.sets_14d || a.display_order - b.display_order);

  healthReadiness.replaceChildren(
    ...readinessItems.map((item) => {
      const row = document.createElement("div");
      row.className = `readiness-item status-${item.status || "unknown"}`;
      row.innerHTML = `
        <div>
          <strong>${item.label}</strong>
          <small>${item.reason}</small>
        </div>
        <span>${readinessLabel(item.status)}</span>
      `;
      return row;
    }),
  );

  if (!recommendations.length) {
    healthRecommendations.innerHTML = '<p class="empty">오늘은 특정 부위 추천보다 기록 유지가 우선입니다.</p>';
  } else {
    healthRecommendations.replaceChildren(
      ...recommendations.map((item) => {
        const row = document.createElement("article");
        row.className = "recommendation-item";
        row.innerHTML = `
          <strong>${item.label}</strong>
          <p>${item.suggestion}</p>
          <small>${item.reason}</small>
        `;
        return row;
      }),
    );
  }

  const header = `
    <div class="heatmap-corner"></div>
    ${dates.map((date) => `<div class="heatmap-date">${shortDate(date)}</div>`).join("")}
  `;
  const body = rows.map((row) => `
    <div class="heatmap-label">${row.label}</div>
    ${row.cells.map((cell) => `
      <button
        class="heatmap-cell intensity-${cell.intensity || 0}"
        type="button"
        data-muscle="${row.muscle_group}"
        data-label="${row.label}"
        data-date="${cell.date}"
        data-entries='${JSON.stringify(cell.entries || [])}'
        aria-label="${row.label} ${cell.date} ${cell.set_count || 0} sets"
      >
        ${cell.set_count || ""}
      </button>
    `).join("")}
  `).join("");
  muscleHeatmap.innerHTML = `<div class="heatmap-grid">${header}${body}</div>`;

  const muscleOrder = ["chest", "back", "shoulders", "arms", "core", "legs", "full_body"];
  const summaryByMuscle = new Map(summaries.map((item) => [item.muscle_group, item]));
  const orderedSummaries = muscleOrder
    .map((muscle) => summaryByMuscle.get(muscle))
    .filter(Boolean);
  const maxSets = Math.max(...orderedSummaries.map((item) => item.sets_14d || 0), 1);
  muscleSummary.innerHTML = `
    <div class="body-figure" aria-hidden="true">
      <span class="body-head"></span>
      <span class="body-shoulders"></span>
      <span class="body-torso"></span>
      <span class="body-arm left"></span>
      <span class="body-arm right"></span>
      <span class="body-leg left"></span>
      <span class="body-leg right"></span>
    </div>
    <div class="muscle-map-cards">
      ${orderedSummaries.map((item) => {
        const interval = item.days_since_last === null ? "기록 없음" : `${item.days_since_last}일 전`;
        const intensity = Math.max(8, Math.round(((item.sets_14d || 0) / maxSets) * 100));
        return `
          <article class="muscle-map-card muscle-${item.muscle_group}" style="--muscle-intensity: ${intensity}%">
            <span>${item.label}</span>
            <strong>${item.sets_14d || 0} set</strong>
            <small>7d ${item.sets_7d || 0} · last ${interval}</small>
          </article>
        `;
      }).join("")}
    </div>
  `;

  renderMuscleDetail(null, null, []);
}

function renderMuscleDetail(label, date, entries = []) {
  if (!entries.length) {
    muscleDetail.innerHTML = '<p class="empty">선택한 날짜와 부위의 세트 기록이 없습니다.</p>';
    return;
  }

  muscleDetail.replaceChildren(
    ...entries.map((entry) => {
      const row = document.createElement("article");
      row.className = "capture-item";
      const rpe = entry.rpe ? ` · RPE ${entry.rpe}` : "";
      row.innerHTML = `
        <div>
          <header>
            <strong>${label} · ${exerciseLabel(entry.muscle_group || "other", entry.exercise)}</strong>
            <span class="badge">${shortDate(date)}</span>
          </header>
          <p>${exerciseLabel(entry.muscle_group || "other", entry.exercise)} · ${entry.weight_kg ?? "-"}kg x ${entry.reps ?? "-"}회${rpe}</p>
          <small>${entry.workout_id || ""}</small>
        </div>
      `;
      return row;
    }),
  );
}

function renderCouncil(items = []) {
  if (!items.length) {
    council.innerHTML = '<p class="empty">No agent council data yet.</p>';
    return;
  }

  council.replaceChildren(
    ...items.map((item) => {
      const card = document.createElement("article");
      card.className = "agent-card";
      card.innerHTML = `
        <header>
          <h3>${item.label || item.agent}</h3>
          <span class="badge">${item.status || "unknown"}</span>
        </header>
        <p>${item.insight || ""}</p>
        <p>${item.recommendation || ""}</p>
      `;
      return card;
    }),
  );
}

function renderLifeBalance(items = []) {
  if (!items.length) {
    lifeBars.innerHTML = '<p class="empty">No life balance data yet.</p>';
    return;
  }

  lifeBars.replaceChildren(
    ...items.map((item) => {
      const row = document.createElement("div");
      row.className = "life-row";
      const width = Math.max(0, Math.min(100, (Number(item.score || 0) / 5) * 100));
      row.innerHTML = `
        <strong>${item.name}</strong>
        <div class="bar-track" aria-label="${item.name} score ${item.score} out of 5">
          <div class="bar-fill" style="width: ${width}%"></div>
        </div>
        <span class="intent">${item.intent || "unknown"}</span>
      `;
      return row;
    }),
  );
}

function formatDuration(minutes = 0) {
  const value = Number(minutes || 0);
  const hours = Math.floor(value / 60);
  const mins = value % 60;
  if (hours && mins) {
    return `${hours}h ${mins}m`;
  }
  if (hours) {
    return `${hours}h`;
  }
  return `${mins}m`;
}

function formatPercent(value = 0) {
  return `${(Number(value || 0) * 100).toFixed(1)}%`;
}

function formatSyncTime(value) {
  if (!value) {
    return "-";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat("ko-KR", {
    month: "numeric",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(date);
}

function minutesSince(value) {
  if (!value) {
    return null;
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return null;
  }
  return Math.max(0, Math.round((Date.now() - date.getTime()) / 60000));
}

function formatSyncAge(minutes) {
  if (minutes === null) {
    return "not published";
  }
  if (minutes < 1) {
    return "just now";
  }
  if (minutes < 60) {
    return `${minutes}m ago`;
  }
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  return mins ? `${hours}h ${mins}m ago` : `${hours}h ago`;
}

function syncFreshnessStatus(summary = {}) {
  const pendingTotal = Number(summary.pending_captures || 0) + Number(summary.pending_workouts || 0);
  const ageMinutes = minutesSince(summary.last_publish_at);
  if (summary.last_failure_at) {
    return {
      status: "attention",
      label: "attention",
      detail: `failure · ${formatSyncTime(summary.last_failure_at)}`,
      ageMinutes,
    };
  }
  if (pendingTotal > 0) {
    return {
      status: "pending",
      label: "pending",
      detail: `${formatSyncAge(ageMinutes)} publish`,
      ageMinutes,
    };
  }
  if (ageMinutes === null || ageMinutes > 60) {
    return {
      status: "attention",
      label: "stale",
      detail: formatSyncAge(ageMinutes),
      ageMinutes,
    };
  }
  if (ageMinutes > 15) {
    return {
      status: "idle",
      label: "idle",
      detail: formatSyncAge(ageMinutes),
      ageMinutes,
    };
  }
  return {
    status: "ok",
    label: "fresh",
    detail: formatSyncAge(ageMinutes),
    ageMinutes,
  };
}

function colorForArea(area = "") {
  return ACTIVITY_COLORS[area] || ACTIVITY_COLORS.Unclassified;
}

function renderActivityStack(element, title, areas = [], totalShare = 0) {
  if (!areas.length) {
    element.innerHTML = '<p class="empty">No time allocation candidates yet.</p>';
    return;
  }

  const graph = document.createElement("article");
  graph.className = "activity-stack-card";

  const trackedShare = Math.max(0, Math.min(1, Number(totalShare || 0)));
  const segments = areas.map((item) => {
    const share = Math.max(0, Math.min(1, Number(item.share_of_capacity || 0)));
    const width = Math.max(0.5, share * 100);
    const color = colorForArea(item.area);
    return `<span class="activity-segment" style="width: ${width}%; background: ${color}" title="${item.area} ${formatPercent(share)}"></span>`;
  }).join("");

  const untrackedWidth = Math.max(0, (1 - trackedShare) * 100);
  const legend = areas.map((item) => {
    const color = colorForArea(item.area);
    return `
      <div class="activity-legend-item">
        <span class="legend-dot" style="background: ${color}"></span>
        <strong>${item.area}</strong>
        <small>${formatDuration(item.minutes)} · ${formatPercent(item.share_of_capacity)}</small>
      </div>
    `;
  }).join("");

  graph.innerHTML = `
    <header class="activity-stack-header">
      <strong>${title}</strong>
      <span>${formatPercent(trackedShare)} tracked</span>
    </header>
    <div class="activity-stack-track" aria-label="${title} activity share">
      ${segments}
      <span class="activity-segment activity-untracked" style="width: ${untrackedWidth}%"></span>
    </div>
    <div class="activity-legend">
      ${legend}
      <div class="activity-legend-item">
        <span class="legend-dot legend-dot-muted"></span>
        <strong>Untracked</strong>
        <small>${formatPercent(1 - trackedShare)}</small>
      </div>
    </div>
  `;

  element.replaceChildren(graph);
}

function renderCumulativeTime(areas = []) {
  if (!areas.length) {
    activityCumulative.innerHTML = '<p class="empty">No cumulative time yet.</p>';
    return;
  }

  activityCumulative.replaceChildren(
    ...areas.map((item) => {
      const row = document.createElement("div");
      row.className = "cumulative-item";
      row.innerHTML = `
        <span>${item.area}</span>
        <strong>${formatDuration(item.minutes)}</strong>
        <small>${item.source_count || 0} session(s) · ${formatPercent(item.share)} of tracked</small>
      `;
      return row;
    }),
  );
}

function renderActivityAllocation(payload = {}) {
  const summary = payload.summary || {};
  const monthSummary = payload.month_summary || {};
  const qualityNotes = payload.data_quality?.notes || [];
  const areas = summary.areas || [];
  const monthAreas = monthSummary.areas || [];
  const sessions = payload.sessions || [];

  activitySummary.replaceChildren(
    ...[
      ["Today Tracked", formatDuration(summary.total_tracked_minutes || 0)],
      ["24h Share", formatPercent(summary.tracked_share_of_capacity || 0)],
      ["Month Tracked", formatDuration(monthSummary.total_tracked_minutes || 0)],
      ["Month Share", formatPercent(monthSummary.tracked_share_of_capacity || 0)],
    ].map(([label, value]) => {
      const item = document.createElement("div");
      item.className = "metric-item";
      item.innerHTML = `<span>${label}</span><strong>${value}</strong>`;
      return item;
    }),
  );

  renderActivityStack(activityBars, "Daily 24h", areas, summary.tracked_share_of_capacity);
  renderActivityStack(activityMonthBars, "Month to Date", monthAreas, monthSummary.tracked_share_of_capacity);
  renderCumulativeTime(monthAreas);

  if (!sessions.length) {
    activitySessions.innerHTML = '<p class="empty">No activity sessions yet.</p>';
    return;
  }

  activitySessions.replaceChildren(
    ...sessions.map((item) => {
      const row = document.createElement("article");
      row.className = item.review_required ? "capture-item needs-review" : "capture-item";
      const time = [item.start_time, item.end_time].filter(Boolean).join(" - ") || "time unknown";
      const review = item.review_required
        ? `<small class="review-note">${item.review_reason || "Review required"}</small>`
        : "";
      row.innerHTML = `
        <div>
          <header>
            <strong>${item.area}</strong>
            <span class="badge">${item.review_required ? "Review" : formatDuration(item.duration_minutes)}</span>
          </header>
          <p>${item.source_text || item.label || ""}</p>
          <small>${time} · ${item.status || "candidate"} · ${formatDuration(item.duration_minutes)} · confidence ${item.confidence ?? "unknown"}</small>
          ${review}
        </div>
        <span class="review-label">${item.parse_method || "time"}</span>
      `;
      return row;
    }),
  );

  if (qualityNotes.length) {
    const note = document.createElement("p");
    note.className = "data-quality-note";
    note.textContent = qualityNotes.slice(0, 2).join(" ");
    activitySessions.prepend(note);
  }
}

function renderActions(items = []) {
  if (!items.length) {
    actionsList.innerHTML = '<p class="empty">No action suggestions yet.</p>';
    return;
  }

  actionsList.replaceChildren(
    ...items.map((item) => {
      const action = document.createElement("article");
      action.className = "action-item";
      action.innerHTML = `
        <header>
          <h3>${item.title}</h3>
          <span class="badge">${item.status}</span>
        </header>
        <p>${item.approval_required ? "Approval required" : "No approval required"}</p>
      `;
      return action;
    }),
  );
}

function renderNotifications(items = []) {
  if (!items.length) {
    notificationsList.innerHTML = '<p class="empty">No notification candidates.</p>';
    return;
  }

  notificationsList.replaceChildren(
    ...items.map((item) => {
      const notification = document.createElement("article");
      notification.className = "action-item";
      notification.innerHTML = `
        <header>
          <h3>${item.title}</h3>
          <span class="badge">${item.priority || "low"}</span>
        </header>
        <p>${item.message || ""}</p>
        <p>${item.send_allowed ? "Ready to send" : "Candidate only · approval required before send"}</p>
      `;
      return notification;
    }),
  );
}

function renderSyncStatus(payload = {}) {
  const summary = payload.summary || {};
  const recentEvents = payload.recent_events || [];
  const pendingCaptures = summary.pending_captures ?? "-";
  const pendingWorkouts = summary.pending_workouts ?? "-";
  const freshness = syncFreshnessStatus(summary);
  const cards = [
    ["Status", freshness.label, freshness.detail],
    ["Pending Captures", pendingCaptures, "capture_queue"],
    ["Pending Workouts", pendingWorkouts, "workout_queue"],
    ["Last Pull", formatSyncTime(summary.last_pull_at), "queue check"],
    ["Last Publish", formatSyncTime(summary.last_publish_at), "dashboard snapshots"],
    ["Freshness", formatSyncAge(freshness.ageMinutes), "published snapshot age"],
  ];

  const eventRows = recentEvents.slice(0, 5).map((event) => {
    const detail = event.details?.snapshot_key || event.details?.pending_count;
    return `
      <div class="sync-event">
        <span>${formatSyncTime(event.created_at)}</span>
        <strong>${event.action || "event"}</strong>
        <small>${event.target_table || "-"} · ${event.status || "unknown"}${detail !== undefined ? ` · ${detail}` : ""}</small>
      </div>
    `;
  }).join("");

  syncStatusList.innerHTML = `
    <div class="sync-metrics">
      ${cards.map(([label, value, detail]) => `
        <article class="sync-card status-${freshness.status}">
          <span>${label}</span>
          <strong>${value}</strong>
          <small>${detail}</small>
        </article>
      `).join("")}
    </div>
    <article class="sync-events">
      <h3 class="panel-title">Recent Worker Events</h3>
      ${eventRows || '<p class="empty">No sync events published yet.</p>'}
    </article>
  `;
}

function shortId(id = "") {
  return id.replace("capture_", "").slice(0, 22);
}

function renderCaptures(items = []) {
  if (!items.length) {
    capturesList.innerHTML = '<p class="empty">No captures yet.</p>';
    return;
  }

  capturesList.replaceChildren(
    ...items.slice().reverse().map((item) => {
      const row = document.createElement("article");
      row.className = item.status === "ignored" ? "capture-item ignored" : "capture-item";
      const agents = (item.linked_agents || []).map((agent) => agent.replace("nomad-", "")).join(", ");
      row.innerHTML = `
        <div>
          <header>
            <strong>${shortId(item.id)}</strong>
            <span class="badge">${item.status || "unknown"}</span>
          </header>
          <p>${item.raw_content || ""}</p>
          <small>${agents || "uncategorized"}</small>
        </div>
        <button class="button-ghost capture-ignore" type="button" ${item.status === "ignored" ? "disabled" : ""} data-capture-id="${item.id}">
          Ignore
        </button>
      `;
      return row;
    }),
  );
}

function formatMoney(amount, currency) {
  if (amount === null || amount === undefined) {
    return "Amount unknown";
  }
  return `${Number(amount).toLocaleString("ko-KR")} ${currency || ""}`.trim();
}

function renderExpenseCandidates(items = []) {
  if (!items.length) {
    expenseCandidatesList.innerHTML = '<p class="empty">No imported finance signals yet.</p>';
    return;
  }

  expenseCandidatesList.replaceChildren(
    ...items.slice().reverse().map((item) => {
      const row = document.createElement("article");
      row.className = "capture-item";
      const category = [item.category, item.subcategory].filter(Boolean).join(" / ") || "needs category";
      row.innerHTML = `
        <div>
          <header>
            <strong>${formatMoney(item.amount, item.currency)}</strong>
            <span class="badge">${item.status || "candidate"}</span>
          </header>
          <p>${item.note || ""}</p>
          <small>${category} · ${item.date || ""} · source ${shortId(item.source || "")}</small>
        </div>
        <span class="review-label">Review</span>
      `;
      return row;
    }),
  );
}

function renderHermesDraft(payload) {
  if (!payload?.exists) {
    hermesDraft.innerHTML = '<p class="empty">No Hermes draft generated yet.</p>';
    return;
  }

  const content = payload.content || "";
  const title = content.match(/^#\s+(.+)$/m)?.[1] || "Hermes Coordinator Draft";
  const excerpt = content
    .replace(/^# .+$/m, "")
    .trim()
    .split("\n")
    .filter(Boolean)
    .slice(0, 18)
    .join("\n");

  hermesDraft.innerHTML = `
    <div class="draft-meta">
      <span class="badge">draft</span>
      <span>${payload.path}</span>
    </div>
    <h3>${title}</h3>
    <pre>${excerpt}</pre>
  `;
}

function renderLocalContext(context = {}) {
  const entries = [
    ["Calendar", context.calendar, "event_count"],
    ["Notes", context.notes, "note_count"],
  ];

  localContextList.replaceChildren(
    ...entries.map(([label, payload, countKey]) => {
      const card = document.createElement("article");
      card.className = "context-card";
      const quality = payload?.data_quality;
      const summary = payload?.summary;
      const status = quality?.status || (payload?.connected ? "unknown" : "not connected");
      const count = summary?.[countKey] ?? 0;
      const signals = (summary?.signals || []).map((signal) => signal.message).filter(Boolean);
      const contextLine = label === "Calendar"
        ? `density: ${summary?.schedule_density || "unknown"} · timed: ${summary?.timed_event_count ?? 0}`
        : `candidates: ${(summary?.candidate_agents || []).map((agent) => agent.replace("nomad-", "")).join(", ") || "none"}`;
      const notes = signals.slice(0, 2).join(" ") || (quality?.notes || []).slice(0, 2).join(" ");
      card.innerHTML = `
        <header>
          <h3>${label}</h3>
          <span class="badge">${status}</span>
        </header>
        <p>${count} item(s)</p>
        <small>${contextLine}</small>
        <small>${notes || "No local app snapshot yet."}</small>
      `;
      return card;
    }),
  );
}

async function loadJson(path) {
  const response = await fetch(path, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Failed to load ${path}`);
  }
  return response.json();
}

async function loadDashboard() {
  setCloudModeUi();
  const [today, life] = await Promise.all([
    loadDashboardJson("today", "/dashboard/today.json", {
      date: "Today",
      summary: "Dashboard snapshot이 아직 없습니다.",
      focus_today: [],
      let_go_today: [],
      missions: [],
      agent_council: [],
      actions: [],
      local_app_context: {},
    }),
    loadDashboardJson("life-balance", "/dashboard/life-balance.json", { areas: [] }),
  ]);
  const notifications = await loadDashboardJson("notifications", "/dashboard/notifications.json", { notifications: [] });
  const syncStatus = await loadDashboardJson("sync-status", "/dashboard/sync-status.json", { summary: {}, recent_events: [] });
  const expenseCandidates = isSupabaseMode()
    ? { candidates: [] }
    : await loadJson("/data/expenses/expense-candidates.json").catch(() => ({ candidates: [] }));
  const activityAllocation = await loadDashboardJson("activity-allocation", "/dashboard/activity-allocation.json", { summary: {}, sessions: [] });
  const health = await loadDashboardJson("health", "/dashboard/health.json", { summary: {}, muscle_dashboard: {} });
  const workoutHistory = isSupabaseMode()
    ? await loadDashboardSnapshot("workout-history").catch(() => ({ sessions: [] }))
    : await loadJson("/api/workout-history").catch(() => ({ sessions: [] }));
  workoutHistorySessions = workoutHistory.sessions || [];

  todayDate.textContent = today.date || "Today";
  summary.textContent = today.summary || "No summary yet.";
  renderList(focusList, today.focus_today);
  renderList(letGoList, today.let_go_today);
  renderList(missionsList, today.missions);
  renderCouncil(today.agent_council);
  renderActions(today.actions);
  renderNotifications(notifications.notifications);
  renderSyncStatus(syncStatus);
  renderHealthDashboard(health);
  renderRoutineCards(workoutHistorySessions);
  renderExerciseHistory(workoutExercise.value);
  updateLatestExerciseGuide();
  renderActivityAllocation(activityAllocation);
  renderLocalContext(today.local_app_context);
  renderLifeBalance(life.areas);
  const captures = isSupabaseMode()
    ? { captures: [] }
    : await loadJson(`/api/captures?date=${encodeURIComponent(today.date)}`).catch(() => ({ captures: [] }));
  renderCaptures(captures.captures);
  renderExpenseCandidates(expenseCandidates.candidates);
  renderWorkspaceOverview({
    today,
    health,
    activityAllocation,
    captures,
    expenseCandidates,
    notifications,
    syncStatus,
  });
  const draft = isSupabaseMode()
    ? {}
    : await loadJson(`/api/hermes-draft?date=${encodeURIComponent(today.date)}`).catch(() => ({}));
  renderHermesDraft(draft);
}

muscleHeatmap.addEventListener("click", (event) => {
  const cell = event.target.closest(".heatmap-cell");
  if (!cell) {
    return;
  }
  const entries = JSON.parse(cell.dataset.entries || "[]");
  renderMuscleDetail(cell.dataset.label, cell.dataset.date, entries);
});

captureForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const value = captureText.value.trim();
  if (!value) {
    captureStatus.textContent = "Capture text is empty.";
    return;
  }
  captureStatus.textContent = "Saving...";
  const payload = {
    type: "text",
    text: value,
  };
  const savePromise = isSupabaseMode()
    ? supabaseRequest("capture_queue", {
      method: "POST",
      headers: {
        prefer: "return=minimal",
      },
      body: JSON.stringify({
        source: "dashboard",
        status: "pending",
        payload,
      }),
    })
    : fetch("/api/capture", {
      method: "POST",
      headers: {
        "content-type": "application/json",
      },
      body: JSON.stringify(payload),
    });
  savePromise
    .then(async (response) => {
      if (isSupabaseMode()) {
        return response;
      }
      const responsePayload = await response.json();
      if (!response.ok) {
        throw new Error(responsePayload.error || "Capture failed.");
      }
      return responsePayload;
    })
    .then(() => {
      captureText.value = "";
      captureStatus.textContent = isSupabaseMode()
        ? "Capture queued. Mac Hermes가 처리합니다."
        : "Saved. Dashboard updated.";
      if (!isSupabaseMode()) {
        return loadDashboard();
      }
      return null;
    })
    .catch((error) => {
      captureStatus.textContent = error.message;
    });
});

syncInboxButton.addEventListener("click", () => {
  if (isSupabaseMode()) {
    captureStatus.textContent = "Cloud mode에서는 Mac Hermes Worker가 queue를 처리합니다.";
    return;
  }
  captureStatus.textContent = "Syncing inbox...";
  syncInboxButton.disabled = true;
  fetch("/api/sync-inbox", {
    method: "POST",
  })
    .then(async (response) => {
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.error || "Sync failed.");
      }
      const processed = payload.processed?.length || 0;
      const errors = payload.errors?.length || 0;
      captureStatus.textContent = errors
        ? `Synced ${processed}, ${errors} error(s).`
        : `Synced ${processed} inbox file(s).`;
      return loadDashboard();
    })
    .catch((error) => {
      captureStatus.textContent = error.message;
    })
    .finally(() => {
      syncInboxButton.disabled = false;
    });
});

syncLocalAppsButton.addEventListener("click", () => {
  if (isSupabaseMode()) {
    captureStatus.textContent = "Local app context refresh는 Mac local dashboard에서 실행합니다.";
    return;
  }
  captureStatus.textContent = "Refreshing local app context...";
  syncLocalAppsButton.disabled = true;
  fetch("/api/sync-local-apps", {
    method: "POST",
  })
    .then(async (response) => {
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.error || "Local app refresh failed.");
      }
      captureStatus.textContent = "Local app context refreshed.";
      return loadDashboard();
    })
    .catch((error) => {
      captureStatus.textContent = error.message;
    })
    .finally(() => {
      syncLocalAppsButton.disabled = false;
    });
});

workoutMuscle.addEventListener("change", refreshExerciseOptions);
workoutExercise.addEventListener("change", () => {
  refreshExerciseActions();
  renderExerciseHistory(workoutExercise.value);
});
exerciseSearch.addEventListener("input", refreshExerciseOptions);
openWorkoutTime.addEventListener("click", () => {
  setTimePickerValue(new Date(workoutStartedAt));
  workoutTimePopover.hidden = !workoutTimePopover.hidden;
});
applyWorkoutTime.addEventListener("click", applyWorkoutStartedAt);

routineFilters.addEventListener("click", (event) => {
  const button = event.target.closest("[data-routine-filter]");
  if (!button) {
    return;
  }
  selectedRoutineFilter = button.dataset.routineFilter || "all";
  renderRoutineCards(workoutHistorySessions);
});

routinePrev.addEventListener("click", () => {
  routineTrack.scrollBy({ left: -Math.max(280, routineTrack.clientWidth * 0.78), behavior: "smooth" });
});

routineNext.addEventListener("click", () => {
  routineTrack.scrollBy({ left: Math.max(280, routineTrack.clientWidth * 0.78), behavior: "smooth" });
});

routineTrack.addEventListener("click", (event) => {
  const button = event.target.closest("[data-exercise-id]");
  if (!button) {
    return;
  }
  const exerciseId = button.dataset.exerciseId;
  renderExerciseHistory(exerciseId);
  if ([...workoutExercise.options].some((option) => option.value === exerciseId)) {
    workoutExercise.value = exerciseId;
    refreshExerciseActions();
  }
});

favoriteExercise.addEventListener("click", () => {
  const item = selectedExercise();
  if (!item) {
    workoutStatus.textContent = "운동을 먼저 선택하세요.";
    return;
  }
  if (isSupabaseMode()) {
    workoutStatus.textContent = "Cloud mode에서는 Like 저장을 다음 단계에서 연결합니다.";
    return;
  }
  favoriteExercise.disabled = true;
  fetch("/api/exercises/favorite", {
    method: "POST",
    headers: {
      "content-type": "application/json",
    },
    body: JSON.stringify({
      exercise_id: item.id,
      favorite: !item.favorite,
    }),
  })
    .then(async (response) => {
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.error || "Favorite update failed.");
      }
      return loadExerciseLibrary();
    })
    .then(() => {
      workoutStatus.textContent = `${item.name_ko || item.name_en} preference updated.`;
    })
    .catch((error) => {
      workoutStatus.textContent = error.message;
    })
    .finally(() => {
      refreshExerciseActions();
    });
});

exerciseDetail.addEventListener("click", () => {
  renderExerciseDialog(selectedExercise());
});

addWorkoutSet.addEventListener("click", () => {
  const weight = Number(workoutWeight.value);
  const reps = Number.parseInt(workoutReps.value, 10);
  const rpe = workoutRpe.value ? Number(workoutRpe.value) : null;
  if (!Number.isFinite(weight) || weight < 0 || !Number.isFinite(reps) || reps <= 0) {
    workoutStatus.textContent = "무게와 반복 수를 확인하세요.";
    return;
  }

  const muscle = workoutMuscle.value;
  const exercise = workoutExercise.value;
  const nextEntry = {
    muscle_group: muscle,
    exercise,
    weight_kg: weight,
    reps,
    rpe,
    note: null,
  };

  if (editingWorkoutIndex !== null) {
    workoutEntries[editingWorkoutIndex] = {
      ...workoutEntries[editingWorkoutIndex],
      ...nextEntry,
    };
    reindexWorkoutEntries();
    renderWorkoutSets();
    workoutStatus.textContent = `${exerciseLabel(muscle, exercise)} set edited.`;
    const returnState = editingReturnState;
    resetWorkoutEditMode();
    applyWorkoutFormState(returnState);
    persistWorkoutDraft();
    return;
  }

  addWorkoutEntry(nextEntry);
  workoutStatus.textContent = `${exerciseLabel(muscle, exercise)} set added.`;
});

workoutSetList.addEventListener("click", (event) => {
  const editButton = event.target.closest(".workout-edit");
  const removeButton = event.target.closest(".workout-remove");
  if (!editButton && !removeButton) {
    return;
  }
  const button = editButton || removeButton;
  const index = Number(button.dataset.index);
  if (!Number.isInteger(index) || !workoutEntries[index]) {
    return;
  }

  if (editButton) {
    if (editingWorkoutIndex === null) {
      editingReturnState = currentWorkoutFormState();
    }
    editingWorkoutIndex = index;
    loadWorkoutEntryIntoForm(workoutEntries[index]);
    addWorkoutSet.textContent = "Edit Set";
    workoutStatus.textContent = `${exerciseLabel(workoutEntries[index].muscle_group, workoutEntries[index].exercise)} set editing.`;
    return;
  }

  workoutEntries.splice(index, 1);
  reindexWorkoutEntries();
  if (editingWorkoutIndex !== null) {
    const returnState = editingReturnState;
    resetWorkoutEditMode();
    applyWorkoutFormState(returnState);
  }
  renderWorkoutSets();
  persistWorkoutDraft();
  workoutStatus.textContent = "Set removed.";
});

workoutForm.addEventListener("submit", (event) => {
  event.preventDefault();
  if (!workoutEntries.length) {
    workoutStatus.textContent = "Add at least one set.";
    return;
  }

  workoutStatus.textContent = "Saving workout...";
  const payload = buildStrengthWorkoutPayload({
    startedAt: workoutStartedAt,
    muscleGroup: workoutMuscle.value,
    entries: workoutEntries,
    note: workoutNote.value,
  });
  const savePromise = isSupabaseMode()
    ? supabaseRequest("workout_queue", {
      method: "POST",
      headers: {
        prefer: "return=minimal",
      },
      body: JSON.stringify({
        source: "dashboard",
        status: "pending",
        payload,
      }),
    })
    : fetch("/api/workout-session", {
      method: "POST",
      headers: {
        "content-type": "application/json",
      },
      body: JSON.stringify(payload),
    });
  savePromise
    .then(async (response) => {
      if (isSupabaseMode()) {
        return response;
      }
      const responsePayload = await response.json();
      if (!response.ok) {
        throw new Error(responsePayload.error || "Workout save failed.");
      }
      return responsePayload;
    })
    .then(() => {
      workoutEntries = [];
      workoutNote.value = "";
      clearWorkoutDraft();
      resetWorkoutStartedAt();
      resetWorkoutEditMode();
      renderWorkoutSets();
      workoutStatus.textContent = isSupabaseMode()
        ? "Workout queued. Mac Hermes가 처리합니다."
        : "Workout saved. Health Agent updated.";
      if (!isSupabaseMode()) {
        return loadDashboard();
      }
      return null;
    })
    .catch((error) => {
      workoutStatus.textContent = error.message;
    });
});

capturesList.addEventListener("click", (event) => {
  const button = event.target.closest(".capture-ignore");
  if (!button) {
    return;
  }

  const captureId = button.dataset.captureId;
  button.disabled = true;
  captureStatus.textContent = "Ignoring capture...";
  fetch("/api/captures/ignore", {
    method: "POST",
    headers: {
      "content-type": "application/json",
    },
    body: JSON.stringify({ capture_id: captureId }),
  })
    .then(async (response) => {
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.error || "Ignore failed.");
      }
      captureStatus.textContent = "Capture ignored. Dashboard updated.";
      return loadDashboard();
    })
    .catch((error) => {
      captureStatus.textContent = error.message;
      button.disabled = false;
    });
});

workspaceLinks.forEach((link) => {
  link.addEventListener("click", (event) => {
    event.preventDefault();
    setActiveView(link.dataset.viewLink);
  });
});

window.addEventListener("hashchange", () => {
  setActiveView(window.location.hash.replace("#", ""), false);
});

workspaceOverview.addEventListener("click", (event) => {
  const card = event.target.closest("[data-overview-view]");
  if (!card) {
    return;
  }
  setActiveView(card.dataset.overviewView);
});

[workoutMuscle, workoutExercise, exerciseSearch, workoutWeight, workoutReps, workoutRpe, workoutNote].forEach((element) => {
  element.addEventListener("change", persistWorkoutDraft);
  element.addEventListener("input", persistWorkoutDraft);
});

window.addEventListener("storage", (event) => {
  if (event.key !== WORKOUT_DRAFT_STORAGE_KEY) {
    return;
  }
  if (!event.newValue) {
    workoutEntries = [];
    workoutNote.value = "";
    resetWorkoutEditMode();
    renderWorkoutSets();
    return;
  }
  restoreWorkoutDraft();
});

resetWorkoutStartedAt();
renderWorkoutSets();
setActiveView(window.location.hash.replace("#", "") || "today", false);
loadAppConfig()
  .then(() => {
    setCloudModeUi();
    return loadExerciseLibrary();
  })
  .then(() => {
    restoreWorkoutDraft();
  })
  .then(loadDashboard)
  .catch((error) => {
    summary.textContent = error.message;
    workoutStatus.textContent = error.message;
  });

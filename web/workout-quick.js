const muscleSelect = document.querySelector("#muscle-select");
const exerciseSelect = document.querySelector("#exercise-select");
const favoriteButton = document.querySelector("#favorite-button");
const infoButton = document.querySelector("#info-button");
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
const timeStatus = document.querySelector("#time-status");
const timePanel = document.querySelector("#time-panel");
const startDate = document.querySelector("#start-date");
const startTime = document.querySelector("#start-time");
const applyTime = document.querySelector("#apply-time");
const quickForm = document.querySelector("#quick-form");
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

let exerciseLibrary = [];
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
  return appConfig.mode === "supabase" && appConfig.supabaseUrl && appConfig.supabaseAnonKey;
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

function setWorkoutStartedAt(value = new Date()) {
  workoutStartedAt = value.toISOString();
  setTimeFields(value);
  timeStatus.textContent = `${formatTime(workoutStartedAt)} 적용`;
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

function exerciseName(exerciseId) {
  const item = exerciseLibrary.find((exercise) => exercise.id === exerciseId);
  return item?.name_ko || item?.name_en || exerciseId;
}

function selectedExercise() {
  return exerciseLibrary.find((exercise) => exercise.id === exerciseSelect.value) || null;
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
  return `${weight}kg X ${reps}`;
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

function refreshExerciseActions() {
  const item = selectedExercise();
  favoriteButton.textContent = item?.favorite ? "♥" : "♡";
  favoriteButton.classList.toggle("active", Boolean(item?.favorite));
  favoriteButton.disabled = !item;
  infoButton.disabled = !item;
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
  const counts = {};
  workoutEntries = workoutEntries.map((entry) => {
    const key = entry.exercise || "exercise";
    counts[key] = (counts[key] || 0) + 1;
    return { ...entry, set_index: counts[key] };
  });
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
  addSetButton.textContent = "Add Set";
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

function renderDraft() {
  if (!workoutEntries.length) {
    draftList.innerHTML = '<p class="empty">아직 추가된 세트가 없습니다.</p>';
    return;
  }
  draftList.innerHTML = groupedEntries().map((group) => `
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
    quickStatus.textContent = `${exerciseName(entry.exercise)} set edited.`;
    const returnState = editingReturnState;
    resetEditMode();
    applyFormState(returnState);
    return;
  }

  const sameExerciseCount = workoutEntries.filter((item) => item.exercise === entry.exercise).length;
  workoutEntries.push({ ...entry, set_index: sameExerciseCount + 1 });
  renderDraft();
  quickStatus.textContent = `${exerciseName(entry.exercise)} set added.`;
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

async function loadInitialData() {
  const exercisePath = isSupabaseMode() ? "/web/data/exercise-library.json" : "/api/exercises";
  const historyLoader = isSupabaseMode()
    ? Promise.resolve({ sessions: [] })
    : loadJson("/api/workout-history").catch(() => ({ sessions: [] }));
  const [exercisePayload, historyPayload] = await Promise.all([
    loadJson(exercisePath).catch(() => ({ exercises: [] })),
    historyLoader,
  ]);
  exerciseLibrary = exercisePayload.exercises || [];
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

muscleSelect.addEventListener("change", refreshExerciseOptions);
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
    quickStatus.textContent = `${exerciseName(workoutEntries[index].exercise)} set editing.`;
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
  quickStatus.textContent = "Set removed.";
});

quickForm.addEventListener("submit", (event) => {
  event.preventDefault();
  if (!workoutEntries.length) {
    quickStatus.textContent = "Add at least one set.";
    return;
  }
  saveWorkoutButton.disabled = true;
  quickStatus.textContent = "Saving workout...";
  const payload = {
    type: "strength",
    started_at: workoutStartedAt,
    ended_at: new Date().toISOString(),
    muscle_group: muscleSelect.value,
    entries: workoutEntries,
    note: noteInput.value.trim(),
  };
  const savePromise = isSupabaseMode()
    ? supabaseRequest("workout_queue", {
      method: "POST",
      headers: {
        prefer: "return=minimal",
      },
      body: JSON.stringify({
        source: "workout_quick",
        status: "pending",
        payload,
      }),
    })
    : fetch("/api/workout-session", {
    method: "POST",
    headers: { "content-type": "application/json" },
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
    .then(async () => {
      workoutEntries = [];
      noteInput.value = "";
      resetEditMode();
      setWorkoutStartedAt(new Date());
      renderDraft();
      await loadInitialData();
      quickStatus.textContent = isSupabaseMode() ? "Workout queued. Mac Hermes가 처리합니다." : "Workout saved.";
    })
    .catch((error) => {
      quickStatus.textContent = error.message;
    })
    .finally(() => {
      saveWorkoutButton.disabled = false;
    });
});

setWorkoutStartedAt(new Date());
loadAppConfig()
  .then(loadInitialData)
  .then(() => {
    if (isSupabaseMode()) {
      quickStatus.textContent = "Cloud mode: Supabase queue에 저장됩니다.";
    }
  })
  .catch((error) => {
    quickStatus.textContent = error.message;
  });

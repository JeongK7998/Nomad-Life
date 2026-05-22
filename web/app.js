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
const aiWorkStatus = document.querySelector("#ai-work-status");
const aiWorkSummary = document.querySelector("#ai-work-summary");
const aiWorkVisuals = document.querySelector("#ai-work-visuals");
const aiWorkProjectCount = document.querySelector("#ai-work-project-count");
const aiWorkProjects = document.querySelector("#ai-work-projects");
const aiWorkDetailTitle = document.querySelector("#ai-work-detail-title");
const aiWorkDetail = document.querySelector("#ai-work-detail");
const aiWorkAddButton = document.querySelector("#ai-work-add-button");
const aiWorkEditButton = document.querySelector("#ai-work-edit-button");
const aiWorkImportButton = document.querySelector("#ai-work-import-button");
const aiWorkProjectDialog = document.querySelector("#ai-work-project-dialog");
const aiWorkDialogTitle = document.querySelector("#ai-work-dialog-title");
const aiWorkDialogClose = document.querySelector("#ai-work-dialog-close");
const aiWorkProjectForm = document.querySelector("#ai-work-project-form");
const aiWorkProjectMode = document.querySelector("#ai-work-project-mode");
const aiWorkProjectId = document.querySelector("#ai-work-project-id");
const aiWorkProjectName = document.querySelector("#ai-work-project-name");
const aiWorkProjectType = document.querySelector("#ai-work-project-type");
const aiWorkProjectStatus = document.querySelector("#ai-work-project-status");
const aiWorkProjectPriority = document.querySelector("#ai-work-project-priority");
const aiWorkProjectPath = document.querySelector("#ai-work-project-path");
const aiWorkBrowseFolder = document.querySelector("#ai-work-browse-folder");
const aiWorkCurrentFocus = document.querySelector("#ai-work-current-focus");
const aiWorkNextAction = document.querySelector("#ai-work-next-action");
const aiWorkSuccessCriteria = document.querySelector("#ai-work-success-criteria");
const aiWorkSensitivity = document.querySelector("#ai-work-sensitivity");
const aiWorkEvidenceMode = document.querySelector("#ai-work-evidence-mode");
const aiWorkOutputPath = document.querySelector("#ai-work-output-path");
const aiWorkProjectAliases = document.querySelector("#ai-work-project-aliases");
const aiWorkExcludePaths = document.querySelector("#ai-work-exclude-paths");
const aiWorkPublishDashboard = document.querySelector("#ai-work-publish-dashboard");
const aiWorkFormStatus = document.querySelector("#ai-work-form-status");
const aiWorkSubmitProject = document.querySelector("#ai-work-submit-project");
const mainAgentSummary = document.querySelector("#main-agent-summary");
const mainAgentMetrics = document.querySelector("#main-agent-metrics");
const mainDailyBars = document.querySelector("#main-daily-bars");
const mainMonthBars = document.querySelector("#main-month-bars");
const mainCumulative = document.querySelector("#main-cumulative");
const mainAgentSignals = document.querySelector("#main-agent-signals");
const mainShareTitle = document.querySelector("#main-share-title");
const mainPeriodToggle = document.querySelector("#main-period-toggle");
const englishSummary = document.querySelector("#english-summary");
const syncEnglishReviewsButton = document.querySelector("#sync-english-reviews-button");
const englishReviewFileStats = document.querySelector("#english-review-file-stats");
const englishReviewFileGraph = document.querySelector("#english-review-file-graph");
const englishImportDetails = document.querySelector("#english-import-details");
const englishImportDetailList = document.querySelector("#english-import-detail-list");
const englishSyncStatus = document.querySelector("#english-sync-status");
const englishDecisionHeader = document.querySelector("#english-decision-header");
const englishAgentInterpretation = document.querySelector("#english-agent-interpretation");
const englishValidationAgent = document.querySelector("#english-validation-agent");
const englishProgression = document.querySelector("#english-progression");
const englishImprovementSignals = document.querySelector("#english-improvement-signals");
const englishPersistentIssues = document.querySelector("#english-persistent-issues");
const englishNextFocus = document.querySelector("#english-next-focus");
const englishPerformanceMetrics = document.querySelector("#english-performance-metrics");
const englishIssueTracker = document.querySelector("#english-issue-tracker");
const englishDailyLog = document.querySelector("#english-daily-log");
const englishDailyLogPager = document.querySelector("#english-daily-log-pager");
const englishPreStudyContext = document.querySelector("#english-pre-study-context");
const englishWeeklySummary = document.querySelector("#english-weekly-summary");
const englishHabitRecommendations = document.querySelector("#english-habit-recommendations");
const englishHabits = document.querySelector("#english-habits");
const englishNextActions = document.querySelector("#english-next-actions");
const englishLearnedItems = document.querySelector("#english-learned-items");
const englishCorrections = document.querySelector("#english-corrections");
const englishReviewCards = document.querySelector("#english-review-cards");
const englishReviews = document.querySelector("#english-reviews");
let englishDailyLogPage = 0;
const healthSummary = document.querySelector("#health-summary");
const healthWindowNote = document.querySelector("#health-window-note");
const healthReadiness = document.querySelector("#health-readiness");
const healthRecommendations = document.querySelector("#health-recommendations");
const routineTrack = document.querySelector("#routine-track");
const routinePrev = document.querySelector("#routine-prev");
const routineNext = document.querySelector("#routine-next");
const routineYearSelect = document.querySelector("#routine-year-select");
const routineMonthSelect = document.querySelector("#routine-month-select");
const exerciseHistoryTitle = document.querySelector("#exercise-history-title");
const exerciseHistory = document.querySelector("#exercise-history");
const muscleHeatmap = document.querySelector("#muscle-heatmap");
const muscleSummary = document.querySelector("#muscle-summary");
const muscleDetail = document.querySelector("#muscle-detail");
const actionsList = document.querySelector("#actions-list");
const capturesList = document.querySelector("#captures-list");
const captureYearFilter = document.querySelector("#capture-year-filter");
const captureMonthFilter = document.querySelector("#capture-month-filter");
const captureStatusFilter = document.querySelector("#capture-status-filter");
const captureDetailDialog = document.querySelector("#capture-detail-dialog");
const captureDetailTitle = document.querySelector("#capture-detail-title");
const captureDetailContent = document.querySelector("#capture-detail-content");
const expenseCandidatesList = document.querySelector("#expense-candidates-list");
const financeReviewPanel = document.querySelector("#finance-review-panel");
const syncFinanceButton = document.querySelector("#sync-finance-button");
const financeSyncStatus = document.querySelector("#finance-sync-status");
const hermesDraft = document.querySelector("#hermes-draft");
const localContextList = document.querySelector("#local-context-list");
const localContextSyncStatus = document.querySelector("#local-context-sync-status");
const syncStatusList = document.querySelector("#sync-status-list");
const captureStatus = document.querySelector("#capture-status");
const activityForm = document.querySelector("#activity-form");
const activityDate = document.querySelector("#activity-date");
const activityDurationSlider = document.querySelector("#activity-duration-slider");
const activityDurationLabel = document.querySelector("#activity-duration-label");
const activityStartButton = document.querySelector("#activity-start-button");
const activityEndButton = document.querySelector("#activity-end-button");
const activityTimerStatus = document.querySelector("#activity-timer-status");
const activityPlace = document.querySelector("#activity-place");
const activitySubcategory = document.querySelector("#activity-subcategory");
const activityDetail = document.querySelector("#activity-detail");
const activityParseMemo = document.querySelector("#activity-parse-memo");
const activityStatus = document.querySelector("#activity-status");
const deleteRoutineCardButton = document.querySelector("#delete-routine-card");
const healthQuickBuilder = document.querySelector("#health-quick-builder");
const healthQuickTotal = document.querySelector("#health-quick-total");
const addHealthActivity = document.querySelector("#add-health-activity");
const healthActivityDraftList = document.querySelector("#health-activity-draft-list");
const openQuickButton = document.querySelector("#open-quick-button");
const floatingQuickButton = document.querySelector("#floating-quick-button");
const closeQuickButton = document.querySelector("#close-quick-button");
const quickDialog = document.querySelector("#quick-dialog");
const openMenuButton = document.querySelector("#open-menu-button");
const closeMenuButton = document.querySelector("#close-menu-button");
const drawerBackdrop = document.querySelector("#drawer-backdrop");
const sidebar = document.querySelector(".sidebar");
const mobileViewTitle = document.querySelector("#mobile-view-title");
const activeStayPill = document.querySelector("#active-stay-pill");
const mobileActiveStay = document.querySelector("#mobile-active-stay");
const syncInboxButton = document.querySelector("#sync-inbox-button");
const syncLocalAppsButton = document.querySelector("#sync-local-apps-button");
const currentStayForm = document.querySelector("#current-stay-form");
const settingsStayId = document.querySelector("#settings-stay-id");
const settingsStartDate = document.querySelector("#settings-start-date");
const settingsEndDate = document.querySelector("#settings-end-date");
const settingsCurrentPlace = document.querySelector("#settings-current-place");
const settingsCountry = document.querySelector("#settings-country");
const settingsTimezone = document.querySelector("#settings-timezone");
const settingsDatasetScope = document.querySelector("#settings-dataset-scope");
const settingsStayNote = document.querySelector("#settings-stay-note");
const currentStayStatus = document.querySelector("#current-stay-status");
const stayIndexCount = document.querySelector("#stay-index-count");
const stayIndexList = document.querySelector("#stay-index-list");
const stayBackupButton = document.querySelector("#stay-backup-button");
const stayBackupStatus = document.querySelector("#stay-backup-status");
const workoutDialog = document.querySelector("#workout-dialog");
const openWorkoutDialogButton = document.querySelector("#open-workout-dialog");
const closeWorkoutDialogButton = document.querySelector("#close-workout-dialog");
const workoutForm = document.querySelector("#workout-form");
const exerciseLibrarySummary = document.querySelector("#exercise-library-summary");
const exerciseCategoryList = document.querySelector("#exercise-category-list");
const exerciseLibraryStatus = document.querySelector("#exercise-library-status");
const exerciseEditMode = document.querySelector("#exercise-edit-mode");
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
const exerciseRecent = document.querySelector("#exercise-recent");
const quickAddExercise = document.querySelector("#quick-add-exercise");
const latestExerciseGuide = document.querySelector("#latest-exercise-guide");
const exerciseDialog = document.querySelector("#exercise-dialog");
const exerciseDialogTitle = document.querySelector("#exercise-dialog-title");
const exerciseDialogContent = document.querySelector("#exercise-dialog-content");
const workoutWeight = document.querySelector("#workout-weight");
const workoutReps = document.querySelector("#workout-reps");
const workoutBodyweight = document.querySelector("#workout-bodyweight");
const workoutRpe = document.querySelector("#workout-rpe");
const addWorkoutSet = document.querySelector("#add-workout-set");
const workoutStatus = document.querySelector("#workout-status");
const workoutSetList = document.querySelector("#workout-set-list");
const workoutNote = document.querySelector("#workout-note");
const workspaceViews = [...document.querySelectorAll(".workspace-view")];
const workspaceLinks = [...document.querySelectorAll("[data-view-link]")];
const workspaceOverview = document.querySelector("#workspace-overview");
const VIEW_ALIASES = {
  input: "main",
  quick: "main",
  "nomad-quick": "main",
  today: "daily",
  captures: "capture",
  workout: "health",
  "health-dashboard": "health",
  work: "ai-work",
  "aiwork": "ai-work",
  life: "main",
  dashboard: "main",
  "expense-candidates": "finance",
  hermes: "reports",
  "local-context": "context",
  notifications: "council",
  actions: "council",
};

const ACTIVITY_COLORS = {
  "AI Work": "#99e7ff",
  Health: "#00a86b",
  English: "#7c3aed",
  "Creator/Social": "#f97316",
  "Travel/Experience": "#0ea5e9",
  Rest: "#64748b",
  Finance: "#eab308",
  Unclassified: "#989ba2",
};

const ACTIVE_ACTIVITY_STORAGE_KEY = "nomad_active_activity";
const QUICK_AREA_PREFILL_KEY = "nomad_quick_prefill_area";
const NOMAD_CURRENT_STAY_STORAGE_KEY = "nomad.currentStay.v1";
const NOMAD_INPUT_HISTORY_STORAGE_KEY = "nomad.inputHistory.v1";
const NOMAD_PENDING_HEALTH_STORAGE_KEY = "nomad.pendingHealth.v1";
const NOMAD_HEALTH_QUICK_DRAFT_STORAGE_KEY = "nomad.healthQuickDraft.v1";
const NOMAD_CLOUD_QUEUE_FALLBACK_KEY = "nomad.cloudQueueFallback.v1";
const DEFAULT_CURRENT_STAY = {
  schema_version: "0.1.0",
  stay_id: "bali-2026-05",
  region: "Bali",
  country: "Indonesia",
  timezone: "Asia/Makassar",
  start_date: "2026-05-19",
  end_date: null,
  status: "active",
  dataset_scope: "current",
  notes: ["Bali active stay"],
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
const MUSCLE_GROUPS = Object.entries(MUSCLE_LABELS);

let workoutStartedAt = new Date().toISOString();
let workoutEntries = [];
let healthActivityDrafts = [];
let editingHealthActivityIndex = null;
let editingGenericActivityId = null;
let editingSavedActivityId = null;
let editingSavedWorkoutId = null;
let editingRoutineGroupKey = null;
let editingRoutineDeleteTargets = null;
let activeStrengthDraftIndex = null;
let returnToQuickAfterStrength = false;
let exerciseLibrary = [];
let workoutHistorySessions = [];
let latestRoutineGroups = [];
let selectedRoutineMonth = "";
let latestHealthSessions = [];
let exerciseLibraryEditMode = false;
let editingExerciseId = null;
let editingWorkoutIndex = null;
let editingReturnState = null;
let activeActivity = null;
let lastTimerActivity = null;
let activeActivityTick = null;
let activitySubmitInFlight = false;
let activeStay = { ...DEFAULT_CURRENT_STAY };
let mainPeriodMode = "month";
let latestMainAgentPayload = null;
let aiWorkState = { projects: [], progress: {}, recent_events: [] };
let selectedAiWorkProjectId = null;
let captureHistoryState = [];
let selectedHistoryMonth = "";
let mainActivityHistoryCount = 0;
const LOCAL_EXERCISE_MUTATIONS_KEY = "nomad.exerciseLibraryMutations.v1";
let appConfig = {
  mode: "local",
  supabaseUrl: "",
  supabaseAnonKey: "",
};

function isSupabaseMode() {
  return isNomadCloudMode(appConfig);
}

async function loadAppConfig() {
  appConfig = await loadJson("/api/config").catch(() => appConfig);
  if (!appConfig.mode) {
    appConfig.mode = "local";
  }
}

async function supabaseRequest(path, options = {}) {
  await requireNomadSession();
  const baseUrl = appConfig.supabaseUrl.replace(/\/$/, "");
  const authToken = getNomadAuthToken();
  const response = await fetch(`${baseUrl}/rest/v1/${path}`, {
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

function newClientSubmissionId(prefix = "input") {
  return `${prefix}_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 9)}`;
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

async function loadDashboardJson(snapshotKey, localPath, fallback) {
  if (isSupabaseMode()) {
    return loadDashboardSnapshot(snapshotKey).catch(() => fallback);
  }
  return loadJson(localPath).catch(() => fallback);
}

function setCloudModeUi() {
  const cloud = isSupabaseMode();
  if (syncInboxButton) {
    syncInboxButton.disabled = cloud;
  }
  if (syncLocalAppsButton) {
    syncLocalAppsButton.disabled = cloud;
  }
  if (stayBackupButton) {
    stayBackupButton.disabled = cloud;
  }
  if (cloud && captureStatus) {
    captureStatus.textContent = "Saved inputs and analysis history";
  }
  if (cloud && stayBackupStatus) {
    stayBackupStatus.textContent = "Hosted mode에서는 Mac Hermes Worker에서 stay backup을 실행합니다.";
  }
}

function normalizeCurrentStay(stay = {}) {
  const merged = { ...DEFAULT_CURRENT_STAY, ...(stay || {}) };
  merged.stay_id = String(merged.stay_id || DEFAULT_CURRENT_STAY.stay_id).trim();
  merged.region = String(merged.region || DEFAULT_CURRENT_STAY.region).trim();
  merged.country = String(merged.country || DEFAULT_CURRENT_STAY.country).trim();
  merged.timezone = String(merged.timezone || DEFAULT_CURRENT_STAY.timezone).trim();
  merged.start_date = String(merged.start_date || DEFAULT_CURRENT_STAY.start_date).trim();
  merged.end_date = merged.end_date || null;
  merged.status = merged.end_date ? "closed" : "active";
  merged.dataset_scope = merged.dataset_scope || "current";
  merged.notes = Array.isArray(merged.notes) ? merged.notes : [String(merged.notes || "Bali active stay")];
  return merged;
}

function readStoredCurrentStay() {
  try {
    return normalizeCurrentStay(JSON.parse(localStorage.getItem(NOMAD_CURRENT_STAY_STORAGE_KEY) || "null") || DEFAULT_CURRENT_STAY);
  } catch {
    return normalizeCurrentStay(DEFAULT_CURRENT_STAY);
  }
}

function writeStoredCurrentStay(stay) {
  localStorage.setItem(NOMAD_CURRENT_STAY_STORAGE_KEY, JSON.stringify(normalizeCurrentStay(stay)));
}

function renderCurrentStay(stay = {}) {
  if (!currentStayForm) return;
  activeStay = normalizeCurrentStay(stay);
  settingsStayId.value = stay.stay_id || "";
  settingsStayId.value = activeStay.stay_id || "";
  settingsCurrentPlace.value = activeStay.region || "";
  settingsCountry.value = activeStay.country || "";
  settingsStartDate.value = activeStay.start_date || "";
  settingsEndDate.value = activeStay.end_date || "";
  settingsTimezone.value = activeStay.timezone || "Asia/Makassar";
  settingsDatasetScope.value = activeStay.dataset_scope || "current";
  settingsStayNote.value = (activeStay.notes || [])[0] || "";
  const statusLabel = activeStay.status ? `${activeStay.status} · ` : "";
  renderActiveStayChrome(activeStay);
  setWorkspaceStatus(currentStayStatus, `${statusLabel}${activeStay.region} · ${activeStay.timezone}`, "");
}

function renderActiveStayChrome(stay = {}) {
  const region = stay.region || "지역 미설정";
  const status = stay.status || (stay.end_date ? "closed" : "active");
  const label = status === "active" ? `현재 활성: ${region}` : `완료 지역: ${region}`;
  if (activeStayPill) {
    activeStayPill.textContent = label;
    activeStayPill.dataset.status = status;
  }
  if (mobileActiveStay) {
    mobileActiveStay.textContent = status === "active" ? region : `완료: ${region}`;
    mobileActiveStay.dataset.status = status;
  }
  document.title = region === "지역 미설정" ? "Nomad Dashboard" : `Nomad Dashboard · ${region}`;
}

function renderStayIndex(index = {}) {
  if (!stayIndexList) return;
  const stays = index.stays || [];
  stayIndexCount.textContent = String(stays.length);
  if (!stays.length) {
    stayIndexList.innerHTML = '<p class="empty">아직 저장된 지역 기록이 없습니다.</p>';
    return;
  }
  stayIndexList.innerHTML = stays.map((stay) => {
    const active = stay.stay_id === index.active_stay_id || stay.status === "active";
    const period = `${stay.start_date || "?"} - ${stay.end_date || "진행중"}`;
    return `
      <article class="stay-index-card ${active ? "active" : ""}">
        <header>
          <div>
            <h3>${escapeHtml(stay.region || stay.stay_id || "Unknown Stay")}</h3>
            <p>${escapeHtml(stay.country || "")} · ${escapeHtml(stay.timezone || "")}</p>
          </div>
          <span class="badge">${active ? "active" : "closed"}</span>
        </header>
        <dl>
          <div><dt>Period</dt><dd>${escapeHtml(period)}</dd></div>
          <div><dt>Stay ID</dt><dd>${escapeHtml(stay.stay_id || "")}</dd></div>
          <div><dt>Scope</dt><dd>${escapeHtml(stay.dataset_scope || "current")}</dd></div>
        </dl>
      </article>
    `;
  }).join("");
}

async function loadCurrentStay() {
  if (!currentStayForm) return;
  if (isSupabaseMode()) {
    const stay = readStoredCurrentStay();
    renderCurrentStay(stay);
    renderStayIndex({ active_stay_id: stay.stay_id, stays: [stay] });
    return;
  }
  const payload = await loadJson("/api/current-stay").catch(() => null);
  if (payload?.stay) {
    renderCurrentStay(payload.stay);
  }
  renderStayIndex(payload?.index || {});
}

function currentStayContext() {
  const stay = normalizeCurrentStay(activeStay);
  if (!stay.region || !stay.stay_id || !stay.timezone) {
    throw new Error("지역 설정이 필요합니다. Settings에서 현재 지역을 먼저 저장하세요.");
  }
  return {
    stay_id: stay.stay_id,
    region: stay.region,
    country: stay.country,
    timezone: stay.timezone,
    dataset_scope: stay.dataset_scope,
  };
}

function currentStayPayloadFromForm() {
  return {
    stay_id: settingsStayId.value.trim(),
    region: settingsCurrentPlace.value.trim(),
    country: settingsCountry.value.trim(),
    start_date: settingsStartDate.value,
    end_date: settingsEndDate.value || null,
    timezone: settingsTimezone.value,
    dataset_scope: settingsDatasetScope.value,
    note: settingsStayNote.value.trim(),
  };
}

function setMobileDrawer(open) {
  const isOpen = Boolean(open);
  const drawerMode = window.matchMedia("(max-width: 860px)").matches;
  document.body.classList.toggle("mobile-drawer-open", isOpen);
  sidebar?.toggleAttribute("inert", drawerMode && !isOpen);
  sidebar?.setAttribute("aria-hidden", String(drawerMode && !isOpen));
}

setMobileDrawer(false);
window.matchMedia("(max-width: 860px)").addEventListener("change", () => {
  setMobileDrawer(document.body.classList.contains("mobile-drawer-open"));
});

function openQuickDialog() {
  setMobileDrawer(false);
  if (!editingRoutineGroupKey && !editingSavedActivityId && !editingSavedWorkoutId && activityDate) {
    activityDate.value = todayLocalDateValue();
  }
  if (selectedRadioValue("area") === "health") {
    restoreHealthQuickDraft();
  }
  if (quickDialog?.open) {
    return;
  }
  if (quickDialog?.showModal) {
    quickDialog.showModal();
  } else {
    quickDialog?.setAttribute("open", "");
  }
}

function openWorkoutDialog(options = {}) {
  setMobileDrawer(false);
  returnToQuickAfterStrength = Boolean(options.returnToQuick);
  if (options.muscle) {
    workoutMuscle.value = options.muscle;
    refreshExerciseOptions();
  }
  if (!workoutStartedAt) {
    resetWorkoutStartedAt();
  }
  if (workoutDialog?.showModal && !workoutDialog.open) {
    workoutDialog.showModal();
  } else {
    workoutDialog?.setAttribute("open", "");
  }
}

function closeWorkoutDialog() {
  if (workoutDialog?.close) {
    workoutDialog.close();
  } else {
    workoutDialog?.removeAttribute("open");
  }
  if (returnToQuickAfterStrength) {
    returnToQuickAfterStrength = false;
    requestAnimationFrame(openQuickDialog);
  }
}

function selectedRadioValue(name) {
  return document.querySelector(`input[name="${name}"]:checked`)?.value || "";
}

function roundToStep(value, step = 15, min = 30, max = 300) {
  return Math.max(min, Math.min(max, Math.round(Number(value || min) / step) * step));
}

function formatActivityDuration(minutes = 0) {
  const value = Number(minutes || 0);
  if (value < 60) {
    return `${value}분`;
  }
  const hours = Math.floor(value / 60);
  const mins = value % 60;
  return mins ? `${hours}시간 ${mins}분` : `${hours}시간`;
}

function healthTypeLabel(type = "other") {
  return {
    strength: "헬스",
    swimming: "수영",
    running: "러닝",
    walking: "걷기",
    surfing: "서핑",
    yoga: "요가/스트레칭",
    other: "기타",
  }[type] || type;
}

function healthTypeOptions(selected = "strength") {
  return [
    ["strength", "헬스"],
    ["swimming", "수영"],
    ["running", "러닝"],
    ["walking", "걷기"],
    ["surfing", "서핑"],
    ["yoga", "요가/스트레칭"],
    ["other", "기타"],
  ].map(([value, label]) => `<option value="${value}" ${value === selected ? "selected" : ""}>${label}</option>`).join("");
}

function defaultHealthActivityDraft(activityType = "strength") {
  return {
    activity_type: activityType,
    duration_minutes: 30,
    detail: "",
    strength_entries: [],
    strength_note: "",
    swim_meters: "",
    swim_turns: "",
    swim_note: "",
  };
}

function normalizeHealthActivityDraft(item = {}) {
  const fallback = defaultHealthActivityDraft(item.activity_type || "strength");
  return {
    ...fallback,
    ...item,
    activity_type: item.activity_type || fallback.activity_type,
    duration_minutes: Number(item.duration_minutes || fallback.duration_minutes),
    detail: item.detail || "",
    strength_entries: Array.isArray(item.strength_entries) ? reindexStrengthEntries(item.strength_entries) : [],
    strength_note: item.strength_note || "",
    swim_meters: item.swim_meters ?? item.metadata?.swim_meters ?? "",
    swim_turns: item.swim_turns ?? item.metadata?.swim_turns ?? "",
    swim_note: item.swim_note || "",
  };
}

function readHealthQuickDraft() {
  try {
    const payload = JSON.parse(localStorage.getItem(NOMAD_HEALTH_QUICK_DRAFT_STORAGE_KEY) || "null");
    if (!payload || !Array.isArray(payload.drafts)) return null;
    return {
      ...payload,
      drafts: payload.drafts.map(normalizeHealthActivityDraft),
    };
  } catch {
    return null;
  }
}

function writeHealthQuickDraft() {
  if (editingRoutineGroupKey || editingSavedActivityId || editingSavedWorkoutId) {
    return;
  }
  const meaningful = healthActivityDrafts.some((item) => {
    const normalized = normalizeHealthActivityDraft(item);
    return normalized.detail
      || normalized.strength_entries.length
      || normalized.strength_note
      || normalized.activity_type !== "strength"
      || Number(normalized.duration_minutes) !== 30;
  });
  if (!meaningful) {
    localStorage.removeItem(NOMAD_HEALTH_QUICK_DRAFT_STORAGE_KEY);
    return;
  }
  localStorage.setItem(NOMAD_HEALTH_QUICK_DRAFT_STORAGE_KEY, JSON.stringify({
    schema_version: "0.1.0",
    updated_at: new Date().toISOString(),
    drafts: healthActivityDrafts.map(normalizeHealthActivityDraft),
  }));
}

function clearHealthQuickDraft() {
  localStorage.removeItem(NOMAD_HEALTH_QUICK_DRAFT_STORAGE_KEY);
}

function restoreHealthQuickDraft() {
  if (healthActivityDrafts.length || editingRoutineGroupKey || editingSavedActivityId || editingSavedWorkoutId) {
    return false;
  }
  const draft = readHealthQuickDraft();
  if (!draft?.drafts?.length) {
    return false;
  }
  healthActivityDrafts = draft.drafts;
  renderHealthActivityDrafts();
  activityStatus.textContent = "입력 중이던 헬스 디테일을 복원했습니다.";
  return true;
}

function summarizeStrengthEntries(entries = []) {
  if (!entries.length) return "";
  const groups = groupEntriesByExercise(entries);
  return Object.entries(groups).map(([exercise, items]) => {
    const label = exerciseLabel(items[0]?.muscle_group || "other", exercise);
    return `${label} ${items.length}set`;
  }).join(" · ");
}

function swimDetailText(item = {}) {
  const meters = Number(item.swim_meters || 0);
  const turns = Number(item.swim_turns || 0);
  const parts = [];
  if (meters > 0) parts.push(`${meters}m`);
  if (turns > 0) parts.push(`${turns}턴`);
  if (item.swim_note) parts.push(item.swim_note);
  return parts.join(" · ");
}

function renderHealthActivityDrafts() {
  if (!healthActivityDraftList) return;
  const total = healthActivityDrafts.reduce((sum, item) => sum + Number(item.duration_minutes || 0), 0);
  healthQuickTotal.textContent = formatActivityDuration(total);
  if (!healthActivityDrafts.length) {
    healthActivityDraftList.innerHTML = '<p class="empty">운동 추가를 눌러 항목을 입력하세요.</p>';
    return;
  }
  healthActivityDraftList.innerHTML = healthActivityDrafts.map((item, index) => ({ item, index })).reverse().map(({ item, index }) => {
    const strengthSummary = item.strength_entries?.length ? summarizeStrengthEntries(item.strength_entries) : "";
    const swimSummary = item.activity_type === "swimming" ? swimDetailText(item) : "";
    const detailValue = item.detail || strengthSummary || swimSummary || "";
    const detailControl = item.activity_type === "swimming"
      ? `
        <div class="swim-detail-grid">
          <input class="health-draft-swim-meters" type="number" inputmode="numeric" min="0" step="25" value="${escapeHtml(String(item.swim_meters || ""))}" placeholder="미터" aria-label="수영 미터" />
          <input class="health-draft-swim-turns" type="number" inputmode="numeric" min="0" step="1" value="${escapeHtml(String(item.swim_turns || ""))}" placeholder="턴" aria-label="수영 턴" />
          <input class="health-draft-swim-note" type="text" value="${escapeHtml(item.swim_note || item.detail || "")}" placeholder="메모" aria-label="수영 메모" />
        </div>
      `
      : `
        <div class="inline-input-action">
          <input class="health-draft-detail" type="text" value="${escapeHtml(detailValue)}" placeholder="${item.activity_type === "strength" ? "상체 루틴" : "25m 레인 10회"}" />
          ${item.activity_type === "strength" ? `<button class="button-secondary health-draft-strength" type="button">루틴</button>` : ""}
        </div>
      `;
    return `
      <article class="health-activity-draft-row" data-index="${index}">
        <label>
          <span>운동 종류</span>
          <select class="health-draft-type">${healthTypeOptions(item.activity_type)}</select>
        </label>
        <label>
          <span>시간</span>
          <input class="health-draft-minutes" type="number" inputmode="numeric" min="5" step="5" value="${escapeHtml(String(item.duration_minutes || 30))}" />
        </label>
        <label class="health-draft-detail-field">
          <span>디테일</span>
          ${detailControl}
        </label>
        <button class="button-ghost health-draft-remove" type="button" aria-label="운동 항목 삭제">×</button>
      </article>
    `;
  }).join("");
}

function resetHealthEditingState() {
  editingGenericActivityId = null;
  editingSavedActivityId = null;
  editingSavedWorkoutId = null;
  editingRoutineGroupKey = null;
  editingRoutineDeleteTargets = null;
  deleteRoutineCardButton?.setAttribute("hidden", "");
  deleteRoutineCardButton && (deleteRoutineCardButton.disabled = false);
}

function syncHealthDraftRow(row) {
  if (!row) return null;
  const index = Number(row.dataset.index);
  if (!Number.isInteger(index) || !healthActivityDrafts[index]) return null;
  const previous = healthActivityDrafts[index];
  const activityType = row.querySelector(".health-draft-type")?.value || "other";
  const minutes = Number.parseInt(row.querySelector(".health-draft-minutes")?.value, 10);
  const swimMeters = row.querySelector(".health-draft-swim-meters")?.value || "";
  const swimTurns = row.querySelector(".health-draft-swim-turns")?.value || "";
  const swimNote = row.querySelector(".health-draft-swim-note")?.value.trim() || "";
  const detail = activityType === "swimming"
    ? (swimDetailText({ swim_meters: swimMeters, swim_turns: swimTurns, swim_note: swimNote }) || "수영")
    : (row.querySelector(".health-draft-detail")?.value.trim() || "");
  healthActivityDrafts[index] = {
    ...previous,
    activity_type: activityType,
    duration_minutes: Number.isFinite(minutes) && minutes > 0 ? minutes : 0,
    detail,
    strength_entries: activityType === "strength" ? (previous.strength_entries || []) : [],
    strength_note: activityType === "strength" ? (previous.strength_note || "") : "",
    swim_meters: activityType === "swimming" ? swimMeters : "",
    swim_turns: activityType === "swimming" ? swimTurns : "",
    swim_note: activityType === "swimming" ? swimNote : "",
  };
  writeHealthQuickDraft();
  return healthActivityDrafts[index];
}

function clearHealthDraftForm() {
  editingHealthActivityIndex = null;
  activeStrengthDraftIndex = null;
  workoutEntries = [];
  workoutNote.value = "";
  resetWorkoutEditMode();
  renderWorkoutSets();
  updateHealthQuickUi();
}

function updateHealthQuickUi() {
  const isHealth = selectedRadioValue("area") === "health";
  healthQuickBuilder.hidden = !isHealth;
  document.querySelector(".quick-timer")?.toggleAttribute("hidden", isHealth);
  activityDetail.closest("label")?.toggleAttribute("hidden", isHealth);
  if (isHealth && !healthActivityDrafts.length) {
    if (!restoreHealthQuickDraft()) {
      healthActivityDrafts.push(defaultHealthActivityDraft());
      renderHealthActivityDrafts();
    }
  }
}

function readActiveActivity() {
  try {
    return JSON.parse(localStorage.getItem(ACTIVE_ACTIVITY_STORAGE_KEY) || "null");
  } catch {
    return null;
  }
}

function writeActiveActivity(value) {
  if (!value) {
    localStorage.removeItem(ACTIVE_ACTIVITY_STORAGE_KEY);
    return;
  }
  localStorage.setItem(ACTIVE_ACTIVITY_STORAGE_KEY, JSON.stringify(value));
}

function activeElapsedMinutes(activity = activeActivity) {
  if (!activity?.started_at) {
    return 0;
  }
  const startedAt = new Date(activity.started_at).getTime();
  if (Number.isNaN(startedAt)) {
    return 0;
  }
  return Math.max(1, Math.round((Date.now() - startedAt) / 60000));
}

function updateDurationSlider(minutes = activityDurationSlider.value, source = "manual") {
  const rounded = roundToStep(minutes);
  activityDurationSlider.value = String(rounded);
  activityDurationLabel.textContent = formatActivityDuration(rounded);
  if (activityTimerStatus) {
    activityTimerStatus.textContent = "선택한 날짜에 이만큼 한 것으로 저장합니다.";
  }
}

function todayLocalDateValue() {
  return toLocalDateTimeValue(new Date()).slice(0, 10);
}

function selectedActivityDate() {
  return activityDate?.value || todayLocalDateValue();
}

function selectedActivityDateTimeIso() {
  const [, timePart] = toLocalDateTimeValue(new Date()).split("T");
  return new Date(`${selectedActivityDate()}T${timePart}`).toISOString();
}

function resetActivityDate() {
  if (activityDate && !activityDate.value) {
    activityDate.value = todayLocalDateValue();
  }
}

function syncActiveActivityUi() {
  activeActivity = null;
  writeActiveActivity(null);
  if (activityTimerStatus) {
    activityTimerStatus.textContent = "선택한 날짜에 이만큼 한 것으로 저장합니다.";
  }
}

function startActiveActivity() {
  activeActivity = {
    area: selectedRadioValue("area"),
    started_at: new Date().toISOString(),
  };
  lastTimerActivity = null;
  writeActiveActivity(activeActivity);
  syncActiveActivityUi();
  if (activeActivityTick) {
    clearInterval(activeActivityTick);
  }
  activeActivityTick = setInterval(syncActiveActivityUi, 30000);
}

function endActiveActivity() {
  if (!activeActivity) {
    return;
  }
  const endedAt = new Date().toISOString();
  const duration = roundToStep(activeElapsedMinutes(activeActivity));
  activeActivity.ended_at = endedAt;
  lastTimerActivity = { ...activeActivity };
  updateDurationSlider(duration, "timer");
  if (activityTimerStatus) {
    activityTimerStatus.textContent = "종료됨. 저장하면 측정 시간이 기록됩니다.";
  }
  writeActiveActivity(null);
  activeActivity = null;
  activityStartButton.disabled = false;
  activityEndButton.disabled = true;
  if (activeActivityTick) {
    clearInterval(activeActivityTick);
    activeActivityTick = null;
  }
}

function updateActivityAreaUi() {
  const area = selectedRadioValue("area");
  updateHealthQuickUi();
}

function selectActivityArea(area) {
  const option = activityForm.querySelector(`input[name="area"][value="${CSS.escape(area)}"]`);
  if (!option) {
    return false;
  }
  option.checked = true;
  updateActivityAreaUi();
  if (activeActivity) {
    activeActivity.area = selectedRadioValue("area");
    writeActiveActivity(activeActivity);
  }
  return true;
}

function applyQuickAreaPrefill() {
  const area = localStorage.getItem(QUICK_AREA_PREFILL_KEY);
  if (!area) {
    return;
  }
  localStorage.removeItem(QUICK_AREA_PREFILL_KEY);
  selectActivityArea(area);
}

function activityPayloadFromForm() {
  const area = selectedRadioValue("area");
  const durationMinutes = roundToStep(activityDurationSlider.value);
  const stay = currentStayContext();
  const date = selectedActivityDate();
  const payload = {
    kind: "activity_session",
    date,
    client_created_at: new Date().toISOString(),
    area,
    time_mode: "duration",
    duration_minutes: durationMinutes,
    start_time: null,
    end_time: null,
    place: activityPlace.value,
    subcategory: activitySubcategory.value.trim(),
    detail: activityDetail.value.trim(),
    review_required: Boolean(activityParseMemo.checked),
    review_reason: activityParseMemo.checked ? "메모 구조화 후보 확인 필요" : null,
    metadata: {
      parse_memo: Boolean(activityParseMemo.checked),
      duration_source: "manual_slider",
      timer_started_at: null,
      timer_ended_at: null,
      client_timezone: stay.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone,
      stay,
    },
  };
  if (!payload.detail) {
    payload.detail = payload.subcategory || area;
  }
  return payload;
}

function healthActivityPayloadsFromDrafts() {
  const stay = currentStayContext();
  const date = selectedActivityDate();
  return healthActivityDrafts.map((item, index) => ({
    kind: "activity_session",
    date,
    client_created_at: new Date().toISOString(),
    area: "health",
    time_mode: "duration",
    duration_minutes: item.duration_minutes,
    start_time: null,
    end_time: null,
    place: activityPlace.value,
    subcategory: item.activity_type,
    detail: item.detail || healthTypeLabel(item.activity_type),
    review_required: false,
    review_reason: null,
    metadata: {
      exercise_type: item.activity_type,
      strength_entries: item.strength_entries || [],
      strength_note: item.strength_note || "",
      swim_meters: item.activity_type === "swimming" ? Number(item.swim_meters || 0) || null : null,
      swim_turns: item.activity_type === "swimming" ? Number(item.swim_turns || 0) || null : null,
      swim_note: item.activity_type === "swimming" ? item.swim_note || "" : "",
      draft_index: index,
      source_workout_session_id: item.source_workout_session_id || null,
      source_activity_id: item.source_activity_id || null,
      client_timezone: stay.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone,
      stay,
    },
  }));
}

async function saveActivityPayload(payload) {
  if (isSupabaseMode()) {
    return supabaseQueueInsert("capture_queue", {
      user_id: getNomadUserId(),
      source: "capture_quick",
      status: "pending",
      payload,
    });
  }
  const response = await fetch("/api/activity-session", {
    method: "POST",
    headers: {
      "content-type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  const responsePayload = await response.json();
  if (!response.ok) {
    throw new Error(responsePayload.error || "Activity save failed.");
  }
  return responsePayload;
}

async function updateActivityPayload(activityId, payload) {
  if (!activityId) return saveActivityPayload(payload);
  if (isSupabaseMode()) {
    return supabaseQueueInsert("capture_queue", {
      user_id: getNomadUserId(),
      source: "capture_quick",
      status: "pending",
      payload: {
        ...payload,
        edit_source_id: activityId,
        edit_mode: "update_requested",
      },
    });
  }
  const response = await fetch("/api/activity-session/update", {
    method: "POST",
    headers: {
      "content-type": "application/json",
    },
    body: JSON.stringify({ activity_id: activityId, updates: payload }),
  });
  const responsePayload = await response.json();
  if (!response.ok) {
    throw new Error(responsePayload.error || "Activity update failed.");
  }
  return responsePayload;
}

async function ignoreActivitySession(activityId) {
  return updateActivityPayload(activityId, {
    status: "ignored",
    review_required: true,
    review_reason: "히스토리에서 제외 처리됨",
  });
}

async function updateCapturePayload(captureId, updates = {}) {
  const response = await fetch("/api/captures/update", {
    method: "POST",
    headers: {
      "content-type": "application/json",
    },
    body: JSON.stringify({ capture_id: captureId, updates }),
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error || "Capture update failed.");
  }
  return payload;
}

async function saveStrengthWorkoutDraft(item) {
  if (!item?.strength_entries?.length) return null;
  const payload = buildStrengthWorkoutPayload({
    startedAt: selectedActivityDateTimeIso(),
    muscleGroup: item.strength_entries[0]?.muscle_group || "full_body",
    entries: item.strength_entries,
    note: item.strength_note || item.detail || "",
  });
  payload.date = selectedActivityDate();
  payload.client_created_at = new Date().toISOString();
  payload.client_submission_id = item.client_submission_id || null;
  payload.ended_at = selectedActivityDateTimeIso();
  payload.duration_minutes = item.duration_minutes;
  payload.activity_type = "strength";
  payload.stay = currentStayContext();
  payload.client_timezone = payload.stay.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone;
  if (isSupabaseMode()) {
    return supabaseQueueInsert("workout_queue", {
      user_id: getNomadUserId(),
      source: "dashboard",
      status: "pending",
      payload,
    });
  }
  const response = await fetch("/api/workout-session", {
    method: "POST",
    headers: {
      "content-type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  const responsePayload = await response.json();
  if (!response.ok) {
    throw new Error(responsePayload.error || "운동 저장에 실패했습니다.");
  }
  return responsePayload;
}

async function updateStrengthWorkoutDraft(sessionId, item) {
  if (!sessionId) return saveStrengthWorkoutDraft(item);
  if (!item?.strength_entries?.length) {
    throw new Error("헬스 루틴에는 최소 1개 세트가 필요합니다.");
  }
  const payload = buildStrengthWorkoutPayload({
    startedAt: selectedActivityDateTimeIso(),
    muscleGroup: item.strength_entries[0]?.muscle_group || "full_body",
    entries: item.strength_entries,
    note: item.strength_note || item.detail || "",
  });
  payload.date = selectedActivityDate();
  payload.client_created_at = new Date().toISOString();
  payload.client_submission_id = item.client_submission_id || null;
  payload.ended_at = selectedActivityDateTimeIso();
  payload.duration_minutes = item.duration_minutes;
  payload.activity_type = "strength";
  payload.stay = currentStayContext();
  payload.client_timezone = payload.stay.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone;
  if (isSupabaseMode()) {
    return supabaseQueueInsert("workout_queue", {
      user_id: getNomadUserId(),
      source: "dashboard",
      status: "pending",
      payload: {
        ...payload,
        edit_source_id: sessionId,
        edit_mode: "update_requested",
      },
    });
  }
  const response = await fetch("/api/workout-session/update", {
    method: "POST",
    headers: {
      "content-type": "application/json",
    },
    body: JSON.stringify({ session_id: sessionId, updates: payload }),
  });
  const responsePayload = await response.json();
  if (!response.ok) {
    throw new Error(responsePayload.error || "Workout update failed.");
  }
  return responsePayload;
}

async function updateWorkoutPayload(sessionId, payload) {
  if (!sessionId) throw new Error("Workout session id is required.");
  if (isSupabaseMode()) {
    return supabaseQueueInsert("workout_queue", {
      user_id: getNomadUserId(),
      source: "dashboard",
      status: "pending",
      payload: {
        ...payload,
        edit_source_id: sessionId,
        edit_mode: "update_requested",
      },
    });
  }
  const response = await fetch("/api/workout-session/update", {
    method: "POST",
    headers: {
      "content-type": "application/json",
    },
    body: JSON.stringify({ session_id: sessionId, updates: payload }),
  });
  const responsePayload = await response.json();
  if (!response.ok) {
    throw new Error(responsePayload.error || "Workout update failed.");
  }
  return responsePayload;
}

async function deleteCurrentRoutineGroup() {
  if (!editingRoutineGroupKey || !editingRoutineDeleteTargets) {
    activityStatus.textContent = "삭제할 루틴 카드가 없습니다.";
    return;
  }
  const group = latestRoutineGroups.find((item) => item.key === editingRoutineGroupKey);
  if (!group) {
    activityStatus.textContent = "삭제할 루틴 카드를 찾지 못했습니다.";
    return;
  }
  deleteRoutineCardButton.disabled = true;
  activityStatus.textContent = "Deleting routine card...";
  const activityDeletes = (editingRoutineDeleteTargets.activities || []).map((activity) => updateActivityPayload(activity.id, {
    kind: "activity_session",
    area: "health",
    time_mode: "duration",
    duration_minutes: activity.duration_minutes || 1,
    subcategory: activity.type || "other",
    detail: activity.detail || healthTypeLabel(activity.type),
    status: "ignored",
    review_required: false,
    metadata: {
      deleted_from_routine_card: editingRoutineGroupKey,
    },
  }));
  const workoutDeletes = group.workouts.map((session) => updateWorkoutPayload(session.id, {
    type: session.type || "strength",
    activity_type: session.activity_type || "strength",
    duration_minutes: session.duration_minutes || 1,
    entries: session.entries || [],
    note: session.note || "",
    status: "ignored",
  }));
  Promise.all([...activityDeletes, ...workoutDeletes])
    .then(() => {
      const deletedWorkoutIds = group.workouts.map((session) => session.id).filter(Boolean);
      const deletedActivityIds = (editingRoutineDeleteTargets.activities || [])
        .map((activity) => activity.id || activity.source)
        .filter(Boolean);
      removePendingHealthItems(deletedWorkoutIds, deletedActivityIds);
      workoutHistorySessions = workoutHistorySessions.filter((session) => !deletedWorkoutIds.includes(session.id));
      latestHealthSessions = latestHealthSessions.filter((session) => {
        const id = session.source || session.id;
        return !deletedActivityIds.includes(id);
      });
      healthActivityDrafts = [];
      resetHealthEditingState();
      clearHealthDraftForm();
      renderHealthActivityDrafts();
      renderRoutineCards(workoutHistorySessions, latestHealthSessions);
      activityStatus.textContent = isSupabaseMode()
        ? "Delete request saved. Dashboard update pending."
        : "Routine card deleted.";
      if (!isSupabaseMode()) {
        return loadDashboard();
      }
      return null;
    })
    .catch((error) => {
      deleteRoutineCardButton.disabled = false;
      activityStatus.textContent = error.message;
    });
}

function deletedRoutineRowSaves() {
  if (!editingRoutineGroupKey || !editingRoutineDeleteTargets) {
    return [];
  }
  const group = latestRoutineGroups.find((item) => item.key === editingRoutineGroupKey);
  if (!group) {
    return [];
  }
  const remainingActivityIds = new Set(
    healthActivityDrafts
      .map((item) => item.source_activity_id)
      .filter(Boolean),
  );
  const activityDeletes = (editingRoutineDeleteTargets.activities || [])
    .filter((activity) => activity.id && !remainingActivityIds.has(activity.id))
    .map((activity) => updateActivityPayload(activity.id, {
      kind: "activity_session",
      area: "health",
      time_mode: "duration",
      duration_minutes: activity.duration_minutes || 1,
      subcategory: activity.type || "other",
      detail: activity.detail || healthTypeLabel(activity.type),
      status: "ignored",
      review_required: false,
      metadata: {
        deleted_from_routine_card: editingRoutineGroupKey,
        deleted_row: true,
      },
    }));
  const remainingWorkoutIds = new Set(
    healthActivityDrafts
      .map((item) => item.source_workout_session_id)
      .filter(Boolean),
  );
  const workoutDeletes = (editingRoutineDeleteTargets.workoutIds || [])
    .filter((sessionId) => sessionId && !remainingWorkoutIds.has(sessionId))
    .map((sessionId) => {
      const session = group.workouts.find((item) => item.id === sessionId) || {};
      return updateWorkoutPayload(sessionId, {
        type: session.type || "strength",
        activity_type: session.activity_type || "strength",
        duration_minutes: session.duration_minutes || 1,
        entries: session.entries || [],
        note: session.note || "",
        status: "ignored",
      });
    });
  return [...activityDeletes, ...workoutDeletes];
}

function cloneHealthDrafts(drafts = []) {
  return drafts.map((item) => ({
    ...item,
    strength_entries: (item.strength_entries || []).map((entry) => ({ ...entry })),
  }));
}

function applyOptimisticRoutineGroupEdit(groupKey, drafts = []) {
  const group = latestRoutineGroups.find((item) => item.key === groupKey);
  if (!group) return;
  const remainingWorkoutIds = new Set(
    drafts.map((item) => item.source_workout_session_id).filter(Boolean),
  );
  const remainingActivityIds = new Set(
    drafts.map((item) => item.source_activity_id).filter(Boolean),
  );
  const originalWorkoutIds = new Set(group.workouts.map((session) => session.id).filter(Boolean));
  const originalActivityIds = new Set(
    group.activities
      .map((session) => session.source || session.id)
      .filter(Boolean),
  );

  workoutHistorySessions = workoutHistorySessions
    .filter((session) => !originalWorkoutIds.has(session.id) || remainingWorkoutIds.has(session.id))
    .map((session) => {
      const draft = drafts.find((item) => item.source_workout_session_id === session.id);
      if (!draft) return session;
      return {
        ...session,
        duration_minutes: draft.duration_minutes,
        entries: draft.strength_entries || [],
        note: draft.strength_note || draft.detail || session.note || "",
        activity_type: "strength",
        status: "completed",
      };
    });

  drafts
    .filter((item) => item.activity_type === "strength" && !item.source_workout_session_id && item.strength_entries?.length)
    .forEach((item, index) => {
      workoutHistorySessions.push({
        id: `pending_workout_${groupKey}_${index}`,
        date: group.date,
        type: "strength",
        activity_type: "strength",
        duration_minutes: item.duration_minutes,
        entries: item.strength_entries || [],
        note: item.strength_note || item.detail || "",
        status: "completed",
      });
    });

  latestHealthSessions = latestHealthSessions
    .filter((session) => {
      const id = session.source || session.id;
      return !originalActivityIds.has(id) || remainingActivityIds.has(id);
    })
    .map((session) => {
      const id = session.source || session.id;
      const draft = drafts.find((item) => item.source_activity_id === id);
      if (!draft) return session;
      return {
        ...session,
        type: draft.activity_type,
        subcategory: draft.activity_type,
        duration_minutes: draft.duration_minutes,
        detail: draft.detail || healthTypeLabel(draft.activity_type),
        status: "completed",
      };
    });

  drafts
    .filter((item) => item.activity_type !== "strength" && !item.source_activity_id)
    .forEach((item, index) => {
      latestHealthSessions.push({
        id: `pending_activity_${groupKey}_${index}`,
        source: `pending_activity_${groupKey}_${index}`,
        date: group.date,
        area: "health",
        type: item.activity_type,
        subcategory: item.activity_type,
        duration_minutes: item.duration_minutes,
        detail: item.detail || healthTypeLabel(item.activity_type),
        status: "completed",
      });
    });

  writePendingHealthFromMemory();
  renderRoutineCards(workoutHistorySessions, latestHealthSessions);
}

function toLocalDateTimeValue(date = new Date()) {
  const localDate = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
  return localDate.toISOString().slice(0, 16);
}

function resetWorkoutStartedAt() {
  workoutStartedAt = new Date().toISOString();
  setTimePickerValue(new Date());
  workoutTimeStatus.textContent = "시간은 Quick 운동 항목에서 관리됩니다.";
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

function escapeHtml(value = "") {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function splitCsv(value = "") {
  return value.split(",").map((item) => item.trim()).filter(Boolean);
}

function muscleOptions(selectedValue = "other") {
  return MUSCLE_GROUPS
    .map(([value, label]) => `<option value="${value}" ${selectedValue === value ? "selected" : ""}>${label}</option>`)
    .join("");
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

function externalExerciseSlug(item = {}) {
  return String(item.name_en || item.id || "")
    .trim()
    .toLowerCase()
    .replaceAll("&", "and")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function muscleWikiUrl(item = {}) {
  const slug = externalExerciseSlug(item);
  return slug ? `https://musclewiki.com/exercise/${encodeURIComponent(slug)}` : "https://musclewiki.com/";
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
  const base = externalExerciseSlug({ name_en: exercise.name_en || exercise.name_ko || exercise.id }) || "custom-exercise";
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

function applyExerciseMutationToMemory(action, payload = {}) {
  const result = storeLocalExerciseMutation(action, payload);
  exerciseLibrary = applyLocalExerciseMutations(exerciseLibrary);
  refreshExerciseOptions();
  renderExerciseLibraryManager();
  return result;
}

function isQueuePolicyError(error) {
  return String(error?.message || error || "").includes("row-level security policy")
    || String(error?.message || error || "").includes("42501");
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
        source: "dashboard",
        status: "pending",
        payload: {
          kind: "exercise_library_mutation",
          origin: "exercise_library_manager",
          action,
          ...normalizedPayload,
        },
      });
      const result = applyExerciseMutationToMemory(action, normalizedPayload);
      exerciseLibraryStatus.textContent = "Saved. Library analysis and dashboard update pending.";
      return { queued: true, ...result };
    } catch (error) {
      if (!isQueuePolicyError(error)) {
        throw error;
      }
      const result = applyExerciseMutationToMemory(action, normalizedPayload);
      exerciseLibraryStatus.textContent = "Supabase 정책이 막혀 이 기기에 임시 저장했습니다. DB 정책 적용 후 중앙 동기화됩니다.";
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
    bodyweight: Boolean(workoutBodyweight?.checked),
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
  if (workoutBodyweight) {
    workoutBodyweight.checked = Boolean(state.bodyweight);
  }
  syncBodyweightInputState();
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
  if (workoutBodyweight) {
    workoutBodyweight.checked = Boolean(entry.bodyweight);
  }
  syncBodyweightInputState();
  refreshExerciseActions();
  renderExerciseHistory(workoutExercise.value);
}

function resetWorkoutEditMode() {
  editingWorkoutIndex = null;
  editingReturnState = null;
  addWorkoutSet.textContent = "세트 추가";
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
  const nextView = knownView ? normalizedView : "main";
  workspaceViews.forEach((view) => {
    view.classList.toggle("active", view.dataset.view === nextView);
  });
  workspaceLinks.forEach((link) => {
    link.classList.toggle("active", link.dataset.viewLink === nextView);
  });
  const activeLink = workspaceLinks.find((link) => link.dataset.viewLink === nextView);
  if (mobileViewTitle && activeLink) {
    const linkLabel = [...activeLink.childNodes]
      .filter((node) => node.nodeType === Node.TEXT_NODE)
      .map((node) => node.textContent.trim())
      .filter(Boolean)
      .join(" ");
    mobileViewTitle.textContent = linkLabel || activeLink.textContent.trim();
  }
  if (updateHash && window.location.hash !== `#${nextView}`) {
    history.replaceState(null, "", `#${nextView}`);
  }
  requestAnimationFrame(() => window.scrollTo({ top: 0, left: 0, behavior: "auto" }));
}

function handleRouteHash(rawHash = window.location.hash) {
  const requestedView = rawHash.replace("#", "") || "main";
  if (requestedView === "quick" || requestedView === "nomad-quick") {
    setActiveView("main", true);
    return;
  }
  setActiveView(requestedView, false);
}

function setWorkspaceStatus(element, message, tone = "") {
  if (!element) return;
  element.textContent = message || "";
  element.dataset.tone = tone;
}

function setNavBadge(viewName, value, options = {}) {
  const link = workspaceLinks.find((item) => item.dataset.viewLink === viewName);
  if (!link) return;
  const existing = link.querySelector(".nav-badge");
  const numericValue = Number(value || 0);
  if (!numericValue) {
    existing?.remove();
    link.removeAttribute("data-badge-tone");
    link.removeAttribute("title");
    return;
  }
  const badge = existing || document.createElement("span");
  badge.className = "nav-badge";
  badge.textContent = numericValue > 99 ? "99+" : String(numericValue);
  badge.setAttribute("aria-label", options.label || `${numericValue} updates`);
  link.dataset.badgeTone = options.tone || "info";
  link.title = options.title || `${numericValue} updates`;
  if (!existing) {
    link.append(badge);
  }
}

function renderNavBadges({ today = {}, health = {}, english = {}, expenseCandidates = {}, notifications = {}, syncStatus = {} }) {
  workspaceLinks.forEach((link) => {
    link.querySelector(".nav-badge")?.remove();
    link.removeAttribute("data-badge-tone");
    link.removeAttribute("title");
  });

  const englishUpdates = Number(english.summary?.reviewed_session_count || 0);
  setNavBadge("english", englishUpdates, {
    tone: english.import_status?.status === "warning" ? "warning" : "info",
    label: `${englishUpdates} English reviews imported`,
    title: `오늘 영어 학습 리뷰 ${englishUpdates}개`,
  });

  const healthUpdates = Number(health.summary?.structured_workout_count || 0) + Number(health.summary?.session_count || 0);
  setNavBadge("health", healthUpdates, {
    tone: "info",
    label: `${healthUpdates} health updates`,
    title: `오늘 Health 기록 ${healthUpdates}개`,
  });

  const financeReviews = (expenseCandidates.candidates || []).length;
  setNavBadge("finance", financeReviews, {
    tone: "warning",
    label: `${financeReviews} finance items need review`,
    title: `검토할 Finance 후보 ${financeReviews}개`,
  });

  const notificationCount = (notifications.notifications || []).length;
  const actionCount = (today.actions || []).filter((item) => item.approval_required && item.status !== "done").length;
  setNavBadge("council", notificationCount + actionCount, {
    tone: actionCount ? "warning" : "info",
    label: `${notificationCount + actionCount} council updates`,
    title: `알림 후보 ${notificationCount}개 · 승인 후보 ${actionCount}개`,
  });

  const syncSummary = syncStatus.summary || {};
  const pendingSync = Number(syncSummary.pending_captures || 0) + Number(syncSummary.pending_workouts || 0);
  setNavBadge("context", pendingSync, {
    tone: "warning",
    label: `${pendingSync} sync items pending`,
    title: `동기화 대기 ${pendingSync}개`,
  });
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

function renderWorkspaceOverview({ today, health, english, activityAllocation, captures, expenseCandidates, notifications, syncStatus }) {
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
      view: "main",
      label: "Main Agent",
      value: `${formatDuration(activityAllocation.month_summary?.total_tracked_minutes || 0)}`,
      detail: "Life direction and time allocation",
    },
    {
      view: "daily",
      label: "Daily Detail",
      value: `${(today.focus_today || []).length} focus`,
      detail: today.summary || "Coordinator summary",
    },
    {
      view: "capture",
      label: "Input History",
      value: `${(captures.captures || []).length} items`,
      detail: "Recent Quick inputs",
    },
    {
      view: "health",
      label: "Health Agent",
      value: `${health.summary?.strength_set_count || 0} sets`,
      detail: healthRecommendation ? `Candidates: ${healthRecommendation}` : "Workout readiness",
    },
    {
      view: "english",
      label: "English Agent",
      value: `${english.summary?.study_minutes || 0} min`,
      detail: `${english.summary?.reviewed_session_count || 0} reviews · ${english.summary?.habit_pattern_count || 0} habits`,
    },
    {
      view: "finance",
      label: "Finance Agent",
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
    {
      view: "settings",
      label: "Settings",
      value: "MVP",
      detail: "Start day, places, agents, backup",
    },
  ];

  workspaceOverview.replaceChildren(
    ...cards.map((card) => {
      const button = document.createElement("button");
      button.className = ["overview-card", card.status ? `status-${card.status}` : ""].filter(Boolean).join(" ");
      button.type = "button";
      button.dataset.overviewView = card.view;
      button.setAttribute("aria-label", `${card.label} workspace shortcut: ${card.value}. ${card.detail}`);
      button.innerHTML = `
        <span>${card.label} workspace</span>
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

function isBodyweightExercise(exerciseId = "") {
  const exercise = exerciseLibrary.find((item) => item.id === exerciseId);
  if (!exercise) return false;
  const equipment = exercise.equipment || [];
  if (!equipment.length) return true;
  return equipment.every((item) => ["pull_up_bar", "dip_bar", "mat"].includes(item));
}

function formatSetLine(entry = {}) {
  const reps = entry.reps ?? "-";
  const rpe = entry.rpe ? ` · RPE ${entry.rpe}` : "";
  if (entry.bodyweight || (Number(entry.weight_kg) === 0 && isBodyweightExercise(entry.exercise))) {
    return `맨몸 X ${reps}${rpe}`;
  }
  const weight = entry.weight_kg ?? "-";
  return `${weight}kg X ${reps}${rpe}`;
}

function sortedSessions(sessions = []) {
  const sessionDateKey = (session = {}) => session.started_at || session.created_at || session.date || "";
  return sessions.slice().sort((a, b) => sessionDateKey(b).localeCompare(sessionDateKey(a)));
}

function exerciseHistoryItems(exerciseId) {
  const items = [];
  sortedSessions(workoutHistorySessions).forEach((session) => {
    const entries = (session.entries || []).filter((entry) => entry.exercise === exerciseId);
    if (!entries.length) {
      return;
    }
    const weightedEntries = entries.filter((entry) => !entry.bodyweight && Number.isFinite(Number(entry.weight_kg)));
    const maxWeight = weightedEntries.length ? Math.max(...weightedEntries.map((entry) => Number(entry.weight_kg) || 0)) : null;
    items.push({
      session,
      entries,
      maxWeight,
      setCount: entries.length,
    });
  });
  return items;
}

function routineDateKey(value = "") {
  const raw = String(value || "");
  if (!raw) return "";
  if (/^\d{4}-\d{2}-\d{2}$/.test(raw)) return raw;
  const parsed = new Date(raw);
  return Number.isNaN(parsed.getTime()) ? raw.slice(0, 10) : parsed.toISOString().slice(0, 10);
}

function formatRoutineDate(value = "") {
  const date = new Date(`${value}T00:00:00`);
  if (Number.isNaN(date.getTime())) return value || "날짜 없음";
  return new Intl.DateTimeFormat("ko-KR", { month: "numeric", day: "numeric", weekday: "short" }).format(date);
}

function isStrengthPayload(payload = {}) {
  const type = payload.subcategory || payload.metadata?.exercise_type || payload.activity_type;
  return type === "strength" && (payload.metadata?.strength_entries || []).length > 0;
}

function workoutFingerprint(session = {}) {
  const entries = (session.entries || [])
    .map((entry) => [
      entry.exercise || "",
      entry.muscle_group || "",
      Number(entry.set_index || 0),
      entry.bodyweight ? "bodyweight" : Number(entry.weight_kg || 0),
      Number(entry.reps || 0),
      Number(entry.rpe || 0),
    ].join(":"))
    .sort()
    .join("|");
  return [
    routineDateKey(session.date || session.started_at),
    Number(session.duration_minutes || 0),
    String(session.note || "").trim(),
    entries,
  ].join("::");
}

function uniqueWorkoutSessions(sessions = []) {
  const seen = new Set();
  return sessions.filter((session) => {
    const key = workoutFingerprint(session);
    if (!key || seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function activityFingerprint(session = {}) {
  return [
    routineDateKey(session.date || session.started_at),
    session.activity_type || session.subcategory || session.type || "",
    Number(session.duration_minutes || 0),
    String(session.detail || "").trim(),
  ].join("::");
}

function uniqueHealthActivities(sessions = []) {
  const seen = new Set();
  return sessions.filter((session) => {
    const key = activityFingerprint(session);
    if (!key || seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function buildRoutineGroups(sessions = [], healthSessions = []) {
  const groups = new Map();
  const ensureGroup = (date) => {
    const key = routineDateKey(date);
    if (!groups.has(key)) {
      groups.set(key, { key, date: key, workouts: [], activities: [] });
    }
    return groups.get(key);
  };

  uniqueWorkoutSessions(sessions.filter((session) => session.status !== "ignored"))
    .forEach((session) => {
      ensureGroup(session.date || session.started_at).workouts.push(session);
    });

  uniqueHealthActivities(healthSessions || [])
    .filter((session) => session.status === "completed")
    .filter((session) => {
      const type = session.activity_type || session.subcategory || "exercise";
      const hasStrengthDetail = type === "strength" && (session.metadata?.strength_entries || []).length;
      return !hasStrengthDetail;
    })
    .forEach((session) => {
      ensureGroup(session.date).activities.push({
        ...session,
        type: session.activity_type || session.subcategory || "exercise",
        is_health_activity: true,
      });
    });

  return [...groups.values()]
    .map((group) => {
      const duration = [
        ...group.workouts.map((session) => Number(session.duration_minutes || 0)),
        ...group.activities.map((session) => Number(session.duration_minutes || 0)),
      ].reduce((sum, value) => sum + value, 0);
      return { ...group, duration };
    })
    .sort((a, b) => b.key.localeCompare(a.key));
}

function routineMonthKey(group = {}) {
  return String(group.key || group.date || "").slice(0, 7);
}

function setSelectOptions(select, options = [], value = "") {
  if (!select) return;
  const signature = options.map((option) => `${option.value}:${option.label}`).join("|");
  if (select.dataset.optionSignature !== signature) {
    select.replaceChildren(
      ...options.map((option) => {
        const element = document.createElement("option");
        element.value = option.value;
        element.textContent = option.label;
        return element;
      }),
    );
    select.dataset.optionSignature = signature;
  }
  select.value = value;
}

function syncRoutineMonthControls(groups = []) {
  const monthKeys = [...new Set(groups.map(routineMonthKey).filter(Boolean))].sort();
  if (!monthKeys.length) {
    selectedRoutineMonth = "";
    setSelectOptions(routineYearSelect, [], "");
    setSelectOptions(routineMonthSelect, [], "");
    return [];
  }

  if (!monthKeys.includes(selectedRoutineMonth)) {
    selectedRoutineMonth = monthKeys.at(-1);
  }

  const selectedYear = selectedRoutineMonth.slice(0, 4);
  const years = [...new Set(monthKeys.map((key) => key.slice(0, 4)))].sort((a, b) => b.localeCompare(a));
  const monthsForYear = monthKeys
    .filter((key) => key.startsWith(`${selectedYear}-`))
    .map((key) => key.slice(5, 7));

  setSelectOptions(
    routineYearSelect,
    years.map((year) => ({ value: year, label: `${year}년` })),
    selectedYear,
  );
  setSelectOptions(
    routineMonthSelect,
    monthsForYear.map((month) => ({ value: month, label: `${Number(month)}월` })),
    selectedRoutineMonth.slice(5, 7),
  );

  return groups.filter((group) => routineMonthKey(group) === selectedRoutineMonth);
}

function routineGroupTags(group) {
  const tags = [];
  group.workouts.forEach((session) => {
    const muscles = uniqueMuscles(session.entries || []);
    if (!muscles.length) {
      tags.push("헬스");
      return;
    }
    muscles.forEach((muscle) => tags.push(`헬스-${MUSCLE_LABELS[muscle] || muscle}`));
  });
  if (!group.workouts.length && group.activities.length) {
    tags.push("운동");
  }
  return [...new Set(tags)].slice(0, 6);
}

function latestExerciseEntries(exerciseId) {
  return exerciseHistoryItems(exerciseId)[0]?.entries || [];
}

function updateLatestExerciseGuide() {
  const exercise = workoutExercise.value;
  const latestEntries = latestExerciseEntries(exercise);
  if (!latestEntries.length) {
    latestExerciseGuide.textContent = "이전 운동 기록이 있으면 여기에 표시됩니다.";
    workoutWeight.placeholder = workoutBodyweight?.checked ? "맨몸" : "예: 60";
    workoutReps.placeholder = "예: 10";
    return;
  }
  const latest = latestEntries.at(-1);
  workoutWeight.placeholder = workoutBodyweight?.checked ? "맨몸" : latest.weight_kg ? `${latest.weight_kg}` : "예: 60";
  workoutReps.placeholder = latest.reps ? `${latest.reps}` : "예: 10";
  latestExerciseGuide.textContent = `최근 ${exerciseLabel(latest.muscle_group, exercise)}: ${latestEntries.map(formatSetLine).join(" · ")}`;
}

function syncBodyweightInputState() {
  const isBodyweight = Boolean(workoutBodyweight?.checked);
  if (!workoutWeight) return;
  workoutWeight.disabled = isBodyweight;
  workoutWeight.closest("label")?.classList.toggle("is-disabled", isBodyweight);
  if (isBodyweight) {
    workoutWeight.value = "";
    workoutWeight.placeholder = "맨몸";
  } else if (!workoutWeight.placeholder || workoutWeight.placeholder === "맨몸") {
    workoutWeight.placeholder = "예: 60";
  }
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
  exerciseRecent.disabled = !item;
  updateLatestExerciseGuide();
}

function renderExerciseLibraryManager() {
  if (!exerciseLibrarySummary || !exerciseCategoryList) {
    return;
  }
  const visibleExercises = sortedExerciseItems(exerciseLibrary.filter((item) => !item.archived));
  const favoriteCount = visibleExercises.filter((item) => item.favorite).length;
  const customCount = visibleExercises.filter((item) => String(item.source || "").includes("custom")).length;
  const grouped = MUSCLE_GROUPS.map(([muscle, label]) => {
    const items = visibleExercises.filter((item) => item.primary_muscle === muscle || (item.secondary_muscles || []).includes(muscle));
    return { muscle, label, items };
  });

  exerciseLibrarySummary.replaceChildren(
    ...[
      ["전체", visibleExercises.length],
      ["부위", grouped.filter((group) => group.items.length).length],
      ["즐겨찾기", favoriteCount],
      ["직접추가", customCount],
    ].map(([label, value]) => {
      const item = document.createElement("div");
      item.className = "metric-item";
      item.innerHTML = `<span>${label}</span><strong>${value}</strong>`;
      return item;
    }),
  );

  if (exerciseEditMode) {
    exerciseEditMode.textContent = exerciseLibraryEditMode ? "완료" : "편집";
  }
  if (exerciseLibraryEditMode) {
    renderExerciseLibraryEditor(visibleExercises);
    return;
  }

  exerciseCategoryList.replaceChildren(
    ...grouped.map((group) => {
      const card = document.createElement("article");
      card.className = "exercise-category-card";
      const topItems = group.items.slice(0, 8);
      card.innerHTML = `
        <header>
          <div>
            <strong>${group.label}</strong>
            <small>${group.items.length} exercises</small>
          </div>
          <span class="badge">${group.muscle}</span>
        </header>
        <div class="exercise-chip-list">
          ${topItems.length
            ? topItems.map((item) => `
              <button type="button" data-exercise-id="${escapeHtml(item.id)}">
                ${item.favorite ? "★ " : ""}${escapeHtml(item.name_ko || item.name_en || item.id)}
              </button>
            `).join("")
            : '<span class="empty">아직 등록된 운동이 없습니다.</span>'}
        </div>
      `;
      return card;
    }),
  );
}

function renderExerciseLibraryEditor(visibleExercises = []) {
  const archivedCount = exerciseLibrary.filter((item) => item.archived).length;
  const grouped = MUSCLE_GROUPS
    .map(([muscle, label]) => ({
      muscle,
      label,
      items: visibleExercises.filter((item) => item.primary_muscle === muscle || (item.secondary_muscles || []).includes(muscle)),
    }))
    .filter((group) => group.items.length);
  exerciseCategoryList.innerHTML = `
    <div class="exercise-editor">
      <section class="exercise-editor-panel">
        <h3 class="panel-title">빠른 추가</h3>
        <div class="exercise-quick-add-grid">
          <label>부위 <select id="editor-new-muscle">${muscleOptions("chest")}</select></label>
          <label>한글명 <input id="editor-new-ko" placeholder="예: 케이블 플라이" /></label>
          <label>영문명 <input id="editor-new-en" placeholder="Cable Fly" /></label>
        </div>
        <div class="library-heading-actions">
          <button id="editor-add-exercise" type="button">운동 추가</button>
          <span class="section-subtext">숨김 ${archivedCount}개</span>
        </div>
      </section>
      <div class="exercise-editor-groups">
        ${grouped.map((group) => `
          <section class="exercise-editor-group muscle-${escapeHtml(group.muscle)}">
            <header>
              <strong>${group.label}</strong>
              <span>${group.items.length}</span>
            </header>
            <div class="exercise-editor-list">
              ${group.items.map((item, index) => renderExerciseEditorItem(item, index, group.items.length, group.muscle)).join("")}
            </div>
          </section>
        `).join("")}
      </div>
    </div>
  `;
}

function renderExerciseEditorItem(item, index, total, groupMuscle = item.primary_muscle || "other") {
  const isEditing = editingExerciseId === item.id;
  const label = item.name_ko || item.name_en || item.id;
  return `
    <article class="exercise-editor-item" data-exercise-id="${escapeHtml(item.id)}" data-group-muscle="${escapeHtml(groupMuscle)}">
      <div class="exercise-editor-row">
        <div class="exercise-editor-name">
          <strong>${escapeHtml(label)}</strong>
          <small>${escapeHtml((item.equipment || []).join(", ") || "장비 없음")}</small>
        </div>
        <div class="exercise-editor-actions">
          <button class="button-ghost icon-action editor-move-up" type="button" aria-label="위로" title="위로" ${index === 0 ? "disabled" : ""}>↑</button>
          <button class="button-ghost icon-action editor-move-down" type="button" aria-label="아래로" title="아래로" ${index === total - 1 ? "disabled" : ""}>↓</button>
          <button class="button-ghost icon-action editor-toggle-edit" type="button" aria-label="${isEditing ? "닫기" : "수정"}" title="${isEditing ? "닫기" : "수정"}">${isEditing ? "×" : "✎"}</button>
          <button class="button-ghost icon-action editor-archive" type="button" aria-label="숨김" title="숨김">⊘</button>
          <button class="button-ghost icon-action danger editor-delete" type="button" aria-label="삭제" title="삭제">×</button>
        </div>
      </div>
      ${isEditing ? `
        <div class="exercise-editor-grid editor-detail">
          <label>한글명 <input id="editor-ko-${escapeHtml(item.id)}" value="${escapeHtml(item.name_ko || "")}" /></label>
          <label>영문명 <input id="editor-en-${escapeHtml(item.id)}" value="${escapeHtml(item.name_en || "")}" /></label>
          <label>주 부위 <select id="editor-muscle-${escapeHtml(item.id)}">${muscleOptions(item.primary_muscle || "other")}</select></label>
          <label>장비 <input id="editor-equipment-${escapeHtml(item.id)}" value="${escapeHtml((item.equipment || []).join(", "))}" /></label>
          <label>동작 패턴 <input id="editor-pattern-${escapeHtml(item.id)}" value="${escapeHtml(item.movement_pattern || "")}" /></label>
          <label>난이도 <input id="editor-difficulty-${escapeHtml(item.id)}" value="${escapeHtml(item.difficulty || "")}" /></label>
          <label class="editor-wide">설명 <textarea id="editor-instructions-${escapeHtml(item.id)}" rows="3">${escapeHtml((item.instructions || []).join("\\n"))}</textarea></label>
          <div class="editor-wide">
            <button class="editor-save" type="button">수정 저장</button>
          </div>
        </div>
      ` : ""}
    </article>
  `;
}

async function loadExerciseLibrary() {
  const payload = isSupabaseMode()
    ? await loadDashboardSnapshot("exercise-library").catch(() => loadJson("/data/exercise-library.json").catch(() => ({ exercises: [] })))
    : await loadJson("/api/exercises?include_archived=1").catch(() => ({ exercises: [] }));
  exerciseLibrary = applyLocalExerciseMutations(payload.exercises || []);
  refreshExerciseOptions();
  renderExerciseLibraryManager();
  renderRoutineCards(workoutHistorySessions, health.sessions || []);
  renderExerciseHistory(workoutExercise.value);
}

async function reloadExerciseLibraryAfterMutation() {
  if (isSupabaseMode()) {
    refreshExerciseOptions();
    renderExerciseLibraryManager();
    return;
  }
  await loadExerciseLibrary();
}

async function quickAddExerciseFromWorkout(rawName = exerciseSearch.value.trim()) {
  if (!rawName) {
    workoutStatus.textContent = "추가할 운동명을 입력하세요.";
    return;
  }
  const normalizedName = rawName.toLowerCase();
  const existing = exerciseLibrary.find((item) => [
    item.name_ko,
    item.name_en,
    item.id,
  ].filter(Boolean).some((value) => String(value).toLowerCase() === normalizedName));
  if (existing) {
    workoutMuscle.value = existing.primary_muscle || workoutMuscle.value;
    exerciseSearch.value = "";
    refreshExerciseOptions();
    workoutExercise.value = existing.id;
    refreshExerciseActions();
    workoutStatus.textContent = `${existing.name_ko || existing.name_en} 선택됨.`;
    return;
  }

  quickAddExercise.disabled = true;
  workoutStatus.textContent = "운동을 빠르게 추가하는 중...";
  try {
    await queueExerciseLibraryMutation("add", {
      name_ko: rawName,
      name_en: rawName,
      primary_muscle: workoutMuscle.value || "other",
      equipment: [],
      favorite: true,
    });
    await reloadExerciseLibraryAfterMutation();
    const added = exerciseLibrary.find((item) => [
      item.name_ko,
      item.name_en,
    ].filter(Boolean).some((value) => String(value).toLowerCase() === normalizedName));
    exerciseSearch.value = "";
    refreshExerciseOptions();
    if (added) {
      workoutExercise.value = added.id;
      refreshExerciseActions();
    }
    workoutStatus.textContent = added ? `${added.name_ko || added.name_en} 추가됨.` : "운동을 추가했습니다.";
  } finally {
    quickAddExercise.disabled = false;
  }
}

function renderQuickAddExerciseDialog() {
  const muscle = workoutMuscle.value || "other";
  const muscleLabel = MUSCLE_LABELS[muscle] || muscle;
  exerciseDialogTitle.textContent = "운동 추가";
  exerciseDialogContent.innerHTML = `
    <div class="quick-add-dialog">
      <p class="section-subtext">선택된 부위: ${escapeHtml(muscleLabel)}</p>
      <label>
        <span>운동명</span>
        <input id="dialog-exercise-name" type="text" placeholder="예: 케이블 플라이" autofocus />
      </label>
      <button id="dialog-add-exercise" type="button">추가</button>
    </div>
  `;
  exerciseDialog.showModal();
  exerciseDialogContent.querySelector("#dialog-exercise-name")?.focus();
}

function isExerciseInMuscleGroup(exercise = {}, muscle = "other") {
  return exercise.primary_muscle === muscle || (exercise.secondary_muscles || []).includes(muscle);
}

function reorderVisibleExercise(exerciseId, direction, groupMuscle = null) {
  const visible = sortedExerciseItems(exerciseLibrary.filter((item) => !item.archived));
  const item = visible.find((exercise) => exercise.id === exerciseId);
  if (!item) {
    return null;
  }
  const muscle = groupMuscle || item.primary_muscle;
  const groupItems = visible.filter((exercise) => isExerciseInMuscleGroup(exercise, muscle));
  const groupIndex = groupItems.findIndex((exercise) => exercise.id === exerciseId);
  const targetGroupIndex = groupIndex + direction;
  if (groupIndex < 0 || targetGroupIndex < 0 || targetGroupIndex >= groupItems.length) {
    return null;
  }
  const targetId = groupItems[targetGroupIndex].id;
  const index = visible.findIndex((exercise) => exercise.id === exerciseId);
  const targetIndex = visible.findIndex((exercise) => exercise.id === targetId);
  const next = visible.slice();
  [next[index], next[targetIndex]] = [next[targetIndex], next[index]];
  return next.map((item) => item.id);
}

function readExerciseEditorUpdates(exerciseId) {
  return {
    name_ko: exerciseCategoryList.querySelector(`#editor-ko-${CSS.escape(exerciseId)}`).value,
    name_en: exerciseCategoryList.querySelector(`#editor-en-${CSS.escape(exerciseId)}`).value,
    primary_muscle: exerciseCategoryList.querySelector(`#editor-muscle-${CSS.escape(exerciseId)}`).value,
    equipment: splitCsv(exerciseCategoryList.querySelector(`#editor-equipment-${CSS.escape(exerciseId)}`).value),
    movement_pattern: exerciseCategoryList.querySelector(`#editor-pattern-${CSS.escape(exerciseId)}`).value,
    difficulty: exerciseCategoryList.querySelector(`#editor-difficulty-${CSS.escape(exerciseId)}`).value,
    instructions: exerciseCategoryList.querySelector(`#editor-instructions-${CSS.escape(exerciseId)}`).value.split("\n").map((item) => item.trim()).filter(Boolean),
  };
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
  const muscleWiki = `<a href="${muscleWikiUrl(item)}" target="_blank" rel="noreferrer">MuscleWiki 열기</a>`;
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
    <p class="source-line">Source: ${source} · ${muscleWiki}</p>
  `;
  exerciseDialog.showModal();
}

function renderRecentExerciseDialog(item) {
  if (!item) {
    return;
  }
  const items = exerciseHistoryItems(item.id);
  exerciseDialogTitle.textContent = `${item.name_ko || item.name_en || item.id} 최근 기록`;
  if (!items.length) {
    exerciseDialogContent.innerHTML = '<p class="empty">아직 이 운동의 과거 세트 기록이 없습니다.</p>';
    exerciseDialog.showModal();
    return;
  }
  exerciseDialogContent.innerHTML = `
    <div class="recent-session-list">
      ${items.slice(0, 5).map((historyItem, index) => {
        const started = historyItem.session.started_at || historyItem.session.created_at || historyItem.session.date || "";
        const date = started ? formatRoutineTime(started) : "날짜 확인 필요";
        return `
          <article class="recent-session">
            <header>
              <strong>${index === 0 ? "최신 운동" : "이전 운동"}</strong>
              <small>${escapeHtml(date)}</small>
            </header>
            <div class="recent-set-list">
              ${historyItem.entries.map((entry) => `<span>${entry.set_index || ""}. ${escapeHtml(formatSetLine(entry))}</span>`).join("")}
            </div>
            ${historyItem.session.note ? `<span>${escapeHtml(historyItem.session.note)}</span>` : ""}
          </article>
        `;
      }).join("")}
    </div>
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
    ...groups.map((group) => ({
      ...group,
      items: group.items.slice().reverse(),
    })).reverse().map((group) => {
      const card = document.createElement("article");
      card.className = "workout-draft-card";
      const rows = group.items.map(({ entry, index }) => {
        return `
          <div class="workout-draft-set">
            <span>${entry.set_index}. ${formatSetLine(entry)}</span>
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
        <strong>${item.maxWeight === null ? "맨몸" : `${item.maxWeight || "-"}kg`}</strong>
        <small>${item.setCount} set · ${item.entries.map(formatSetLine).join(" · ")}</small>
      `;
      return row;
    }),
  );
}

function renderRoutineCards(sessions = [], healthSessions = []) {
  const allGroups = buildRoutineGroups(sessions, healthSessions);
  const groups = syncRoutineMonthControls(allGroups);
  latestRoutineGroups = groups;

  if (!allGroups.length) {
    routineTrack.innerHTML = '<p class="empty">아직 표시할 루틴 기록이 없습니다.</p>';
    return;
  }

  if (!groups.length) {
    routineTrack.innerHTML = '<p class="empty">선택한 월에 표시할 루틴 기록이 없습니다.</p>';
    return;
  }

  routineTrack.replaceChildren(
    ...groups.map((group) => {
      const card = document.createElement("article");
      card.className = "routine-card";
      const primaryMuscle = uniqueMuscles(group.workouts.flatMap((session) => session.entries || []))[0] || "full_body";
      card.dataset.muscle = primaryMuscle;
      const tags = routineGroupTags(group).map((tag) => `<span class="routine-tag">${escapeHtml(tag)}</span>`).join("");
      const workoutDetails = group.workouts.map((session) => {
        const exerciseGroups = groupEntriesByExercise(session.entries || []);
        return Object.entries(exerciseGroups).map(([exercise, entries]) => {
          const label = exerciseLabel(entries[0]?.muscle_group || "other", exercise);
          return `
            <button class="routine-exercise routine-detail-group" type="button" data-exercise-id="${escapeHtml(exercise)}">
              <strong>${escapeHtml(label)}</strong>
              <small>${entries.length}set</small>
              <span class="routine-set-list">
                ${entries.map((entry) => `<span>${formatSetLine(entry)}</span>`).join("")}
              </span>
            </button>
          `;
        }).join("");
      }).join("");
      const activityDetails = group.activities.map((activity) => {
        const activityId = activity.source || activity.id || "";
        return `
          <button
            class="routine-exercise routine-detail-group routine-activity-row"
            type="button"
            data-health-session-id="${escapeHtml(activityId)}"
            data-activity-type="${escapeHtml(activity.type)}"
            data-activity-minutes="${escapeHtml(String(activity.duration_minutes || 30))}"
            data-activity-detail="${escapeHtml(activity.detail || "")}"
            data-activity-date="${escapeHtml(activity.date || group.date || "")}"
            data-swim-meters="${escapeHtml(String(activity.metadata?.swim_meters || ""))}"
            data-swim-turns="${escapeHtml(String(activity.metadata?.swim_turns || ""))}"
            data-swim-note="${escapeHtml(activity.metadata?.swim_note || "")}"
          >
            <strong>${escapeHtml(healthTypeLabel(activity.type))}</strong>
            <small>${formatActivityDuration(activity.duration_minutes || 0)}</small>
            <span class="routine-set-list"><span>${escapeHtml(activity.detail || "디테일 없음")}</span></span>
          </button>
        `;
      }).join("");
      card.innerHTML = `
        <header>
          <div class="routine-card-title">
            <strong>${escapeHtml(formatRoutineDate(group.date))}</strong>
            <small>총 ${formatActivityDuration(group.duration || 0)}</small>
          </div>
          <div class="routine-card-actions">
            <button
              class="button-ghost routine-edit-button"
              type="button"
              data-routine-edit="group"
              data-routine-group-key="${escapeHtml(group.key)}"
            >편집</button>
          </div>
        </header>
        <div class="routine-tag-row">${tags}</div>
        <div class="routine-exercise-list">${workoutDetails}${activityDetails}</div>
      `;
      return card;
    }),
  );
  requestAnimationFrame(() => {
    routineTrack.scrollTo({ left: 0, behavior: "auto" });
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
  const todayKey = payload.date || dates.at(-1) || "";
  const recentMuscle = (summary.muscle_groups || [])[0];
  const recentLabel = recentMuscle ? (MUSCLE_LABELS[recentMuscle] || recentMuscle) : "없음";
  const gapCount = readiness.filter((item) => ["overdue", "untracked"].includes(item.status)).length;
  if (healthWindowNote) {
    healthWindowNote.textContent = dates.length
      ? `최근 ${dashboard.window_days || dates.length}일 기준 · ${shortDate(dates[0])} - ${shortDate(dates.at(-1))}`
      : "최근 운동 기록 기준";
  }
  healthSummary.replaceChildren(
    ...[
      ["오늘 운동", summary.structured_workout_count ? `${summary.structured_workout_count}회` : "없음"],
      ["총 세트", `${summary.strength_set_count || 0} set`],
      ["최근 부위", recentLabel],
      ["공백 부위", `${gapCount}개`],
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
        const suggestion = String(item.suggestion || "").replace(new RegExp(`^${item.label}\\s*`), "");
        row.innerHTML = `
          <strong>${item.label}</strong>
          <p>${suggestion || "가볍게 확인"}</p>
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
  const tiers = [
    {
      label: "Act Now",
      items: items.filter((item) => ["good", "steady", "protect", "watch"].includes(item.status) && item.status !== "empty"),
    },
    {
      label: "Watch",
      items: items.filter((item) => ["light", "context", "needs_review"].includes(item.status)),
    },
    {
      label: "Stale / Empty",
      items: items.filter((item) => ["empty", "unknown"].includes(item.status)),
    },
  ].map((tier) => ({ ...tier, items: tier.items.slice(0, tier.label === "Stale / Empty" ? 4 : 3) })).filter((tier) => tier.items.length);

  council.replaceChildren(
    ...tiers.map((tier) => {
      const group = document.createElement("section");
      group.className = "agent-tier";
      group.innerHTML = `<h3>${tier.label}</h3>`;
      const grid = document.createElement("div");
      grid.className = "agent-tier-grid";
      tier.items.forEach((item) => {
      const card = document.createElement("article");
      card.className = "agent-card";
      card.innerHTML = `
        <header>
          <h3>${item.label || item.agent}</h3>
          <span class="badge">${item.status || "unknown"}</span>
        </header>
        <p>${item.insight || ""}</p>
        <p>${item.recommendation || ""}</p>
        <small>${item.confidence != null ? `confidence ${Math.round(Number(item.confidence) * 100)}%` : "confidence pending"}</small>
      `;
      grid.append(card);
      });
      group.append(grid);
      return group;
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
  renderCumulativeTimeInto(activityCumulative, areas);
}

function renderCumulativeTimeInto(element, areas = []) {
  if (!element) return;
  if (!areas.length) {
    element.innerHTML = '<p class="empty">No cumulative time yet.</p>';
    return;
  }

  element.replaceChildren(
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

function summarizeSessionsByDay(sessions = []) {
  const days = new Map();
  sessions.forEach((session) => {
    const date = session.date || "unknown";
    const minutes = Number(session.duration_minutes || 0);
    if (!minutes) return;
    const current = days.get(date) || {
      date,
      totalMinutes: 0,
      areas: new Map(),
      reviewRequired: 0,
    };
    const area = session.area || "Unclassified";
    current.totalMinutes += minutes;
    current.areas.set(area, (current.areas.get(area) || 0) + minutes);
    if (session.review_required) {
      current.reviewRequired += 1;
    }
    days.set(date, current);
  });

  const rows = [...days.values()]
    .sort((a, b) => a.date.localeCompare(b.date))
    .map((day) => ({
      ...day,
      areas: [...day.areas.entries()]
        .map(([area, minutes]) => ({
          area,
          minutes,
          share: day.totalMinutes ? minutes / day.totalMinutes : 0,
        }))
        .sort((a, b) => b.minutes - a.minutes),
    }));
  const maxMinutes = Math.max(0, ...rows.map((day) => day.totalMinutes));
  return { rows, maxMinutes };
}

function renderActivityShareStack(element, title, areas = []) {
  if (!element) return;
  if (!areas.length) {
    element.innerHTML = '<p class="empty">No activity share yet.</p>';
    return;
  }

  const totalMinutes = areas.reduce((sum, item) => sum + Number(item.minutes || 0), 0);
  const segments = areas.map((item) => {
    const share = totalMinutes ? Number(item.minutes || 0) / totalMinutes : Number(item.share || 0);
    return `<span class="activity-segment" style="width: ${Math.max(1, share * 100)}%; background: ${colorForArea(item.area)}" title="${item.area} ${formatPercent(share)}"></span>`;
  }).join("");
  const legend = areas.map((item) => {
    const share = totalMinutes ? Number(item.minutes || 0) / totalMinutes : Number(item.share || 0);
    return `
      <div class="activity-legend-item">
        <span class="legend-dot" style="background: ${colorForArea(item.area)}"></span>
        <strong>${item.area}</strong>
        <small>${formatDuration(item.minutes)} · ${formatPercent(share)}</small>
      </div>
    `;
  }).join("");

  element.innerHTML = `
    <article class="activity-stack-card compact">
      <header class="activity-stack-header">
        <strong>${title}</strong>
        <span>${formatDuration(totalMinutes)}</span>
      </header>
      <div class="activity-stack-track" aria-label="${title} activity share">${segments}</div>
      <div class="activity-legend">${legend}</div>
    </article>
  `;
}

function renderDailyAreaChart(element, sessions = []) {
  if (!element) return;
  const { rows, maxMinutes } = summarizeSessionsByDay(sessions);
  if (!rows.length) {
    element.innerHTML = '<p class="empty">No daily activity yet.</p>';
    return;
  }

  element.replaceChildren(
    ...rows.map((day) => {
      const card = document.createElement("article");
      card.className = "daily-area-day";
      const height = maxMinutes ? Math.max(10, (day.totalMinutes / maxMinutes) * 100) : 0;
      const segments = day.areas.map((item) => `
        <span
          style="height: ${Math.max(4, item.share * 100)}%; background: ${colorForArea(item.area)}"
          title="${day.date} · ${item.area} · ${formatDuration(item.minutes)}"
        ></span>
      `).join("");
      const date = new Date(`${day.date}T00:00:00`);
      const label = Number.isNaN(date.getTime())
        ? day.date
        : new Intl.DateTimeFormat("ko-KR", { day: "2-digit" }).format(date);
      card.innerHTML = `
        <div class="daily-area-bar" style="height: ${height}%">${segments}</div>
        <small>${label}</small>
      `;
      return card;
    }),
  );
}

function renderMainAgent({ today = {}, activityAllocation = {}, health = {}, english = {}, expenseCandidates = {}, syncStatus = {} }) {
  latestMainAgentPayload = { today, activityAllocation, health, english, expenseCandidates, syncStatus };
  const summary = activityAllocation.summary || {};
  const monthSummary = activityAllocation.month_summary || {};
  const monthAreas = monthSummary.areas || [];
  const periodSummary = activityAllocation.period_summary || monthSummary;
  const periodAreas = periodSummary.areas || monthAreas;
  const selectedSummary = mainPeriodMode === "period" ? periodSummary : monthSummary;
  const selectedAreas = mainPeriodMode === "period" ? periodAreas : monthAreas;
  const monthSessions = activityAllocation.month_sessions || activityAllocation.sessions || [];
  const councilItems = today.agent_council || [];
  const leadingArea = selectedAreas[0]?.area ? `${selectedAreas[0].area}` : "판단 보류";

  if (mainAgentSummary) {
    mainAgentSummary.textContent = `${selectedSummary.month || "Current period"} 활동 기록의 중심은 ${leadingArea}입니다. 전체 시간 대비 추적률보다, 기록된 활동 안에서 어떤 영역이 삶의 방향을 잡고 있는지를 우선 봅니다.`;
  }

  if (mainAgentMetrics) {
    mainAgentMetrics.replaceChildren(
      ...[
        ["Top Area", leadingArea],
        ["Activity", formatDuration(selectedSummary.total_tracked_minutes || 0)],
        ["Active Days", `${summarizeSessionsByDay(monthSessions).rows.length}`],
        ["Agents", `${councilItems.length}`],
        ["English", `${english.summary?.study_minutes || 0}m`],
        ["Health", `${health.summary?.strength_set_count || 0} sets`],
      ].map(([label, value]) => {
        const item = document.createElement("div");
        item.className = "metric-item";
        item.innerHTML = `<span>${label}</span><strong>${value}</strong>`;
        return item;
      }),
    );
  }

  if (mainShareTitle) {
    mainShareTitle.textContent = mainPeriodMode === "period" ? "Period" : "Month";
  }
  if (mainPeriodToggle) {
    mainPeriodToggle.textContent = mainPeriodMode === "period" ? "Period" : "Month";
  }

  renderActivityShareStack(mainMonthBars, mainPeriodMode === "period" ? "전체 기간 활동 비중" : "월간 활동 비중", selectedAreas);
  renderDailyAreaChart(mainDailyBars, monthSessions);
  renderCumulativeTimeInto(mainCumulative, selectedAreas);

  if (!mainAgentSignals) return;
  const signalPriority = { watch: 0, protect: 1, needs_review: 2, good: 3, steady: 4, light: 5, context: 6, empty: 7, unknown: 8 };
  const visibleSignals = councilItems
    .slice()
    .sort((a, b) => (signalPriority[a.status] ?? 9) - (signalPriority[b.status] ?? 9) || Number(b.confidence || 0) - Number(a.confidence || 0))
    .slice(0, 3);
  if (!visibleSignals.length) {
    mainAgentSignals.innerHTML = '<p class="empty">No agent signals yet.</p>';
    return;
  }
  mainAgentSignals.replaceChildren(
    ...visibleSignals.map((item) => {
      const card = document.createElement("article");
      card.className = "main-signal-item";
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

function activityHistoryItem(item = {}) {
  const areaLabels = {
    work: "AI Work",
    health: "Health",
    food: "Food",
    english: "English",
    creator: "Creator/Social",
    travel: "Travel/Experience",
    social: "Creator/Social",
    rest: "Rest",
    admin: "Admin",
    unclassified: "Unclassified",
  };
  return {
    id: item.id,
    date: item.date,
    area: item.area_label || areaLabels[item.area] || "Unclassified",
    area_key: item.area || "unclassified",
    label: item.subcategory || item.detail || item.area_label,
    start_time: item.start_time,
    end_time: item.end_time,
    duration_minutes: Number(item.duration_minutes || 0),
    source: item.id,
    source_text: item.detail || "",
    subcategory: item.subcategory,
    place: item.place,
    confidence: item.confidence,
    status: item.status || "completed",
    review_required: Boolean(item.review_required),
    review_reason: item.review_reason,
    parse_method: "history",
  };
}

function renderActivityAllocation(payload = {}, historyPayload = null) {
  const summary = payload.summary || {};
  const monthSummary = payload.month_summary || {};
  const qualityNotes = payload.data_quality?.notes || [];
  const areas = summary.areas || [];
  const monthAreas = monthSummary.areas || [];
  const sessions = historyPayload?.sessions?.length
    ? historyPayload.sessions.map(activityHistoryItem)
    : payload.sessions || [];

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
      row.className = item.status === "ignored"
        ? "capture-item ignored"
        : item.review_required ? "capture-item needs-review" : "capture-item";
      const time = [item.start_time, item.end_time].filter(Boolean).join(" - ") || "time unknown";
      const review = item.review_required
        ? `<small class="review-note">${item.review_reason || "Review required"}</small>`
        : "";
      const editable = String(item.source || "").startsWith("activity_");
      const actions = editable
        ? `
          <div class="activity-history-actions">
            <button class="button-secondary compact activity-history-edit" type="button"
              data-activity-id="${escapeHtml(item.source)}"
              data-activity-date="${escapeHtml(item.date || "")}"
              data-activity-area="${escapeHtml(item.area_key || "")}"
              data-activity-minutes="${escapeHtml(String(item.duration_minutes || 30))}"
              data-activity-detail="${escapeHtml(item.source_text || "")}"
              data-activity-subcategory="${escapeHtml(item.subcategory || "")}"
              data-activity-place="${escapeHtml(item.place || "")}">${item.status === "ignored" ? "복원/수정" : "수정"}</button>
            ${item.status === "ignored" ? "" : `<button class="button-secondary compact danger-action activity-history-ignore" type="button"
              data-activity-id="${escapeHtml(item.source)}">제외</button>`}
          </div>
        `
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
          ${actions}
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

function projectProgressFor(projectId) {
  return (aiWorkState.progress?.projects || []).find((item) => item.project_id === projectId) || {};
}

function projectEvents(projectId) {
  return (aiWorkState.recent_events || [])
    .filter((item) => item.project_id === projectId)
    .slice()
    .reverse();
}

function latestAiWorkProjectId(projects = []) {
  return projects
    .slice()
    .sort((a, b) => String(b.tracking?.latest_event_at || "").localeCompare(String(a.tracking?.latest_event_at || "")))[0]
    ?.project_id || null;
}

function selectedAiWorkProject() {
  return (aiWorkState.projects || []).find((item) => item.project_id === selectedAiWorkProjectId) || null;
}

function outputPathForProject(project = {}) {
  return (project.evidence_sources || []).find((source) => source.type === "output_folder")?.path || "";
}

function sourceTypesForProject(project = {}) {
  return new Set((project.evidence_sources || []).filter((source) => source.enabled !== false).map((source) => source.type));
}

function setAiWorkSourceChecks(types = new Set(["git", "codex"])) {
  aiWorkProjectForm?.querySelectorAll('input[name="evidence_source"]').forEach((input) => {
    input.checked = types.has(input.value);
  });
}

function linesToList(value = "") {
  return String(value || "")
    .split(/\n|,/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function openAiWorkProjectDialog(mode = "create", project = null) {
  if (isSupabaseMode()) {
    setWorkspaceStatus(aiWorkStatus, "Hosted mode 프로젝트 관리는 저장 이후 분석 단계에서 지원합니다.", "warning");
    return;
  }
  aiWorkProjectForm?.reset();
  setWorkspaceStatus(aiWorkFormStatus, "", "");
  aiWorkProjectMode.value = mode;
  aiWorkProjectId.value = mode === "update" ? project?.project_id || "" : "";
  aiWorkDialogTitle.textContent = mode === "update" ? "Edit Project" : "Add Project";
  aiWorkSubmitProject.textContent = mode === "update" ? "Update Project" : "Add Project";

  if (mode === "update" && project) {
    aiWorkProjectName.value = project.name || "";
    aiWorkProjectType.value = project.type || "ai-product";
    aiWorkProjectStatus.value = project.status || "in_progress";
    aiWorkProjectPriority.value = project.priority || "P2";
    aiWorkProjectPath.value = project.path || "";
    aiWorkCurrentFocus.value = project.current_focus || "";
    aiWorkNextAction.value = project.next_action || "";
    aiWorkSuccessCriteria.value = (project.success_criteria || []).join("\n");
    aiWorkSensitivity.value = project.sensitivity || "personal-private";
    aiWorkEvidenceMode.value = project.evidence_mode || "codex_and_git";
    aiWorkOutputPath.value = outputPathForProject(project);
    aiWorkProjectAliases.value = (project.aliases || []).join(", ");
    aiWorkExcludePaths.value = (project.exclude_paths || []).join("\n");
    aiWorkPublishDashboard.checked = project.publish_to_dashboard !== false;
    setAiWorkSourceChecks(sourceTypesForProject(project));
  } else {
    aiWorkProjectStatus.value = "in_progress";
    aiWorkProjectPriority.value = "P2";
    aiWorkSensitivity.value = "personal-private";
    aiWorkEvidenceMode.value = "codex_and_git";
    aiWorkPublishDashboard.checked = true;
    setAiWorkSourceChecks(new Set(["git", "codex"]));
  }

  if (aiWorkProjectDialog?.showModal) {
    aiWorkProjectDialog.showModal();
  }
}

function aiWorkPayloadFromForm() {
  const evidenceSources = [...aiWorkProjectForm.querySelectorAll('input[name="evidence_source"]:checked')]
    .map((item) => item.value);
  return {
    mode: aiWorkProjectMode.value,
    project_id: aiWorkProjectId.value,
    name: aiWorkProjectName.value.trim(),
    type: aiWorkProjectType.value,
    status: aiWorkProjectStatus.value,
    priority: aiWorkProjectPriority.value,
    path: aiWorkProjectPath.value.trim(),
    current_focus: aiWorkCurrentFocus.value.trim(),
    next_action: aiWorkNextAction.value.trim(),
    success_criteria: linesToList(aiWorkSuccessCriteria.value),
    sensitivity: aiWorkSensitivity.value,
    evidence_mode: aiWorkEvidenceMode.value,
    output_path: aiWorkOutputPath.value.trim(),
    aliases: splitCsv(aiWorkProjectAliases.value),
    exclude_paths: linesToList(aiWorkExcludePaths.value),
    publish_to_dashboard: aiWorkPublishDashboard.checked,
    evidence_sources: evidenceSources,
  };
}

function evidenceSourceLabel(source = {}) {
  if (source.type === "output_folder") {
    return `Output${source.path ? ` · ${source.path}` : ""}`;
  }
  if (source.type === "git") return "Git";
  if (source.type === "codex") return "Codex";
  return source.type || "Source";
}

function trackingSignalLabel(signal = "") {
  return {
    active: "Active",
    blocked: "Blocked",
    idle: "Idle",
    paused: "Paused",
  }[signal] || "Unknown";
}

function statusMapLabel(key = "") {
  return {
    Moving: "Moving",
    "Needs Decision": "Needs Decision",
    "Needs Review": "Needs Review",
    Quiet: "Quiet",
    Blocked: "Blocked",
  }[key] || key;
}

function latestWorkSignal(project = {}) {
  const experience = project.experience || {};
  if (experience.signal) {
    return experience.signal;
  }
  const tracking = project.tracking || {};
  const git = tracking.git || {};
  if (tracking.blocker_count) {
    return "Blocked";
  }
  if (git.dirty) {
    return "Local changes";
  }
  if (tracking.latest_event_at) {
    return "Evidence logged";
  }
  return "Watching";
}

function projectOutcome(project = {}) {
  if (project.success_criteria?.length) {
    return project.success_criteria[0];
  }
  if (project.kpis?.length) {
    return project.kpis[0].target || project.kpis[0].label || "";
  }
  return "";
}

function designerStatusLabel(project = {}, experience = {}) {
  if (project.status === "paused") return "보류";
  if (project.status === "shipped") return "완료";
  if (experience.review_need === "Decision needed") return "결정 필요";
  if (experience.review_need === "Review ready") return "리뷰 가능";
  if (experience.signal === "Blocked") return "막힘";
  if (experience.signal === "Moving") return "진행중";
  return "정리 필요";
}

function projectCardStatusLabel(project = {}, experience = {}) {
  if (project.status === "paused") return "보류 중";
  if (project.status === "shipped") return "완료됨";
  if (experience.review_need === "Decision needed") return "결정 필요";
  if (experience.review_need === "Review ready") return "리뷰 가능";
  if (experience.latest_change) return "최근 업데이트";
  return "시작 준비";
}

function projectFreshnessLabel(tracking = {}) {
  if (!tracking.latest_event_at) return "기록 없음";
  const value = String(tracking.latest_event_at);
  if (value.includes("T")) {
    return `최근 기록 ${value.slice(5, 16).replace("T", " ")}`;
  }
  return "최근 기록 있음";
}

function renderMiniBar(label, value, maxValue = 1, tone = "") {
  const raw = Number(value || 0);
  const width = maxValue ? Math.max(4, Math.round((raw / maxValue) * 100)) : 0;
  return `
    <div class="ai-work-mini-bar ${tone}">
      <span>${escapeHtml(label)}</span>
      <strong>${Math.round(raw * 100)}%</strong>
      <i style="width: ${width}%"></i>
    </div>
  `;
}

function renderPulseSegment(label, value, tone = "") {
  const raw = Math.max(0, Math.min(1, Number(value || 0)));
  return `
    <span class="ai-work-pulse-segment ${tone}" style="--pulse: ${raw}">
      <i></i>
      <em>${escapeHtml(label)}</em>
    </span>
  `;
}

function renderAiWorkSummary() {
  const projects = aiWorkState.projects || [];
  const summary = aiWorkState.summary || {};
  const totalProjects = summary.project_count ?? projects.length;
  const activeProjects = summary.active_count ?? projects.filter((item) => !["paused", "shipped"].includes(item.status)).length;
  const droppedProjects = projects.filter((item) => item.status === "paused").length;
  const shippedProjects = projects.filter((item) => item.status === "shipped").length;
  const blockedProjects = summary.blocked_count ?? projects.filter((item) => item.status === "blocked" || item.tracking?.blocker_count).length;
  const reviewProjects = (summary.status_map?.["Needs Review"] || []).length;
  aiWorkProjectCount.textContent = String(projects.length);
  aiWorkSummary.innerHTML = `
    <span><strong>${totalProjects}</strong> 전체 프로젝트</span>
    <span><strong>${activeProjects}</strong> 현재 진행중</span>
    <span><strong>${droppedProjects}</strong> 드랍/보류</span>
    <span><strong>${reviewProjects}</strong> 리뷰 필요</span>
    <span><strong>${blockedProjects}</strong> 이슈</span>
    <span><strong>${shippedProjects}</strong> 완료</span>
  `;
  renderAiWorkVisuals();
}

function renderStatusSegment(key, ids = [], total = 1, projects = []) {
  const count = ids.length;
  const names = ids.map((id) => projects.find((project) => project.project_id === id)?.name || id);
  const width = total ? Math.max(count ? 8 : 3, Math.round((count / total) * 100)) : 3;
  return `
    <span class="ai-work-status-segment ${key.toLowerCase().replaceAll(" ", "-")}" style="--segment: ${width}">
      <i></i>
      <em>${statusMapLabel(key)}</em>
      <strong>${count}</strong>
      <small>${names.length ? names.map(escapeHtml).join(", ") : ""}</small>
    </span>
  `;
}

function renderAiWorkVisuals() {
  aiWorkVisuals.innerHTML = "";
}

function renderAiWorkProjects() {
  const projects = aiWorkState.projects || [];
  if (!projects.length) {
    aiWorkProjects.innerHTML = '<p class="empty">추적 중인 프로젝트가 없습니다. Add Project로 첫 프로젝트를 등록하세요.</p>';
    renderAiWorkDetail(null);
    return;
  }
  if (!selectedAiWorkProjectId || !projects.some((item) => item.project_id === selectedAiWorkProjectId)) {
    selectedAiWorkProjectId = latestAiWorkProjectId(projects) || projects[0].project_id;
  }
  if (aiWorkEditButton) {
    aiWorkEditButton.disabled = !selectedAiWorkProjectId;
  }
  aiWorkProjects.replaceChildren(
    ...projects.map((project) => {
      const card = document.createElement("button");
      card.type = "button";
      card.className = "ai-work-project-card";
      card.classList.toggle("active", project.project_id === selectedAiWorkProjectId);
      card.dataset.projectId = project.project_id;
      const tracking = project.tracking || {};
      const experience = project.experience || {};
      const statusLabel = projectCardStatusLabel(project, experience);
      const nextAction = experience.next_open || project.next_action || "다음 행동을 정리해야 합니다.";
      const outcome = projectOutcome(project) || "완료 기준을 정리해야 합니다.";
      card.innerHTML = `
        <span class="ai-work-card-topline">
          <span class="badge">${escapeHtml(project.priority || "P2")}</span>
          <span class="badge">${escapeHtml(statusLabel)}</span>
        </span>
        <span class="ai-work-card-main">
          <strong>${escapeHtml(project.name)}</strong>
          <small>${escapeHtml(project.current_focus || experience.latest_change || project.type || "project")}</small>
        </span>
        <span class="ai-work-card-story">
          <span>다음</span>
          <strong>${escapeHtml(nextAction)}</strong>
        </span>
        <span class="ai-work-card-story muted">
          <span>완료 기준</span>
          <strong>${escapeHtml(outcome)}</strong>
        </span>
        <span class="ai-work-card-foot">${escapeHtml(projectFreshnessLabel(tracking))}</span>
      `;
      return card;
    }),
  );
  renderAiWorkDetail(projects.find((item) => item.project_id === selectedAiWorkProjectId));
}

function renderAiWorkDetail(project) {
  if (!project) {
    aiWorkDetailTitle.textContent = "Select";
    aiWorkDetail.innerHTML = '<p class="empty">프로젝트를 선택하면 목표, 다음 행동, 리뷰 포인트를 보여줍니다.</p>';
    return;
  }
  const progress = projectProgressFor(project.project_id);
  const events = projectEvents(project.project_id);
  const tracking = project.tracking || {};
  const git = tracking.git || {};
  const outputs = tracking.outputs || [];
  const experience = project.experience || {};
  aiWorkDetailTitle.textContent = project.name;
  const designerLabel = designerStatusLabel(project, experience);
  const outcome = projectOutcome(project);
  const sourceItems = (project.evidence_sources || []).map((source) => `
    <li>
      <strong>${escapeHtml(evidenceSourceLabel(source))}</strong>
      <span>${source.enabled === false ? "off" : "on"}</span>
    </li>
  `).join("");
  const projectNextAction = project.next_action ? `<li>${escapeHtml(project.next_action)}</li>` : "";
  const nextActions = (progress.next_actions || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("");
  const inferredActions = (tracking.recent_next_actions || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("");
  const successCriteria = (project.success_criteria || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("");
  const decisions = (tracking.recent_decisions || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("");
  const blockers = (tracking.recent_blockers || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("");
  const changedFiles = (git.changed_files || []).slice(0, 10).map((item) => `<li>${escapeHtml(item)}</li>`).join("");
  const outputItems = outputs.map((item) => `
    <li>
      <strong>${item.available ? `${item.file_count || 0} files` : "Missing"}</strong>
      <span>${escapeHtml(item.latest_modified_at || item.path || "No output folder")}</span>
    </li>
  `).join("");
  const eventItems = events.slice(0, 6).map((event) => `
    <article class="ai-work-event">
      <header>
        <strong>${escapeHtml(event.source || "evidence")}</strong>
        <time>${escapeHtml(event.captured_at || "")}</time>
      </header>
      <p>${escapeHtml(event.evidence_summary || event.goal || "Evidence captured")}</p>
      ${(event.changed_files || []).length ? `<small>${event.changed_files.length} changed file(s)</small>` : ""}
    </article>
  `).join("");
  aiWorkDetail.innerHTML = `
    <section class="ai-work-design-hero">
      <div>
        <span class="eyebrow">Selected Project</span>
        <h3>${escapeHtml(project.name)}</h3>
        <p>${escapeHtml(progress.current_focus || project.current_focus || "이 프로젝트가 지금 무엇을 만들고 싶은지 정리가 필요합니다.")}</p>
      </div>
      <div class="ai-work-design-status">
        <strong>${escapeHtml(designerLabel)}</strong>
        <span>${escapeHtml(project.priority || "P2")} · ${escapeHtml(project.type || "project")}</span>
      </div>
    </section>
    <section class="ai-work-next-panel ai-work-primary-next">
      <span>Next Action</span>
      <strong>${escapeHtml(experience.next_open || "다음 행동이 아직 정리되지 않았습니다.")}</strong>
      <p>${escapeHtml(outcome || "완료 기준이나 기대 산출물이 아직 비어 있습니다.")}</p>
    </section>
    <div class="ai-work-designer-grid">
      <div>
        <span>Desired Outcome</span>
        <strong>${escapeHtml(outcome || "정의 필요")}</strong>
      </div>
      <div>
        <span>Review State</span>
        <strong>${escapeHtml(experience.review_need || "Low")}</strong>
      </div>
      <div>
        <span>Recent Change</span>
        <strong>${escapeHtml(experience.latest_change || "아직 의미 있는 변화가 없습니다.")}</strong>
      </div>
      <div>
        <span>Rhythm</span>
        <strong>${escapeHtml(project.review_cadence || "daily")} · ${escapeHtml(tracking.latest_event_at ? tracking.latest_event_at.slice(5, 16).replace("T", " ") : "no evidence")}</strong>
      </div>
    </div>
    <h3 class="panel-title">Action</h3>
    <ul class="ai-work-next-actions">${projectNextAction || nextActions || inferredActions || "<li>Evidence import 후 생성됩니다.</li>"}</ul>
    <h3 class="panel-title">Success Criteria</h3>
    <ul class="ai-work-next-actions">${successCriteria || "<li>아직 성공 기준이 없습니다.</li>"}</ul>
    <h3 class="panel-title">Decisions / Risks</h3>
    <div class="ai-work-two-column">
      <ul class="ai-work-next-actions">${decisions || "<li>최근 decision 없음</li>"}</ul>
      <ul class="ai-work-next-actions">${blockers || "<li>현재 blocker 없음</li>"}</ul>
    </div>
    <details class="ai-work-technical-detail">
      <summary>Technical Evidence</summary>
      <div class="ai-work-detail-grid">
        <div>
          <span>Folder</span>
          <strong>${project.folder_status === "missing" ? "Missing" : "Ready"}</strong>
        </div>
        <div>
          <span>Branch</span>
          <strong>${escapeHtml(git.branch || "No Git")}</strong>
        </div>
        <div>
          <span>Local Changes</span>
          <strong>${git.available ? `${tracking.changed_file_count || 0} files` : "N/A"}</strong>
        </div>
        <div>
          <span>Last Commit</span>
          <strong>${escapeHtml(git.last_commit?.subject || "No commit")}</strong>
        </div>
      </div>
      <h3 class="panel-title">Evidence Sources</h3>
      <ul class="ai-work-source-list">${sourceItems || "<li><strong>No source</strong><span>off</span></li>"}</ul>
      <h3 class="panel-title">Changed Files</h3>
      <ul class="ai-work-file-list">${changedFiles || "<li>변경 파일 없음</li>"}</ul>
      <h3 class="panel-title">Output Tracking</h3>
      <ul class="ai-work-source-list">${outputItems || "<li><strong>No output folder</strong><span>not configured</span></li>"}</ul>
      <h3 class="panel-title">Recent Evidence</h3>
      <div class="ai-work-events">${eventItems || '<p class="empty">아직 수집된 evidence가 없습니다.</p>'}</div>
    </details>
  `;
}

function renderAiWork(payload = {}) {
  aiWorkState = {
    summary: payload.summary || {},
    projects: payload.projects || [],
    progress: payload.progress || { projects: [] },
    recent_events: payload.recent_events || [],
  };
  renderAiWorkSummary();
  renderAiWorkProjects();
}

async function refreshAiWork() {
  if (isSupabaseMode()) {
    renderAiWork(await loadDashboardSnapshot("work-projects").catch(() => ({ projects: [], progress: {}, recent_events: [] })));
    return;
  }
  renderAiWork(await loadJson("/api/work-projects").catch(() => ({ projects: [], progress: {}, recent_events: [] })));
}

function renderEnglishList(element, items = [], renderer, emptyText) {
  if (!items.length) {
    element.innerHTML = `<p class="empty">${emptyText}</p>`;
    return false;
  }
  element.replaceChildren(
    ...items.map((item) => {
      const card = document.createElement("article");
      card.className = "english-card";
      card.innerHTML = renderer(item);
      return card;
    }),
  );
  return true;
}

function humanizeEnglishSignal(value = "") {
  const labels = {
    continues_speaking_despite_uncertainty: "불확실해도 대화를 이어감",
    uses_short_practical_questions_effectively: "짧고 실용적인 질문을 잘 사용함",
    sometimes_combines_multiple_ideas_into_one_sentence: "한 문장에 여러 생각을 섞음",
    relies_on_approximate_vocabulary_when_unsure: "모르는 단어를 비슷한 단어로 대체함",
    hesitates_during_longer_question_structures: "긴 질문을 만들 때 망설임",
    uses_korean_sentence_order_occasionally: "가끔 한국어 어순으로 말함",
    comfortable_with_emotional_small_talk: "감정 기반 스몰톡에 편안함",
    adds_detail_after_short_answers: "짧은 답 뒤에 디테일을 추가함",
    missing_auxiliary_verbs: "조동사 누락",
    trying_to_build_overly_long_sentences: "긴 문장을 만들다 구조가 무너짐",
    direct_korean_sentence_order: "한국어식 어순",
    good_immediate_repetition_after_correction: "교정 직후 반복이 좋음",
    uses_context_well: "상황 맥락을 잘 활용함",
    confidence_improves_after_warm_up: "워밍업 후 자신감이 올라감",
    good_follow_up_question_ability: "후속 질문 능력이 좋음",
    vocabulary_precision: "어휘 정확도",
    question_structure: "질문 구조",
    sentence_structure: "문장 구조",
    natural_phrasing: "자연스러운 표현",
    fluency: "유창성",
    confidence: "자신감",
  };
  const key = String(value || "").trim();
  return labels[key] || key.replaceAll("_", " ");
}

function correctionOriginal(item = {}) {
  return item.user_said || item.user_expression || item.original || "";
}

function correctionBetter(item = {}) {
  return item.better || item.recommended_expression || item.improved || "";
}

function correctionCategory(item = {}) {
  return item.category || item.type || "correction";
}

function reviewCardFront(item = {}) {
  const front = item.front || "Card";
  return humanizeEnglishSignal(front);
}

function renderDetailList(items = []) {
  const filtered = items.filter(Boolean).slice(0, 8);
  if (!filtered.length) {
    return "";
  }
  return `<ul>${filtered.map((item) => `<li>${escapeHtml(String(item))}</li>`).join("")}</ul>`;
}

function renderLogColumn(title, items = []) {
  const detail = renderDetailList(items);
  if (!detail) return "";
  return `
    <div>
      <b>${escapeHtml(title)}</b>
      ${detail}
    </div>
  `;
}

function renderLearningContinuity(continuity = {}) {
  const daily = continuity.daily || [];
  if (!daily.length) {
    englishSummary.innerHTML = '<p class="empty">No learning timeline yet.</p>';
    return;
  }
  const maxMinutes = Math.max(continuity.max_daily_minutes || 0, 1);
  const focusText = (continuity.focus_distribution || []).map((item) => `${item.name} ${item.count}`).join(" · ");
  englishSummary.innerHTML = `
    <div class="continuity-head">
      <strong>${escapeHtml(continuity.summary || "")}</strong>
      <span>${escapeHtml(`${continuity.current_streak_days || 0} day streak · avg ${continuity.average_minutes_per_active_day || 0} min`)}</span>
    </div>
    <div class="continuity-bars" aria-label="최근 14일 영어 학습 시간">
      ${daily.map((day) => {
        const height = Math.max(6, Math.round(((day.minutes || 0) / maxMinutes) * 72));
        const active = day.minutes || day.session_count;
        return `
          <div class="continuity-day ${active ? "active" : ""}">
            <div class="bar-wrap"><span style="height:${height}px"></span></div>
            <small>${escapeHtml(day.date.slice(5))}</small>
            <b>${day.minutes || 0}</b>
          </div>
        `;
      }).join("")}
    </div>
    <div class="continuity-foot">
      <span>${escapeHtml(`${continuity.active_day_count || 0} active days / ${continuity.window?.days || 14} days`)}</span>
      <span>${escapeHtml(`${continuity.session_count || 0} sessions`)}</span>
      <span>${escapeHtml(focusText || "No focus distribution yet")}</span>
    </div>
  `;
}

function setEnglishSectionVisible(element, visible) {
  const section = element?.closest("section");
  if (section) {
    section.hidden = !visible;
  }
}

function renderMetricEvidence(item = {}) {
  const examples = item.examples || [];
  const turns = item.turn_examples || [];
  const scoreHistory = item.score_history || [];
  const exampleList = examples.map((example) => {
    const before = example.user_said || example.evidence || "Observed";
    const after = example.better ? ` -> ${example.better}` : "";
    return `${example.date || ""} · ${before}${after}`;
  });
  const turnList = turns.map((turn) => {
    const score = turn.score === undefined || turn.score === null ? "" : ` · score ${turn.score}`;
    const better = turn.better ? ` -> ${turn.better}` : "";
    return `${turn.date || ""} · ${turn.situation || "turn"}${score} · ${turn.user_said || ""}${better}`;
  });
  const historyText = scoreHistory.map((score) => `${score.date}: ${score.score}`).join(" · ");
  return `
    <details class="english-card-detail">
      <summary>근거 보기</summary>
      <p>${escapeHtml(item.why_it_matters || "")}</p>
      ${exampleList.length ? `<h4>Issue Evidence</h4>${renderDetailList(exampleList)}` : ""}
      ${turnList.length ? `<h4>Turn Evidence</h4>${renderDetailList(turnList)}` : ""}
      ${historyText ? `<small>Score history · ${escapeHtml(historyText)}</small>` : ""}
      ${item.next_review_check ? `<small>Next check · ${escapeHtml(item.next_review_check)}</small>` : ""}
    </details>
  `;
}

function renderValidationAgent(agent = {}) {
  if (!englishValidationAgent) return;
  const checks = agent.checks || [];
  if (!checks.length) {
    setEnglishSectionVisible(englishValidationAgent, false);
    return;
  }
  setEnglishSectionVisible(englishValidationAgent, true);
  englishValidationAgent.innerHTML = `
    <div class="english-validation-strip">
      <strong>${escapeHtml(agent.agent_name || "validator")}</strong>
      <span>${escapeHtml(`${agent.usefulness_score ?? "-"}점 · ${agent.status || "unknown"}`)}</span>
      <details>
        <summary>검증 결과</summary>
        <ul>
          ${checks.map((check) => `
            <li class="${check.passed ? "passed" : "failed"}">
              <b>${check.passed ? "OK" : "FIX"} · ${escapeHtml(check.key)}</b>
              <span>${escapeHtml(check.fix || check.finding || "")}</span>
            </li>
          `).join("")}
        </ul>
      </details>
    </div>
  `;
}

function renderIssueProgress(issueProgress = {}, fallbackActions = []) {
  const repeated = issueProgress.repeated_issues || [];
  const improving = issueProgress.improving_issues || [];
  const growth = issueProgress.expression_growth || [];
  const items = repeated.length
    ? repeated.map((issue) => ({
      title: issue.title,
      meta: `${issue.observation_count || 0}회 관측 · 최근 ${issue.recent_observation_count || 0}회`,
      example: issue.examples?.[0],
      plan: issue.remediation?.plan,
      drill: issue.remediation?.drill,
    }))
    : fallbackActions.slice(0, 5).map((item) => ({
      title: item.title,
      meta: item.why,
      example: item.example,
      plan: item.how_to_fix,
      drill: item.drill,
    }));
  const progressBlocks = [
    ...items.map((item) => ({ ...item, kind: "반복 문제" })),
    ...improving.slice(0, 2).map((item) => ({
      title: item.title,
      meta: `${item.observation_count || 0}회 관측 · 최근 ${item.recent_observation_count || 0}회`,
      plan: item.signal,
      kind: "개선 후보",
    })),
    ...growth.slice(-2).map((item) => ({
      title: item.title,
      meta: `${item.learned_count || 0} expressions · ${item.date || ""}`,
      plan: (item.items || []).join(" · "),
      kind: "표현 확장",
    })),
  ];
  return renderEnglishList(
    englishIssueTracker,
    progressBlocks.slice(0, 7),
    (item) => `
      <header>
        <strong>${escapeHtml(item.title || "Issue")}</strong>
        <span>${escapeHtml(item.kind || "")}</span>
      </header>
      <small>${escapeHtml(item.meta || "")}</small>
      ${item.example?.user_said || item.example?.evidence ? `<p>${escapeHtml(item.example.user_said || item.example.evidence)}${item.example.better ? ` → ${escapeHtml(item.example.better)}` : ""}</p>` : ""}
      ${item.plan ? `<p>${escapeHtml(item.plan)}</p>` : ""}
      ${item.drill ? `<small>${escapeHtml(item.drill)}</small>` : ""}
    `,
    "No tracked English issues yet.",
  );
}

function renderDailyReviewLog(days = []) {
  if (!englishDailyLog) return;
  if (!days.length) {
    englishDailyLog.innerHTML = '<p class="empty">No daily review log yet.</p>';
    if (englishDailyLogPager) englishDailyLogPager.replaceChildren();
    setEnglishSectionVisible(englishDailyLog, false);
    return;
  }
  setEnglishSectionVisible(englishDailyLog, true);
  const pageSize = 5;
  const pageCount = Math.max(1, Math.ceil(days.length / pageSize));
  englishDailyLogPage = Math.min(englishDailyLogPage, pageCount - 1);
  const visibleDays = days.slice(englishDailyLogPage * pageSize, englishDailyLogPage * pageSize + pageSize);
  englishDailyLog.replaceChildren(
    ...visibleDays.map((day, index) => {
      const details = document.createElement("details");
      details.className = "daily-log-day";
      details.open = index < 2;
      details.innerHTML = `
        <summary>
          <strong>${escapeHtml(day.date)}</strong>
          <span>${escapeHtml(`${day.study_minutes || 0} min · ${day.session_count || 0} files`)}</span>
        </summary>
        <div class="daily-log-sessions">
          ${(day.sessions || []).map((session) => `
            <article class="daily-log-session">
              <header>
                <strong>${escapeHtml(session.title || session.session_id || "Review")}</strong>
                <span>${escapeHtml(`${session.duration_minutes || 0} min · ${session.focus_area || "review"}`)}</span>
              </header>
              <small>${escapeHtml(session.source_file || "")}</small>
              <div class="daily-log-columns">
                ${renderLogColumn("나쁜 습관/약점", [
                  ...(session.weak_points || []).map((item) => `${humanizeEnglishSignal(item.area)} · ${item.evidence || ""}`),
                  ...(session.habit_patterns || []).map((item) => `${humanizeEnglishSignal(item.habit)} · ${item.evidence || ""}`),
                ].slice(0, 6))}
                ${renderLogColumn("틀린 표현", (session.corrections || []).map((item) => `${item.user_said || "Correction"} -> ${item.better || ""}`))}
                ${renderLogColumn("배운 표현", (session.learned_items || []).map((item) => `${item.item || "Expression"}${item.meaning ? ` · ${item.meaning}` : ""}`))}
              </div>
            </article>
          `).join("")}
        </div>
      `;
      return details;
    }),
  );
  if (englishDailyLogPager) {
    englishDailyLogPager.innerHTML = `
      <button class="button-ghost" type="button" data-daily-log-page="prev" ${englishDailyLogPage === 0 ? "disabled" : ""}>Prev</button>
      <div class="daily-log-dots">
        ${Array.from({ length: pageCount }, (_item, index) => `<button type="button" class="${index === englishDailyLogPage ? "active" : ""}" data-daily-log-page="${index}" aria-label="Daily log page ${index + 1}"></button>`).join("")}
      </div>
      <span>${englishDailyLogPage + 1} / ${pageCount}</span>
      <button class="button-ghost" type="button" data-daily-log-page="next" ${englishDailyLogPage >= pageCount - 1 ? "disabled" : ""}>Next</button>
    `;
    englishDailyLogPager.onclick = (event) => {
      const button = event.target.closest("[data-daily-log-page]");
      if (!button) return;
      const action = button.dataset.dailyLogPage;
      if (action === "prev") englishDailyLogPage = Math.max(0, englishDailyLogPage - 1);
      else if (action === "next") englishDailyLogPage = Math.min(pageCount - 1, englishDailyLogPage + 1);
      else englishDailyLogPage = Number(action) || 0;
      renderDailyReviewLog(days);
    };
  }
}

function renderEnglishDecisionHeader({ summary = {}, importStatus = {}, issueActionPlan = [], nextActions = [], reviews = [] }) {
  if (!englishDecisionHeader) return;
  const topIssue = issueActionPlan.find((item) => item.severity === "high" || item.status === "persistent") || issueActionPlan[0];
  const topAction = nextActions[0];
  const latestReview = reviews[0];
  const issueTitle = topIssue?.title || topAction?.action || "오늘은 새 리뷰를 먼저 확인";
  const example = topIssue?.example?.user_said
    ? `${topIssue.example.user_said}${topIssue.example.better ? ` -> ${topIssue.example.better}` : ""}`
    : latestReview?.transcript_summary || "아직 대표 예시가 없습니다.";
  const drill = topIssue?.drill || topIssue?.how_to_fix || topAction?.action || "5분짜리 짧은 복습 1개만 선택";
  const freshness = `${summary.reviewed_session_count || 0} reviews · ${summary.study_minutes || 0} min · ${importStatus.status || "unknown"}`;
  englishDecisionHeader.innerHTML = `
    <article class="english-decision-card primary">
      <span>Top Issue</span>
      <strong>${escapeHtml(issueTitle)}</strong>
      <p>${escapeHtml(example)}</p>
    </article>
    <article class="english-decision-card">
      <span>1 Drill</span>
      <strong>${escapeHtml(drill)}</strong>
      <p>${escapeHtml(freshness)}</p>
    </article>
  `;
}

function renderEnglishReviewFileLoadStatus(reviewFileStats = {}, reviewFileTimeline = [], learningContinuity = {}) {
  const statusLabelMap = {
    ok: "Ready",
    warning: "Needs Review",
    error: "Import Error",
    empty: "No Files",
  };
  if (englishReviewFileStats) {
    const importStatus = reviewFileStats.import_status || {};
    const statusLabel = statusLabelMap[importStatus.status] || "Unknown";
    const issueCount = Number(importStatus.file_error_count || 0) + Number(importStatus.validation_error_count || 0);
    const total = Number(reviewFileStats.total_files || 0);
    const analyzed = Number(reviewFileStats.analyzed_files || 0);
    const pending = Number(reviewFileStats.pending_files || 0);
    const minutes = Number(reviewFileStats.total_study_minutes || 0);
    englishReviewFileStats.innerHTML = `
      <span class="chip status">Inbox ${escapeHtml(statusLabel)} · imported ${Number(importStatus.imported_count || 0)} · errors ${issueCount} · warnings ${Number(importStatus.validation_warning_count || 0)}</span>
      <span class="chip">총 파일 ${total}</span>
      <span class="chip">분석 완료 ${analyzed}</span>
      <span class="chip">분석 대기 ${pending}</span>
      <span class="chip">총 대화 시간 ${minutes}분</span>
    `;
  }
  if (!englishReviewFileGraph) return;
  if (!reviewFileTimeline.length) {
    englishReviewFileGraph.innerHTML = '<p class="empty">No review load timeline yet.</p>';
    return;
  }
  const maxLoaded = Math.max(...reviewFileTimeline.map((item) => Number(item.loaded_count || 0)), 1);
  const continuitySummary = learningContinuity?.summary
    ? `${learningContinuity.summary} · ${learningContinuity.current_streak_days || 0} day streak · avg ${learningContinuity.average_minutes_per_active_day || 0} min`
    : "";
  englishReviewFileGraph.innerHTML = `
    <div class="english-review-file-legend">
      <span><i class="dot analyzed"></i>로드+분석 완료</span>
      <span><i class="dot loaded_only"></i>로드만 완료(분석 대기)</span>
    </div>
    <div class="english-review-file-vbars" aria-label="날짜별 리뷰 파일 로드/분석 상태">
      ${reviewFileTimeline.map((item) => {
    const loaded = Number(item.loaded_count || 0);
    const analyzed = Number(item.analyzed_count || 0);
    const pending = Number(item.pending_count || Math.max(0, loaded - analyzed));
    const analyzedPct = Math.max(0, Math.min(100, Math.round((analyzed / maxLoaded) * 100)));
    const pendingPct = Math.max(0, Math.min(100 - analyzedPct, Math.round((pending / maxLoaded) * 100)));
    const emptyPct = Math.max(0, 100 - analyzedPct - pendingPct);
    const rawDate = String(item.date || "");
    const day = rawDate === "unknown" ? "미분류" : rawDate.slice(5);
    return `
      <div class="english-review-file-day">
        <div class="bar" aria-label="${escapeHtml(`${item.date} loaded ${loaded} analyzed ${analyzed}`)}">
          <span class="segment analyzed" style="height:${analyzedPct}%;"></span>
          ${pendingPct > 0 ? `<span class="segment loaded_only" style="height:${pendingPct}%;"></span>` : ""}
          ${emptyPct > 0 ? `<span class="segment empty" style="height:${emptyPct}%;"></span>` : ""}
          <span class="bar-count">${loaded}</span>
        </div>
        <small>${escapeHtml(day)}</small>
      </div>
    `;
  }).join("")}
    </div>
    ${continuitySummary ? `<p class="english-review-meta">${escapeHtml(continuitySummary)}</p>` : ""}
  `;
}

function renderEnglishDashboard(payload = {}) {
  const summary = payload.summary || {};
  const summaryMetrics = payload.summary_metrics || [];
  const importStatus = payload.import_status || {};
  const learnedItems = payload.learned_items || [];
  const corrections = payload.corrections || [];
  const nextActions = payload.next_actions || [];
  const reviewCards = payload.review_cards || [];
  const reviewCardQueue = payload.review_card_queue || [];
  const reviews = payload.gpts_reviews || [];
  const habitFocus = payload.habit_focus || summary.top_habit_tags || [];
  const habitPatterns = payload.habit_patterns || [];
  const weeklySummary = payload.weekly_summary || {};
  const habitRecommendations = payload.habit_recommendations || [];
  const learningProfile = payload.learning_profile || {};
  const studySchedule = payload.study_schedule || {};
  const performanceMetrics = payload.performance_metrics || {};
  const issueActionPlan = payload.issue_action_plan || [];
  const issueTracker = payload.issue_tracker || {};
  const preStudyContext = payload.pre_study_context || {};
  const learningContinuity = payload.learning_continuity || {};
  const dailyReviewLog = payload.daily_review_log || [];
  const issueProgressSummary = payload.issue_progress_summary || {};
  const dashboardValidationAgent = payload.dashboard_validation_agent || {};
  const reviewFileStats = payload.review_file_stats || {};
  const reviewFileTimeline = payload.review_file_timeline || [];

  renderEnglishDecisionHeader({ summary, importStatus, issueActionPlan, nextActions, reviews });

  const issueItems = [
    ...(importStatus.file_errors || []).map((item) => `${item.file}: ${item.error}`),
    ...(importStatus.validation_errors || []).map((item) => `${item.file}: ${(item.errors || []).join(", ")}`),
    ...(importStatus.validation_warnings || []).map((item) => `${item.file}: ${(item.warnings || []).join(", ")}`),
  ].slice(0, 3);
  renderEnglishReviewFileLoadStatus({ ...reviewFileStats, import_status: importStatus }, reviewFileTimeline, learningContinuity);
  setEnglishSectionVisible(englishSummary, false);
  if (englishImportDetails && englishImportDetailList) {
    englishImportDetails.hidden = !issueItems.length;
    englishImportDetailList.innerHTML = issueItems.map((item) => `<li>${escapeHtml(item)}</li>`).join("");
  }

  if (englishAgentInterpretation) {
    englishAgentInterpretation.textContent = learningProfile.agent_interpretation || "누적 학습 데이터가 아직 충분하지 않습니다.";
  }

  renderValidationAgent(dashboardValidationAgent);

  renderEnglishList(
    englishProgression,
    [
      {
        title: `${studySchedule.window?.start_date || "-"} - ${studySchedule.window?.end_date || "-"}`,
        meta: `${studySchedule.active_day_count || 0} active days`,
        detail: `${studySchedule.session_count || 0} sessions · ${studySchedule.study_minutes || 0} min · cadence ${studySchedule.cadence || "unknown"}`,
      },
      {
        title: "Focus Distribution",
        meta: studySchedule.most_repeated_focus ? `${studySchedule.most_repeated_focus.name} ${studySchedule.most_repeated_focus.count}x` : "none",
        detail: (studySchedule.focus_distribution || []).map((item) => `${item.name} ${item.count}`).join(" · "),
      },
      ...((studySchedule.recommendations || []).slice(0, 2).map((item) => ({
        title: "Schedule Adjustment",
        meta: "guide",
        detail: item,
      }))),
    ],
    (item) => `
      <header>
        <strong>${escapeHtml(item.title)}</strong>
        <span>${escapeHtml(item.meta)}</span>
      </header>
      <p>${escapeHtml(item.detail || "")}</p>
    `,
    "No study schedule data yet.",
  );
  setEnglishSectionVisible(englishProgression, true);

  renderEnglishList(
    englishPerformanceMetrics,
    (performanceMetrics.priority_metrics || performanceMetrics.metrics || []).slice(0, 6),
    (item) => `
      <header>
        <strong>${escapeHtml(item.label || item.category)}</strong>
        <span>${escapeHtml(`${item.score ?? "-"} · ${item.status || ""}`)}</span>
      </header>
      <p>${escapeHtml(item.interpretation || "")}</p>
      <small>${escapeHtml(`${item.observation_count || 0} observations · recent ${item.recent_observation_count || 0} · ${item.score_source || ""}`)}</small>
      ${renderMetricEvidence(item)}
    `,
    "No performance metrics yet.",
  );
  setEnglishSectionVisible(englishPerformanceMetrics, true);

  renderIssueProgress(issueProgressSummary, issueActionPlan);
  setEnglishSectionVisible(englishIssueTracker, true);

  if (englishPreStudyContext) {
    englishPreStudyContext.textContent = preStudyContext.prompt || "No pre-study context yet.";
  }

  renderDailyReviewLog(dailyReviewLog);

  const weeklyItems = [
    {
      title: `${weeklySummary.window?.start_date || "-"} - ${weeklySummary.window?.end_date || "-"}`,
      meta: `${weeklySummary.study_minutes || 0} min`,
      detail: `${weeklySummary.active_day_count || 0} active days · ${weeklySummary.review_session_count || 0} GPTs reviews · ${weeklySummary.activity_session_count || 0} activity logs`,
    },
    weeklySummary.correction_goal
      ? {
        title: weeklySummary.correction_goal.title || "Correction Goal",
        meta: "goal",
        detail: weeklySummary.correction_goal.recommendation || weeklySummary.correction_goal.practice || "",
      }
      : null,
  ].filter(Boolean);

  const hasWeekly = renderEnglishList(
    englishWeeklySummary,
    weeklyItems,
    (item) => `
      <header>
        <strong>${escapeHtml(item.title)}</strong>
        <span>${escapeHtml(item.meta)}</span>
      </header>
      <p>${escapeHtml(item.detail)}</p>
    `,
    "No weekly English data yet.",
  );
  setEnglishSectionVisible(englishWeeklySummary, hasWeekly);

  const hasHabitRecommendations = renderEnglishList(
    englishHabitRecommendations,
    habitRecommendations.slice(0, 3),
    (item) => `
      <header>
        <strong>${escapeHtml(humanizeEnglishSignal(item.habit || item.title))}</strong>
        <span>${item.duration_minutes || 5} min</span>
      </header>
      <p>${escapeHtml(item.recommendation || "")}</p>
      <small>${escapeHtml(item.practice || "")}</small>
    `,
    "No habit recommendations yet.",
  );
  setEnglishSectionVisible(englishHabitRecommendations, hasHabitRecommendations && habitRecommendations.length > 0);

  const habitItems = habitFocus.length
    ? habitFocus
    : habitPatterns.map((item) => ({ name: item.habit, count: item.severity || "" })).filter((item) => item.name);

  const hasHabits = renderEnglishList(
    englishHabits,
    habitItems,
    (item) => `
      <header>
        <strong>${escapeHtml(humanizeEnglishSignal(item.name || item.habit))}</strong>
        <span>${escapeHtml(String(item.count || item.severity || ""))}</span>
      </header>
      ${item.evidence ? `<p>${escapeHtml(item.evidence)}</p>` : ""}
      ${item.suggestion ? `<small>${escapeHtml(item.suggestion)}</small>` : ""}
    `,
    "No habit signals yet.",
  );
  setEnglishSectionVisible(englishHabits, hasHabits && habitItems.length > 0);

  const hasNextActions = renderEnglishList(
    englishNextActions,
    nextActions.slice(0, 5),
    (item) => `
      <header>
        <strong>${escapeHtml(item.action || "Practice")}</strong>
        <span>${escapeHtml(item.priority || "")}</span>
      </header>
      <p>${item.duration_minutes ? `${item.duration_minutes} min` : "short practice"}</p>
    `,
    "No next actions yet.",
  );
  setEnglishSectionVisible(englishNextActions, hasNextActions && nextActions.length > 0);

  const hasLearned = renderEnglishList(
    englishLearnedItems,
    learnedItems.slice(0, 5),
    (item) => {
      const detail = item.meaning_ko || item.example || item.context || "";
      return `
        <header>
          <strong>${escapeHtml(item.item || item.type || "Learned item")}</strong>
          <span>${escapeHtml(item.type || "")}</span>
        </header>
        ${detail ? `<p>${escapeHtml(detail)}</p>` : ""}
      `;
    },
    "No learned items yet.",
  );
  setEnglishSectionVisible(englishLearnedItems, hasLearned && learnedItems.length > 0);

  const hasCorrections = renderEnglishList(
    englishCorrections,
    corrections.slice(0, 10),
    (item) => `
      <header>
        <strong>${escapeHtml(correctionOriginal(item) || "Correction")}</strong>
        <span>${escapeHtml(correctionCategory(item))}</span>
      </header>
      <p class="correction-arrow">→ ${escapeHtml(correctionBetter(item) || "Needs review")}</p>
      ${item.reason_ko ? `<small>${escapeHtml(item.reason_ko)}</small>` : ""}
    `,
    "No corrections yet.",
  );
  setEnglishSectionVisible(englishCorrections, hasCorrections && corrections.length > 0);

  const reviewCardItems = reviewCardQueue.length ? reviewCardQueue : reviewCards;
  const hasReviewCards = renderEnglishList(
    englishReviewCards,
    reviewCardItems.slice(0, 10),
    (item) => `
      <header>
        <strong>${escapeHtml(reviewCardFront(item))}</strong>
        <span>${escapeHtml(item.status || (item.tags || []).slice(0, 2).join(", "))}</span>
      </header>
      <p>${escapeHtml(item.back || "")}</p>
    `,
    "No review cards yet.",
  );
  setEnglishSectionVisible(englishReviewCards, hasReviewCards && reviewCardItems.length > 0);

  const hasReviews = renderEnglishList(
    englishReviews,
    reviews.slice(0, 6),
    (item) => `
      <header>
        <strong>${escapeHtml(item.conversation_title || item.focus_area || "GPTs Review")}</strong>
        <span>${item.duration_minutes || 0} min</span>
      </header>
      <p>${escapeHtml(item.transcript_summary || item.user_goal || item.source_file || "")}</p>
      <small>${escapeHtml([item.focus_area, item.level].filter(Boolean).join(" · "))}</small>
    `,
    "No GPTs review files yet.",
  );
  setEnglishSectionVisible(englishReviews, hasReviews && reviews.length > 0);
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
      const needsApproval = Boolean(item.approval_required);
      action.innerHTML = `
        <header>
          <h3>${item.title}</h3>
          <span class="badge">${item.status}</span>
        </header>
        <p>${needsApproval ? "Draft only · Hermes Worker approval endpoint pending" : "No approval required"}</p>
        <div class="action-controls" aria-label="Action review controls">
          <button class="button-secondary" type="button" disabled title="Approval queue endpoint is not connected yet">Approve</button>
          <button class="button-secondary" type="button" disabled title="Approval queue endpoint is not connected yet">Defer</button>
          <button class="button-secondary" type="button" disabled title="Approval queue endpoint is not connected yet">Reject</button>
        </div>
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

function installInputFocusMode() {
  const focusSelector = 'input:not([type="hidden"]), select, textarea';
  let activeSurface = null;
  const surfaceSelector = [
    "dialog[open]",
    ".quick-dialog-panel",
    ".workout-dialog-panel",
    ".exercise-dialog-content",
    ".ai-work-dialog-panel",
    ".auth-panel",
    ".section",
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

function readInputHistory() {
  try {
    const records = JSON.parse(localStorage.getItem(NOMAD_INPUT_HISTORY_STORAGE_KEY) || "[]");
    return Array.isArray(records) ? records : [];
  } catch {
    return [];
  }
}

function writeInputHistory(records = []) {
  localStorage.setItem(NOMAD_INPUT_HISTORY_STORAGE_KEY, JSON.stringify(records.slice(-80)));
}

function deleteInputHistoryRecord(historyId) {
  writeInputHistory(readInputHistory().filter((item) => item.id !== historyId && item.history_id !== historyId));
}

function readPendingHealthStore() {
  try {
    const records = JSON.parse(localStorage.getItem(NOMAD_PENDING_HEALTH_STORAGE_KEY) || "{}");
    return {
      workouts: Array.isArray(records.workouts) ? records.workouts : [],
      activities: Array.isArray(records.activities) ? records.activities : [],
    };
  } catch {
    return { workouts: [], activities: [] };
  }
}

function writePendingHealthStore(store = {}) {
  localStorage.setItem(NOMAD_PENDING_HEALTH_STORAGE_KEY, JSON.stringify({
    workouts: uniqueWorkoutSessions(store.workouts || []).slice(-80),
    activities: uniqueHealthActivities(store.activities || []).slice(-80),
  }));
}

function appendPendingHealthItems(workouts = [], activities = []) {
  if (!workouts.length && !activities.length) return;
  const store = readPendingHealthStore();
  writePendingHealthStore({
    workouts: [...store.workouts, ...workouts],
    activities: [...store.activities, ...activities],
  });
}

function mergePendingHealthItems(workouts = [], activities = []) {
  const store = readPendingHealthStore();
  return {
    workouts: uniqueWorkoutSessions([...(workouts || []), ...store.workouts]),
    activities: uniqueHealthActivities([...(activities || []), ...store.activities]),
  };
}

function isPendingHealthItem(item = {}) {
  const id = String(item.id || item.source || "");
  return Boolean(item.pending_analysis || item.source === "pending_quick_save" || id.startsWith("pending_"));
}

function writePendingHealthFromMemory() {
  writePendingHealthStore({
    workouts: workoutHistorySessions.filter(isPendingHealthItem),
    activities: latestHealthSessions.filter(isPendingHealthItem),
  });
}

function removePendingHealthItems(workoutIds = [], activityIds = []) {
  const workoutSet = new Set(workoutIds.filter(Boolean));
  const activitySet = new Set(activityIds.filter(Boolean));
  if (!workoutSet.size && !activitySet.size) return;
  const store = readPendingHealthStore();
  writePendingHealthStore({
    workouts: store.workouts.filter((item) => !workoutSet.has(item.id)),
    activities: store.activities.filter((item) => !activitySet.has(item.id) && !activitySet.has(item.source)),
  });
}

function appendInputHistory(record = {}) {
  const stay = currentStayContext();
  const item = {
    id: `input_${Date.now().toString(36)}`,
    captured_at: new Date().toISOString(),
    status: "saved",
    raw_content: record.raw_content || record.detail || "Saved input",
    linked_agents: record.linked_agents || [],
    stay,
    ...record,
  };
  const records = [...readInputHistory(), item];
  writeInputHistory(records);
  return item;
}

function inputHistoryItems(captures = [], activityHistory = null) {
  const activityDates = new Set((activityHistory?.sessions || [])
    .filter((session) => session.status !== "ignored")
    .map((session) => `${session.date}:${session.area || session.area_label || ""}`));
  const workoutDates = new Set(workoutHistorySessions
    .filter((session) => session.status !== "ignored")
    .map((session) => session.date || session.started_at?.slice(0, 10))
    .filter(Boolean));
  const resultSubmissionIds = [
    ...workoutHistorySessions,
    ...((activityHistory?.sessions || [])),
    ...(captures || []),
  ]
    .map((item) => item.client_submission_id || item.metadata?.client_submission_id || item.parsed_result?.client_submission_id)
    .filter(Boolean);
  const healthResultDates = new Set([
    ...workoutHistorySessions
      .filter((session) => session.status !== "ignored")
      .map((session) => session.date || session.started_at?.slice(0, 10)),
    ...((activityHistory?.sessions || [])
      .filter((session) => session.status !== "ignored")
      .filter((session) => session.area === "health" || session.area_label === "Health")
      .map((session) => session.date)),
  ].filter(Boolean));
  return [
    ...workoutHistorySessions.map(normalizeWorkoutHistoryItem),
    ...((activityHistory?.sessions || []).map(normalizeActivityHistoryItem)),
    ...(captures || []).map((item) => normalizeCaptureHistoryItem(item, activityDates, workoutDates)),
    ...readInputHistory().map((item) => normalizeLocalInputHistoryItem(item, resultSubmissionIds, healthResultDates)),
  ];
}

function setCapturePeriodControls(defaultMonth) {
  if (!captureYearFilter || !captureMonthFilter) return;
  const currentYear = Number((defaultMonth || todayLocalDateValue()).slice(0, 4));
  const selectedYear = selectedHistoryMonth.slice(0, 4) || String(currentYear);
  const selectedMonth = selectedHistoryMonth.slice(5, 7) || (defaultMonth || todayLocalDateValue()).slice(5, 7);
  setSelectOptions(
    captureYearFilter,
    [currentYear - 1, currentYear, currentYear + 1].map((year) => ({ value: String(year), label: `${year}년` })),
    selectedYear,
  );
  setSelectOptions(
    captureMonthFilter,
    Array.from({ length: 12 }, (_, index) => {
      const month = String(index + 1).padStart(2, "0");
      return { value: month, label: `${index + 1}월` };
    }),
    selectedMonth,
  );
}

function selectedCaptureMonth(fallbackDate = todayLocalDateValue()) {
  const fallbackMonth = fallbackDate.slice(0, 7);
  if (!selectedHistoryMonth) selectedHistoryMonth = fallbackMonth;
  return selectedHistoryMonth;
}

function historyRecordMatchesMonth(record = {}, month = "") {
  const candidates = [
    record.date,
    record.applied_date,
    record.created_at,
    record.captured_at,
    record.updated_at,
  ];
  return candidates.some((value) => String(value || "").startsWith(month));
}

function syncSelectedHistoryMonthFromControls() {
  const year = captureYearFilter?.value || selectedHistoryMonth.slice(0, 4) || todayLocalDateValue().slice(0, 4);
  const month = captureMonthFilter?.value || selectedHistoryMonth.slice(5, 7) || todayLocalDateValue().slice(5, 7);
  selectedHistoryMonth = `${year}-${month}`;
}

function normalizeCaptureHistoryItem(item = {}, activityDates = new Set(), workoutDates = new Set()) {
  const raw = item.raw_content || "";
  const agents = item.linked_agents || [];
  const isActivityShadow = raw.startsWith("근력운동 기록:")
    && agents.includes("nomad-health")
    && (activityDates.has(`${item.date}:health`) || workoutDates.has(item.date));
  return {
    ...item,
    history_kind: "capture",
    history_id: item.id,
    title: captureHistoryTitle(item),
    body: raw,
    applied_date: captureAppliedDate(item),
    applied_area: captureAgentLabels(item),
    input_at: item.created_at || item.captured_at,
    shadow_of_result: isActivityShadow,
  };
}

function healthHistoryTypeLabel(item = {}) {
  if (item.history_kind === "workout" || item.type === "strength" || item.activity_type === "strength") {
    return "헬스";
  }
  const type = item.activity_type || item.subcategory || item.metadata?.exercise_type || "";
  return type ? healthTypeLabel(type) : "운동";
}

function historyAreaLabel(item = {}, fallbackArea = "") {
  const area = fallbackArea || item.area_label || item.area || "";
  const isHealth = area === "Health"
    || area === "health"
    || item.area === "health"
    || (item.linked_agents || []).includes("nomad-health");
  if (!isHealth) {
    return area || captureAgentLabels(item);
  }
  return `Health · ${healthHistoryTypeLabel(item)}`;
}

function normalizeActivityHistoryItem(item = {}) {
  const area = item.area_label || item.area || "Activity";
  const detail = item.detail || item.subcategory || area;
  const appliedArea = historyAreaLabel(item, area);
  return {
    ...item,
    history_kind: "activity",
    history_id: item.id,
    raw_content: detail,
    title: `${formatHistoryDate(item.created_at || item.updated_at)} → ${item.date || "-"} · ${appliedArea}`,
    body: detail,
    applied_date: item.date || "-",
    applied_area: appliedArea,
    input_at: item.created_at || item.updated_at,
    linked_agents: item.linked_agents || [],
  };
}

function normalizeWorkoutHistoryItem(item = {}) {
  const entries = reindexStrengthEntries(item.entries || []);
  const summary = summarizeWorkoutHistoryEntries(entries);
  return {
    ...item,
    history_kind: "workout",
    history_id: item.id,
    raw_content: summary || item.note || "헬스 루틴",
    title: `${formatHistoryDate(item.created_at || item.started_at)} → ${item.date || "-"} · Health · 헬스`,
    body: summary || item.note || "헬스 루틴",
    applied_date: item.date || item.started_at?.slice(0, 10) || "-",
    applied_area: "Health · 헬스",
    area_label: "Health",
    input_at: item.created_at || item.started_at,
    linked_agents: ["nomad-health"],
    duration_minutes: item.duration_minutes,
    entries,
  };
}

function normalizeLocalInputHistoryItem(item = {}, resultSubmissionIds = [], healthResultDates = new Set()) {
  const agents = item.linked_agents || [];
  const clientSubmissionId = item.client_submission_id || item.metadata?.client_submission_id;
  const isHealthReceipt = agents.includes("nomad-health");
  const isShadowedBySubmission = clientSubmissionId
    && resultSubmissionIds.some((id) => id === clientSubmissionId || String(id).startsWith(`${clientSubmissionId}_`));
  const isLegacyHealthShadow = !clientSubmissionId && isHealthReceipt && healthResultDates.has(captureAppliedDate(item));
  return {
    ...item,
    history_kind: "local_pending",
    history_id: item.id,
    title: captureHistoryTitle(item),
    body: item.raw_content || "",
    applied_date: captureAppliedDate(item),
    applied_area: captureAgentLabels(item),
    input_at: item.captured_at || item.created_at,
    shadow_of_result: Boolean(isShadowedBySubmission || isLegacyHealthShadow),
  };
}

function captureViewStatus(item = {}) {
  const status = item.status || "unknown";
  if (["ignored", "canceled", "cancelled"].includes(status)) {
    return { key: "canceled", label: "취소됨" };
  }
  if (["pending", "queued", "saved"].includes(status)) {
    return { key: "pending", label: "반영 대기" };
  }
  if (item.review_required || ["review", "needs_review"].includes(status)) {
    return { key: "review", label: "확인 필요" };
  }
  if (["parsed", "applied", "completed"].includes(status)) {
    return { key: "applied", label: "반영됨" };
  }
  return { key: "review", label: status };
}

function captureAgentLabels(item = {}) {
  if (item.applied_area) return item.applied_area;
  if (item.area_label) return item.area_label;
  if (item.area) return item.area;
  return (item.linked_agents || [])
    .map((agent) => agent.replace("nomad-", ""))
    .join(", ") || "미분류";
}

function captureAppliedDate(item = {}) {
  return item.date || item.applied_date || item.created_at?.slice(0, 10) || item.captured_at?.slice(0, 10) || "-";
}

function captureInputTime(item = {}) {
  return formatSyncTime(item.input_at || item.created_at || item.captured_at || item.updated_at);
}

function formatHistoryDate(value) {
  return formatSyncTime(value);
}

function captureHistoryTitle(item = {}) {
  return `${formatHistoryDate(item.created_at || item.captured_at || item.input_at)} → ${captureAppliedDate(item)} · ${captureAgentLabels(item)}`;
}

function captureHistoryBody(item = {}) {
  return item.body || item.raw_content || item.detail || item.note || "";
}

function captureByHistoryId(historyId) {
  return captureHistoryState.find((item) => item.history_id === historyId || item.id === historyId);
}

function captureDurationMinutes(item = {}) {
  return item.duration_minutes ?? item.parsed_result?.activity?.duration_minutes ?? null;
}

function summarizeWorkoutHistoryEntries(entries = []) {
  const groups = groupEntriesByExercise(entries);
  return Object.entries(groups).map(([exercise, items]) => {
    const label = exerciseLabel(items[0]?.muscle_group || "other", exercise);
    const setLines = items.map(formatSetLine).join(", ");
    return `${label}: ${setLines}`;
  }).join(" / ");
}

function formatHistoryAppliedDate(value = "") {
  const [, month, day] = String(value || "").split("-");
  if (!month || !day) return value || "날짜 없음";
  return `${Number(month)}월 ${Number(day)}일`;
}

function captureWrittenDate(item = {}) {
  const value = item.input_at || item.created_at || item.captured_at || item.updated_at;
  return formatSyncTime(value);
}

function groupHistoryByAppliedDate(items = []) {
  return items.reduce((groups, item) => {
    const date = captureAppliedDate(item);
    if (!groups.has(date)) groups.set(date, []);
    groups.get(date).push(item);
    return groups;
  }, new Map());
}

function filteredCaptureItems(items = []) {
  const mode = captureStatusFilter?.value || "applied";
  return items.filter((item) => {
    const viewStatus = captureViewStatus(item).key;
    const localPending = item.history_kind === "local_pending" && ["pending", "saved", "queued"].includes(item.status || "");
    if (mode === "all") return true;
    if (mode === "applied") return (viewStatus === "applied" || localPending) && !item.shadow_of_result;
    if (mode === "canceled") return viewStatus === "canceled";
    if (mode === "review") return (viewStatus === "review" || viewStatus === "pending") && !item.shadow_of_result;
    return true;
  });
}

function payloadHistorySummary(payloads = [], area = selectedRadioValue("area")) {
  if (area === "health") {
    const details = payloads
      .map((payload) => `${healthTypeLabel(payload.subcategory || payload.metadata?.exercise_type || "other")}: ${payload.detail || payload.subcategory}`)
      .filter(Boolean);
    return details.length ? `Health: ${details.join(" · ")}` : "Health saved";
  }
  const payload = payloads[0] || {};
  return payload.detail || payload.subcategory || area || "Saved input";
}

function optimisticHealthActivityFromPayload(payload = {}) {
  const now = new Date().toISOString();
  return {
    id: `pending_activity_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 7)}`,
    source: "pending_quick_save",
    status: "completed",
    date: payload.date || now.slice(0, 10),
    activity_type: payload.subcategory || payload.metadata?.exercise_type || "other",
    subcategory: payload.subcategory || payload.metadata?.exercise_type || "other",
    duration_minutes: Number(payload.duration_minutes || 0),
    detail: payload.detail || payload.subcategory || "운동",
    metadata: payload.metadata || {},
    client_submission_id: payload.client_submission_id || payload.metadata?.client_submission_id || null,
    pending_analysis: true,
    stay: payload.metadata?.stay || currentStayContext(),
  };
}

function optimisticWorkoutFromDraft(item = {}) {
  if (!item?.strength_entries?.length) return null;
  const now = new Date().toISOString();
  return {
    id: `pending_workout_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 7)}`,
    source: "pending_quick_save",
    status: "completed",
    date: selectedActivityDate() || now.slice(0, 10),
    started_at: now,
    duration_minutes: Number(item.duration_minutes || 0),
    activity_type: "strength",
    muscle_group: item.strength_entries[0]?.muscle_group || "full_body",
    entries: reindexStrengthEntries(item.strength_entries || []),
    note: item.strength_note || item.detail || "",
    client_submission_id: item.client_submission_id || null,
    pending_analysis: true,
    stay: currentStayContext(),
  };
}

function applyOptimisticHealthSave(payloads = [], strengthDrafts = []) {
  const workoutItems = strengthDrafts
    .map(optimisticWorkoutFromDraft)
    .filter(Boolean);
  const workoutSourceKeys = new Set(strengthDrafts.map((item) => item.source_workout_session_id).filter(Boolean));
  const activityItems = payloads
    .filter((payload) => !isStrengthPayload(payload))
    .filter((payload) => !workoutSourceKeys.has(payload.metadata?.source_workout_session_id))
    .map(optimisticHealthActivityFromPayload);
  appendPendingHealthItems(workoutItems, activityItems);
  workoutHistorySessions = [...workoutItems, ...workoutHistorySessions];
  latestHealthSessions = [...activityItems, ...latestHealthSessions];
  renderRoutineCards(workoutHistorySessions, latestHealthSessions);
}

function renderCaptures(items = captureHistoryState) {
  captureHistoryState = items || [];
  const filteredItems = filteredCaptureItems(captureHistoryState);
  if (!filteredItems.length) {
    capturesList.innerHTML = '<p class="empty">No captures yet.</p>';
    if (captureStatus) {
      captureStatus.textContent = `Input history ${captureHistoryState.length}개 중 현재 보기 조건에 맞는 항목이 없습니다.`;
    }
    return;
  }

  if (captureStatus) {
    const appliedActivityCount = captureHistoryState.filter((item) => item.history_kind === "activity" && captureViewStatus(item).key === "applied").length;
    const matchNote = mainActivityHistoryCount
      ? ` · 활동 집계 ${appliedActivityCount}/${mainActivityHistoryCount}개 매칭`
      : "";
    captureStatus.textContent = `Input history ${captureHistoryState.length}개 중 ${filteredItems.length}개 표시${matchNote}`;
  }

  const groups = [...groupHistoryByAppliedDate(filteredItems).entries()]
    .sort(([left], [right]) => right.localeCompare(left));
  const nodes = [];
  groups.forEach(([date, groupItems]) => {
    const divider = document.createElement("div");
    divider.className = "history-date-divider";
    divider.innerHTML = `<span>${escapeHtml(formatHistoryAppliedDate(date))}</span>`;
    nodes.push(divider);
    groupItems
      .slice()
      .sort((a, b) => String(b.input_at || b.created_at || "").localeCompare(String(a.input_at || a.created_at || "")))
      .forEach((item) => {
      const row = document.createElement("article");
      const status = captureViewStatus(item);
      row.className = status.key === "canceled" ? "capture-item ignored" : status.key === "review" ? "capture-item needs-review" : "capture-item";
      const agents = captureAgentLabels(item);
      const historyId = item.history_id || item.id || "";
      const duration = captureDurationMinutes(item);
      row.innerHTML = `
        <div>
          <header>
            <strong>${escapeHtml(agents)}</strong>
            <span>${escapeHtml(captureWrittenDate(item))}</span>
            <span>${duration ? escapeHtml(formatActivityDuration(duration)) : "시간 미지정"}</span>
            <span class="badge">${status.label}</span>
          </header>
          <p class="capture-body-preview">${escapeHtml(captureHistoryBody(item))}</p>
        </div>
        <div class="capture-history-actions">
          <button class="button-secondary capture-view" type="button" data-history-id="${escapeHtml(historyId)}">디테일 & 수정</button>
        </div>
      `;
      nodes.push(row);
    });
  });
  capturesList.replaceChildren(...nodes);
}

function openCaptureDetail(historyId) {
  const item = captureByHistoryId(historyId);
  if (!item || !captureDetailDialog || !captureDetailContent) return;
  const status = captureViewStatus(item);
  const duration = captureDurationMinutes(item);
  captureDetailTitle.textContent = `${captureAgentLabels(item)} · ${formatHistoryAppliedDate(captureAppliedDate(item))}`;
  captureDetailContent.innerHTML = `
    <div class="capture-edit-form" data-history-id="${escapeHtml(historyId)}">
      <label>
        <span>내용</span>
        <textarea id="capture-edit-content" rows="7">${escapeHtml(captureHistoryBody(item) || "")}</textarea>
      </label>
      <div class="capture-edit-grid">
        <label>
          <span>활동 시간</span>
          <input id="capture-edit-duration" type="number" min="0" step="5" value="${duration ?? ""}" placeholder="분" />
        </label>
        <label>
          <span>적용일</span>
          <input id="capture-edit-date" type="date" value="${escapeHtml(captureAppliedDate(item))}" />
        </label>
        <label>
          <span>반영 상태</span>
          <select id="capture-edit-status">
            <option value="applied" ${status.key === "applied" ? "selected" : ""}>반영</option>
            <option value="canceled" ${status.key === "canceled" ? "selected" : ""}>미반영</option>
          </select>
        </label>
      </div>
      <div class="capture-edit-actions">
        <button class="button-secondary" type="button" data-capture-detail-close>닫기</button>
        <button class="button-secondary danger-action" type="button" data-capture-detail-delete>원장 삭제</button>
        <button type="button" data-capture-detail-save>저장</button>
      </div>
    </div>
  `;
  captureDetailDialog.showModal?.();
}

function saveCaptureDetail(historyId) {
  const item = captureByHistoryId(historyId);
  if (!item) return Promise.resolve();
  const content = captureDetailContent.querySelector("#capture-edit-content")?.value || "";
  const date = captureDetailContent.querySelector("#capture-edit-date")?.value || captureAppliedDate(item);
  const duration = Number(captureDetailContent.querySelector("#capture-edit-duration")?.value || captureDurationMinutes(item) || 0);
  const statusMode = captureDetailContent.querySelector("#capture-edit-status")?.value || "applied";
  const nextStatus = statusMode === "canceled"
    ? "ignored"
    : (item.history_kind === "activity" || String(historyId).startsWith("activity_") ? "completed" : "parsed");
  if (item.history_kind === "workout" || String(historyId).startsWith("workout_session_")) {
    return updateWorkoutPayload(historyId, {
      type: item.type || "strength",
      activity_type: item.activity_type || "strength",
      date,
      duration_minutes: duration || item.duration_minutes || 0,
      entries: item.entries || [],
      note: content,
      status: statusMode === "canceled" ? "ignored" : "completed",
    });
  }
  if (item.history_kind === "activity" || String(historyId).startsWith("activity_")) {
    return updateActivityPayload(historyId, {
      date,
      time_mode: "duration",
      duration_minutes: duration || item.duration_minutes || 0,
      detail: content,
      status: nextStatus,
      review_required: nextStatus === "ignored",
      review_reason: nextStatus === "ignored" ? "히스토리에서 미반영 처리됨" : null,
    });
  }

  return updateCapturePayload(historyId, {
    raw_content: content,
    date,
    status: nextStatus,
  });
}

async function deleteCaptureDetail(historyId) {
  const item = captureByHistoryId(historyId);
  if (!item) return null;
  if (item.history_kind === "local_pending") {
    deleteInputHistoryRecord(historyId);
    return { deleted: item };
  }
  if (isSupabaseMode()) {
    const result = await supabaseQueueInsert("capture_queue", {
      user_id: getNomadUserId(),
      source: "dashboard",
      status: "pending",
      payload: {
        kind: "input_history_delete",
        history_kind: item.history_kind,
        history_id: historyId,
      },
    });
    return { queued: true, ...result };
  }
  const isWorkout = item.history_kind === "workout" || String(historyId).startsWith("workout_session_");
  const endpoint = isWorkout
    ? "/api/workout-session/delete"
    : item.history_kind === "activity" || String(historyId).startsWith("activity_")
    ? "/api/activity-session/delete"
    : "/api/captures/delete";
  const body = isWorkout
    ? { session_id: historyId }
    : item.history_kind === "activity" || String(historyId).startsWith("activity_")
    ? { activity_id: historyId }
    : { capture_id: historyId };
  const response = await fetch(endpoint, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error || "History delete failed.");
  }
  return payload;
}

function updateCaptureHistoryStatus(historyId, status) {
  if (String(historyId).startsWith("activity_")) {
    return updateActivityPayload(historyId, {
      status,
      review_required: status === "ignored",
      review_reason: status === "ignored" ? "히스토리에서 취소 처리됨" : null,
    });
  }
  return updateCapturePayload(historyId, { status });
}

function formatMoney(amount, currency) {
  if (amount === null || amount === undefined) {
    return "Amount unknown";
  }
  return `${Number(amount).toLocaleString("ko-KR")} ${currency || ""}`.trim();
}

function parseDateValue(value) {
  if (!value) {
    return null;
  }
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? null : date;
}

function formatDateTime(value) {
  const date = parseDateValue(value);
  if (!date) {
    return "unknown";
  }
  return new Intl.DateTimeFormat("ko-KR", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function formatMonthLabel(monthKey) {
  if (!monthKey || !monthKey.includes("-")) {
    return "This month";
  }
  const [year, month] = monthKey.split("-");
  return `${year}.${month}`;
}

function getExpenseCategory(expense) {
  return expense?.metadata?.source_category_name || expense?.category || "미분류";
}

function getExpenseSubcategory(expense) {
  return expense?.metadata?.source_subcategory_name || expense?.subcategory || "미분류";
}

function getCurrentMonthKey(payload) {
  const latestExpenseDate = (payload?.expenses || []).map((expense) => expense.date).filter(Boolean).sort().at(-1);
  if (latestExpenseDate) {
    return latestExpenseDate.slice(0, 7);
  }
  const latestExport = payload?.source?.files?.[0]?.exported_at;
  const exportDate = parseDateValue(latestExport);
  if (exportDate) {
    return `${exportDate.getFullYear()}-${String(exportDate.getMonth() + 1).padStart(2, "0")}`;
  }
  return new Date().toISOString().slice(0, 7);
}

function sumBy(items, keyGetter) {
  return items.reduce((acc, item) => {
    const key = keyGetter(item);
    acc.set(key, (acc.get(key) || 0) + Number(item.amount || 0));
    return acc;
  }, new Map());
}

function topEntries(map, limit = 5) {
  return [...map.entries()].sort((a, b) => b[1] - a[1]).slice(0, limit);
}

function findMonthlyBudget(payload, monthKey) {
  const [year, month] = monthKey.split("-").map(Number);
  return (payload?.budgets || [])
    .filter((budget) => budget.is_active !== false)
    .filter((budget) => budget.period_type === "monthly" && budget.filter_type === "total")
    .find((budget) => Number(budget.year) === year && Number(budget.month) === month);
}

function dateDiffDays(startDate, endDate) {
  const start = parseDateValue(`${startDate}T00:00:00`);
  const end = parseDateValue(`${endDate}T00:00:00`);
  if (!start || !end) {
    return 0;
  }
  return Math.max(1, Math.round((end - start) / 86400000) + 1);
}

function buildRegionReviews(expenses = [], latestTradeDate = null) {
  const grouped = expenses.reduce((acc, expense) => {
    const region = expense.place || "지역 미지정";
    if (!acc.has(region)) {
      acc.set(region, []);
    }
    acc.get(region).push(expense);
    return acc;
  }, new Map());

  return [...grouped.entries()]
    .map(([region, regionExpenses]) => {
      const total = regionExpenses.reduce((sum, expense) => sum + Number(expense.amount || 0), 0);
      const dates = regionExpenses.map((expense) => expense.date).filter(Boolean).sort();
      const startDate = dates[0] || null;
      const endDate = dates.at(-1) || null;
      const isActiveRegion = regionExpenses.some((expense) => expense?.metadata?.source_region_is_active);
      const projectionEndDate = isActiveRegion && latestTradeDate && latestTradeDate > endDate ? latestTradeDate : endDate;
      const observedDays = startDate && endDate ? dateDiffDays(startDate, endDate) : 0;
      const totalDays = startDate && projectionEndDate ? dateDiffDays(startDate, projectionEndDate) : observedDays;
      const dailyAverage = observedDays ? Math.round(total / observedDays) : 0;
      const projectedTotal = observedDays && totalDays ? Math.round((total / observedDays) * totalDays) : total;
      const byCategory = topEntries(sumBy(regionExpenses, getExpenseCategory), 4);
      const categoryTotal = byCategory.reduce((sum, [, amount]) => sum + amount, 0);
      const categoryRows = byCategory.map(([category, amount]) => {
        const ratio = total ? Math.round((amount / total) * 100) : 0;
        const details = regionExpenses
          .filter((expense) => getExpenseCategory(expense) === category)
          .slice()
          .sort((a, b) => Number(b.amount || 0) - Number(a.amount || 0))
          .slice(0, 8);
        return { category, amount, ratio, details };
      });
      const topCategories = new Set(byCategory.map(([category]) => category));
      const otherDetails = regionExpenses
        .filter((expense) => !topCategories.has(getExpenseCategory(expense)))
        .slice()
        .sort((a, b) => Number(b.amount || 0) - Number(a.amount || 0))
        .slice(0, 8);
      return {
        region,
        total,
        count: regionExpenses.length,
        startDate,
        endDate: projectionEndDate,
        lastExpenseDate: endDate,
        isActiveRegion,
        totalDays,
        observedDays,
        dailyAverage,
        projectedTotal,
        categoryRows,
        otherTotal: Math.max(0, total - categoryTotal),
        otherDetails,
      };
    })
    .sort((a, b) => b.total - a.total);
}

function renderFinanceAnalysisReview(payload = {}) {
  const analysis = payload.analysis || {};
  const sourceFile = payload.source?.source_file || {};
  const categoryPalette = ["#7dd3fc", "#14b8a6", "#8b5cf6", "#f59e0b", "#64748b", "#ef4444"];
  const categoryRows = analysis.category_rows || [];
  const categoryShareBar = categoryRows.map((row, index) => (
    `<span title="${escapeHtml(`${row.category} ${row.ratio}%`)}" style="--share:${row.ratio}%; --finance-color:${categoryPalette[index % categoryPalette.length]}"></span>`
  )).join("");
  const categoryReview = `
    <div class="finance-category-share" aria-label="당월 카테고리 비중">${categoryShareBar}</div>
    <ul class="finance-category-list">
      ${categoryRows.map((row, index) => `
        <li class="finance-category-row" style="--share:${row.ratio}%; --finance-color:${categoryPalette[index % categoryPalette.length]}">
          <strong>${escapeHtml(row.category)}</strong>
          <span class="finance-category-track"><span></span></span>
          <em>${formatMoney(row.total, "KRW")} · ${row.ratio}%</em>
        </li>
      `).join("")}
    </ul>
  `;
  const renderRegionCategoryDetails = (details = []) => {
    if (!details.length) {
      return '<p class="finance-region-empty">세부 거래 없음</p>';
    }
    return `
      <div class="finance-region-details">
        ${details.map((expense) => `
          <div class="finance-region-detail-row">
            <span>${escapeHtml(expense.merchant || expense.subcategory || "미분류")}</span>
            <small>${escapeHtml([expense.date, expense.subcategory].filter(Boolean).join(" · "))}</small>
            <strong>${formatMoney(expense.amount, expense.currency || "KRW")}</strong>
          </div>
        `).join("")}
      </div>
    `;
  };
  const regionReview = (analysis.region_reviews || []).map((review) => {
    const period = review.startDate && review.endDate ? `${review.startDate}~${review.endDate}` : "기간 미상";
    const activeLabel = review.isActiveRegion ? " · active" : "";
    const observedLabel = review.lastExpenseDate && review.lastExpenseDate !== review.endDate ? ` · 기록 ${review.lastExpenseDate}까지` : "";
    const categoryRowsHtml = (review.categoryRows || []).map((row) => (
      `<li>
        <details class="finance-region-category">
          <summary>
            <span>${escapeHtml(row.category)}</span>
            <strong>${formatMoney(row.amount, "KRW")} · ${row.ratio}%</strong>
          </summary>
          ${renderRegionCategoryDetails(row.details)}
        </details>
      </li>`
    )).join("");
    const otherRow = review.otherTotal
      ? `<li>
          <details class="finance-region-category">
            <summary>
              <span>기타</span>
              <strong>${formatMoney(review.otherTotal, "KRW")}</strong>
            </summary>
            ${renderRegionCategoryDetails(review.otherDetails)}
          </details>
        </li>`
      : "";
    return `
      <article class="finance-region-card">
        <header>
          <div>
            <h4>${escapeHtml(review.region)}</h4>
            <p>${period} · ${review.totalDays || 0}일 · ${review.count}건${activeLabel}${observedLabel}</p>
          </div>
          <strong>${formatMoney(review.total, "KRW")}</strong>
        </header>
        <div class="finance-region-metrics">
          <span>일평균 ${formatMoney(review.dailyAverage, "KRW")}</span>
          <span>전체 예상 ${formatMoney(review.projectedTotal, "KRW")}</span>
        </div>
        <ul>${categoryRowsHtml}${otherRow}</ul>
      </article>
    `;
  }).join("");
  const topTransactions = (analysis.top_transactions || []).map((expense) => (
    `<li><strong>${escapeHtml(expense.merchant || expense.subcategory || "미분류")}</strong><span>${formatMoney(expense.amount, expense.currency || "KRW")} · ${expense.date}</span></li>`
  )).join("");

  financeReviewPanel.innerHTML = `
    <div class="finance-freshness">
      <strong>최근 수신: ${formatDateTime(payload.source?.normalized_updated_at || payload.generated_at || sourceFile.exported_at)}</strong>
      <span>거래 기준 ${analysis.latest_trade_date || "unknown"}까지 · ${sourceFile.name || payload.source?.selected_file || "finance-review snapshot"}</span>
    </div>
    <div class="finance-metrics">
      <article class="finance-metric ${analysis.status_tone || "ok"}">
        <span>${formatMonthLabel(analysis.month_key)} 지출</span>
        <strong>${formatMoney(analysis.month_total, "KRW")}</strong>
        <small>${analysis.budget_amount ? `예산 ${formatMoney(analysis.budget_amount, "KRW")} · ${analysis.budget_ratio}%` : "예산 미설정"}</small>
      </article>
      <article class="finance-metric">
        <span>월말 예상</span>
        <strong>${formatMoney(analysis.month_end_forecast, "KRW")}</strong>
        <small>현재 일평균 ${formatMoney(analysis.daily_average, "KRW")}</small>
      </article>
      <article class="finance-metric">
        <span>조정 가능 후보</span>
        <strong>${formatMoney(analysis.adjustable_total, "KRW")}</strong>
        <small>주거비/보험/세금 제외</small>
      </article>
    </div>
    <div class="finance-interpretation">
      <strong>${escapeHtml(analysis.status_text || "월 예산 없음")}</strong>
      <span>${escapeHtml(analysis.finance_action || "아직 카테고리별 조정 후보가 충분하지 않습니다.")}</span>
    </div>
    <div class="finance-review-grid">
      <article class="finance-review-block">
        <h3>당월 리뷰</h3>
        ${categoryReview}
      </article>
      <article class="finance-review-block finance-region-review">
        <h3>지역 전체 리뷰</h3>
        <div class="finance-region-list">${regionReview}</div>
      </article>
      <article class="finance-review-block">
        <h3>큰 지출</h3>
        <ul>${topTransactions}</ul>
      </article>
    </div>
    <div class="finance-notes">
      ${(analysis.notes || []).map((note) => `<p>${escapeHtml(note)}</p>`).join("")}
    </div>
  `;
}

function renderFinanceReview(payload = {}) {
  if (!financeReviewPanel) {
    return;
  }

  if (payload.analysis) {
    renderFinanceAnalysisReview(payload);
    return;
  }

  const expenses = payload.expenses || [];
  if (!expenses.length) {
    financeReviewPanel.innerHTML = '<p class="empty">No normalized finance export yet.</p>';
    return;
  }

  const monthKey = getCurrentMonthKey(payload);
  const monthExpenses = expenses.filter((expense) => (expense.date || "").startsWith(monthKey));
  const monthTotal = monthExpenses.reduce((sum, expense) => sum + Number(expense.amount || 0), 0);
  const monthBudget = findMonthlyBudget(payload, monthKey);
  const budgetAmount = Number(monthBudget?.target_amount || 0);
  const budgetGap = budgetAmount ? budgetAmount - monthTotal : null;
  const budgetRatio = budgetAmount ? Math.round((monthTotal / budgetAmount) * 100) : null;
  const latestTradeDate = expenses.map((expense) => expense.date).filter(Boolean).sort().at(-1);
  const sourceFile = payload.source?.files?.[0];
  const receivedAt = payload.updated_at || sourceFile?.exported_at;
  const dailyAverage = monthExpenses.length ? Math.round(monthTotal / Math.max(1, Number(latestTradeDate?.slice(8, 10) || 1))) : 0;
  const monthEndForecast = dailyAverage ? dailyAverage * 30 : 0;
  const byCategory = topEntries(sumBy(monthExpenses, getExpenseCategory), 6);
  const regionReviews = buildRegionReviews(expenses, latestTradeDate).slice(0, 4);
  const adjustable = monthExpenses.filter((expense) => !["주거비", "보험료", "세금"].includes(getExpenseCategory(expense)));
  const adjustableTotal = adjustable.reduce((sum, expense) => sum + Number(expense.amount || 0), 0);
  const foodCafe = monthExpenses.filter((expense) => ["식비"].includes(getExpenseCategory(expense)));
  const foodCafeTotal = foodCafe.reduce((sum, expense) => sum + Number(expense.amount || 0), 0);
  const missingRegionCount = expenses.filter((expense) => !expense.place).length;
  const renderRegionCategoryDetails = (details = []) => {
    if (!details.length) {
      return '<p class="finance-region-empty">세부 거래 없음</p>';
    }
    return `
      <div class="finance-region-details">
        ${details.map((expense) => `
          <div class="finance-region-detail-row">
            <span>${escapeHtml(expense.merchant || getExpenseSubcategory(expense))}</span>
            <small>${escapeHtml([expense.date, getExpenseSubcategory(expense)].filter(Boolean).join(" · "))}</small>
            <strong>${formatMoney(expense.amount, expense.currency || "KRW")}</strong>
          </div>
        `).join("")}
      </div>
    `;
  };
  const regionReview = regionReviews.map((review) => {
    const period = review.startDate && review.endDate ? `${review.startDate}~${review.endDate}` : "기간 미상";
    const activeLabel = review.isActiveRegion ? " · active" : "";
    const observedLabel = review.lastExpenseDate && review.lastExpenseDate !== review.endDate ? ` · 기록 ${review.lastExpenseDate}까지` : "";
    const categoryRows = review.categoryRows.map((row) => (
      `<li>
        <details class="finance-region-category">
          <summary>
            <span>${escapeHtml(row.category)}</span>
            <strong>${formatMoney(row.amount, "KRW")} · ${row.ratio}%</strong>
          </summary>
          ${renderRegionCategoryDetails(row.details)}
        </details>
      </li>`
    )).join("");
    const otherRow = review.otherTotal
      ? `<li>
          <details class="finance-region-category">
            <summary>
              <span>기타</span>
              <strong>${formatMoney(review.otherTotal, "KRW")}</strong>
            </summary>
            ${renderRegionCategoryDetails(review.otherDetails)}
          </details>
        </li>`
      : "";
    return `
      <article class="finance-region-card">
        <header>
          <div>
            <h4>${review.region}</h4>
            <p>${period} · ${review.totalDays || 0}일 · ${review.count}건${activeLabel}${observedLabel}</p>
          </div>
          <strong>${formatMoney(review.total, "KRW")}</strong>
        </header>
        <div class="finance-region-metrics">
          <span>일평균 ${formatMoney(review.dailyAverage, "KRW")}</span>
          <span>전체 예상 ${formatMoney(review.projectedTotal, "KRW")}</span>
        </div>
        <ul>${categoryRows}${otherRow}</ul>
      </article>
    `;
  }).join("");
  const categoryPalette = ["#7dd3fc", "#14b8a6", "#8b5cf6", "#f59e0b", "#64748b", "#ef4444"];
  const categoryReviewRows = byCategory.map(([category, total], index) => ({
    category,
    total,
    ratio: monthTotal ? Math.round((total / monthTotal) * 100) : 0,
    color: categoryPalette[index % categoryPalette.length],
  }));
  const categoryShareBar = categoryReviewRows.map((row) => (
    `<span title="${escapeHtml(`${row.category} ${row.ratio}%`)}" style="--share:${row.ratio}%; --finance-color:${row.color}"></span>`
  )).join("");
  const categoryReview = `
    <div class="finance-category-share" aria-label="당월 카테고리 비중">${categoryShareBar}</div>
    <ul class="finance-category-list">
      ${categoryReviewRows.map((row) => `
        <li class="finance-category-row" style="--share:${row.ratio}%; --finance-color:${row.color}">
          <strong>${escapeHtml(row.category)}</strong>
          <span class="finance-category-track"><span></span></span>
          <em>${formatMoney(row.total, "KRW")} · ${row.ratio}%</em>
        </li>
      `).join("")}
    </ul>
  `;
  const topTransactions = monthExpenses
    .slice()
    .sort((a, b) => Number(b.amount || 0) - Number(a.amount || 0))
    .slice(0, 5)
    .map((expense) => (
      `<li><strong>${expense.merchant || getExpenseSubcategory(expense)}</strong><span>${formatMoney(expense.amount, expense.currency)} · ${expense.date}</span></li>`
    ))
    .join("");
  const topCategory = categoryReviewRows[0];
  const financeAction = topCategory
    ? `${topCategory.category}가 이번 달 지출의 ${topCategory.ratio}%입니다. 오늘 조정은 ${formatMoney(Math.round(adjustableTotal / Math.max(1, 7)), "KRW")} 단위로 가볍게 봅니다.`
    : "아직 카테고리별 조정 후보가 충분하지 않습니다.";
  const statusTone = budgetGap !== null && budgetGap < 0 ? "over" : "ok";
  const statusText = budgetGap === null
    ? "월 예산 없음"
    : budgetGap < 0
      ? `${formatMoney(Math.abs(budgetGap), "KRW")} 초과`
      : `${formatMoney(budgetGap, "KRW")} 남음`;
  const notes = [
    budgetGap !== null && budgetGap < 0
      ? `이번 달은 예산을 ${formatMoney(Math.abs(budgetGap), "KRW")} 초과했습니다.`
      : `이번 달 예산 대비 ${statusText} 상태입니다.`,
    `조정 가능한 생활비 후보는 ${formatMoney(adjustableTotal, "KRW")}이고, 식비 계열은 ${formatMoney(foodCafeTotal, "KRW")}입니다.`,
    missingRegionCount
      ? `전체 기간 기준 지역 미지정 거래가 ${missingRegionCount}건이라 체류지별 리뷰 정확도를 높이려면 region 입력 보강이 필요합니다.`
      : "전체 거래에 지역 정보가 연결되어 있습니다.",
  ];

  financeReviewPanel.innerHTML = `
    <div class="finance-freshness">
      <strong>최근 수신: ${formatDateTime(receivedAt)}</strong>
      <span>거래 기준 ${latestTradeDate || "unknown"}까지 · ${sourceFile?.name || "local normalized file"}</span>
    </div>
    <div class="finance-metrics">
      <article class="finance-metric ${statusTone}">
        <span>${formatMonthLabel(monthKey)} 지출</span>
        <strong>${formatMoney(monthTotal, "KRW")}</strong>
        <small>${budgetAmount ? `예산 ${formatMoney(budgetAmount, "KRW")} · ${budgetRatio}%` : "예산 미설정"}</small>
      </article>
      <article class="finance-metric">
        <span>월말 예상</span>
        <strong>${formatMoney(monthEndForecast, "KRW")}</strong>
        <small>현재 일평균 ${formatMoney(dailyAverage, "KRW")}</small>
      </article>
      <article class="finance-metric">
        <span>조정 가능 후보</span>
        <strong>${formatMoney(adjustableTotal, "KRW")}</strong>
        <small>주거비/보험/세금 제외</small>
      </article>
    </div>
    <div class="finance-interpretation">
      <strong>${statusText}</strong>
      <span>${financeAction}</span>
    </div>
    <div class="finance-review-grid">
      <article class="finance-review-block">
        <h3>당월 리뷰</h3>
        ${categoryReview}
      </article>
      <article class="finance-review-block finance-region-review">
        <h3>지역 전체 리뷰</h3>
        <div class="finance-region-list">${regionReview}</div>
      </article>
      <article class="finance-review-block">
        <h3>큰 지출</h3>
        <ul>${topTransactions}</ul>
      </article>
    </div>
    <div class="finance-notes">
      ${notes.map((note) => `<p>${note}</p>`).join("")}
    </div>
  `;
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
  await loadCurrentStay();
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
  const financeReview = isSupabaseMode()
    ? await loadDashboardSnapshot("finance-review").catch(() => ({ analysis: null }))
    : await loadJson("/data/expenses/normalized-expenses.json").catch(() => ({ expenses: [] }));
  const activityAllocation = await loadDashboardJson("activity-allocation", "/dashboard/activity-allocation.json", { summary: {}, sessions: [] });
  const historyMonth = selectedCaptureMonth(today.date || todayLocalDateValue());
  setCapturePeriodControls(historyMonth);
  mainActivityHistoryCount = (activityAllocation.month_sessions || [])
    .filter((session) => String(session.date || "").startsWith(historyMonth))
    .filter((session) => session.status !== "ignored")
    .length;
  const inputHistorySnapshot = isSupabaseMode()
    ? await loadDashboardSnapshot("input-history").catch(() => ({ captures: [], activity_sessions: [] }))
    : null;
  const activityHistory = isSupabaseMode()
    ? {
      sessions: (inputHistorySnapshot.activity_sessions || [])
        .filter((session) => historyRecordMatchesMonth(session, historyMonth)),
    }
    : await loadJson(`/api/activity-history?month=${encodeURIComponent(historyMonth)}`).catch(() => null);
  const health = await loadDashboardJson("health", "/dashboard/health.json", { summary: {}, muscle_dashboard: {} });
  latestHealthSessions = health.sessions || [];
  const english = await loadDashboardJson("english", "/dashboard/english.json", { summary: {}, gpts_reviews: [] });
  const workoutHistory = isSupabaseMode()
    ? await loadDashboardSnapshot("workout-history").catch(() => ({ sessions: [] }))
    : await loadJson("/api/workout-history").catch(() => ({ sessions: [] }));
  const mergedHealth = mergePendingHealthItems(workoutHistory.sessions || [], latestHealthSessions);
  workoutHistorySessions = mergedHealth.workouts;
  latestHealthSessions = mergedHealth.activities;

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
  renderEnglishDashboard(english);
  renderRoutineCards(workoutHistorySessions, latestHealthSessions);
  renderExerciseHistory(workoutExercise.value);
  updateLatestExerciseGuide();
  renderActivityAllocation(activityAllocation, activityHistory);
  await refreshAiWork();
  renderMainAgent({
    today,
    activityAllocation,
    health,
    english,
    expenseCandidates,
    syncStatus,
  });
  renderLocalContext(today.local_app_context);
  renderLifeBalance(life.areas);
  const captures = isSupabaseMode()
    ? {
      captures: (inputHistorySnapshot.captures || [])
        .filter((capture) => historyRecordMatchesMonth(capture, historyMonth)),
    }
    : await loadJson(`/api/captures?month=${encodeURIComponent(historyMonth)}`).catch(() => ({ captures: [] }));
  const visibleCaptures = { captures: inputHistoryItems(captures.captures, activityHistory) };
  renderCaptures(visibleCaptures.captures);
  renderFinanceReview(financeReview);
  renderExpenseCandidates(expenseCandidates.candidates);
  renderWorkspaceOverview({
    today,
    health,
    english,
    activityAllocation,
    captures: visibleCaptures,
    expenseCandidates,
    notifications,
    syncStatus,
  });
  renderNavBadges({
    today,
    health,
    english,
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

activityForm.addEventListener("change", (event) => {
  if (event.target.name === "area") {
    selectActivityArea(event.target.value);
  }
});

activityDurationSlider.addEventListener("input", () => {
  lastTimerActivity = null;
  updateDurationSlider(activityDurationSlider.value, "manual");
});

activityStartButton?.addEventListener("click", startActiveActivity);
activityEndButton?.addEventListener("click", endActiveActivity);
addHealthActivity?.addEventListener("click", () => {
  healthActivityDrafts.push(defaultHealthActivityDraft("swimming"));
  renderHealthActivityDrafts();
  writeHealthQuickDraft();
  activityStatus.textContent = "운동 항목을 추가했습니다.";
});
deleteRoutineCardButton?.addEventListener("click", deleteCurrentRoutineGroup);
healthActivityDraftList?.addEventListener("click", (event) => {
  const row = event.target.closest(".health-activity-draft-row");
  const button = event.target.closest("button");
  if (!row || !button) return;
  const index = Number(row.dataset.index);
  if (!Number.isInteger(index) || !healthActivityDrafts[index]) return;
  if (button.classList.contains("health-draft-strength")) {
    syncHealthDraftRow(row);
    writeHealthQuickDraft();
    activeStrengthDraftIndex = index;
    workoutEntries = reindexStrengthEntries(healthActivityDrafts[index].strength_entries || []);
    workoutNote.value = healthActivityDrafts[index].strength_note || "";
    renderWorkoutSets();
    quickDialog?.close();
    openWorkoutDialog({ returnToQuick: true, muscle: "full_body" });
    return;
  }
  if (button.classList.contains("health-draft-remove")) {
    healthActivityDrafts.splice(index, 1);
    renderHealthActivityDrafts();
    writeHealthQuickDraft();
  }
});
healthActivityDraftList?.addEventListener("input", (event) => {
  const row = event.target.closest(".health-activity-draft-row");
  syncHealthDraftRow(row);
  const total = healthActivityDrafts.reduce((sum, item) => sum + Number(item.duration_minutes || 0), 0);
  healthQuickTotal.textContent = formatActivityDuration(total);
  writeHealthQuickDraft();
});
healthActivityDraftList?.addEventListener("change", (event) => {
  const row = event.target.closest(".health-activity-draft-row");
  const draft = syncHealthDraftRow(row);
  if (draft && event.target.classList.contains("health-draft-type")) {
    renderHealthActivityDrafts();
  }
  writeHealthQuickDraft();
});

activityForm.addEventListener("submit", (event) => {
  event.preventDefault();
  if (activitySubmitInFlight) {
    return;
  }
  activitySubmitInFlight = true;
  resetActivityDate();
  activityStatus.textContent = "Saving...";
  const area = selectedRadioValue("area");
  if (area === "health") {
    [...healthActivityDraftList.querySelectorAll(".health-activity-draft-row")].forEach(syncHealthDraftRow);
    if (!healthActivityDrafts.length) {
      healthActivityDrafts.push(defaultHealthActivityDraft());
      renderHealthActivityDrafts();
      writeHealthQuickDraft();
    }
    const invalid = healthActivityDrafts.find((item) => !Number.isFinite(Number(item.duration_minutes)) || Number(item.duration_minutes) <= 0);
    if (invalid) {
      activityStatus.textContent = "운동 시간을 확인하세요.";
      activitySubmitInFlight = false;
      return;
    }
  }
  const submissionId = newClientSubmissionId(area === "health" ? "health" : "activity");
  const payloads = area === "health" ? healthActivityPayloadsFromDrafts() : [activityPayloadFromForm()];
  payloads.forEach((payload, index) => {
    payload.client_submission_id = `${submissionId}_${index}`;
    payload.metadata = {
      ...(payload.metadata || {}),
      client_submission_id: payload.client_submission_id,
    };
  });
  const strengthDrafts = area === "health"
    ? healthActivityDrafts
      .filter((item) => item.activity_type === "strength")
      .map((item, index) => ({ ...item, client_submission_id: `${submissionId}_strength_${index}` }))
    : [];
  const editedRoutineGroupKey = area === "health" ? editingRoutineGroupKey : null;
  const editedHealthDrafts = area === "health" ? cloneHealthDrafts(healthActivityDrafts) : [];
  const existingWorkoutIds = new Set(strengthDrafts.map((item) => item.source_workout_session_id).filter(Boolean));
  const activityPayloadsToSave = area === "health"
    ? payloads.filter((payload) => !isStrengthPayload(payload) && !existingWorkoutIds.has(payload.metadata?.source_workout_session_id))
    : payloads;
  const activitySaves = activityPayloadsToSave.map((payload) => {
    const sourceActivityId = payload.metadata?.source_activity_id;
    if (area !== "health" && editingGenericActivityId && payloads.length === 1) {
      return updateActivityPayload(editingGenericActivityId, payload);
    }
    if (area === "health" && sourceActivityId) {
      return updateActivityPayload(sourceActivityId, payload);
    }
    if (area === "health" && editingSavedActivityId && payloads.length === 1) {
      return updateActivityPayload(editingSavedActivityId, payload);
    }
    return saveActivityPayload(payload);
  });
  const workoutSaves = strengthDrafts.map((item) => {
    if (item.source_workout_session_id) {
      return updateStrengthWorkoutDraft(item.source_workout_session_id, item);
    }
    if (editingSavedWorkoutId && strengthDrafts.length === 1) {
      return updateStrengthWorkoutDraft(editingSavedWorkoutId, item);
    }
    return saveStrengthWorkoutDraft(item);
  });
  const rowDeleteSaves = area === "health" ? deletedRoutineRowSaves() : [];
  Promise.all([...activitySaves, ...workoutSaves, ...rowDeleteSaves])
    .then((results) => {
      const queuedLocally = results.some((result) => result?.localPending || result?.queuedLocally);
      activityDetail.value = "";
      activitySubcategory.value = "";
      activityParseMemo.checked = false;
      if (editedRoutineGroupKey && isSupabaseMode()) {
        applyOptimisticRoutineGroupEdit(editedRoutineGroupKey, editedHealthDrafts);
      }
      if (isSupabaseMode()) {
        appendInputHistory({
          raw_content: payloadHistorySummary(payloads, area),
          linked_agents: area === "health" ? ["nomad-health"] : [],
          status: "saved",
          client_submission_id: submissionId,
          date: selectedActivityDate(),
        });
        renderCaptures(inputHistoryItems([]));
        if (area === "health") {
          applyOptimisticHealthSave(payloads, strengthDrafts);
        }
      }
      if (area === "health") {
        healthActivityDrafts = [];
        resetHealthEditingState();
        clearHealthDraftForm();
        clearHealthQuickDraft();
        renderHealthActivityDrafts();
      }
      editingGenericActivityId = null;
      lastTimerActivity = null;
      activityStatus.textContent = isSupabaseMode()
        ? queuedLocally
          ? "이 기기에 임시 저장했습니다. 모바일 로그인/네트워크가 복구되면 cloud queue로 다시 보냅니다."
          : "Saved. Analysis and dashboard update pending."
        : "Activity saved. Dashboard updated.";
      if (quickDialog?.open) {
        quickDialog.close();
      }
      if (!isSupabaseMode()) {
        return loadDashboard();
      }
      return null;
    })
    .catch((error) => {
      activityStatus.textContent = error.message;
    })
    .finally(() => {
      activitySubmitInFlight = false;
    });
});

syncInboxButton?.addEventListener("click", () => {
  if (isSupabaseMode()) {
    captureStatus.textContent = "Hosted mode에서는 저장은 즉시 완료되고, 분석 반영은 Hermes가 이어서 처리합니다.";
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
    setWorkspaceStatus(localContextSyncStatus, "Local app context refresh는 Mac local dashboard에서 실행합니다.", "warning");
    return;
  }
  setWorkspaceStatus(localContextSyncStatus, "Refreshing local app context...");
  syncLocalAppsButton.disabled = true;
  fetch("/api/sync-local-apps", {
    method: "POST",
  })
    .then(async (response) => {
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.error || "Local app refresh failed.");
      }
      setWorkspaceStatus(localContextSyncStatus, "Local app context refreshed.", "ok");
      return loadDashboard();
    })
    .catch((error) => {
      setWorkspaceStatus(localContextSyncStatus, error.message, "error");
    })
    .finally(() => {
      syncLocalAppsButton.disabled = false;
    });
});

if (syncEnglishReviewsButton) {
  syncEnglishReviewsButton.addEventListener("click", () => {
    if (isSupabaseMode()) {
      setWorkspaceStatus(englishSyncStatus, "iCloud 리뷰 import는 Mac local dashboard에서 실행합니다.", "warning");
      return;
    }
    setWorkspaceStatus(englishSyncStatus, "1/2 iCloud 파일 동기화 중...");
    syncEnglishReviewsButton.disabled = true;
    syncEnglishReviewsButton.textContent = "업데이트 중...";
    fetch("/api/sync-english-reviews", {
      method: "POST",
    })
      .then(async (response) => {
        const payload = await response.json();
        if (!response.ok) {
          throw new Error(payload.error || "English review sync failed.");
        }
        const imported = payload.imported?.length || 0;
        const updated = payload.updated?.length || 0;
        const skipped = payload.skipped?.length || 0;
        const errors = payload.errors?.length || 0;
        const pendingCount = Number(payload.review_status?.pending_count ?? 0);
        const analyzedCount = Number(payload.review_status?.analyzed_count ?? 0);
        setWorkspaceStatus(
          englishSyncStatus,
          errors
            ? `업데이트 중 오류 ${errors}건`
            : `2/2 분석 갱신 완료 · new ${imported}, updated ${updated}, unchanged ${skipped} · analyzed ${analyzedCount}, pending ${pendingCount}`,
          errors ? "error" : "ok",
        );
        if (!errors && isSupabaseMode() && pendingCount > 0 && payload.review_status?.guidance) {
          window.alert(payload.review_status.guidance);
        }
        return loadDashboard();
      })
      .catch((error) => {
        setWorkspaceStatus(englishSyncStatus, error.message, "error");
      })
      .finally(() => {
        syncEnglishReviewsButton.disabled = false;
        syncEnglishReviewsButton.textContent = "English 업데이트";
      });
  });
}

if (syncFinanceButton) {
  syncFinanceButton.addEventListener("click", () => {
    if (isSupabaseMode()) {
      setWorkspaceStatus(financeSyncStatus, "Finance sync 요청을 Mac Hermes worker queue에 보냅니다...");
      syncFinanceButton.disabled = true;
      syncFinanceButton.textContent = "Requesting...";
      supabaseQueueInsert("capture_queue", {
        user_id: getNomadUserId(),
        source: "dashboard",
        status: "pending",
        payload: {
          kind: "finance_sync_request",
          requested_at: new Date().toISOString(),
          client_timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        },
      })
        .then(() => {
          setWorkspaceStatus(financeSyncStatus, "Finance sync 요청 완료. Mac worker가 다음 sync에서 iCloud export를 읽고 snapshot을 갱신합니다.", "ok");
        })
        .catch((error) => {
          setWorkspaceStatus(financeSyncStatus, error.message || "Finance sync request failed.", "error");
        })
        .finally(() => {
          syncFinanceButton.disabled = false;
          syncFinanceButton.textContent = "Sync Finance";
        });
      return;
    }
    setWorkspaceStatus(financeSyncStatus, "Reading Finance export from iCloud...");
    syncFinanceButton.disabled = true;
    syncFinanceButton.textContent = "Syncing...";
    fetch("/api/sync-finance-exports", {
      method: "POST",
    })
      .then(async (response) => {
        const payload = await response.json();
        if (!response.ok) {
          throw new Error(payload.error || "Finance sync failed.");
        }
        const expenseCount = payload.normalized?.summary?.expense_count || 0;
        const imported = payload.import?.imported?.length || 0;
        const updated = payload.import?.updated?.length || 0;
        setWorkspaceStatus(financeSyncStatus, `Finance synced: ${expenseCount} expenses · ${imported} new, ${updated} updated.`, "ok");
        return loadDashboard();
      })
      .catch((error) => {
        setWorkspaceStatus(financeSyncStatus, error.message, "error");
      })
      .finally(() => {
        syncFinanceButton.disabled = false;
        syncFinanceButton.textContent = "Sync Finance";
      });
  });
}

workoutMuscle.addEventListener("change", refreshExerciseOptions);
workoutExercise.addEventListener("change", () => {
  refreshExerciseActions();
  renderExerciseHistory(workoutExercise.value);
});
exerciseSearch.addEventListener("input", refreshExerciseOptions);
openWorkoutDialogButton?.addEventListener("click", () => {
  selectActivityArea("health");
  openQuickDialog();
});
closeWorkoutDialogButton?.addEventListener("click", closeWorkoutDialog);
workoutDialog?.addEventListener("click", (event) => {
  if (event.target === workoutDialog) {
    closeWorkoutDialog();
  }
});
quickAddExercise?.addEventListener("click", renderQuickAddExerciseDialog);
exerciseDialogContent.addEventListener("click", (event) => {
  const button = event.target.closest("#dialog-add-exercise");
  if (!button) return;
  const input = exerciseDialogContent.querySelector("#dialog-exercise-name");
  button.disabled = true;
  quickAddExerciseFromWorkout(input?.value.trim() || "")
    .then(() => {
      exerciseDialog.close();
    })
    .catch((error) => {
      workoutStatus.textContent = error.message;
    })
    .finally(() => {
      button.disabled = false;
    });
});
exerciseDialogContent.addEventListener("keydown", (event) => {
  if (event.key !== "Enter" || event.target.id !== "dialog-exercise-name") return;
  event.preventDefault();
  exerciseDialogContent.querySelector("#dialog-add-exercise")?.click();
});
openWorkoutTime?.addEventListener("click", () => {
  setTimePickerValue(new Date(workoutStartedAt));
  workoutTimePopover.hidden = !workoutTimePopover.hidden;
});
applyWorkoutTime?.addEventListener("click", applyWorkoutStartedAt);

routinePrev.addEventListener("click", () => {
  routineTrack.scrollBy({ left: -Math.max(180, routineTrack.clientWidth * 0.64), behavior: "smooth" });
});

routineNext.addEventListener("click", () => {
  routineTrack.scrollBy({ left: Math.max(180, routineTrack.clientWidth * 0.64), behavior: "smooth" });
});

routineYearSelect?.addEventListener("change", () => {
  const selectedYear = routineYearSelect.value;
  const allGroups = buildRoutineGroups(workoutHistorySessions, latestHealthSessions);
  const latestMonthInYear = [...new Set(allGroups.map(routineMonthKey).filter((key) => key.startsWith(`${selectedYear}-`)))].sort().at(-1);
  selectedRoutineMonth = latestMonthInYear || "";
  renderRoutineCards(workoutHistorySessions, latestHealthSessions);
});

routineMonthSelect?.addEventListener("change", () => {
  if (!routineYearSelect?.value || !routineMonthSelect.value) return;
  selectedRoutineMonth = `${routineYearSelect.value}-${routineMonthSelect.value}`;
  renderRoutineCards(workoutHistorySessions, latestHealthSessions);
});

function openRoutineGroupEditor(groupKey) {
  const group = latestRoutineGroups.find((item) => item.key === groupKey);
  if (!group) {
    activityStatus.textContent = "편집할 루틴 카드를 찾지 못했습니다.";
    return;
  }
  selectActivityArea("health");
  resetHealthEditingState();
  editingRoutineGroupKey = group.key;
  if (activityDate) {
    activityDate.value = group.date || group.key || todayLocalDateValue();
  }
  editingRoutineDeleteTargets = {
    workoutIds: group.workouts.map((session) => session.id).filter(Boolean),
    activities: group.activities.map((session) => ({
      id: session.source || session.id,
      type: session.type,
      duration_minutes: session.duration_minutes || 30,
      detail: session.detail || healthTypeLabel(session.type),
    })).filter((item) => item.id?.startsWith("activity_")),
  };
  healthActivityDrafts = [
    ...group.workouts.map((session) => {
      const entries = reindexStrengthEntries(session.entries || []);
      const summary = summarizeStrengthEntries(entries);
      return {
        activity_type: "strength",
        duration_minutes: session.duration_minutes || 30,
        detail: session.note || summary || "헬스 루틴",
        strength_entries: entries,
        strength_note: session.note || "",
        source_workout_session_id: session.id,
      };
    }),
    ...group.activities.map((session) => ({
      activity_type: session.type || "other",
      duration_minutes: session.duration_minutes || 30,
      detail: session.detail || "",
      strength_entries: [],
      strength_note: "",
      swim_meters: session.metadata?.swim_meters || "",
      swim_turns: session.metadata?.swim_turns || "",
      swim_note: session.metadata?.swim_note || "",
      source_activity_id: (session.source || session.id || "").startsWith("activity_") ? (session.source || session.id) : null,
    })),
  ];
  if (!healthActivityDrafts.length) {
    healthActivityDrafts = [defaultHealthActivityDraft()];
  }
  deleteRoutineCardButton?.removeAttribute("hidden");
  renderHealthActivityDrafts();
  openQuickDialog();
  activityStatus.textContent = "이 날짜의 운동 루틴 카드를 편집 중입니다.";
}

routineTrack.addEventListener("click", (event) => {
  const editButton = event.target.closest("[data-routine-edit]");
  if (editButton) {
    if (editButton.dataset.routineEdit === "group") {
      openRoutineGroupEditor(editButton.dataset.routineGroupKey);
      return;
    }
    selectActivityArea("health");
    if (editButton.dataset.routineEdit === "workout") {
      const session = workoutHistorySessions.find((item) => item.id === editButton.dataset.workoutSessionId);
      if (!session) {
        activityStatus.textContent = "편집할 루틴 기록을 찾지 못했습니다.";
        return;
      }
      const entries = reindexStrengthEntries(session.entries || []);
      const summary = summarizeStrengthEntries(entries);
      resetHealthEditingState();
      editingSavedWorkoutId = session.id;
      if (activityDate) {
        activityDate.value = session.date || session.started_at?.slice(0, 10) || todayLocalDateValue();
      }
      healthActivityDrafts = [{
        activity_type: "strength",
        duration_minutes: session.duration_minutes || 30,
        detail: session.note || summary || "헬스 루틴",
        strength_entries: entries,
        strength_note: session.note || "",
        source_workout_session_id: session.id,
      }];
      renderHealthActivityDrafts();
      openQuickDialog();
      activityStatus.textContent = "기존 헬스 루틴을 편집 중입니다.";
      return;
    }
    const activityId = editButton.dataset.healthSessionId || "";
    resetHealthEditingState();
    if (activityId.startsWith("activity_")) {
      editingSavedActivityId = activityId;
    }
    if (activityDate) {
      activityDate.value = editButton.dataset.activityDate || todayLocalDateValue();
    }
    healthActivityDrafts = [{
      activity_type: editButton.dataset.activityType || "other",
      duration_minutes: Number(editButton.dataset.activityMinutes || 30),
      detail: editButton.dataset.activityDetail || "",
      strength_entries: [],
      strength_note: "",
      swim_meters: editButton.dataset.swimMeters || "",
      swim_turns: editButton.dataset.swimTurns || "",
      swim_note: editButton.dataset.swimNote || "",
    }];
    renderHealthActivityDrafts();
    openQuickDialog();
    activityStatus.textContent = editingSavedActivityId
      ? "기존 운동 항목을 편집 중입니다."
      : "이전 후보 기록을 바탕으로 새 운동 항목을 입력합니다.";
    return;
  }
  const healthButton = event.target.closest("[data-health-session-id]");
  if (healthButton) {
    selectActivityArea("health");
    const label = healthButton.querySelector("strong")?.textContent || "운동";
    const detail = healthButton.querySelector(".routine-set-list")?.textContent.trim() || "";
    const minutesText = healthButton.querySelector("small")?.textContent || "";
    const minutesMatch = minutesText.match(/(\d+)/);
    const activityType = Object.entries({
      strength: "헬스",
      swimming: "수영",
      running: "러닝",
      walking: "걷기",
      surfing: "서핑",
      yoga: "요가/스트레칭",
      other: "기타",
    }).find(([, value]) => value === label)?.[0] || "other";
    healthActivityDrafts = [{
      ...defaultHealthActivityDraft(),
      activity_type: activityType,
      duration_minutes: minutesMatch ? Number(minutesMatch[1]) : 30,
      detail,
      swim_meters: healthButton.dataset.swimMeters || "",
      swim_turns: healthButton.dataset.swimTurns || "",
      swim_note: healthButton.dataset.swimNote || "",
    }];
    resetHealthEditingState();
    renderHealthActivityDrafts();
    openQuickDialog();
    activityStatus.textContent = "기존 운동 항목을 참고해 새 수정 기록을 입력합니다.";
    return;
  }
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

exerciseCategoryList.addEventListener("click", (event) => {
  if (exerciseLibraryEditMode) {
    const itemRow = event.target.closest("[data-exercise-id]");
    const addButton = event.target.closest("#editor-add-exercise");
    const work = async () => {
      if (addButton) {
        const exercise = {
          name_ko: exerciseCategoryList.querySelector("#editor-new-ko").value,
          name_en: exerciseCategoryList.querySelector("#editor-new-en").value,
          primary_muscle: exerciseCategoryList.querySelector("#editor-new-muscle").value,
          equipment: [],
          favorite: true,
        };
        await queueExerciseLibraryMutation("add", exercise);
        exerciseLibraryStatus.textContent = isSupabaseMode() ? exerciseLibraryStatus.textContent : "새 운동을 추가했습니다.";
        await reloadExerciseLibraryAfterMutation();
        return;
      }
      if (!itemRow) {
        return;
      }
      const exerciseId = itemRow.dataset.exerciseId;
      const item = exerciseLibrary.find((exercise) => exercise.id === exerciseId);
      if (!item) {
        return;
      }
      if (event.target.closest(".editor-toggle-edit")) {
        editingExerciseId = editingExerciseId === exerciseId ? null : exerciseId;
        renderExerciseLibraryManager();
        return;
      }
      if (event.target.closest(".editor-save")) {
        await queueExerciseLibraryMutation("update", { exercise_id: exerciseId, updates: readExerciseEditorUpdates(exerciseId) });
        exerciseLibraryStatus.textContent = isSupabaseMode() ? exerciseLibraryStatus.textContent : "운동 디테일을 수정했습니다.";
        editingExerciseId = null;
        await reloadExerciseLibraryAfterMutation();
        return;
      }
      if (event.target.closest(".editor-archive")) {
        await queueExerciseLibraryMutation("archive", { exercise_id: exerciseId, archived: true });
        exerciseLibraryStatus.textContent = isSupabaseMode() ? exerciseLibraryStatus.textContent : "운동을 목록에서 숨겼습니다.";
        await reloadExerciseLibraryAfterMutation();
        return;
      }
      if (event.target.closest(".editor-delete")) {
        const label = item.name_ko || item.name_en || exerciseId;
        if (!window.confirm(`${label} 운동을 삭제할까요? 과거 기록에는 운동 ID만 남을 수 있습니다.`)) {
          return;
        }
        await queueExerciseLibraryMutation("delete", { exercise_id: exerciseId });
        exerciseLibraryStatus.textContent = isSupabaseMode() ? exerciseLibraryStatus.textContent : "운동을 삭제했습니다.";
        await reloadExerciseLibraryAfterMutation();
        return;
      }
      const direction = event.target.closest(".editor-move-up") ? -1 : event.target.closest(".editor-move-down") ? 1 : 0;
      if (direction) {
        const orderedIds = reorderVisibleExercise(exerciseId, direction, itemRow.dataset.groupMuscle);
        if (!orderedIds) {
          return;
        }
        exerciseLibrary = exerciseLibrary.map((exercise) => {
          const nextOrder = orderedIds.indexOf(exercise.id);
          return nextOrder >= 0 ? { ...exercise, display_order: nextOrder } : exercise;
        });
        renderExerciseLibraryManager();
        await queueExerciseLibraryMutation("reorder", { ordered_ids: orderedIds });
        exerciseLibraryStatus.textContent = isSupabaseMode() ? exerciseLibraryStatus.textContent : "운동 순서를 저장했습니다.";
        await reloadExerciseLibraryAfterMutation();
      }
    };
    event.target.disabled = true;
    work().catch((error) => {
      exerciseLibraryStatus.textContent = error.message;
    }).finally(() => {
      event.target.disabled = false;
    });
    return;
  }
  const button = event.target.closest("[data-exercise-id]");
  if (!button) {
    return;
  }
  const item = exerciseLibrary.find((exercise) => exercise.id === button.dataset.exerciseId);
  renderExerciseDialog(item);
});

exerciseEditMode.addEventListener("click", () => {
  exerciseLibraryEditMode = !exerciseLibraryEditMode;
  editingExerciseId = null;
  exerciseLibraryStatus.textContent = exerciseLibraryEditMode
    ? "편집 모드: 추가, 수정, 순서 관리"
    : "";
  renderExerciseLibraryManager();
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

exerciseRecent.addEventListener("click", () => {
  renderRecentExerciseDialog(selectedExercise());
});

addWorkoutSet.addEventListener("click", () => {
  const isBodyweight = Boolean(workoutBodyweight?.checked);
  const weight = isBodyweight ? null : Number(workoutWeight.value);
  const reps = Number.parseInt(workoutReps.value, 10);
  const rpe = workoutRpe.value ? Number(workoutRpe.value) : null;
  if ((!isBodyweight && (!Number.isFinite(weight) || weight < 0)) || !Number.isFinite(reps) || reps <= 0) {
    workoutStatus.textContent = "무게와 반복 수를 확인하세요.";
    return;
  }

  const muscle = workoutMuscle.value;
  const exercise = workoutExercise.value;
  if (!exercise) {
    workoutStatus.textContent = "운동을 선택하거나 없는 운동명을 추가하세요.";
    return;
  }
  const nextEntry = {
    muscle_group: muscle,
    exercise,
    weight_kg: weight,
    bodyweight: isBodyweight,
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
    workoutStatus.textContent = `${exerciseLabel(muscle, exercise)} 세트를 수정했습니다.`;
    const returnState = editingReturnState;
    resetWorkoutEditMode();
    applyWorkoutFormState(returnState);
    persistWorkoutDraft();
    return;
  }

  addWorkoutEntry(nextEntry);
  workoutStatus.textContent = `${exerciseLabel(muscle, exercise)} 세트를 추가했습니다.`;
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
    workoutStatus.textContent = `${exerciseLabel(workoutEntries[index].muscle_group, workoutEntries[index].exercise)} 세트를 수정 중입니다.`;
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
  workoutStatus.textContent = "세트를 삭제했습니다.";
});

workoutForm.addEventListener("submit", (event) => {
  event.preventDefault();
  if (!workoutEntries.length) {
    workoutStatus.textContent = "최소 1개 세트를 추가하세요.";
    return;
  }

  const strengthEntries = reindexStrengthEntries(workoutEntries);
  const summary = summarizeStrengthEntries(strengthEntries);
  if (Number.isInteger(activeStrengthDraftIndex) && healthActivityDrafts[activeStrengthDraftIndex]) {
    healthActivityDrafts[activeStrengthDraftIndex] = {
      ...healthActivityDrafts[activeStrengthDraftIndex],
      strength_entries: strengthEntries,
      strength_note: workoutNote.value,
      detail: healthActivityDrafts[activeStrengthDraftIndex].detail || summary || "헬스 루틴",
    };
  } else {
    healthActivityDrafts.push({
      activity_type: "strength",
      duration_minutes: 30,
      detail: summary || "헬스 루틴",
      strength_entries: strengthEntries,
      strength_note: workoutNote.value,
    });
    workoutStatus.textContent = "헬스 루틴 디테일이 Quick 항목에 반영되었습니다.";
  }
  renderHealthActivityDrafts();
  writeHealthQuickDraft();
  activeStrengthDraftIndex = null;
  workoutEntries = [];
  workoutNote.value = "";
  renderWorkoutSets();
  clearWorkoutDraft();
  editingHealthActivityIndex = null;
  closeWorkoutDialog();
});

capturesList.addEventListener("click", (event) => {
  const viewButton = event.target.closest(".capture-view");
  const button = viewButton;
  if (!button) {
    return;
  }

  const historyId = button.dataset.historyId;
  button.disabled = true;

  if (viewButton) {
    openCaptureDetail(historyId);
    button.disabled = false;
    return;
  }
});

captureDetailContent?.addEventListener("click", (event) => {
  const saveButton = event.target.closest("[data-capture-detail-save]");
  const deleteButton = event.target.closest("[data-capture-detail-delete]");
  const closeButton = event.target.closest("[data-capture-detail-close]");
  if (closeButton) {
    captureDetailDialog?.close();
    return;
  }
  if (deleteButton) {
    const historyId = event.target.closest(".capture-edit-form")?.dataset.historyId;
    if (!historyId) return;
    const item = captureByHistoryId(historyId);
    const label = captureHistoryBody(item || {}).slice(0, 48) || historyId;
    if (!window.confirm(`이 입력 히스토리 원장을 삭제할까요?\n\n${label}`)) {
      return;
    }
    captureStatus.textContent = "히스토리 원장 삭제 중...";
    deleteButton.disabled = true;
    deleteCaptureDetail(historyId)
      .then((result) => {
        captureDetailDialog?.close();
        captureHistoryState = captureHistoryState.filter((entry) => entry.history_id !== historyId && entry.id !== historyId);
        renderCaptures(captureHistoryState);
        captureStatus.textContent = result?.queued
          ? "삭제 요청을 저장했습니다. Mac Hermes Worker 처리 후 원장에서도 제거됩니다."
          : "히스토리 원장을 삭제했습니다.";
        if (!isSupabaseMode()) {
          return loadDashboard();
        }
        return null;
      })
      .catch((error) => {
        captureStatus.textContent = error.message;
      })
      .finally(() => {
        deleteButton.disabled = false;
      });
    return;
  }
  if (!saveButton) return;
  const historyId = event.target.closest(".capture-edit-form")?.dataset.historyId;
  if (!historyId) return;
  saveButton.disabled = true;
  captureStatus.textContent = "히스토리 수정 내용을 저장 중...";
  saveCaptureDetail(historyId)
    .then(() => {
      captureDetailDialog?.close();
      captureStatus.textContent = "히스토리 수정 완료. Dashboard updated.";
      return loadDashboard();
    })
    .catch((error) => {
      captureStatus.textContent = error.message;
      saveButton.disabled = false;
    });
});

captureStatusFilter?.addEventListener("change", () => {
  renderCaptures();
});

[captureYearFilter, captureMonthFilter].forEach((control) => {
  control?.addEventListener("change", () => {
    syncSelectedHistoryMonthFromControls();
    loadDashboard();
  });
});

activitySessions?.addEventListener("click", (event) => {
  const ignoreButton = event.target.closest(".activity-history-ignore");
  const editButton = event.target.closest(".activity-history-edit");
  if (!ignoreButton && !editButton) {
    return;
  }

  if (ignoreButton) {
    const activityId = ignoreButton.dataset.activityId;
    ignoreButton.disabled = true;
    activityStatus.textContent = "히스토리에서 제외 중...";
    ignoreActivitySession(activityId)
      .then(() => {
        activityStatus.textContent = "히스토리 항목을 집계에서 제외했습니다.";
        return loadDashboard();
      })
      .catch((error) => {
        activityStatus.textContent = error.message;
        ignoreButton.disabled = false;
      });
    return;
  }

  const area = editButton.dataset.activityArea || "work";
  selectActivityArea(area);
  if (activityDate) {
    activityDate.value = editButton.dataset.activityDate || todayLocalDateValue();
  }
  updateDurationSlider(editButton.dataset.activityMinutes || 30, "history");
  activityPlace.value = editButton.dataset.activityPlace || "";
  activitySubcategory.value = editButton.dataset.activitySubcategory || "";
  activityDetail.value = editButton.dataset.activityDetail || "";
  activityParseMemo.checked = false;
  resetHealthEditingState();
  if (area === "health") {
    editingSavedActivityId = editButton.dataset.activityId || null;
    healthActivityDrafts = [{
      activity_type: editButton.dataset.activitySubcategory || "other",
      duration_minutes: Number(editButton.dataset.activityMinutes || 30),
      detail: editButton.dataset.activityDetail || "",
      strength_entries: [],
      strength_note: "",
      source_activity_id: editButton.dataset.activityId || null,
    }];
    renderHealthActivityDrafts();
  } else {
    editingGenericActivityId = editButton.dataset.activityId || null;
  }
  openQuickDialog();
  activityStatus.textContent = "히스토리 항목을 수정 중입니다.";
});

aiWorkProjects?.addEventListener("click", (event) => {
  const card = event.target.closest("[data-project-id]");
  if (!card) {
    return;
  }
  selectedAiWorkProjectId = card.dataset.projectId;
  renderAiWorkProjects();
});

aiWorkAddButton?.addEventListener("click", () => {
  openAiWorkProjectDialog("create");
});

aiWorkEditButton?.addEventListener("click", () => {
  const project = selectedAiWorkProject();
  if (!project) {
    setWorkspaceStatus(aiWorkStatus, "편집할 프로젝트를 먼저 선택하세요.", "warning");
    return;
  }
  openAiWorkProjectDialog("update", project);
});

aiWorkDialogClose?.addEventListener("click", () => {
  aiWorkProjectDialog?.close();
});

aiWorkBrowseFolder?.addEventListener("click", () => {
  if (isSupabaseMode()) {
    setWorkspaceStatus(aiWorkFormStatus, "Hosted mode에서는 Mac Finder를 열 수 없습니다.", "warning");
    return;
  }
  aiWorkBrowseFolder.disabled = true;
  setWorkspaceStatus(aiWorkFormStatus, "Opening Finder...", "");
  postJson("/api/choose-folder", {})
    .then((result) => {
      if (result.cancelled) {
        setWorkspaceStatus(aiWorkFormStatus, "Folder selection cancelled.", "warning");
        return;
      }
      aiWorkProjectPath.value = result.path || "";
      setWorkspaceStatus(aiWorkFormStatus, "Folder selected.", "ok");
    })
    .catch((error) => {
      setWorkspaceStatus(aiWorkFormStatus, error.message, "error");
    })
    .finally(() => {
      aiWorkBrowseFolder.disabled = false;
    });
});

aiWorkProjectDialog?.addEventListener("click", (event) => {
  if (event.target === aiWorkProjectDialog) {
    aiWorkProjectDialog.close();
  }
});

aiWorkImportButton?.addEventListener("click", () => {
  if (isSupabaseMode()) {
    setWorkspaceStatus(aiWorkStatus, "Hosted mode에서는 저장 이후 evidence 분석 단계가 이어집니다.", "warning");
    return;
  }
  aiWorkImportButton.disabled = true;
  setWorkspaceStatus(aiWorkStatus, "Checking local evidence...", "");
  postJson("/api/work-import", { dry_run: true, include_clean: true })
    .then((result) => {
      setWorkspaceStatus(aiWorkStatus, `Dry run complete · ${result.event_count || 0} event(s)`, "ok");
      return refreshAiWork();
    })
    .catch((error) => {
      setWorkspaceStatus(aiWorkStatus, error.message, "error");
    })
    .finally(() => {
      aiWorkImportButton.disabled = false;
    });
});

aiWorkProjectForm?.addEventListener("submit", (event) => {
  event.preventDefault();
  if (isSupabaseMode()) {
    setWorkspaceStatus(aiWorkFormStatus, "Hosted mode 프로젝트 등록은 Supabase queue 연결 후 지원합니다.", "warning");
    return;
  }
  const payload = aiWorkPayloadFromForm();
  setWorkspaceStatus(aiWorkFormStatus, payload.mode === "update" ? "Updating project..." : "Adding project...", "");
  postJson("/api/work-projects", payload)
    .then((result) => {
      selectedAiWorkProjectId = result.project?.project_id || selectedAiWorkProjectId;
      setWorkspaceStatus(aiWorkFormStatus, payload.mode === "update" ? "Project updated." : "Project added.", "ok");
      aiWorkProjectDialog?.close();
      return refreshAiWork();
    })
    .catch((error) => {
      setWorkspaceStatus(aiWorkFormStatus, error.message, "error");
    });
});

workspaceLinks.forEach((link) => {
  link.addEventListener("click", (event) => {
    event.preventDefault();
    setActiveView(link.dataset.viewLink);
    setMobileDrawer(false);
  });
});

window.addEventListener("hashchange", () => {
  handleRouteHash();
});

openQuickButton?.addEventListener("click", openQuickDialog);
floatingQuickButton?.addEventListener("click", openQuickDialog);

openMenuButton?.addEventListener("click", () => setMobileDrawer(true));
closeMenuButton?.addEventListener("click", () => setMobileDrawer(false));
drawerBackdrop?.addEventListener("click", () => setMobileDrawer(false));

closeQuickButton?.addEventListener("click", () => {
  quickDialog?.close();
});

quickDialog?.addEventListener("click", (event) => {
  if (event.target === quickDialog) {
    quickDialog.close();
  }
});

mainPeriodToggle?.addEventListener("click", () => {
  mainPeriodMode = mainPeriodMode === "month" ? "period" : "month";
  if (latestMainAgentPayload) {
    renderMainAgent(latestMainAgentPayload);
  }
});

workspaceOverview.addEventListener("click", (event) => {
  const card = event.target.closest("[data-overview-view]");
  if (!card) {
    return;
  }
  setActiveView(card.dataset.overviewView);
});

currentStayForm?.addEventListener("submit", (event) => {
  event.preventDefault();
  const payload = currentStayPayloadFromForm();
  if (!payload.stay_id || !payload.region || !payload.start_date || !payload.timezone) {
    setWorkspaceStatus(currentStayStatus, "Stay ID, Region, Start Day, Timezone은 필수입니다.", "error");
    return;
  }
  if (isSupabaseMode()) {
    const stay = normalizeCurrentStay({
      ...payload,
      notes: payload.note ? [payload.note] : DEFAULT_CURRENT_STAY.notes,
    });
    writeStoredCurrentStay(stay);
    renderCurrentStay(stay);
    renderStayIndex({ active_stay_id: stay.stay_id, stays: [stay] });
    setWorkspaceStatus(currentStayStatus, `현재 활성 지역으로 저장됨: ${stay.region} · ${stay.timezone}`, "ok");
    return;
  }
  const submitButton = currentStayForm.querySelector('button[type="submit"]');
  submitButton.disabled = true;
  setWorkspaceStatus(currentStayStatus, "Saving current stay...", "");
  postJson("/api/current-stay", payload)
    .then((result) => {
      renderCurrentStay(result.stay);
      return loadJson("/api/current-stay").then((payload) => {
        renderStayIndex(payload.index || {});
        return result;
      });
    })
    .then((result) => {
      return loadDashboard().then(() => result);
    })
    .then((result) => {
      renderCurrentStay(result.stay);
      const stateLabel = result.stay.status === "closed" ? "완료 지역으로 저장됨" : "현재 활성 지역으로 저장됨";
      setWorkspaceStatus(currentStayStatus, `${stateLabel}: ${result.stay.region} · ${result.stay.timezone}`, "ok");
    })
    .catch((error) => {
      setWorkspaceStatus(currentStayStatus, error.message, "error");
    })
    .finally(() => {
      submitButton.disabled = false;
    });
});

stayBackupButton?.addEventListener("click", () => {
  if (isSupabaseMode()) {
    setWorkspaceStatus(stayBackupStatus, "Hosted mode에서는 Mac Hermes Worker에서 stay backup을 실행합니다.", "warning");
    return;
  }
  stayBackupButton.disabled = true;
  setWorkspaceStatus(stayBackupStatus, "Creating current stay package and backup...", "");
  fetch("/api/stay-package", { method: "POST" })
    .then(async (response) => {
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.error || "Stay backup failed.");
      }
      setWorkspaceStatus(
        stayBackupStatus,
        `Backup created: ${payload.backup_path || payload.package_path} · ${payload.file_count || 0} files`,
        "ok",
      );
    })
    .catch((error) => {
      setWorkspaceStatus(stayBackupStatus, error.message, "error");
    })
    .finally(() => {
      stayBackupButton.disabled = false;
    });
});

[workoutMuscle, workoutExercise, exerciseSearch, workoutWeight, workoutReps, workoutBodyweight, workoutRpe, workoutNote].filter(Boolean).forEach((element) => {
  element.addEventListener("change", persistWorkoutDraft);
  element.addEventListener("input", persistWorkoutDraft);
});

workoutBodyweight?.addEventListener("change", () => {
  syncBodyweightInputState();
  updateLatestExerciseGuide();
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
installInputFocusMode();
activeActivity = readActiveActivity();
updateDurationSlider(activityDurationSlider.value, "manual");
resetActivityDate();
syncActiveActivityUi();
if (activeActivity) {
  activeActivityTick = setInterval(syncActiveActivityUi, 30000);
}
updateActivityAreaUi();
applyQuickAreaPrefill();
syncBodyweightInputState();
renderWorkoutSets();
renderHealthActivityDrafts();
renderCurrentStay(readStoredCurrentStay());
renderStayIndex({ active_stay_id: activeStay.stay_id, stays: [activeStay] });
handleRouteHash();
loadAppConfig()
  .then(() => {
    setCloudModeUi();
    return initNomadAuth(appConfig, {
      onStateChange: (session) => {
        if (isSupabaseMode() && session) {
          flushCloudQueueFallback()
            .then((result) => {
              if (result.flushed && captureStatus) {
                captureStatus.textContent = `모바일 임시 저장 ${result.flushed}개를 cloud queue로 보냈습니다.`;
              }
            })
            .then(loadDashboard)
            .catch((error) => {
              summary.textContent = error.message;
            });
        }
      },
    });
  })
  .then(() => flushCloudQueueFallback())
  .then(() => {
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

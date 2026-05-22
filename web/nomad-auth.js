const AUTH_STORAGE_KEY = "nomad-life.supabase.auth.v1";

let supabaseClient = null;
let authSession = null;
let authConfig = { mode: "local", supabaseUrl: "", supabaseAnonKey: "" };

function authElements() {
  return {
    panel: document.querySelector("#auth-panel"),
    form: document.querySelector("#auth-form"),
    email: document.querySelector("#auth-email"),
    password: document.querySelector("#auth-password"),
    signIn: document.querySelector("#auth-sign-in"),
    signUp: document.querySelector("#auth-sign-up"),
    signOut: document.querySelector("#auth-sign-out"),
    status: document.querySelector("#auth-status"),
    user: document.querySelector("#auth-user"),
  };
}

export function isNomadCloudMode(config = authConfig) {
  return config.mode === "supabase" && config.supabaseUrl && config.supabaseAnonKey;
}

export function getNomadAuthToken() {
  return authSession?.access_token || "";
}

export function getNomadUserId() {
  return authSession?.user?.id || "";
}

export async function requireNomadSession() {
  if (!isNomadCloudMode()) return null;
  if (authSession?.access_token) return authSession;
  throw new Error("로그인이 필요합니다.");
}

function renderAuthState() {
  const elements = authElements();
  if (!elements.panel) return;
  const cloud = isNomadCloudMode();
  const signedIn = Boolean(authSession?.user);
  document.body.classList.toggle("nomad-auth-cloud", cloud);
  document.body.classList.toggle("nomad-auth-signed-in", cloud && signedIn);
  document.body.classList.toggle("nomad-auth-signed-out", cloud && !signedIn);
  elements.panel.hidden = !cloud;
  elements.panel.dataset.state = signedIn ? "signed-in" : "signed-out";
  if (elements.form) {
    elements.form.hidden = signedIn;
  }
  if (elements.signOut) {
    elements.signOut.hidden = !signedIn;
  }
  if (elements.user) {
    elements.user.textContent = signedIn ? authSession.user.email || "로그인됨" : "";
  }
  if (elements.status && signedIn) {
    elements.status.textContent = "이 기기/앱에서는 로그인 세션을 유지합니다.";
  }
}

async function loadSupabaseClient() {
  if (supabaseClient) return supabaseClient;
  const { createClient } = await import("https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/+esm");
  supabaseClient = createClient(authConfig.supabaseUrl, authConfig.supabaseAnonKey, {
    auth: {
      autoRefreshToken: true,
      detectSessionInUrl: true,
      persistSession: true,
      storageKey: AUTH_STORAGE_KEY,
    },
  });
  return supabaseClient;
}

async function refreshSession() {
  if (!supabaseClient) return null;
  const { data, error } = await supabaseClient.auth.getSession();
  if (error) throw error;
  authSession = data.session || null;
  renderAuthState();
  return authSession;
}

export async function initNomadAuth(config, options = {}) {
  authConfig = { ...authConfig, ...config };
  renderAuthState();
  if (!isNomadCloudMode()) {
    options.onStateChange?.(null);
    return null;
  }
  const client = await loadSupabaseClient();
  const elements = authElements();

  elements.form?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const submitter = event.submitter;
    const email = elements.email?.value.trim();
    const password = elements.password?.value || "";
    if (!email || !password) {
      elements.status.textContent = "이메일과 비밀번호를 입력하세요.";
      return;
    }
    elements.status.textContent = "로그인 중...";
    try {
      const isSignUp = submitter?.id === "auth-sign-up";
      const result = isSignUp
        ? await client.auth.signUp({ email, password })
        : await client.auth.signInWithPassword({ email, password });
      if (result.error) throw result.error;
      authSession = result.data.session || authSession;
      if (isSignUp && !result.data.session) {
        elements.status.textContent = "가입 확인 메일을 보냈습니다. 확인 후 다시 로그인하세요.";
        renderAuthState();
        options.onStateChange?.(authSession);
        return;
      }
      renderAuthState();
      options.onStateChange?.(authSession);
    } catch (error) {
      elements.status.textContent = error.message || "로그인에 실패했습니다.";
    }
  });

  elements.signOut?.addEventListener("click", async () => {
    elements.status.textContent = "로그아웃 중...";
    const { error } = await client.auth.signOut();
    if (error) {
      elements.status.textContent = error.message;
      return;
    }
    authSession = null;
    renderAuthState();
    options.onStateChange?.(authSession);
  });

  client.auth.onAuthStateChange((_event, session) => {
    authSession = session || null;
    renderAuthState();
    options.onStateChange?.(authSession);
  });

  return refreshSession();
}

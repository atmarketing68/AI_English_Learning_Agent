import axios, { AxiosError, AxiosHeaders } from 'axios';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

// ── Persist helpers ────────────────────────────────────────────────────────────
function getPersistedAuth(): { token: string | null; refreshToken: string | null } {
  if (typeof window === 'undefined') return { token: null, refreshToken: null };
  try {
    const raw = localStorage.getItem('agen-auth');
    const state = raw ? JSON.parse(raw)?.state ?? {} : {};
    return { token: state.token ?? null, refreshToken: state.refreshToken ?? null };
  } catch {
    return { token: null, refreshToken: null };
  }
}

function clearAuth() {
  if (typeof window !== 'undefined') localStorage.removeItem('agen-auth');
}

function patchStoredAccessToken(newToken: string) {
  if (typeof window === 'undefined') return;
  try {
    const raw = localStorage.getItem('agen-auth');
    if (!raw) return;
    const parsed = JSON.parse(raw);
    parsed.state.token = newToken;
    localStorage.setItem('agen-auth', JSON.stringify(parsed));
  } catch { /* ignore */ }
}

function redirectToLogin() {
  if (typeof window === 'undefined') return;
  clearAuth();
  // eslint-disable-next-line @next/next/no-location-assign-relative-destination
  window.location.href = '/login';
}

// ── Request interceptor — attach JWT ──────────────────────────────────────────
api.interceptors.request.use((config) => {
  const { token } = getPersistedAuth();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// ── Response interceptor — silent token refresh on 401 ────────────────────────
// A single shared promise prevents multiple parallel refresh requests.
let _refreshPromise: Promise<string> | null = null;

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as typeof error.config & { _retried?: boolean };

    // Only intercept 401s that haven't been retried yet. A 401 from login itself
    // means a wrong password — let the form show it instead of redirecting.
    if (error.response?.status !== 401 || !original || original._retried || original.url?.startsWith('/auth/login')) {
      return Promise.reject(error);
    }

    const { refreshToken } = getPersistedAuth();
    if (!refreshToken) {
      redirectToLogin();
      return Promise.reject(error);
    }

    // Deduplicate concurrent refreshes
    if (!_refreshPromise) {
      _refreshPromise = axios
        .post(`${API_BASE}/auth/refresh`, { refresh_token: refreshToken })
        .then((res: { data: { access_token: string } }) => {
          const newToken = res.data.access_token;
          patchStoredAccessToken(newToken);
          return newToken;
        })
        .catch(() => {
          redirectToLogin();
          return Promise.reject(new Error('Session expired'));
        })
        .finally(() => { _refreshPromise = null; });
    }

    try {
      const newToken = await _refreshPromise;
      original._retried = true;
      // error.config.headers is an AxiosHeaders instance on InternalAxiosRequestConfig
      if (original.headers instanceof AxiosHeaders) {
        original.headers.set('Authorization', `Bearer ${newToken}`);
      } else {
        original.headers = AxiosHeaders.from({
          ...(original.headers as Record<string, string> | undefined),
          Authorization: `Bearer ${newToken}`,
        });
      }
      return api(original);
    } catch {
      return Promise.reject(error);
    }
  }
);

export default api;

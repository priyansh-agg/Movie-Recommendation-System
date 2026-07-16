import axios, {
  type AxiosError,
  type AxiosRequestConfig,
  type InternalAxiosRequestConfig,
} from 'axios';

const client = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ── Request Interceptor ──────────────────────────────────────────────
// Attach the access token from persisted Zustand auth store on every request.
client.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    try {
      const raw = localStorage.getItem('auth-storage');
      if (raw) {
        const { state } = JSON.parse(raw);
        if (state?.token) {
          config.headers.Authorization = `Bearer ${state.token}`;
        }
      }
    } catch {
      // localStorage may be unavailable or data malformed — proceed without token
    }
    return config;
  },
  (error) => Promise.reject(error),
);

// ── Response Interceptor — 401 Refresh Logic ─────────────────────────
// When a 401 is received we attempt to refresh the access token exactly once.
// All concurrent requests that fail with 401 while a refresh is in flight are
// queued and retried once the refresh completes (or rejected if it fails).

let isRefreshing = false;
let failedQueue: Array<{
  resolve: (token: string) => void;
  reject: (error: unknown) => void;
}> = [];

function processQueue(error: unknown, token: string | null = null) {
  for (const prom of failedQueue) {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token!);
    }
  }
  failedQueue = [];
}

function clearAuthAndRedirect() {
  try {
    const raw = localStorage.getItem('auth-storage');
    if (raw) {
      const parsed = JSON.parse(raw);
      parsed.state = {
        ...parsed.state,
        token: null,
        refreshToken: null,
        userId: null,
        user: null,
        isAuthenticated: false,
      };
      localStorage.setItem('auth-storage', JSON.stringify(parsed));
    }
  } catch {
    localStorage.removeItem('auth-storage');
  }
  // Only redirect if not already on the login page
  if (!window.location.pathname.includes('/login')) {
    window.location.href = '/login';
  }
}

client.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };

    // Only handle 401 and only once per request
    if (error.response?.status !== 401 || originalRequest._retry) {
      return Promise.reject(error);
    }

    // Don't attempt refresh for auth endpoints themselves
    const url = originalRequest.url ?? '';
    if (url.includes('/auth/login') || url.includes('/auth/register') || url.includes('/auth/refresh')) {
      return Promise.reject(error);
    }

    originalRequest._retry = true;

    // If a refresh is already in flight, queue this request
    if (isRefreshing) {
      return new Promise<string>((resolve, reject) => {
        failedQueue.push({ resolve, reject });
      }).then((token) => {
        originalRequest.headers.Authorization = `Bearer ${token}`;
        return client(originalRequest);
      });
    }

    isRefreshing = true;

    try {
      let refreshToken: string | null = null;
      try {
        const raw = localStorage.getItem('auth-storage');
        if (raw) {
          const { state } = JSON.parse(raw);
          refreshToken = state?.refreshToken ?? null;
        }
      } catch {
        // ignore parse errors
      }

      if (!refreshToken) {
        throw new Error('No refresh token available');
      }

      // Call the refresh endpoint directly with a fresh axios instance
      // to avoid the request interceptor attaching the expired token.
      const refreshClient = axios.create({
        baseURL: 'http://localhost:8000/api/v1',
        timeout: 10000,
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      });

      const response = await refreshClient.post('/auth/refresh', {
        refresh_token: refreshToken,
      });

      const { access_token, refresh_token: newRefreshToken } = response.data;

      // Persist the new tokens into Zustand's persisted storage
      try {
        const raw = localStorage.getItem('auth-storage');
        if (raw) {
          const parsed = JSON.parse(raw);
          parsed.state = {
            ...parsed.state,
            token: access_token,
            refreshToken: newRefreshToken,
          };
          localStorage.setItem('auth-storage', JSON.stringify(parsed));
        }
      } catch {
        // ignore storage errors
      }

      // Process all queued requests with the new token
      processQueue(null, access_token);

      // Retry the original request
      originalRequest.headers.Authorization = `Bearer ${access_token}`;
      return client(originalRequest);
    } catch (refreshError) {
      processQueue(refreshError, null);
      clearAuthAndRedirect();
      return Promise.reject(refreshError);
    } finally {
      isRefreshing = false;
    }
  },
);

export default client;

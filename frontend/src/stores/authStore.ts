import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import * as authApi from '../api/auth';
import { getProfile, type UserProfile } from '../api/user';

interface AuthState {
  token: string | null;
  refreshToken: string | null;
  userId: number | null;
  user: UserProfile | null;
  isAuthenticated: boolean;
}

interface AuthActions {
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, username: string, password: string) => Promise<void>;
  logout: () => void;
  fetchProfile: () => Promise<void>;
  setTokens: (accessToken: string, refreshToken: string) => void;
}

type AuthStore = AuthState & AuthActions;

const initialState: AuthState = {
  token: null,
  refreshToken: null,
  userId: null,
  user: null,
  isAuthenticated: false,
};

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      ...initialState,

      login: async (email, password) => {
        const data = await authApi.login(email, password);
        set({
          token: data.access_token,
          refreshToken: data.refresh_token,
          userId: data.user_id,
          isAuthenticated: true,
        });
        try {
          const profile = await getProfile();
          set({ user: profile });
        } catch { /* profile fetch optional */ }
      },

      register: async (email, username, password) => {
        const data = await authApi.register(email, username, password);
        set({
          token: data.access_token,
          refreshToken: data.refresh_token,
          userId: data.user_id,
          isAuthenticated: true,
        });
        try {
          const profile = await getProfile();
          set({ user: profile });
        } catch { /* profile fetch optional */ }
      },

      logout: () => set(initialState),

      fetchProfile: async () => {
        if (!get().isAuthenticated) return;
        try {
          const profile = await getProfile();
          set({ user: profile });
        } catch { /* interceptor handles auth errors */ }
      },

      setTokens: (accessToken, refreshToken) => {
        set({ token: accessToken, refreshToken, isAuthenticated: true });
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        token: state.token,
        refreshToken: state.refreshToken,
        userId: state.userId,
        isAuthenticated: state.isAuthenticated,
      }),
    },
  ),
);

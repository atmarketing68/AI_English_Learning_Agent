import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { LearnerProfile } from '@/types';

interface AuthState {
  token: string | null;
  refreshToken: string | null;
  learner: LearnerProfile | null;
  isAuthenticated: boolean;
  userRole: 'learner' | 'parent' | null;
  setAuth: (accessToken: string, refreshToken: string | null) => void;
  setLearner: (learner: LearnerProfile) => void;
  setUserRole: (role: 'learner' | 'parent' | null) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      refreshToken: null,
      learner: null,
      userRole: null,
      isAuthenticated: false,

      setAuth: (accessToken, refreshToken) => {
        set({ token: accessToken, refreshToken, isAuthenticated: true });
      },

      setLearner: (learner) => set({ learner }),

      setUserRole: (role) => set({ userRole: role }),

      logout: () => {
        set({ token: null, refreshToken: null, learner: null, userRole: null, isAuthenticated: false });
      },
    }),
    {
      name: 'agen-auth',
      partialize: (state) => ({
        token: state.token,
        refreshToken: state.refreshToken,
        isAuthenticated: state.isAuthenticated,
        userRole: state.userRole,
      }),
    }
  )
);

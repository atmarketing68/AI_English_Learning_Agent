import { useSyncExternalStore } from 'react';
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

const subscribeHydration = (onDone: () => void) => useAuthStore.persist.onFinishHydration(onDone);

/**
 * True once the persisted session has been restored from localStorage.
 * Pages must wait for this before redirecting a "logged-out" user: on a hard
 * reload the store starts empty for a moment, and redirecting then would log
 * out every learner who refreshes the page.
 */
export function useAuthHydrated(): boolean {
  return useSyncExternalStore(
    subscribeHydration,
    () => useAuthStore.persist.hasHydrated(),
    () => false,
  );
}

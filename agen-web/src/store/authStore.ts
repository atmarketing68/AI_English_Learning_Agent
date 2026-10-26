import { useSyncExternalStore } from 'react';
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { LearnerProfile } from '@/types';
import { resetAnalytics } from '@/lib/analytics';

interface AuthState {
  token: string | null;
  refreshToken: string | null;
  learner: LearnerProfile | null;
  isAuthenticated: boolean;
  userRole: 'learner' | 'parent' | 'teacher' | null;
  /** G3 · guest trial account (no email yet). */
  isGuest: boolean;
  setAuth: (accessToken: string, refreshToken: string | null) => void;
  setGuest: (isGuest: boolean) => void;
  setLearner: (learner: LearnerProfile) => void;
  setUserRole: (role: 'learner' | 'parent' | 'teacher' | null) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      refreshToken: null,
      learner: null,
      userRole: null,
      isGuest: false,
      isAuthenticated: false,

      setAuth: (accessToken, refreshToken) => {
        set({ token: accessToken, refreshToken, isAuthenticated: true });
      },

      setGuest: (isGuest) => set({ isGuest }),

      setLearner: (learner) => set({ learner }),

      setUserRole: (role) => set({ userRole: role }),

      logout: () => {
        resetAnalytics();
        set({ token: null, refreshToken: null, learner: null, userRole: null, isGuest: false, isAuthenticated: false });
      },
    }),
    {
      name: 'agen-auth',
      partialize: (state) => ({
        token: state.token,
        refreshToken: state.refreshToken,
        isAuthenticated: state.isAuthenticated,
        userRole: state.userRole,
        isGuest: state.isGuest,
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

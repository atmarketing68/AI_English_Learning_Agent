/**
 * G4 · Giao diện: "vivid" (vui nhộn, cho học sinh nhỏ) hoặc "classic"
 * (chuyên nghiệp, hiện đại — cho người lớn đi làm và phụ huynh).
 *
 * The skin is a `data-skin` attribute on <html>; CSS tokens do the rest.
 * The value is cached in localStorage so the first paint already has the
 * right look (an inline script in layout.tsx reads it before hydration).
 */
import { create } from 'zustand';
import type { LearnerProfile, UiSkin } from '@/types';

export const SKIN_STORAGE_KEY = 'agen-skin';
/** Learners younger than this get the playful look by default. */
export const VIVID_MAX_AGE = 16;

interface SkinState {
  skin: UiSkin;
  setSkin: (skin: UiSkin) => void;
}

export const useSkinStore = create<SkinState>()((set) => ({
  skin: 'classic',
  setSkin: (skin) => {
    set({ skin });
    applySkin(skin);
  },
}));

export function applySkin(skin: UiSkin): void {
  if (typeof document === 'undefined') return;
  document.documentElement.dataset.skin = skin;
  try { localStorage.setItem(SKIN_STORAGE_KEY, skin); } catch { /* private mode */ }
}

/** The look a learner gets: their explicit choice, else by age. */
export function skinForLearner(learner: Pick<LearnerProfile, 'ui_skin' | 'age'> | null | undefined): UiSkin {
  if (!learner) return 'classic';
  if (learner.ui_skin === 'vivid' || learner.ui_skin === 'classic') return learner.ui_skin;
  return learner.age != null && learner.age < VIVID_MAX_AGE ? 'vivid' : 'classic';
}

export const useSkin = () => useSkinStore((s) => s.skin);

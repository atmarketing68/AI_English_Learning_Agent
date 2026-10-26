import api from '@/lib/api';

// ── Types (mirror backend api/speaking.py pronunciation endpoint) ─────────────
export interface PronunciationResult {
  overall_score: number;
  accuracy: number;
  coverage: number;
  fluency: number;
  target_word_count: number;
  said_word_count: number;
  missed_words: string[];
  extra_words: string[];
  feedback_vi: string;
  xp_earned: number;
}

/**
 * Score a read-aloud attempt. The transcript comes from the browser Web Speech
 * API (see speechService.ts); this posts it with the target sentence for scoring.
 */
export async function scorePronunciation(
  targetText: string,
  transcript: string,
  durationSeconds?: number,
): Promise<PronunciationResult> {
  const res = await api.post('/speaking/pronunciation', {
    target_text: targetText,
    transcript,
    duration_seconds: durationSeconds ?? null,
  });
  return res.data;
}

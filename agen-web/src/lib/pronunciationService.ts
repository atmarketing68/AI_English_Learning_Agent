import api from '@/lib/api';

// ── Types (mirror backend api/speaking.py pronunciation endpoint) ─────────────
export interface WordVerdict {
  word: string;
  status: 'ok' | 'wrong' | 'missed';
  heard?: string | null;
}

export interface SoundTip {
  sound: string;
  tip_vi: string;
  words: string[];
}

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
  words: WordVerdict[];
  sound_tips: SoundTip[];
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
  source: string = 'practice',
): Promise<PronunciationResult> {
  const res = await api.post('/speaking/pronunciation', {
    target_text: targetText,
    transcript,
    duration_seconds: durationSeconds ?? null,
    source,
  });
  return res.data;
}

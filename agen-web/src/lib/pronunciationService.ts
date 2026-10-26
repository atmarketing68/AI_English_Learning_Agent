import api from '@/lib/api';

// ── Types (mirror backend api/speaking.py pronunciation endpoints) ────────────
export interface PhonemeVerdict {
  phoneme: string;
  score: number | null;
}

export interface WordVerdict {
  word: string;
  status: 'ok' | 'wrong' | 'missed';
  heard?: string | null;
  /** Phoneme mode only (0–100). */
  score?: number | null;
  phonemes?: PhonemeVerdict[];
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
  /** "phoneme" when the audio was scored to the phoneme, "transcript" otherwise. */
  mode: 'phoneme' | 'transcript';
  completeness?: number | null;
  prosody?: number | null;
  recognized_text?: string | null;
}

export interface PronunciationStatus {
  phoneme_enabled: boolean;
  provider: string | null;
}

let statusPromise: Promise<PronunciationStatus> | null = null;

/** Whether the server can score audio to the phoneme (cached for the session). */
export function getPronunciationStatus(): Promise<PronunciationStatus> {
  if (!statusPromise) {
    statusPromise = api.get<PronunciationStatus>('/speaking/pronunciation/status')
      .then(r => r.data)
      .catch(() => { statusPromise = null; return { phoneme_enabled: false, provider: null }; });
  }
  return statusPromise;
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

/** Phoneme-level scoring of a WAV take (server falls back to the transcript scorer). */
export async function scorePronunciationAudio(
  wav: Blob,
  targetText: string,
  transcript: string,
  durationSeconds?: number,
  source: string = 'practice',
): Promise<PronunciationResult> {
  const form = new FormData();
  form.append('audio', wav, 'take.wav');
  form.append('target_text', targetText);
  form.append('transcript', transcript);
  if (durationSeconds) form.append('duration_seconds', String(durationSeconds));
  form.append('source', source);
  const res = await api.post('/speaking/pronunciation-audio', form, { headers: { 'Content-Type': 'multipart/form-data' } });
  return res.data;
}

/** One call for every "say it" surface: audio when phoneme scoring is on, transcript otherwise. */
export async function scoreAttempt(opts: {
  targetText: string; transcript: string; durationSeconds?: number; wav?: Blob | null; source?: string;
}): Promise<PronunciationResult> {
  const source = opts.source ?? 'practice';
  if (opts.wav) {
    const status = await getPronunciationStatus();
    if (status.phoneme_enabled) {
      try {
        return await scorePronunciationAudio(opts.wav, opts.targetText, opts.transcript, opts.durationSeconds, source);
      } catch {
        // fall through to the transcript scorer
      }
    }
  }
  return scorePronunciation(opts.targetText, opts.transcript, opts.durationSeconds, source);
}

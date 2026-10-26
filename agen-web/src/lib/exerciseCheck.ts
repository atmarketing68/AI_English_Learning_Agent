/**
 * Client-side mirror of the server's answer rules, used only for the retry
 * round at the end of a lesson (the first attempt is always graded by the API).
 */
import type { Exercise } from '@/lib/lessonService';

export const SKIP_ANSWER = '__skip__';

export const normText = (s: string) =>
  (s || '').toLowerCase().replace(/’/g, "'").replace(/[^\p{L}\p{N}\s']/gu, ' ').replace(/\s+/g, ' ').trim();

/** 0–1 similarity (normalised Levenshtein). */
export function similarity(a: string, b: string): number {
  const x = normText(a), y = normText(b);
  if (!x && !y) return 1;
  const dp = Array.from({ length: x.length + 1 }, (_, i) => [i, ...Array(y.length).fill(0)]);
  for (let j = 1; j <= y.length; j++) dp[0][j] = j;
  for (let i = 1; i <= x.length; i++) {
    for (let j = 1; j <= y.length; j++) {
      dp[i][j] = Math.min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + (x[i - 1] === y[j - 1] ? 0 : 1));
    }
  }
  return 1 - dp[x.length][y.length] / Math.max(x.length, y.length);
}

type Pairs = { left: string; right: string }[];

export function isCorrectLocally(ex: Exercise, answer: string): boolean {
  const c = ex.content;
  switch (ex.type) {
    case 'multiple_choice':
    case 'listen_choose':
      return answer.trim().toUpperCase() === String(c.correct_answer ?? '').trim().toUpperCase();
    case 'fill_blank':
      return answer.trim().toLowerCase() === String(c.blank_word ?? '').trim().toLowerCase();
    case 'word_bank':
      return normText(answer) === normText(String(c.answer ?? ''));
    case 'dictation':
      return similarity(answer, String(c.text ?? '')) >= 0.9;
    case 'match_pairs': {
      const pairs = new Map(((c.pairs as Pairs) || []).map(p => [p.left, p.right]));
      try {
        const attempts = JSON.parse(answer) as [string, string][];
        return attempts.every(([l, r]) => pairs.get(l) === r) && new Set(attempts.map(a => a[0])).size === pairs.size;
      } catch { return false; }
    }
    case 'dialogue_order': {
      try {
        const order = JSON.parse(answer) as number[];
        return order.every((v, i) => v === i) && order.length === ((c.lines as unknown[]) || []).length;
      } catch { return false; }
    }
    default:
      return false;
  }
}

/** The answer to show when the learner got it wrong ('' when the exercise explains itself). */
export function correctAnswerText(ex: Exercise): string {
  const c = ex.content;
  switch (ex.type) {
    case 'multiple_choice':
    case 'listen_choose': {
      const key = String(c.correct_answer ?? '');
      const options = c.options as Record<string, string>;
      return options?.[key] ? `${key}. ${options[key]}` : key;
    }
    case 'fill_blank': return String(c.blank_word ?? '');
    case 'word_bank': return String(c.answer ?? '');
    case 'dictation':
    case 'speak_repeat': return String(c.text ?? '');
    default: return '';
  }
}

/** Exercise types that count towards the score and can be retried at the end. */
export const RETRYABLE = new Set(['multiple_choice', 'fill_blank', 'word_bank', 'match_pairs', 'listen_choose', 'dictation', 'dialogue_order']);

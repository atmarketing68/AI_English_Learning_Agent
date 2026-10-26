'use client';

/**
 * G2 · Per-word pronunciation verdict + sound tips for Vietnamese speakers.
 * Used by the speaking steps, shadowing in the listening player and placement.
 */
import { Lightbulb, Volume2 } from 'lucide-react';
import type { PronunciationResult } from '@/lib/pronunciationService';
import { playText } from '@/lib/speechService';

interface Props {
  result: PronunciationResult;
  /** Hide the tips block (e.g. inside a tight sheet). */
  compact?: boolean;
}

export function scoreLabel(score: number): string {
  if (score >= 85) return 'Tuyệt vời';
  if (score >= 70) return 'Tốt';
  if (score >= 50) return 'Khá ổn';
  return 'Thử lại nhé';
}

export default function PronunciationFeedback({ result, compact = false }: Props) {
  const score = Math.round(result.overall_score);
  const tone = score >= 70 ? 'good' : score >= 50 ? 'mid' : 'low';

  return (
    <div className="pron-feedback" data-tone={tone}>
      <div className="pron-score">
        <div className="pron-score-ring" style={{ ['--pct' as string]: `${score}%` }}>
          <span>{score}</span>
        </div>
        <div>
          <div className="pron-score-label">{scoreLabel(score)}</div>
          <div className="pron-score-sub">
            Đúng {result.words.filter(w => w.status === 'ok').length}/{result.words.length} từ
            {result.xp_earned > 0 && <> · +{result.xp_earned} XP</>}
          </div>
        </div>
      </div>

      <div className="pron-words" aria-label="Kết quả từng từ">
        {result.words.map((w, i) => (
          <button
            key={`${w.word}-${i}`}
            type="button"
            className="pron-word"
            data-state={w.status}
            onClick={() => void playText(w.word)}
            title={w.status === 'ok' ? 'Đúng' : w.heard ? `Máy nghe thành “${w.heard}”` : 'Chưa nghe thấy từ này'}
          >
            {w.word}
            {w.status === 'wrong' && w.heard && <small>nghe thành “{w.heard}”</small>}
            {w.status === 'missed' && <small>thiếu</small>}
          </button>
        ))}
      </div>

      {!compact && result.sound_tips.length > 0 && (
        <ul className="pron-tips">
          {result.sound_tips.map(t => (
            <li key={t.sound}>
              <Lightbulb size={15} />
              <div>
                <strong>{t.sound}</strong> — {t.tip_vi}
                <div className="pron-tip-words">
                  {t.words.map(w => (
                    <button key={w} type="button" onClick={() => void playText(w)}><Volume2 size={12} /> {w}</button>
                  ))}
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}
      {!compact && result.sound_tips.length === 0 && <p className="pron-note">{result.feedback_vi}</p>}
    </div>
  );
}

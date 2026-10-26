'use client';

/**
 * G2 · Per-word pronunciation verdict + sound tips for Vietnamese speakers.
 * In phoneme mode (G2 · 9) a tapped word opens its phonemes with a score each.
 * Used by the speaking steps, shadowing in the listening player and placement.
 */
import { useState } from 'react';
import { Lightbulb, Volume2, Waves } from 'lucide-react';
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

const tone = (score: number | null | undefined) => (score == null ? 'none' : score >= 80 ? 'good' : score >= 60 ? 'mid' : 'low');

export default function PronunciationFeedback({ result, compact = false }: Props) {
  const score = Math.round(result.overall_score);
  const overallTone = score >= 70 ? 'good' : score >= 50 ? 'mid' : 'low';
  const phonemeMode = result.mode === 'phoneme';
  const [open, setOpen] = useState<number | null>(() => {
    if (result.mode !== 'phoneme') return null;
    const first = result.words.findIndex(w => w.status !== 'ok' && w.phonemes?.length);
    return first >= 0 ? first : null;
  });

  return (
    <div className="pron-feedback" data-tone={overallTone}>
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
          <div className="pron-mode">
            {phonemeMode ? <><Waves size={12} /> Chấm từng âm</> : 'Chấm theo từ'}
            {phonemeMode && result.prosody != null && <> · ngữ điệu {Math.round(result.prosody)}</>}
            {phonemeMode && <> · trôi chảy {Math.round(result.fluency)}</>}
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
            data-open={open === i}
            onClick={() => { void playText(w.word); if (w.phonemes?.length) setOpen(open === i ? null : i); }}
            title={w.status === 'ok' ? 'Đúng' : w.heard ? `Máy nghe thành “${w.heard}”` : w.status === 'missed' ? 'Chưa nghe thấy từ này' : 'Phát âm chưa chuẩn'}
          >
            {w.word}
            {w.status === 'wrong' && w.heard && <small>nghe thành “{w.heard}”</small>}
            {w.status === 'wrong' && !w.heard && w.score != null && <small>{Math.round(w.score)}/100</small>}
            {w.status === 'missed' && <small>thiếu</small>}
          </button>
        ))}
      </div>

      {open !== null && result.words[open]?.phonemes?.length ? (
        <div className="pron-phonemes" aria-label={`Các âm của từ ${result.words[open].word}`}>
          <span className="pron-phonemes-word">/{result.words[open].word}/</span>
          {result.words[open].phonemes!.map((p, i) => (
            <span key={i} className="pron-phoneme" data-tone={tone(p.score)}>
              {p.phoneme}
              {p.score != null && <small>{Math.round(p.score)}</small>}
            </span>
          ))}
          <span className="pron-phonemes-hint">màu đỏ/cam = âm cần luyện</span>
        </div>
      ) : null}

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

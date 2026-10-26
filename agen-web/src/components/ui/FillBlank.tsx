'use client';

import { useEffect, useState } from 'react';
import { playSound } from '@/lib/soundEffects';
import { Lightbulb } from 'lucide-react';

const escapeRegExp = (s: string) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

/** Split a sentence around its gap: "___" when present, else the answer word itself. */
function splitSentence(sentence: string, blankWord: string): [string, string] | null {
  const gap = sentence.match(/_{2,}/);
  if (gap?.index !== undefined) return [sentence.slice(0, gap.index), sentence.slice(gap.index + gap[0].length)];
  if (!blankWord) return null;
  const m = sentence.match(new RegExp(`\\b${escapeRegExp(blankWord)}\\b`, 'i'));
  if (m?.index === undefined) return null;
  return [sentence.slice(0, m.index), sentence.slice(m.index + m[0].length)];
}

export default function FillBlank({
  sentence, blankWord, options, hint, onAnswer, disabled, result,
}: {
  sentence: string;
  blankWord: string;
  options: string[];
  hint?: string;
  onAnswer: (ans: string) => void;
  disabled: boolean;
  /** After checking: whether the chosen word was right. */
  result?: 'correct' | 'wrong';
}) {
  const [selected, setSelected] = useState<string | null>(null);
  const parts = splitSentence(sentence, blankWord);
  const shown = result === 'wrong' ? blankWord : selected;

  const pick = (opt: string) => {
    if (disabled) return;
    playSound('pop');
    setSelected(opt);
  };

  // Keyboard: 1–4 choose a word, Enter checks.
  useEffect(() => {
    if (disabled) return;
    const onKey = (e: KeyboardEvent) => {
      const idx = Number(e.key) - 1;
      if (options[idx]) { playSound('pop'); setSelected(options[idx]); }
      else if (e.key === 'Enter' && selected) { e.preventDefault(); onAnswer(selected); }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [disabled, options, selected, onAnswer]);

  return (
    <div>
      {hint && (
        <div className="fill-hint"><Lightbulb size={14} color="var(--agen-accent)" /> Gợi ý: {hint}</div>
      )}

      <p className="fill-sentence">
        {parts ? (
          <>
            {parts[0]}
            <span className="fill-gap" data-state={result === 'wrong' ? 'revealed' : result} data-filled={!!shown}>{shown || ' '}</span>
            {parts[1]}
          </>
        ) : sentence}
      </p>

      <div className="choice-grid is-2col">
        {options.map((opt, i) => {
          const state = result
            ? opt.toLowerCase() === blankWord.toLowerCase() ? 'correct' : opt === selected ? 'wrong' : 'muted'
            : opt === selected ? 'selected' : undefined;
          return (
            <button key={opt} type="button" className="choice" data-state={state} disabled={disabled} onClick={() => pick(opt)}>
              <span className="choice-key">{i + 1}</span>
              <span>{opt}</span>
            </button>
          );
        })}
      </div>

      {!result && (
        <button
          type="button"
          className="btn btn-primary btn-full btn-lg"
          style={{ marginTop: 20 }}
          disabled={!selected || disabled}
          onClick={() => { if (selected) onAnswer(selected); }}
        >
          Kiểm tra
        </button>
      )}
    </div>
  );
}

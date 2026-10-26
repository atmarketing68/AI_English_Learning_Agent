'use client';

/**
 * The six interactive exercise types. Each one collects an answer and calls
 * onAnswer(answer) once; grading happens on the server (or, in the retry
 * round, in exerciseCheck.ts). `result` is set after grading to colour it.
 */
import { useEffect, useMemo, useRef, useState } from 'react';
import { Ear, Mic, MicOff, Puzzle, Rabbit, Repeat, Snail, Volume2, ListOrdered, Keyboard, Link2 } from 'lucide-react';
import { playSound } from '@/lib/soundEffects';
import { SpeechRecognizer, speakText } from '@/lib/speechService';
import { SKIP_ANSWER } from '@/lib/exerciseCheck';

type Result = 'correct' | 'wrong' | undefined;

interface BaseProps {
  content: Record<string, unknown>;
  locked: boolean;
  result: Result;
  onAnswer: (answer: string) => void;
}

/** Shuffle with a fixed seed so re-renders keep the same order. */
function seededShuffle<T>(items: T[], seed: string): T[] {
  let h = 2166136261;
  for (let i = 0; i < seed.length; i++) h = Math.imul(h ^ seed.charCodeAt(i), 16777619);
  const out = items.slice();
  for (let i = out.length - 1; i > 0; i--) {
    h = Math.imul(h ^ (h >>> 15), 2246822507);
    const j = Math.abs(h) % (i + 1);
    [out[i], out[j]] = [out[j], out[i]];
  }
  return out;
}

function vibrate(ms: number | number[]) {
  try { navigator.vibrate?.(ms); } catch { /* unsupported */ }
}

function Eyebrow({ icon: Icon, children }: { icon: typeof Ear; children: React.ReactNode }) {
  return <div className="eyebrow lesson-eyebrow"><Icon size={14} /> {children}</div>;
}

// ── Ghép câu từ kho chữ ──────────────────────────────────────────────────────
export function WordBank({ content, locked, result, onAnswer }: BaseProps) {
  const tokens = useMemo(() => (content.tokens as string[]) || [], [content.tokens]);
  const order = useMemo(() => seededShuffle(tokens.map((_, i) => i), String(content.answer)), [tokens, content.answer]);
  const [chosen, setChosen] = useState<number[]>([]);

  const add = (i: number) => { if (locked) return; playSound('pop'); setChosen(c => [...c, i]); };
  const remove = (i: number) => { if (locked) return; setChosen(c => c.filter(x => x !== i)); };

  return (
    <div>
      <Eyebrow icon={Puzzle}>Dịch câu sau sang tiếng Anh</Eyebrow>
      <h3 className="lesson-question">{content.prompt_vi as string}</h3>
      <div className="bank-answer" data-state={result}>
        {chosen.length === 0 && <span className="bank-placeholder">Chạm vào các từ bên dưới để ghép câu</span>}
        {chosen.map(i => (
          <button key={i} type="button" className="bank-chip" onClick={() => remove(i)} disabled={locked}>{tokens[i]}</button>
        ))}
      </div>
      <div className="bank-pool">
        {order.map(i => (
          <button key={i} type="button" className="bank-chip" data-used={chosen.includes(i)}
            onClick={() => add(i)} disabled={locked || chosen.includes(i)}>{tokens[i]}</button>
        ))}
      </div>
      {!result && (
        <button type="button" className="btn btn-primary btn-full btn-lg" style={{ marginTop: 20 }}
          disabled={!chosen.length || locked} onClick={() => onAnswer(chosen.map(i => tokens[i]).join(' '))}>
          Kiểm tra
        </button>
      )}
    </div>
  );
}

// ── Nối cặp ──────────────────────────────────────────────────────────────────
export function MatchPairs({ content, locked, onAnswer }: BaseProps) {
  const pairs = useMemo(() => (content.pairs as { left: string; right: string }[]) || [], [content.pairs]);
  const lefts = useMemo(() => seededShuffle(pairs.map(p => p.left), 'L' + pairs.map(p => p.left).join()), [pairs]);
  const rights = useMemo(() => seededShuffle(pairs.map(p => p.right), 'R' + pairs.map(p => p.right).join()), [pairs]);
  const answerOf = useMemo(() => new Map(pairs.map(p => [p.left, p.right])), [pairs]);
  const [selected, setSelected] = useState<string | null>(null);
  const [matched, setMatched] = useState<Set<string>>(new Set());
  const [wrong, setWrong] = useState<[string, string] | null>(null);
  const attempts = useRef<[string, string][]>([]);

  const pickRight = (right: string) => {
    if (!selected || locked) return;
    attempts.current.push([selected, right]);
    if (answerOf.get(selected) === right) {
      playSound('pop');
      const next = new Set(matched).add(selected);
      setMatched(next);
      setSelected(null);
      if (next.size === pairs.length) onAnswer(JSON.stringify(attempts.current));
    } else {
      playSound('error');
      vibrate(60);
      setWrong([selected, right]);
      setTimeout(() => setWrong(null), 600);
      setSelected(null);
    }
  };
  const matchedRights = new Set([...matched].map(l => answerOf.get(l)));

  return (
    <div>
      <Eyebrow icon={Link2}>Nối từ với nghĩa đúng</Eyebrow>
      <div className="match-grid">
        <div className="match-col">
          {lefts.map(l => (
            <button key={l} type="button" className="choice match-item"
              data-state={matched.has(l) ? 'correct' : wrong?.[0] === l ? 'wrong' : selected === l ? 'selected' : undefined}
              disabled={locked || matched.has(l)}
              onClick={() => { setSelected(l); speakText(l); }}>{l}</button>
          ))}
        </div>
        <div className="match-col">
          {rights.map(r => (
            <button key={r} type="button" className="choice match-item"
              data-state={matchedRights.has(r) ? 'correct' : wrong?.[1] === r ? 'wrong' : undefined}
              disabled={locked || matchedRights.has(r) || !selected}
              onClick={() => pickRight(r)}>{r}</button>
          ))}
        </div>
      </div>
      <div className="match-hint">{matched.size}/{pairs.length} cặp · chạm một từ bên trái, rồi chọn nghĩa bên phải</div>
    </div>
  );
}

// ── Nghe chọn đáp án ─────────────────────────────────────────────────────────
export function ListenChoose({ content, locked, result, onAnswer }: BaseProps) {
  const text = content.audio_text as string;
  const options = Object.entries((content.options as Record<string, string>) || {});
  const correctKey = String(content.correct_answer ?? '').toUpperCase();
  const [picked, setPicked] = useState<string | null>(null);
  useEffect(() => { speakText(text); }, [text]);

  return (
    <div>
      <Eyebrow icon={Ear}>Nghe và chọn nghĩa đúng</Eyebrow>
      <div className="listen-buttons">
        <button type="button" className="listen-play" onClick={() => speakText(text)} aria-label="Nghe lại"><Volume2 size={30} /></button>
        <button type="button" className="listen-slow" onClick={() => speakText(text, undefined, 0.6)} aria-label="Nghe chậm"><Snail size={20} /></button>
      </div>
      {result && <div className="listen-reveal">“{text}”</div>}
      <div className="choice-grid is-2col">
        {options.map(([k, v]) => (
          <button key={k} type="button" className="choice" disabled={locked}
            data-state={!result ? undefined : k === correctKey ? 'correct' : k === picked ? 'wrong' : 'muted'}
            onClick={() => { setPicked(k); onAnswer(k); }}>
            <span className="choice-key">{k}</span><span>{v}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

// ── Nghe – chép ──────────────────────────────────────────────────────────────
export function Dictation({ content, locked, result, onAnswer }: BaseProps) {
  const text = content.text as string;
  const [value, setValue] = useState('');
  useEffect(() => { speakText(text); }, [text]);

  return (
    <div>
      <Eyebrow icon={Keyboard}>Nghe và chép lại câu</Eyebrow>
      <div className="listen-buttons">
        <button type="button" className="listen-play" onClick={() => speakText(text)} aria-label="Nghe lại"><Volume2 size={30} /></button>
        <button type="button" className="listen-slow" onClick={() => speakText(text, undefined, 0.6)} aria-label="Nghe chậm"><Snail size={20} /></button>
      </div>
      <form onSubmit={(e) => { e.preventDefault(); if (value.trim()) onAnswer(value); }}>
        <textarea className="form-input dictation-input" data-state={result} rows={2} value={value}
          onChange={(e) => setValue(e.target.value)} placeholder="Gõ những gì bạn nghe được…"
          disabled={locked} autoCapitalize="sentences" spellCheck={false}
          onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); if (value.trim()) onAnswer(value); } }} />
        {!result && (
          <button type="submit" className="btn btn-primary btn-full btn-lg" style={{ marginTop: 16 }} disabled={!value.trim() || locked}>
            Kiểm tra
          </button>
        )}
      </form>
    </div>
  );
}

// ── Nói lặp lại ──────────────────────────────────────────────────────────────
export function SpeakRepeat({ content, locked, result, onAnswer }: BaseProps) {
  const text = content.text as string;
  const [transcript, setTranscript] = useState('');
  const [listening, setListening] = useState(false);
  const [error, setError] = useState('');
  const recognizer = useRef<SpeechRecognizer | null>(null);
  const [supported, setSupported] = useState(true);

  useEffect(() => {
    const rec = new SpeechRecognizer(
      (r) => setTranscript(r.transcript),
      (err) => { setError(err === 'not-allowed' ? 'Hãy cho phép dùng micro để luyện nói.' : `Lỗi micro: ${err}`); setListening(false); },
      () => setListening(false),
    );
    recognizer.current = rec;
    const ok = rec.isSupported();
    queueMicrotask(() => setSupported(ok));
    return () => rec.stop();
  }, []);

  const toggle = () => {
    const rec = recognizer.current;
    if (!rec) return;
    if (listening) { rec.stop(); setListening(false); return; }
    setError('');
    setTranscript('');
    rec.start();
    setListening(true);
  };

  return (
    <div>
      <Eyebrow icon={Repeat}>Nghe mẫu rồi nói lại</Eyebrow>
      <div className="speak-target">
        <span>{text}</span>
        <button type="button" className="review-speak" onClick={() => speakText(text)} aria-label="Nghe mẫu"><Volume2 size={20} /></button>
        <button type="button" className="review-speak" onClick={() => speakText(text, undefined, 0.6)} aria-label="Nghe chậm"><Rabbit size={18} /></button>
      </div>
      {typeof content.hint === 'string' && content.hint && <div className="review-hint">{content.hint}</div>}

      {supported ? (
        <div className="speak-mic">
          <button type="button" className="mic-button" data-on={listening} onClick={toggle} disabled={locked}
            aria-label={listening ? 'Dừng ghi âm' : 'Bắt đầu nói'}>
            {listening ? <MicOff size={30} /> : <Mic size={30} />}
          </button>
          <div className="speak-transcript" data-state={result}>
            {transcript || (listening ? 'Đang nghe…' : 'Chạm micro và đọc to câu trên')}
          </div>
          {!result && transcript && !listening && (
            <button type="button" className="btn btn-primary btn-full btn-lg" onClick={() => onAnswer(transcript)} disabled={locked}>
              Kiểm tra
            </button>
          )}
        </div>
      ) : (
        <div className="speak-unsupported">Trình duyệt này chưa hỗ trợ nhận giọng nói. Hãy đọc to câu trên rồi bỏ qua.</div>
      )}
      {error && <div className="alert-error" style={{ marginTop: 12 }}>{error}</div>}
      {!result && (
        <button type="button" className="btn btn-ghost btn-full" style={{ marginTop: 10 }} onClick={() => onAnswer(SKIP_ANSWER)} disabled={locked}>
          Không nói được lúc này
        </button>
      )}
    </div>
  );
}

// ── Sắp xếp hội thoại ────────────────────────────────────────────────────────
export function DialogueOrder({ content, locked, result, onAnswer }: BaseProps) {
  const lines = useMemo(() => (content.lines as { speaker: string; text: string }[]) || [], [content.lines]);
  const shuffled = useMemo(() => {
    const idx = lines.map((_, i) => i);
    let out = seededShuffle(idx, lines.map(l => l.text).join('|'));
    if (out.every((v, i) => v === i)) out = [...idx.slice(1), idx[0]];   // never start solved
    return out;
  }, [lines]);
  const [chosen, setChosen] = useState<number[]>([]);
  const shown = result === 'wrong' ? lines.map((_, i) => i) : chosen;

  return (
    <div>
      <Eyebrow icon={ListOrdered}>Sắp xếp đoạn hội thoại theo đúng thứ tự</Eyebrow>
      <ol className="dialogue-answer" data-state={result}>
        {shown.map((i, pos) => (
          <li key={i}>
            <button type="button" className="dialogue-line" disabled={locked}
              onClick={() => setChosen(c => c.filter(x => x !== i))}>
              <span className="dialogue-num">{pos + 1}</span>
              {lines[i].speaker && <strong>{lines[i].speaker}:</strong>} {lines[i].text}
            </button>
          </li>
        ))}
        {!shown.length && <li className="bank-placeholder">Chạm các câu bên dưới theo thứ tự diễn ra</li>}
      </ol>
      {!result && (
        <div className="dialogue-pool">
          {shuffled.filter(i => !chosen.includes(i)).map(i => (
            <button key={i} type="button" className="dialogue-line" disabled={locked}
              onClick={() => { playSound('pop'); setChosen(c => [...c, i]); }}>
              {lines[i].speaker && <strong>{lines[i].speaker}:</strong>} {lines[i].text}
            </button>
          ))}
        </div>
      )}
      {!result && (
        <button type="button" className="btn btn-primary btn-full btn-lg" style={{ marginTop: 16 }}
          disabled={chosen.length !== lines.length || locked} onClick={() => onAnswer(JSON.stringify(chosen))}>
          Kiểm tra
        </button>
      )}
    </div>
  );
}

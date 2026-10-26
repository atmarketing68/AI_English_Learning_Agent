'use client';

/**
 * G2 · Listening player: neural voice per speaker (server TTS with browser
 * fallback), 0,75× speed, a transcript where every word can be tapped to look
 * it up and save it, and a shadowing mode (listen → repeat → per-word score).
 */
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { BookmarkPlus, Check, CircleAlert, Ear, LoaderCircle, Pause, Play, Repeat, Volume2, X } from 'lucide-react';
import { playText, stopSpeech, type Voice } from '@/lib/speechService';
import { addNotebookWord, lookupWord, type WordLookup } from '@/lib/reviewService';
import { scorePronunciation, type PronunciationResult } from '@/lib/pronunciationService';
import { useSpeechRecorder } from '@/lib/useSpeechRecorder';
import PronunciationFeedback from '@/components/speaking/PronunciationFeedback';
import MicButton from '@/components/speaking/MicButton';
import { track } from '@/lib/analytics';

interface ScriptLine {
  speaker: string;
  text: string;
}

interface Props {
  text?: string;
  scriptLines?: ScriptLine[];
  /** Lesson words with a known meaning: shown instantly when tapped, no lookup. */
  knownWords?: { word: string; definition: string }[];
  lessonId?: string;
}

const FEMALE = /female|mary|sarah|anna|emma|linh|lan|mai|hoa|she|woman|girl|mom|mother|ms\.|mrs\.|miss/i;
const MALE = /male|john|tom|david|mike|minh|nam|tuan|hung|he\b|man|boy|dad|father|mr\./i;

/** Deterministic voice per speaker: name hints first, otherwise alternate. */
function voiceFor(speaker: string, index: number, order: string[]): Voice {
  if (FEMALE.test(speaker)) return 'female';
  if (MALE.test(speaker)) return 'male';
  const i = order.indexOf(speaker);
  return (i >= 0 ? i : index) % 2 === 0 ? 'female' : 'male';
}

const cleanToken = (t: string) => t.replace(/^[^A-Za-z0-9']+|[^A-Za-z0-9']+$/g, '');

export default function AudioPlayerTTS({ text, scriptLines, knownWords = [], lessonId }: Props) {
  const lines: ScriptLine[] = useMemo(
    () => (scriptLines?.length ? scriptLines : (text ? [{ speaker: 'Narrator', text }] : [])),
    [scriptLines, text],
  );
  const speakers = useMemo(() => Array.from(new Set(lines.map(l => l.speaker))), [lines]);

  const [playingAll, setPlayingAll] = useState(false);
  const [activeLine, setActiveLine] = useState<number | null>(null);
  const [slow, setSlow] = useState(false);
  const [showTranscript, setShowTranscript] = useState(true);
  const [mode, setMode] = useState<'listen' | 'shadow'>('listen');
  const [error, setError] = useState('');
  const runId = useRef(0);

  // Tap-a-word
  const [popover, setPopover] = useState<{ word: string; context: string } | null>(null);
  const [lookup, setLookup] = useState<WordLookup | null>(null);
  const [lookingUp, setLookingUp] = useState(false);
  const [lookupError, setLookupError] = useState('');
  const [saved, setSaved] = useState<Set<string>>(new Set());
  const [saving, setSaving] = useState(false);

  // Shadowing
  const [shadowIdx, setShadowIdx] = useState(0);
  const [shadowResult, setShadowResult] = useState<PronunciationResult | null>(null);
  const [scoring, setScoring] = useState(false);
  const shadowTarget = useRef('');
  const recorder = useSpeechRecorder({
    onFinish: (transcript, duration) => {
      const target = shadowTarget.current;
      if (!target) return;
      setScoring(true);
      scorePronunciation(target, transcript, duration || undefined, 'shadowing')
        .then(setShadowResult)
        .catch(() => setError('Không chấm được. Hãy thử lại.'))
        .finally(() => setScoring(false));
    },
  });

  const rate = slow ? 0.75 : 1;

  useEffect(() => () => stopSpeech(), []);

  const stopAll = useCallback(() => {
    runId.current++;
    stopSpeech();
    setPlayingAll(false);
    setActiveLine(null);
  }, []);

  const playLine = useCallback(async (i: number) => {
    const line = lines[i];
    if (!line) return;
    runId.current++;
    const id = runId.current;
    setPlayingAll(false);
    setActiveLine(i);
    await playText(line.text, { voice: voiceFor(line.speaker, i, speakers), rate });
    if (runId.current === id) setActiveLine(null);
  }, [lines, speakers, rate]);

  const playAll = async () => {
    if (playingAll) { stopAll(); return; }
    runId.current++;
    const id = runId.current;
    setPlayingAll(true);
    for (let i = 0; i < lines.length; i++) {
      if (runId.current !== id) return;
      setActiveLine(i);
      await playText(lines[i].text, { voice: voiceFor(lines[i].speaker, i, speakers), rate });
      if (runId.current !== id) return;
      await new Promise(r => setTimeout(r, 350));
    }
    if (runId.current === id) { setPlayingAll(false); setActiveLine(null); }
  };

  // ── Tap-a-word ──
  const openWord = async (raw: string, context: string) => {
    const word = cleanToken(raw);
    if (!word) return;
    stopAll();
    setPopover({ word, context });
    setLookup(null);
    setLookupError('');
    void playText(word);
    const known = knownWords.find(k => k.word.toLowerCase() === word.toLowerCase());
    if (known) {
      setLookup({ word: known.word, phonetic: '', part_of_speech: '', meaning_vi: known.definition, definition_en: '', example: context });
      return;
    }
    setLookingUp(true);
    try {
      setLookup(await lookupWord(word, context));
      track('listening_word_lookup', { word });
    } catch (err: unknown) {
      setLookupError((err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Không tra được từ này lúc này.');
    } finally {
      setLookingUp(false);
    }
  };

  const saveWord = async () => {
    if (!popover) return;
    const meaning = lookup?.meaning_vi || '';
    if (!meaning) return;
    setSaving(true);
    try {
      await addNotebookWord({ word: lookup?.word || popover.word, meaning, phonetic: lookup?.phonetic || undefined, example: lookup?.example || popover.context, source_lesson_id: lessonId });
      setSaved(s => new Set(s).add(popover.word.toLowerCase()));
      track('listening_word_saved', { word: popover.word });
    } catch {
      setLookupError('Chưa lưu được. Hãy thử lại.');
    } finally {
      setSaving(false);
    }
  };

  // ── Shadowing ──
  const startShadow = () => {
    stopAll();
    setMode('shadow');
    setShadowIdx(0);
    setShadowResult(null);
    recorder.reset();
    track('listening_shadowing_started', { lines: lines.length });
  };

  const shadowLine = lines[shadowIdx];
  const shadowListen = () => { if (shadowLine) void playLine(shadowIdx); };
  const shadowMic = () => {
    if (recorder.listening) { recorder.stop(); return; }
    stopAll();
    setShadowResult(null);
    shadowTarget.current = shadowLine?.text ?? '';
    recorder.start();
  };

  const shadowNext = () => {
    setShadowResult(null);
    recorder.reset();
    if (shadowIdx + 1 < lines.length) setShadowIdx(shadowIdx + 1);
    else { setMode('listen'); setShadowIdx(0); }
  };

  if (!lines.length) return null;

  return (
    <div className="card listen-player">
      <div className="listen-toolbar">
        <button type="button" onClick={playAll} className="btn btn-primary">
          {playingAll ? <Pause size={16} fill="currentColor" /> : <Play size={16} fill="currentColor" />}
          {playingAll ? 'Dừng' : 'Nghe cả bài'}
        </button>
        <div className="segmented" aria-label="Tốc độ">
          <button type="button" aria-pressed={!slow} onClick={() => setSlow(false)}>1×</button>
          <button type="button" aria-pressed={slow} onClick={() => setSlow(true)}>0,75×</button>
        </div>
        <button type="button" className={`btn btn-sm ${mode === 'shadow' ? 'btn-primary' : 'btn-outline'}`} onClick={mode === 'shadow' ? () => { setMode('listen'); recorder.reset(); } : startShadow} disabled={!recorder.supported} title={recorder.supported ? 'Nghe rồi nói theo từng câu' : 'Trình duyệt chưa hỗ trợ micro'}>
          <Repeat size={14} /> Shadowing
        </button>
        <button type="button" onClick={() => setShowTranscript(!showTranscript)} className="btn btn-ghost btn-sm">
          {showTranscript ? 'Ẩn' : 'Hiện'} lời thoại
        </button>
      </div>

      {error && <div className="alert-error" style={{ marginTop: 12 }}><CircleAlert size={14} /> {error}</div>}

      {mode === 'shadow' && shadowLine && (
        <div className="shadow-box">
          <div className="eyebrow"><Ear size={14} /> Shadowing · câu {shadowIdx + 1}/{lines.length} — nghe rồi nói theo</div>
          <div className="shadow-line">
            {shadowLine.speaker && <strong>{shadowLine.speaker}:</strong>} {shadowLine.text}
          </div>
          <div className="shadow-controls">
            <button type="button" className="review-speak" aria-label="Nghe câu này" onClick={shadowListen}><Volume2 size={20} /></button>
            <MicButton listening={recorder.listening} onClick={shadowMic} disabled={scoring} size={64} />
            <span className="speak-transcript" style={{ textAlign: 'left', flex: 1 }}>
              {scoring ? 'Đang chấm…' : recorder.listening ? (recorder.transcript || 'Đang nghe…') : shadowResult ? `“${recorder.transcript}”` : 'Nghe, rồi chạm micro và nói theo'}
            </span>
          </div>
          {recorder.error && <div className="alert-error" style={{ marginTop: 8 }}>{recorder.error}</div>}
          {shadowResult && <PronunciationFeedback result={shadowResult} compact />}
          <div className="speak-actions" style={{ marginTop: 12 }}>
            <button type="button" className="btn btn-primary" onClick={shadowNext} disabled={scoring}>
              {shadowIdx + 1 < lines.length ? 'Câu tiếp theo' : 'Xong'}
            </button>
          </div>
        </div>
      )}

      {showTranscript && (
        <div className="listen-transcript">
          {lines.map((l, idx) => (
            <div key={idx} className="listen-line" data-active={activeLine === idx}>
              <button type="button" className="listen-line-play" aria-label={`Nghe câu ${idx + 1}`} onClick={() => void playLine(idx)}>
                {activeLine === idx ? <Volume2 size={14} /> : <Play size={12} fill="currentColor" />}
              </button>
              <div>
                {l.speaker && <strong className="listen-speaker">{l.speaker}:</strong>}{' '}
                {l.text.split(/(\s+)/).map((tok, ti) => (
                  /^\s+$/.test(tok) ? tok : (
                    <button key={ti} type="button" className="tap-word" data-saved={saved.has(cleanToken(tok).toLowerCase())} onClick={() => void openWord(tok, l.text)}>{tok}</button>
                  )
                ))}
              </div>
            </div>
          ))}
          <div className="listen-tip">Chạm vào một từ để tra nghĩa và lưu vào Sổ từ vựng.</div>
        </div>
      )}

      {popover && (
        <div className="word-popover animate-fade-in-up" role="dialog" aria-label={`Từ ${popover.word}`}>
          <div className="word-popover-head">
            <button type="button" className="word-popover-word" onClick={() => void playText(popover.word)}>
              <Volume2 size={16} /> {lookup?.word || popover.word}
              {lookup?.phonetic && <span className="word-popover-ipa">{lookup.phonetic}</span>}
            </button>
            <button type="button" className="icon-btn" aria-label="Đóng" onClick={() => setPopover(null)}><X size={16} /></button>
          </div>
          {lookingUp && <div className="word-popover-row" style={{ color: 'var(--text-muted)' }}><LoaderCircle className="animate-spin" size={14} /> Đang tra…</div>}
          {lookup && (
            <>
              <div className="word-popover-row">
                {lookup.part_of_speech && <span className="word-pos">{lookup.part_of_speech}</span>}
                <strong>{lookup.meaning_vi}</strong>
              </div>
              {lookup.definition_en && <div className="word-popover-row" style={{ color: 'var(--text-secondary)' }}>{lookup.definition_en}</div>}
              {lookup.example && <div className="word-popover-row" style={{ color: 'var(--text-muted)', fontStyle: 'italic' }}>“{lookup.example}”</div>}
            </>
          )}
          {lookupError && <div className="word-popover-row" style={{ color: 'var(--agen-secondary)' }}>{lookupError}</div>}
          <div className="word-popover-actions">
            {saved.has(popover.word.toLowerCase()) ? (
              <span className="word-saved"><Check size={14} /> Đã lưu vào Sổ từ vựng</span>
            ) : (
              <button type="button" className="btn btn-sm btn-primary" onClick={saveWord} disabled={!lookup?.meaning_vi || saving}>
                {saving ? <LoaderCircle className="animate-spin" size={14} /> : <BookmarkPlus size={14} />} Thêm vào sổ từ
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

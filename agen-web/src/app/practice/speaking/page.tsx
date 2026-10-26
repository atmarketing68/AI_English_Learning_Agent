'use client';

/**
 * G2 · Luyện nói 3 bước với AI Coach có nhân vật.
 *   1. Học cụm từ   — nghe và xem nghĩa 5–6 câu dùng trong tình huống
 *   2. Nói lặp lại  — nói từng câu, chấm đến từng từ + mẹo âm khó
 *   3. Roleplay     — hội thoại với nhân vật, có gợi ý câu tiếp theo và câu sửa
 */
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import Link from 'next/link';
import { AnimatePresence, motion } from 'framer-motion';
import confetti from 'canvas-confetti';
import {
  ArrowLeft, ArrowRight, Check, ChevronRight, CircleAlert, Keyboard, Lightbulb, LoaderCircle, Mic,
  RotateCcw, Send, Sparkles, Star, Volume2, X,
} from 'lucide-react';
import {
  finishRoleplay, getScenario, getScenarios, handleSpeakingTurn, startRoleplay, startScenarioRoleplay,
  type Persona, type ScenarioDetail, type ScenarioList, type ScenarioSummary,
} from '@/lib/speakingApiService';
import { getPronunciationStatus, scoreAttempt, type PronunciationResult } from '@/lib/pronunciationService';
import { playText, preloadText, stopSpeech } from '@/lib/speechService';
import { useSpeechRecorder } from '@/lib/useSpeechRecorder';
import { getMyProfile, notifyActivityCompleted } from '@/lib/services';
import { useAuthStore } from '@/store/authStore';
import { playSound } from '@/lib/soundEffects';
import { track } from '@/lib/analytics';
import { PageSkeleton } from '@/components/Skeleton';
import PronunciationFeedback from '@/components/speaking/PronunciationFeedback';
import MicButton from '@/components/speaking/MicButton';

type Phase = 'pick' | 'phrases' | 'repeat' | 'roleplay' | 'done';

interface Message {
  role: 'ai' | 'user';
  content: string;
  feedback?: string;
  corrected?: string;
  score?: number;
}

const STEPS = [
  { key: 'phrases', label: 'Học cụm từ' },
  { key: 'repeat', label: 'Nói lặp lại' },
  { key: 'roleplay', label: 'Hội thoại' },
] as const;

const errorText = (err: unknown, fallback: string) =>
  (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || fallback;

// ─── Small pieces ───────────────────────────────────────────────────────────
function PersonaBadge({ persona, size = 40 }: { persona: Persona | null | undefined; size?: number }) {
  const initial = (persona?.name || 'AI').slice(0, 1).toUpperCase();
  return (
    <span className="persona-avatar" data-voice={persona?.voice ?? 'female'} style={{ width: size, height: size, fontSize: size * 0.42 }} aria-hidden>
      {initial}
    </span>
  );
}

function StepBar({ phase }: { phase: Phase }) {
  const idx = STEPS.findIndex(s => s.key === phase);
  return (
    <ol className="speak-steps" aria-label="Các bước luyện nói">
      {STEPS.map((s, i) => (
        <li key={s.key} data-state={i < idx ? 'done' : i === idx ? 'active' : 'todo'}>
          <span className="speak-step-num">{i < idx ? <Check size={13} /> : i + 1}</span>
          <span className="speak-step-label">{s.label}</span>
        </li>
      ))}
    </ol>
  );
}

// ─── Page ───────────────────────────────────────────────────────────────────
export default function SpeakingPracticePage() {
  const { setLearner } = useAuthStore();
  const onTake = useRef<(transcript: string, duration: number, wav?: Blob | null) => void>(() => {});
  const [captureAudio, setCaptureAudio] = useState(false);
  const recorder = useSpeechRecorder({ onFinish: (t, d, wav) => onTake.current(t, d, wav), captureAudio });

  // Catalogue
  const [catalogue, setCatalogue] = useState<ScenarioList | null>(null);
  const [category, setCategory] = useState<string>('all');
  const [loadError, setLoadError] = useState('');
  const [freeTopic, setFreeTopic] = useState('');

  // Session
  const [phase, setPhase] = useState<Phase>('pick');
  const [scenario, setScenario] = useState<ScenarioDetail | null>(null);
  const [persona, setPersona] = useState<Persona | null>(null);
  const [topic, setTopic] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Step 2
  const [phraseIdx, setPhraseIdx] = useState(0);
  const [attempt, setAttempt] = useState<PronunciationResult | null>(null);
  const [scoring, setScoring] = useState(false);
  const [bestScores, setBestScores] = useState<Record<number, number>>({});

  // Step 3
  const [session, setSession] = useState<{ id: string; systemPrompt: string } | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [hint, setHint] = useState('');
  const [showHint, setShowHint] = useState(false);
  const [typing, setTyping] = useState(false);
  const [typed, setTyped] = useState('');
  const [summary, setSummary] = useState<{ xp: number; turns: number; avg: number } | null>(null);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    getScenarios().then(setCatalogue).catch(err => setLoadError(errorText(err, 'Không tải được danh sách tình huống.')));
    getPronunciationStatus().then(st => setCaptureAudio(st.phoneme_enabled));
    return () => stopSpeech();
  }, []);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages, typing, recorder.transcript]);

  const voice = persona?.voice ?? 'female';
  const say = useCallback((text: string, rate = 1) => playText(text, { voice, rate }), [voice]);

  // ── Pick ──
  const visible = useMemo(() => {
    const list = catalogue?.scenarios ?? [];
    const filtered = category === 'all' ? list : list.filter(s => s.category === category);
    return [...filtered].sort((a, b) => Number(b.recommended) - Number(a.recommended));
  }, [catalogue, category]);

  const chooseScenario = async (s: ScenarioSummary) => {
    setLoading(true);
    setError('');
    try {
      const detail = await getScenario(s.id);
      setScenario(detail);
      setPersona(detail.persona);
      setTopic(detail.title_en);
      setPhraseIdx(0);
      setAttempt(null);
      setBestScores({});
      setPhase('phrases');
      track('speaking_scenario_started', { scenario: s.id, level: s.level });
      detail.phrases.slice(0, 3).forEach(p => preloadText(p.en, detail.persona.voice));
    } catch (err) {
      setError(errorText(err, 'Không tải được tình huống.'));
    } finally {
      setLoading(false);
    }
  };

  const startFreeTopic = async () => {
    const t = freeTopic.trim();
    if (!t) return;
    setLoading(true);
    setError('');
    try {
      const res = await startRoleplay(t);
      setScenario(null);
      setPersona(res.persona ?? null);
      setTopic(t);
      setSession({ id: res.session_id, systemPrompt: res.system_prompt });
      setMessages([{ role: 'ai', content: res.ai_first_message }]);
      setHint('');
      setPhase('roleplay');
      track('speaking_scenario_started', { scenario: 'free', topic: t });
      void playText(res.ai_first_message, { voice: res.persona?.voice ?? 'female' });
    } catch (err) {
      setError(errorText(err, 'Không tạo được tình huống. Hãy thử lại.'));
    } finally {
      setLoading(false);
    }
  };

  // ── Step 2 ──
  const phrase = scenario?.phrases[phraseIdx];
  useEffect(() => {
    if (phase !== 'repeat' || !phrase) return;
    const t = setTimeout(() => void say(phrase.en), 250);
    const next = scenario?.phrases[phraseIdx + 1];
    if (next) preloadText(next.en, voice);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [phase, phraseIdx]);

  const toggleMic = () => {
    if (recorder.listening) { recorder.stop(); return; }
    stopSpeech();
    setAttempt(null);
    recorder.start();
  };

  // Score as soon as a take ends with a transcript.
  const scoreTake = useCallback((transcript: string, duration: number, wav?: Blob | null) => {
    if (!phrase) return;
    setScoring(true);
    scoreAttempt({ targetText: phrase.en, transcript, durationSeconds: duration || undefined, wav, source: 'scenario_repeat' })
      .then(res => {
        setAttempt(res);
        setBestScores(b => ({ ...b, [phraseIdx]: Math.max(b[phraseIdx] ?? 0, res.overall_score) }));
        playSound(res.overall_score >= 70 ? 'success' : 'pop');
        track('speaking_phrase_scored', { scenario: scenario?.id, score: Math.round(res.overall_score) });
      })
      .catch(err => setError(errorText(err, 'Không chấm được. Hãy thử lại.')))
      .finally(() => setScoring(false));
  }, [phrase, phraseIdx, scenario?.id]);

  const retryPhrase = () => { setAttempt(null); recorder.reset(); void say(phrase?.en ?? ''); };
  const nextPhrase = () => {
    setAttempt(null);
    recorder.reset();
    if (scenario && phraseIdx + 1 < scenario.phrases.length) setPhraseIdx(phraseIdx + 1);
    else void enterRoleplay();
  };

  // ── Step 3 ──
  const enterRoleplay = async () => {
    if (!scenario) return;
    setLoading(true);
    setError('');
    try {
      const res = await startScenarioRoleplay(scenario.id);
      setSession({ id: res.session_id, systemPrompt: res.system_prompt });
      setMessages([{ role: 'ai', content: res.ai_first_message }]);
      setHint(scenario.phrases[0]?.en ?? '');
      setShowHint(false);
      setPhase('roleplay');
      void playText(res.ai_first_message, { voice: scenario.persona.voice });
    } catch (err) {
      setError(errorText(err, 'Không bắt đầu được hội thoại.'));
    } finally {
      setLoading(false);
    }
  };

  const send = useCallback(async (text: string) => {
    const clean = text.trim();
    if (!clean || !session || typing) return;
    stopSpeech();
    const history = messages.map(m => ({ role: m.role, content: m.content }));
    setMessages(m => [...m, { role: 'user', content: clean }]);
    setTyped('');
    setShowHint(false);
    setTyping(true);
    playSound('pop');
    try {
      const res = await handleSpeakingTurn(session.id, session.systemPrompt, history, clean);
      setMessages(m => {
        const out = [...m];
        const last = out[out.length - 1];
        if (last?.role === 'user') out[out.length - 1] = { ...last, feedback: res.feedback, corrected: res.corrected, score: res.score };
        out.push({ role: 'ai', content: res.ai_reply });
        return out;
      });
      setHint(res.hint_en || '');
      void playText(res.ai_reply, { voice });
    } catch (err) {
      setError(errorText(err, 'Không gửi được câu trả lời. Hãy thử lại.'));
    } finally {
      setTyping(false);
    }
  }, [session, typing, messages, voice]);

  // A finished take is scored (step 2) or sent to the character (step 3).
  useEffect(() => {
    onTake.current = (transcript, duration, wav) => {
      if (phase === 'repeat') scoreTake(transcript, duration, wav);
      else if (phase === 'roleplay') { recorder.reset(); void send(transcript); }
    };
  }, [phase, scoreTake, send, recorder]);

  const finish = async () => {
    if (!session) return;
    setLoading(true);
    try {
      const turns = messages.filter(m => m.role === 'user').length;
      const scores = messages.filter(m => typeof m.score === 'number').map(m => m.score as number);
      const avg = scores.length ? scores.reduce((a, b) => a + b, 0) / scores.length : 0;
      const res = await finishRoleplay(session.id, topic, turns, avg);
      setSummary({ xp: res.xp_earned, turns: res.total_turns, avg: res.average_score });
      track('speaking_session_completed', { scenario: scenario?.id ?? 'free', turns: res.total_turns, avg_score: Math.round(res.average_score) });
      await notifyActivityCompleted('speaking');
      setLearner(await getMyProfile());
      playSound('success');
      confetti({ particleCount: 90, spread: 70, origin: { y: 0.6 }, colors: ['#0071E3', '#1F9D55', '#D97A00', '#D6336C'] });
      setPhase('done');
    } catch (err) {
      setError(errorText(err, 'Không kết thúc được bài luyện.'));
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    stopSpeech();
    recorder.reset();
    setPhase('pick');
    setScenario(null);
    setPersona(null);
    setSession(null);
    setMessages([]);
    setSummary(null);
    setAttempt(null);
    setError('');
  };

  // ─── Screens ──────────────────────────────────────────────────────────────
  const errorBox = error && (
    <div className="alert-error" style={{ marginBottom: 16 }}>
      <CircleAlert size={16} style={{ flexShrink: 0 }} /> <span style={{ flex: 1 }}>{error}</span>
      <button type="button" className="icon-btn" aria-label="Đóng" onClick={() => setError('')}><X size={14} /></button>
    </div>
  );

  if (phase === 'pick') {
    return (
      <main className="speak-page">
        <div className="speak-column">
          <h1 style={{ fontSize: 'clamp(1.8rem, 4vw, 2.4rem)', marginBottom: 6 }}>Luyện nói</h1>
          <p style={{ color: 'var(--text-secondary)', marginBottom: 20 }}>
            Chọn một tình huống quen thuộc: học cụm từ → nói lặp lại có chấm → hội thoại với nhân vật AI.
          </p>
          {loadError && <div className="alert-error" style={{ marginBottom: 16 }}><CircleAlert size={16} /> {loadError}</div>}
          {errorBox}
          {!catalogue && !loadError && <PageSkeleton />}
          {catalogue && (
            <>
              <div className="speak-filters" role="tablist" aria-label="Chủ đề">
                {[['all', 'Tất cả'], ...Object.entries(catalogue.categories)].map(([key, label]) => (
                  <button key={key} type="button" role="tab" aria-selected={category === key} className="speak-filter" data-on={category === key} onClick={() => setCategory(key)}>
                    {label}
                  </button>
                ))}
              </div>
              <div className="scenario-grid">
                {visible.map(s => (
                  <button key={s.id} type="button" className="scenario-card" onClick={() => chooseScenario(s)} disabled={loading}>
                    <span className="scenario-emoji" aria-hidden>{s.emoji}</span>
                    <span className="scenario-body">
                      <span className="scenario-title">{s.title_vi}</span>
                      <span className="scenario-sub">{s.title_en}</span>
                      <span className="scenario-meta">
                        <span className="level-badge">{s.level}</span>
                        {s.recommended && <span className="scenario-flag"><Sparkles size={12} /> Hợp trình độ</span>}
                        <PersonaBadge persona={s.persona} size={20} />
                        <span>{s.persona.name} · {s.persona.role_vi}</span>
                      </span>
                    </span>
                    <ChevronRight size={18} className="scenario-chevron" />
                  </button>
                ))}
              </div>
              <div className="card" style={{ marginTop: 24 }}>
                <div style={{ fontWeight: 600, marginBottom: 4 }}>Hoặc tự chọn chủ đề</div>
                <p style={{ fontSize: '0.88rem', color: 'var(--text-muted)', marginBottom: 12 }}>AI sẽ dựng một tình huống mới (bỏ qua bước học cụm từ).</p>
                <form style={{ display: 'flex', gap: 8 }} onSubmit={e => { e.preventDefault(); void startFreeTopic(); }}>
                  <input className="form-input" value={freeTopic} onChange={e => setFreeTopic(e.target.value)} placeholder="Ví dụ: Talking about my favourite movie" maxLength={120} />
                  <button type="submit" className="btn btn-primary" disabled={!freeTopic.trim() || loading}>{loading ? <LoaderCircle className="animate-spin" size={16} /> : 'Bắt đầu'}</button>
                </form>
              </div>
            </>
          )}
        </div>
      </main>
    );
  }

  if (phase === 'done' && summary) {
    const pronScores = Object.values(bestScores);
    const pronAvg = pronScores.length ? Math.round(pronScores.reduce((a, b) => a + b, 0) / pronScores.length) : null;
    return (
      <main className="speak-page" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div className="card animate-bounce-in" style={{ maxWidth: 480, width: '100%', textAlign: 'center', padding: 'clamp(24px, 5vw, 40px)', border: 'none', boxShadow: 'var(--shadow-md)' }}>
          <span className="icon-tile" style={{ width: 64, height: 64, borderRadius: 18, background: 'color-mix(in srgb, var(--skill-speaking) 12%, transparent)', color: 'var(--skill-speaking)', marginBottom: 18 }}><Mic size={30} strokeWidth={1.6} /></span>
          <h2 style={{ marginBottom: 6 }}>Hoàn thành luyện nói</h2>
          <p style={{ color: 'var(--text-muted)', marginBottom: 20 }}>{scenario ? scenario.title_vi : topic}{persona && <> · cùng {persona.name}</>}</p>
          <div className="speak-summary">
            <div><strong>{summary.turns}</strong><span>lượt nói</span></div>
            <div><strong>{Math.round(summary.avg)}</strong><span>điểm hội thoại</span></div>
            {pronAvg !== null && <div><strong>{pronAvg}</strong><span>điểm phát âm</span></div>}
          </div>
          <div className="xp-badge" style={{ fontSize: '1.1rem', padding: '8px 16px', margin: '20px 0 28px' }}>
            <Star size={16} fill="currentColor" /> +{summary.xp} XP
          </div>
          <div style={{ display: 'grid', gap: 10 }}>
            <button type="button" className="btn btn-primary btn-lg btn-full" onClick={reset}>Luyện tình huống khác</button>
            <Link href="/dashboard" className="btn btn-ghost btn-full">Về trang chủ</Link>
          </div>
        </div>
      </main>
    );
  }

  const header = (
    <div className="speak-head">
      <button type="button" className="icon-btn" aria-label="Quay lại" onClick={reset}><ArrowLeft size={18} /></button>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div className="speak-head-title">{scenario?.title_vi ?? topic}</div>
        {persona && <div className="speak-head-sub">{persona.name} · {persona.role_vi}</div>}
      </div>
      <PersonaBadge persona={persona} size={36} />
    </div>
  );

  if (phase === 'phrases' && scenario) {
    return (
      <main className="speak-page">
        <div className="speak-column">
          {header}
          <StepBar phase={phase} />
          {errorBox}
          <div className="card speak-goal">
            <div><strong>Mục tiêu:</strong> {scenario.goal_vi}</div>
            <div style={{ color: 'var(--text-muted)' }}>Bạn là <strong>{scenario.learner_role_vi}</strong>, nói chuyện với <strong>{scenario.persona.name}</strong> ({scenario.persona.role_vi}).</div>
          </div>
          <div className="eyebrow" style={{ margin: '20px 0 10px' }}>Cụm từ hữu ích · chạm để nghe</div>
          <div className="phrase-list">
            {scenario.phrases.map((p, i) => (
              <button key={i} type="button" className="phrase-card" onClick={() => void say(p.en)}>
                <span className="phrase-en">{p.en}</span>
                <span className="phrase-vi">{p.vi}</span>
                <Volume2 size={18} className="phrase-icon" />
              </button>
            ))}
          </div>
          <button type="button" className="btn btn-primary btn-lg btn-full" style={{ marginTop: 24 }} onClick={() => { stopSpeech(); setPhase('repeat'); }}>
            Tập nói từng câu <ArrowRight size={18} />
          </button>
        </div>
      </main>
    );
  }

  if (phase === 'repeat' && scenario && phrase) {
    const isLast = phraseIdx + 1 >= scenario.phrases.length;
    return (
      <main className="speak-page">
        <div className="speak-column">
          {header}
          <StepBar phase={phase} />
          {errorBox}
          <div className="speak-progress-dots" aria-label={`Câu ${phraseIdx + 1} / ${scenario.phrases.length}`}>
            {scenario.phrases.map((_, i) => <span key={i} data-state={i < phraseIdx ? 'done' : i === phraseIdx ? 'active' : 'todo'} />)}
          </div>
          <AnimatePresence mode="wait">
            <motion.div key={phraseIdx} initial={{ opacity: 0, x: 24 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -24 }} transition={{ duration: 0.2 }}>
              <div className="speak-target" style={{ marginTop: 12 }}>
                <span>{phrase.en}</span>
                <button type="button" className="review-speak" onClick={() => void say(phrase.en)} aria-label="Nghe mẫu"><Volume2 size={20} /></button>
                <button type="button" className="review-speak" onClick={() => void say(phrase.en, 0.75)} aria-label="Nghe chậm" title="0,75×"><span style={{ fontSize: '0.72rem', fontWeight: 700 }}>0,75×</span></button>
              </div>
              <div className="review-hint">{phrase.vi}</div>

              {recorder.supported ? (
                <div className="speak-mic">
                  <MicButton listening={recorder.listening} onClick={toggleMic} disabled={scoring} />
                  <div className="speak-transcript">
                    {scoring ? <><LoaderCircle className="animate-spin" size={16} /> Đang chấm…</>
                      : recorder.listening ? (recorder.transcript || 'Đang nghe… nói xong chạm để dừng')
                      : attempt ? `Máy nghe được: “${recorder.transcript || '…'}”`
                      : 'Chạm micro, đọc to cả câu, rồi chạm lại để dừng'}
                  </div>
                </div>
              ) : (
                <div className="speak-unsupported">Trình duyệt này chưa hỗ trợ nhận giọng nói (hãy dùng Chrome hoặc Edge). Bạn vẫn có thể nghe mẫu và đọc theo.</div>
              )}
              {recorder.error && <div className="alert-error" style={{ marginTop: 12 }}><CircleAlert size={16} /> {recorder.error}</div>}

              {attempt && (
                <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
                  <PronunciationFeedback result={attempt} />
                </motion.div>
              )}

              <div className="speak-actions">
                {attempt && (
                  <button type="button" className="btn btn-outline btn-lg" onClick={retryPhrase}><RotateCcw size={16} /> Thử lại</button>
                )}
                <button type="button" className={`btn btn-lg ${attempt || !recorder.supported ? 'btn-primary' : 'btn-ghost'}`} style={{ flex: 1 }} onClick={nextPhrase} disabled={loading || scoring}>
                  {loading ? <LoaderCircle className="animate-spin" size={16} /> : isLast ? <>Vào hội thoại <ArrowRight size={16} /></> : <>{attempt ? 'Câu tiếp theo' : 'Bỏ qua câu này'} <ArrowRight size={16} /></>}
                </button>
              </div>
            </motion.div>
          </AnimatePresence>
        </div>
      </main>
    );
  }

  // roleplay
  return (
    <main className="speak-page speak-page-chat">
      <div className="speak-column speak-chat">
        <div className="speak-chat-head">
          {header}
          {scenario && <StepBar phase="roleplay" />}
          <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
            <button type="button" onClick={finish} className="btn btn-sm btn-outline" disabled={loading || typing || messages.filter(m => m.role === 'user').length === 0}>
              {loading ? <LoaderCircle className="animate-spin" size={14} /> : 'Kết thúc'}
            </button>
          </div>
        </div>
        {errorBox}

        <div className="speak-messages">
          {messages.map((m, i) => (
            <motion.div key={i} initial={{ opacity: 0, y: 10, scale: 0.97 }} animate={{ opacity: 1, y: 0, scale: 1 }} className="speak-msg" data-role={m.role}>
              {m.role === 'ai' && <PersonaBadge persona={persona} size={30} />}
              <div className="speak-msg-body">
                <div className="speak-bubble" data-role={m.role}>
                  {m.content}
                  {m.role === 'ai' && (
                    <button type="button" className="speak-bubble-play" aria-label="Nghe lại" onClick={() => void say(m.content)}><Volume2 size={14} /></button>
                  )}
                </div>
                {m.role === 'user' && typeof m.score === 'number' && (
                  <div className="speak-turn-score" data-good={m.score >= 70}>{Math.round(m.score)} điểm</div>
                )}
                {m.corrected && (
                  <div className="speak-corrected"><Check size={13} /> <span>Cách nói tự nhiên: <strong>{m.corrected}</strong></span>
                    <button type="button" className="icon-btn" aria-label="Nghe câu sửa" onClick={() => void say(m.corrected!)} style={{ width: 24, height: 24 }}><Volume2 size={12} /></button>
                  </div>
                )}
                {m.feedback && m.feedback !== 'Rất tốt!' && (
                  <div className="speak-feedback"><Lightbulb size={13} /> <span>{m.feedback}</span></div>
                )}
              </div>
            </motion.div>
          ))}
          {recorder.listening && recorder.transcript && (
            <div className="speak-msg" data-role="user"><div className="speak-msg-body"><div className="speak-bubble speak-bubble-live" data-role="user">{recorder.transcript}…</div></div></div>
          )}
          {typing && (
            <div className="speak-msg" data-role="ai">
              <PersonaBadge persona={persona} size={30} />
              <div className="speak-bubble speak-typing" data-role="ai"><span /><span /><span /></div>
            </div>
          )}
          <div ref={endRef} />
        </div>

        <div className="speak-dock">
          {hint && (
            <div className="speak-hint">
              {showHint ? (
                <div className="speak-hint-body">
                  <Lightbulb size={14} /> <span>Bạn có thể nói: <strong>{hint}</strong></span>
                  <button type="button" className="icon-btn" aria-label="Nghe gợi ý" onClick={() => void say(hint)} style={{ width: 26, height: 26 }}><Volume2 size={13} /></button>
                </div>
              ) : (
                <button type="button" className="speak-hint-btn" onClick={() => setShowHint(true)}><Lightbulb size={14} /> Gợi ý câu trả lời</button>
              )}
            </div>
          )}
          {recorder.error && <div className="alert-error" style={{ marginBottom: 8 }}><CircleAlert size={14} /> {recorder.error}</div>}
          {typed !== '' || !recorder.supported ? (
            <form className="speak-typebar" onSubmit={e => { e.preventDefault(); void send(typed); }}>
              <input className="form-input" value={typed} onChange={e => setTyped(e.target.value)} placeholder="Gõ câu trả lời bằng tiếng Anh…" autoFocus maxLength={500} disabled={typing} />
              <button type="submit" className="btn btn-primary" aria-label="Gửi" disabled={!typed.trim() || typing}><Send size={16} /></button>
              {recorder.supported && <button type="button" className="icon-btn" aria-label="Dùng micro" onClick={() => setTyped('')}><Mic size={18} /></button>}
            </form>
          ) : (
            <div className="speak-dock-mic">
              <button type="button" className="icon-btn" aria-label="Gõ thay vì nói" onClick={() => setTyped(' ')} title="Gõ câu trả lời"><Keyboard size={18} /></button>
              <MicButton listening={recorder.listening} onClick={() => { if (recorder.listening) recorder.stop(); else { stopSpeech(); recorder.start(); } }} disabled={typing || loading} size={72} />
              <span className="speak-dock-note">{recorder.listening ? 'Đang nghe… chạm để gửi' : 'Chạm để nói'}</span>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}

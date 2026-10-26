'use client';

import { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import confetti from 'canvas-confetti';
import { startRoleplay, handleSpeakingTurn, finishRoleplay } from '@/lib/speakingApiService';
import { SpeechRecognizer, speakText, SpeechResult } from '@/lib/speechService';
import { notifyActivityCompleted } from '@/lib/services';
import { useAuthStore } from '@/store/authStore';
import { getMyProfile } from '@/lib/services';
import { playSound } from '@/lib/soundEffects';
import { ArrowLeft, ChevronRight, CircleAlert, Lightbulb, LoaderCircle, Mic, Star } from 'lucide-react';
import { track } from '@/lib/analytics';
import { apiErrorMessage } from '@/lib/apiError';

interface Message {
  role: 'ai' | 'user';
  content: string;
  feedback?: string;
}

export default function SpeakingPracticePage() {
  const { setLearner } = useAuthStore();
  
  // Setup state
  const [topic, setTopic] = useState<string>('');
  const [session, setSession] = useState<{ id: string; systemPrompt: string } | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [scores, setScores] = useState<number[]>([]);
  
  // UI state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [isFinished, setIsFinished] = useState(false);
  const [earnedXp, setEarnedXp] = useState(0);

  // Speech state
  const [recognizer, setRecognizer] = useState<SpeechRecognizer | null>(null);
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const transcriptRef = useRef(''); // always holds latest transcript value
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Scroll to bottom when messages change
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, transcript]);

  // Init speech recognizer
  useEffect(() => {
    const rec = new SpeechRecognizer(
      (result: SpeechResult) => {
        setTranscript(result.transcript);
        transcriptRef.current = result.transcript; // keep ref in sync
      },
      (err) => setError(`Lỗi Mic: ${err}`),
      () => setIsListening(false)
    );
    if (!rec.isSupported()) {
      setError('Trình duyệt không hỗ trợ Web Speech API. Vui lòng dùng Chrome hoặc Edge.');
    } else {
      setRecognizer(rec);
    }
  }, []);

  const handleStart = async (selectedTopic: string) => {
    setLoading(true);
    setError('');
    setTopic(selectedTopic);
    try {
      const res = await startRoleplay(selectedTopic);
      setSession({ id: res.session_id, systemPrompt: res.system_prompt });
      setMessages([{ role: 'ai', content: res.ai_first_message }]);
      speakText(res.ai_first_message);
    } catch (err: unknown) {
      setError(apiErrorMessage(err, 'Lỗi khởi tạo roleplay'));
    } finally {
      setLoading(false);
    }
  };

  const handleSend = async (text: string) => {
    if (!text.trim() || !session) return;
    
    // Add user message to UI immediately
    const userMsg: Message = { role: 'user', content: text };
    const newHistory = [...messages, userMsg];
    setMessages(newHistory);
    setTranscript('');
    setLoading(true);
    playSound('pop');

    try {
      const res = await handleSpeakingTurn(
        session.id,
        session.systemPrompt,
        messages.map(m => ({ role: m.role, content: m.content })),
        text
      );

      // Add feedback to user message
      const updatedHistory = [...newHistory];
      if (res.feedback) {
        updatedHistory[updatedHistory.length - 1].feedback = res.feedback;
      }
      
      // Add AI reply
      updatedHistory.push({ role: 'ai', content: res.ai_reply });
      setMessages(updatedHistory);
      setScores([...scores, res.score]);
      
      // AI Speaks
      speakText(res.ai_reply);
      playSound('pop');

    } catch (err: unknown) {
      setError(apiErrorMessage(err, 'Lỗi khi gửi câu trả lời'));
    } finally {
      setLoading(false);
    }
  };

  const startListening = () => {
    setError('');
    setTranscript('');
    recognizer?.start();
    setIsListening(true);
  };

  const stopListening = () => {
    recognizer?.stop();
    setIsListening(false);
    // Use ref to get the latest transcript value, not the stale closure value
    const finalTranscript = transcriptRef.current.trim();
    if (finalTranscript) {
      handleSend(finalTranscript);
      setTranscript('');
      transcriptRef.current = '';
    }
  };

  const handleFinish = async () => {
    if (!session) return;
    setLoading(true);
    try {
      const avgScore = scores.length > 0 ? scores.reduce((a, b) => a + b, 0) / scores.length : 0;
      const res = await finishRoleplay(session.id, topic, messages.filter(m => m.role === 'user').length, avgScore);
      setEarnedXp(res.xp_earned);
      track('speaking_session_completed', { topic, turns: messages.filter(m => m.role === 'user').length, avg_score: Math.round(avgScore) });

      // Update streak + daily challenge + refresh profile
      await notifyActivityCompleted('speaking');
      const freshProfile = await getMyProfile();
      setLearner(freshProfile);

      playSound('success');
      confetti({ particleCount: 90, spread: 70, origin: { y: 0.6 }, colors: ['#0071E3', '#1F9D55', '#D97A00', '#8E4EC6'] });
      setIsFinished(true);
    } catch {
      setError('Lỗi kết thúc bài học');
    } finally {
      setLoading(false);
    }
  };

  // --- Screens ---

  if (isFinished) {
    return (
      <main style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 'var(--spacing-lg)' }}>
        <div className="card animate-bounce-in" style={{ maxWidth: 480, width: '100%', textAlign: 'center', padding: 'clamp(24px, 5vw, 40px)', border: 'none', boxShadow: 'var(--shadow-md)' }}>
          <span className="icon-tile" style={{ width: 64, height: 64, borderRadius: 18, background: 'color-mix(in srgb, var(--skill-speaking) 12%, transparent)', color: 'var(--skill-speaking)', marginBottom: 18 }}><Mic size={30} strokeWidth={1.6} /></span>
          <h2 style={{ marginBottom: 6 }}>Hoàn thành luyện nói</h2>
          <p style={{ color: 'var(--text-muted)', marginBottom: 24 }}>Chủ đề: {topic}</p>
          <div className="xp-badge" style={{ fontSize: '1.1rem', padding: '8px 16px', marginBottom: 32 }}>
            <Star size={16} fill="currentColor" /> +{earnedXp} XP
          </div>
          <Link href="/dashboard" className="btn btn-primary btn-lg btn-full">Về Dashboard</Link>
        </div>
      </main>
    );
  }

  if (!session) {
    return (
      <main style={{ padding: 'var(--spacing-lg)', minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ maxWidth: 520, width: '100%' }}>
          <Link href="/dashboard" style={{ display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: '0.92rem', marginBottom: 20 }}><ArrowLeft size={16} /> Quay lại</Link>
          <h1 style={{ fontSize: 'clamp(1.9rem, 4vw, 2.5rem)', marginBottom: 10 }}>Luyện nói</h1>
          <p style={{ color: 'var(--text-secondary)', marginBottom: 28 }}>
            Chọn một tình huống để bắt đầu luyện tập phản xạ giao tiếp với AI. 
            Giữ nút Micro để nói, thả ra để gửi.
          </p>
          
          {error && <div className="alert-error" style={{ marginBottom: 16 }}><CircleAlert size={16} style={{ flexShrink: 0 }} /> {error}</div>}

          <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
            {['At the coffee shop', 'Checking in at a hotel', 'Job Interview', 'Ordering food in a restaurant'].map((t, i) => (
              <button
                key={t}
                onClick={() => handleStart(t)}
                disabled={loading}
                style={{
                  width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                  padding: '16px 20px', background: 'transparent', border: 'none',
                  borderTop: i ? '1px solid var(--border-subtle)' : 'none',
                  color: 'var(--text-primary)', fontFamily: 'inherit', fontSize: '1rem', textAlign: 'left',
                  cursor: loading ? 'default' : 'pointer', opacity: loading ? 0.5 : 1,
                }}
              >
                {t}
                <ChevronRight size={18} color="var(--text-muted)" />
              </button>
            ))}
          </div>
          {loading && <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 8, marginTop: 16, color: 'var(--text-muted)', fontSize: '0.9rem' }}><LoaderCircle className="animate-spin" size={16} /> Đang tải kịch bản…</div>}
        </div>
      </main>
    );
  }

  return (
    <main style={{ height: '100vh', display: 'flex', flexDirection: 'column', background: 'var(--bg-base)' }}>
      {/* Header */}
      <div style={{ padding: '12px 24px', background: 'var(--bg-nav)', backdropFilter: 'saturate(180%) blur(20px)', WebkitBackdropFilter: 'saturate(180%) blur(20px)', borderBottom: '1px solid var(--border-subtle)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <div style={{ fontWeight: 600 }}>{topic}</div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Roleplay cùng AI AGENT ENGLISH</div>
        </div>
        <button onClick={handleFinish} className="btn btn-sm btn-ghost" style={{ color: 'var(--agen-primary-light)' }}>Kết thúc</button>
      </div>

      {/* Chat Area */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '24px', display: 'flex', flexDirection: 'column', gap: 24 }}>
        {messages.map((m, i) => (
          <motion.div key={i} 
            initial={{ opacity: 0, y: 10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            style={{ display: 'flex', flexDirection: 'column', alignItems: m.role === 'ai' ? 'flex-start' : 'flex-end' }}
          >
            <div style={{
              maxWidth: '75%',
              padding: '12px 16px',
              borderRadius: 20,
              background: m.role === 'ai' ? 'var(--bg-surface)' : 'var(--agen-primary)',
              color: m.role === 'ai' ? 'var(--text-primary)' : 'white',
              lineHeight: 1.45
            }}>
              {m.content}
            </div>
            
            {/* Feedback for user message */}
            {m.feedback && (
              <motion.div 
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                style={{
                  marginTop: 8, maxWidth: '75%', fontSize: '0.85rem',
                  padding: '8px 12px', borderRadius: 12,
                  background: 'color-mix(in srgb, var(--agen-accent) 10%, transparent)', color: 'var(--text-secondary)',
                  display: 'flex', gap: 6, alignItems: 'flex-start'
                }}>
                <Lightbulb size={14} color="var(--agen-accent)" style={{ flexShrink: 0, marginTop: 3 }} /> <span>{m.feedback}</span>
              </motion.div>
            )}
          </motion.div>
        ))}

        {/* Live Transcript Bubble */}
        {isListening && transcript && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end' }}>
             <div style={{
              maxWidth: '75%', padding: '12px 16px', borderRadius: 20,
              background: 'var(--agen-primary)', color: 'white', opacity: 0.6
            }}>
              {transcript} <i>(đang nghe…)</i>
            </div>
          </motion.div>
        )}

        {/* Typing Indicator */}
        {loading && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start' }}>
            <div style={{
              padding: '12px 16px', borderRadius: 20,
              background: 'var(--bg-surface)',
              display: 'flex', gap: 6, alignItems: 'center', height: 48
            }}>
              <motion.div animate={{ y: [0, -5, 0] }} transition={{ repeat: Infinity, duration: 0.6, delay: 0 }} style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--text-muted)' }} />
              <motion.div animate={{ y: [0, -5, 0] }} transition={{ repeat: Infinity, duration: 0.6, delay: 0.2 }} style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--text-muted)' }} />
              <motion.div animate={{ y: [0, -5, 0] }} transition={{ repeat: Infinity, duration: 0.6, delay: 0.4 }} style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--text-muted)' }} />
            </div>
          </motion.div>
        )}
        
        {error && <div className="alert-error"><CircleAlert size={16} style={{ flexShrink: 0 }} /> {error}</div>}
        <div ref={messagesEndRef} />
      </div>

      {/* Control Area */}
      <div style={{ padding: '20px 24px 8px', background: 'var(--bg-nav)', backdropFilter: 'saturate(180%) blur(20px)', WebkitBackdropFilter: 'saturate(180%) blur(20px)', borderTop: '1px solid var(--border-subtle)', display: 'flex', justifyContent: 'center' }}>
        <button
          onMouseDown={startListening}
          onMouseUp={stopListening}
          onTouchStart={startListening}
          onTouchEnd={stopListening}
          disabled={loading}
          style={{
            width: 72, height: 72, borderRadius: '50%',
            background: isListening ? 'var(--agen-secondary)' : 'var(--agen-primary)',
            color: 'white', border: 'none', cursor: 'pointer',
            boxShadow: isListening ? '0 0 0 8px rgba(255,59,48,0.15)' : 'var(--shadow-md)',
            transition: 'all 0.2s',
            transform: isListening ? 'scale(1.06)' : 'scale(1)',
            display: 'flex', alignItems: 'center', justifyContent: 'center'
          }}
        >
          <Mic size={30} strokeWidth={1.8} />
        </button>
      </div>
      <div style={{ textAlign: 'center', padding: '6px 0 16px', color: 'var(--text-muted)', fontSize: '0.82rem', background: 'var(--bg-nav)' }}>
        Nhấn giữ để nói, thả ra để gửi
      </div>
    </main>
  );
}

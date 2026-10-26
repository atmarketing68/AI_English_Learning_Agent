'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuthStore } from '@/store/authStore';
import { updateMyProfile } from '@/lib/services';
import confetti from 'canvas-confetti';

const GOALS = [
  { id: 'giao_tiep', icon: '🗣️', label: 'Giao tiếp hằng ngày', desc: 'Tự tin nói tiếng Anh khi đi du lịch, giao tiếp cơ bản.' },
  { id: 'hoc_thuat', icon: '🎓', label: 'Học thuật / Trường lớp', desc: 'Cải thiện điểm số trên lớp, xây dựng nền tảng vững chắc.' },
  { id: 'cong_viec', icon: '💼', label: 'Công việc / Đi làm', desc: 'Tiếng Anh cho môi trường công sở, viết email, thuyết trình.' },
  { id: 'luyen_thi', icon: '🏆', label: 'Luyện thi (IELTS, TOEIC)', desc: 'Chuẩn bị cho các kỳ thi chứng chỉ quốc tế.' },
];

const STUDY_MINUTES = [
  { id: 5, label: '5 phút/ngày', desc: 'Nhẹ nhàng, thư giãn', badge: null },
  { id: 10, label: '10 phút/ngày', desc: 'Học đều đặn mỗi ngày', badge: null },
  { id: 15, label: '15 phút/ngày', desc: 'Tiến bộ nhanh chóng', badge: 'Khuyên dùng' },
  { id: 30, label: '30 phút/ngày', desc: 'Thử thách, cường độ cao', badge: null },
];

export default function OnboardingPage() {
  const router = useRouter();
  const { learner, setLearner } = useAuthStore();
  const [step, setStep] = useState(1);
  const [goal, setGoal] = useState('');
  const [studyTime, setStudyTime] = useState(15);
  const [loading, setLoading] = useState(false);

  const handleNext = () => {
    if (step < 3) setStep(step + 1);
    if (step === 2) {
      // Trigger confetti on final step
      confetti({ particleCount: 150, spread: 80, origin: { y: 0.6 } });
    }
  };

  const handleComplete = async () => {
    if (!learner) return;
    setLoading(true);
    try {
      const updated = await updateMyProfile({
        learning_goal: goal,
        daily_study_minutes: studyTime,
      });
      setLearner(updated);
      router.push('/placement');
    } catch (err) {
      console.error('Error updating profile:', err);
      // Even if update fails, we shouldn't block the user from taking the placement test
      router.push('/placement');
    } finally {
      setLoading(false);
    }
  };

  if (!learner) return null; // Or a loading spinner

  return (
    <main style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 'var(--spacing-lg)' }}>
      <div className="container" style={{ maxWidth: 640 }}>
        
        {/* Progress Bar */}
        <div style={{ marginBottom: 40 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8, fontSize: '0.85rem', color: 'var(--text-muted)', fontWeight: 600 }}>
            <span>Bước {step}/3</span>
            <span>{step === 1 ? 'Mục tiêu' : step === 2 ? 'Thời gian' : 'Sẵn sàng'}</span>
          </div>
          <div className="progress-bar" style={{ height: 6 }}>
            <div className="progress-fill" style={{ width: `${(step / 3) * 100}%` }} />
          </div>
        </div>

        <AnimatePresence mode="wait">
          {/* STEP 1: Goal */}
          {step === 1 && (
            <motion.div
              key="step1"
              initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}
              style={{ textAlign: 'center' }}
            >
              <div style={{ fontSize: '3rem', marginBottom: 16 }}>🎯</div>
              <h2 style={{ marginBottom: 8 }}>Mục tiêu học tập của bạn là gì?</h2>
              <p style={{ color: 'var(--text-secondary)', marginBottom: 32 }}>Giúp AGEN cá nhân hoá lộ trình phù hợp nhất với bạn.</p>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 12, textAlign: 'left', marginBottom: 32 }}>
                {GOALS.map(g => (
                  <motion.button
                    key={g.id}
                    whileHover={{ scale: 1.01 }} whileTap={{ scale: 0.99 }}
                    onClick={() => setGoal(g.id)}
                    style={{
                      padding: '20px', borderRadius: 16, cursor: 'pointer',
                      border: `2px solid ${goal === g.id ? 'var(--agen-primary)' : 'var(--border-subtle)'}`,
                      background: goal === g.id ? 'rgba(108,99,255,0.08)' : 'var(--bg-elevated)',
                      display: 'flex', alignItems: 'center', gap: 16, transition: 'all 0.2s',
                    }}
                  >
                    <div style={{ fontSize: '2rem' }}>{g.icon}</div>
                    <div>
                      <div style={{ fontWeight: 700, fontSize: '1.05rem', color: 'var(--text-primary)', marginBottom: 4 }}>{g.label}</div>
                      <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>{g.desc}</div>
                    </div>
                  </motion.button>
                ))}
              </div>
              <button className="btn btn-primary btn-lg btn-full" onClick={handleNext} disabled={!goal}>
                Tiếp tục
              </button>
            </motion.div>
          )}

          {/* STEP 2: Study Time */}
          {step === 2 && (
            <motion.div
              key="step2"
              initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}
              style={{ textAlign: 'center' }}
            >
              <div style={{ fontSize: '3rem', marginBottom: 16 }}>⏱️</div>
              <h2 style={{ marginBottom: 8 }}>Bạn có thể học bao lâu mỗi ngày?</h2>
              <p style={{ color: 'var(--text-secondary)', marginBottom: 32 }}>AGEN sẽ chia nhỏ bài học vừa vặn với lịch trình của bạn.</p>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 16, marginBottom: 32 }}>
                {STUDY_MINUTES.map(s => (
                  <motion.button
                    key={s.id}
                    whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                    onClick={() => setStudyTime(s.id)}
                    style={{
                      padding: '24px 16px', borderRadius: 16, cursor: 'pointer', textAlign: 'center', position: 'relative',
                      border: `2px solid ${studyTime === s.id ? 'var(--agen-primary)' : 'var(--border-subtle)'}`,
                      background: studyTime === s.id ? 'rgba(108,99,255,0.08)' : 'var(--bg-elevated)',
                      transition: 'all 0.2s',
                    }}
                  >
                    {s.badge && (
                      <div style={{ position: 'absolute', top: -10, left: '50%', transform: 'translateX(-50%)', padding: '4px 12px', borderRadius: 99, background: 'var(--agen-accent)', color: 'black', fontSize: '0.7rem', fontWeight: 800, whiteSpace: 'nowrap' }}>
                        {s.badge}
                      </div>
                    )}
                    <div style={{ fontWeight: 800, fontSize: '1.2rem', color: 'var(--text-primary)', marginBottom: 6 }}>{s.label}</div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{s.desc}</div>
                  </motion.button>
                ))}
              </div>
              
              <div style={{ display: 'flex', gap: 12 }}>
                <button className="btn btn-ghost btn-lg" onClick={() => setStep(1)}>Quay lại</button>
                <button className="btn btn-primary btn-lg" style={{ flex: 1 }} onClick={handleNext}>Tiếp tục</button>
              </div>
            </motion.div>
          )}

          {/* STEP 3: Ready */}
          {step === 3 && (
            <motion.div
              key="step3"
              initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}
              style={{ textAlign: 'center' }}
            >
              <div style={{ position: 'relative', display: 'inline-block', marginBottom: 24 }}>
                <div style={{ position: 'absolute', inset: -20, background: 'radial-gradient(circle, rgba(108,99,255,0.4) 0%, transparent 70%)', zIndex: 0, animation: 'pulse-glow 2s infinite' }} />
                <div style={{ fontSize: '4rem', position: 'relative', zIndex: 1 }}>🎉</div>
              </div>
              <h2 style={{ marginBottom: 12 }}>Tuyệt vời, {learner.display_name}!</h2>
              <p style={{ color: 'var(--text-secondary)', marginBottom: 32, fontSize: '1.05rem', lineHeight: 1.6 }}>
                Hồ sơ học tập của bạn đã được thiết lập thành công.
                <br />
                Mục tiêu: <strong style={{ color: 'var(--text-primary)' }}>{GOALS.find(g => g.id === goal)?.label}</strong>
                <br />
                Thời gian: <strong style={{ color: 'var(--text-primary)' }}>{studyTime} phút/ngày</strong>
              </p>

              <div className="card" style={{ background: 'linear-gradient(135deg, rgba(6,214,160,0.1), rgba(108,99,255,0.1))', borderColor: 'var(--agen-success)', marginBottom: 32 }}>
                <h3 style={{ fontSize: '1.1rem', marginBottom: 8, color: 'var(--agen-success)' }}>🧭 Bước tiếp theo: Kiểm tra trình độ</h3>
                <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Hãy dành 5 phút làm bài test nhanh để AGEN xây dựng lộ trình học phù hợp nhất với trình độ hiện tại của bạn.</p>
              </div>

              <button className="btn btn-primary btn-lg btn-full" onClick={handleComplete} disabled={loading} style={{ background: 'linear-gradient(135deg, var(--agen-success), var(--agen-primary))' }}>
                {loading ? '⏳ Đang xử lý...' : 'Bắt đầu Placement Test 🚀'}
              </button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </main>
  );
}

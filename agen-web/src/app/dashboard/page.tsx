'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { motion, Variants } from 'framer-motion';
import { useAuthStore } from '@/store/authStore';
import { getMyProfile, getDailyChallenge } from '@/lib/services';
import { getNextLesson, type NextLesson } from '@/lib/curriculumService';
import NotificationBell from '@/components/NotificationBell';
import { PageSkeleton } from '@/components/Skeleton';
import type { LearnerProfile, DailyChallenge } from '@/types';

const SKILL_ICONS: Record<string, string> = {
  vocabulary: '📚', grammar: '📝', reading: '📖',
  listening: '🎧', speaking: '🗣️', writing: '✍️',
};

const containerVariants: Variants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.1 }
  }
};

const itemVariants: Variants = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { type: 'spring', stiffness: 300, damping: 24 } }
};

// --- Sub-components ---

function SkillBar({ label, score, color }: { label: string; score: number; color: string }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
        <span style={{ color: 'var(--text-secondary)', fontWeight: 500 }}>{label}</span>
        <span style={{ color, fontWeight: 700 }}>{score.toFixed(0)}%</span>
      </div>
      <div className="progress-bar">
        <div className="progress-fill" style={{ width: `${score}%`, background: color }} />
      </div>
    </div>
  );
}

function StatCard({ emoji, value, label }: { emoji: string; value: string | number; label: string }) {
  return (
    <div className="card card-hover" style={{ textAlign: 'center', padding: 'var(--spacing-md)' }}>
      <div style={{ fontSize: '1.8rem', marginBottom: 6 }}>{emoji}</div>
      <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--agen-primary-light)' }}>{value}</div>
      <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: 4 }}>{label}</div>
    </div>
  );
}

import Link from 'next/link';

// --- Mission Card ---
function MissionCard({ learner, nextLesson }: { learner: LearnerProfile; nextLesson: NextLesson | null }) {
  const isPlacementDone = learner.placement_completed === 'done';
  return (
    <div className="card-gradient" style={{ padding: 'var(--spacing-xl)', borderRadius: 'var(--radius-xl)', position: 'relative', overflow: 'hidden' }}>
      {/* Background glow */}
      <div style={{ position: 'absolute', top: -40, right: -40, width: 180, height: 180, borderRadius: '50%', background: 'radial-gradient(circle, rgba(108,99,255,0.3) 0%, transparent 70%)' }} />

      <div style={{ position: 'relative', zIndex: 1 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 'var(--spacing-md)' }}>
          <span style={{ fontSize: '1.4rem' }}>🎯</span>
          <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--agen-accent)', letterSpacing: 1, textTransform: 'uppercase' }}>Today&apos;s Mission</span>
        </div>

        {!isPlacementDone ? (
          <>
            <h3 style={{ marginBottom: 8 }}>Kiểm tra đầu vào</h3>
            <p style={{ marginBottom: 'var(--spacing-lg)', fontSize: '0.9rem' }}>
              Hãy làm bài kiểm tra đầu vào để AGEN tạo lộ trình học riêng cho bạn! 🚀
            </p>
            <Link href="/placement" className="btn btn-primary">
              ▶️ Bắt đầu Placement Test
            </Link>
          </>
        ) : nextLesson ? (
          <>
            <h3 style={{ marginBottom: 6 }}>
              {SKILL_ICONS[nextLesson.skill] || '📌'} {nextLesson.title}
            </h3>
            <div style={{ fontSize: '0.75rem', color: 'var(--agen-accent)', fontWeight: 600, marginBottom: 8, textTransform: 'uppercase', letterSpacing: 0.5 }}>
              {nextLesson.unit_title} · {nextLesson.skill}
            </div>
            <p style={{ marginBottom: 'var(--spacing-lg)', fontSize: '0.9rem' }}>{nextLesson.reason}</p>
            <Link href={`/learn?code=${encodeURIComponent(nextLesson.code)}`} className="btn btn-primary">
              ▶️ Bắt đầu nhiệm vụ
            </Link>
          </>
        ) : (
          <>
            <h3 style={{ marginBottom: 8 }}>🎉 Hoàn thành lộ trình!</h3>
            <p style={{ marginBottom: 'var(--spacing-lg)', fontSize: '0.9rem' }}>
              Bạn đã hoàn thành toàn bộ lộ trình cấp độ hiện tại. Tự do luyện tập thêm nhé!
            </p>
            <Link href="/learn" className="btn btn-primary">
              ▶️ Luyện tập tự do
            </Link>
          </>
        )}
      </div>
    </div>
  );
}

// --- Daily Challenge Card ---
function DailyChallengeCard({ challenge }: { challenge: DailyChallenge }) {
  return (
    <div className="card" style={{ padding: 'var(--spacing-md)', border: '1px solid var(--agen-accent)', position: 'relative' }}>
      <div style={{ position: 'absolute', top: -10, right: -10, background: 'var(--agen-accent)', color: '#fff', padding: '4px 8px', borderRadius: 12, fontSize: '0.75rem', fontWeight: 'bold', boxShadow: '0 4px 10px rgba(255, 152, 0, 0.3)' }}>
        ⭐ +{challenge.xp_reward} XP
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
        <span style={{ fontSize: '1.2rem' }}>🎯</span>
        <h4 style={{ margin: 0, color: 'var(--agen-primary)' }}>{challenge.title}</h4>
      </div>
      <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: 12 }}>{challenge.description}</p>
      
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: 4 }}>
        <span style={{ color: 'var(--text-muted)' }}>Progress</span>
        <span style={{ fontWeight: 600 }}>{challenge.current_value} / {challenge.target_value}</span>
      </div>
      <div className="progress-bar" style={{ height: 6, marginBottom: 12 }}>
        <div className="progress-fill" style={{ width: `${challenge.progress_pct}%`, background: 'var(--agen-accent)' }} />
      </div>
      
      {challenge.is_completed ? (
        <div style={{ background: 'rgba(76, 175, 80, 0.1)', color: '#4caf50', padding: '6px', borderRadius: '4px', textAlign: 'center', fontSize: '0.85rem', fontWeight: 600 }}>
          ✅ Đã hoàn thành
        </div>
      ) : (
        <div style={{ background: 'rgba(255, 152, 0, 0.1)', color: 'var(--agen-accent)', padding: '6px', borderRadius: '4px', textAlign: 'center', fontSize: '0.85rem', fontWeight: 600 }}>
          ⏳ Đang thực hiện
        </div>
      )}
    </div>
  );
}

// --- Main Dashboard Page ---
export default function DashboardPage() {
  const router = useRouter();
  const { isAuthenticated, learner, setLearner, logout } = useAuthStore();
  const [dailyChallenge, setDailyChallenge] = useState<DailyChallenge | null>(null);
  const [nextLesson, setNextLesson] = useState<NextLesson | null>(null);

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }
    // Always fetch fresh profile on mount; challenge + next lesson run after profile
    getMyProfile()
      .then((profile) => {
        setLearner(profile);
        getDailyChallenge().then(setDailyChallenge).catch(console.error);
        // Only fetch the roadmap next lesson once placement is done
        if (profile.placement_completed === 'done') {
          getNextLesson(profile.overall_level).then(setNextLesson).catch(console.error);
        }
      })
      .catch(() => logout());
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated]);

  if (!learner) {
    return <PageSkeleton maxWidth={900} cards={3} />;
  }

  return (
    <main style={{ minHeight: '100vh', padding: 'var(--spacing-lg)' }}>
      <motion.div 
        className="container" 
        style={{ maxWidth: 900 }}
        variants={containerVariants}
        initial="hidden"
        animate="show"
      >
        
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--spacing-xl)' }}>
          <motion.div variants={itemVariants}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)', marginBottom: 6 }}>
              <span className="streak-badge">🔥 {learner.current_streak} Day Streak</span>
              <span className="xp-badge">⭐ {learner.total_xp} XP</span>
              <span className="level-badge">{learner.overall_level}</span>
            </div>
            <h2>👋 Xin chào, {learner.display_name}!</h2>
            <p style={{ marginTop: 4 }}>Hôm nay bạn sẽ học gì?</p>
          </motion.div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)' }}>
            <NotificationBell />
            <button
              className="btn btn-ghost btn-sm"
              onClick={() => { logout(); router.push('/'); }}
            >
              Đăng xuất
            </button>
          </div>
        </div>

        {/* Today's Mission & Daily Challenge */}
        <motion.div variants={itemVariants} style={{ marginBottom: 'var(--spacing-xl)', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 'var(--spacing-md)' }}>
          <MissionCard learner={learner} nextLesson={nextLesson} />
          {dailyChallenge && <DailyChallengeCard challenge={dailyChallenge} />}
        </motion.div>

        {/* Stats Row */}
        <motion.div variants={itemVariants} style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: 'var(--spacing-md)', marginBottom: 'var(--spacing-xl)' }}>
          <StatCard emoji="📚" value={learner.total_lessons_completed} label="Bài đã học" />
          <StatCard emoji="🔥" value={learner.current_streak} label="Ngày liên tiếp" />
          <StatCard emoji="⭐" value={learner.total_xp} label="Điểm XP" />
          <StatCard emoji="🎯" label="Trình độ" value={learner.overall_level} />
        </motion.div>

        {/* 4-Skill Tracker */}
        <motion.div variants={itemVariants} className="card" style={{ marginBottom: 'var(--spacing-xl)' }}>
          <h3 style={{ marginBottom: 'var(--spacing-lg)' }}>📊 Biểu đồ 4 Kỹ năng</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-md)' }}>
            <SkillBar label="🎧 Listening" score={learner.listening_score} color="var(--skill-listening)" />
            <SkillBar label="🗣️ Speaking" score={learner.speaking_score} color="var(--skill-speaking)" />
            <SkillBar label="📖 Reading" score={learner.reading_score} color="var(--skill-reading)" />
            <SkillBar label="✍️ Writing" score={learner.writing_score} color="var(--skill-writing)" />
          </div>
        </motion.div>

        {/* Quick Access */}
        <motion.div variants={itemVariants}>
          <h3 style={{ marginBottom: 'var(--spacing-md)' }}>⚡ Học nhanh</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 'var(--spacing-md)' }}>
            {[
              { emoji: '🎧', label: 'Listening', color: 'var(--skill-listening)', href: '/learn' },
              { emoji: '🗣️', label: 'Speaking', color: 'var(--skill-speaking)', href: '/practice/speaking' },
              { emoji: '📖', label: 'Reading',  color: 'var(--skill-reading)',  href: '/learn' },
              { emoji: '✍️', label: 'Writing',  color: 'var(--skill-writing)',  href: '/practice/writing' },
            ].map((skill) => (
              <motion.div key={skill.label} whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                <Link
                  href={skill.href}
                  className="card"
                  style={{ textAlign: 'center', display: 'block', border: `1px solid ${skill.color}33`, background: 'transparent' }}
                >
                  <div style={{ fontSize: '1.8rem', marginBottom: 8 }}>{skill.emoji}</div>
                  <div style={{ fontWeight: 600, color: skill.color }}>{skill.label}</div>
                </Link>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Parent invite code */}
        {learner.invite_code && (
          <motion.div variants={itemVariants} className="card" style={{ marginTop: 'var(--spacing-xl)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap', background: 'var(--bg-elevated)' }}>
            <div>
              <div style={{ fontWeight: 600, marginBottom: 2 }}>👨‍👩‍👧 Mã liên kết phụ huynh</div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                Đưa mã này cho bố mẹ để theo dõi tiến bộ của bạn
              </div>
            </div>
            <div style={{
              fontFamily: 'monospace', fontSize: '1.3rem', fontWeight: 800, letterSpacing: 2,
              color: 'var(--agen-primary-light)', padding: '8px 16px',
              background: 'var(--bg-base)', borderRadius: 8, border: '1px dashed var(--agen-primary)',
            }}>
              {learner.invite_code}
            </div>
          </motion.div>
        )}

        {/* Upgrade Banner for Free users */}
        <motion.div
          variants={itemVariants}
          style={{ marginTop: 'var(--spacing-lg)' }}
        >
          <Link href="/upgrade" style={{ textDecoration: 'none', display: 'block' }}>
            <motion.div
              whileHover={{ scale: 1.01, y: -2 }}
              style={{
                padding: '16px 24px',
                borderRadius: 14,
                background: 'linear-gradient(135deg, rgba(108,99,255,0.12), rgba(255,152,0,0.08))',
                border: '1px solid rgba(108,99,255,0.3)',
                display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12,
                cursor: 'pointer',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <span style={{ fontSize: '1.8rem' }}>⚡</span>
                <div>
                  <div style={{ fontWeight: 700, color: 'var(--agen-primary-light)', marginBottom: 2 }}>Nâng cấp lên AGEN Premium</div>
                  <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>Bài học không giới hạn · Báo cáo phụ huynh · Lộ trình cá nhân hóa</div>
                </div>
              </div>
              <div style={{ flexShrink: 0, padding: '8px 18px', borderRadius: 99, background: 'linear-gradient(135deg, var(--agen-primary), var(--agen-accent))', color: 'white', fontWeight: 700, fontSize: '0.85rem' }}>
                Xem ngay →
              </div>
            </motion.div>
          </Link>
        </motion.div>

      </motion.div>
    </main>
  );
}

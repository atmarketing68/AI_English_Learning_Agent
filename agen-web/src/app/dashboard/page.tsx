'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { motion, Variants } from 'framer-motion';
import { useAuthStore, useAuthHydrated } from '@/store/authStore';
import { getMyProfile } from '@/lib/services';
import { getNextLesson, type NextLesson } from '@/lib/curriculumService';
import { getReviewSummary, type ReviewSummary } from '@/lib/reviewService';
import { getEngagement, type Engagement } from '@/lib/engagementService';
import DailyQuests from '@/components/engagement/DailyQuests';
import StreakWeekCard from '@/components/engagement/StreakWeekCard';
import ReminderCard from '@/components/engagement/ReminderCard';
import NotificationBell from '@/components/NotificationBell';
import { PageSkeleton } from '@/components/Skeleton';
import type { LearnerProfile } from '@/types';
import Link from 'next/link';
import {
  ArrowRight, BookMarked, BookOpen, BookText, Brain, ChevronRight, CircleCheck, Copy, Flame, GraduationCap, Headphones,
  Mic, PenLine, Sparkles, Star, Target, Users, type LucideIcon,
} from 'lucide-react';

const SKILL_ICONS: Record<string, LucideIcon> = {
  vocabulary: BookText, grammar: PenLine, reading: BookOpen,
  listening: Headphones, speaking: Mic, writing: PenLine,
};

const containerVariants: Variants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.06 }
  }
};

const itemVariants: Variants = {
  hidden: { opacity: 0, y: 12 },
  show: { opacity: 1, y: 0, transition: { duration: 0.45, ease: [0.25, 0.1, 0.25, 1] } }
};

// --- Sub-components ---

function SkillBar({ label, icon: Icon, score, color }: { label: string; icon: LucideIcon; score: number; color: string }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem' }}>
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8, color: 'var(--text-secondary)' }}>
          <Icon size={16} color={color} /> {label}
        </span>
        <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{score.toFixed(0)}%</span>
      </div>
      <div className="progress-bar">
        <div className="progress-fill" style={{ width: `${score}%`, background: color }} />
      </div>
    </div>
  );
}

function StatCard({ icon: Icon, color, value, label }: { icon: LucideIcon; color: string; value: string | number; label: string }) {
  return (
    <div className="card" style={{ padding: 20 }}>
      <Icon size={20} color={color} strokeWidth={1.8} style={{ marginBottom: 14 }} />
      <div style={{ fontSize: '1.75rem', fontWeight: 600, letterSpacing: '-0.03em', lineHeight: 1 }}>{value}</div>
      <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginTop: 6 }}>{label}</div>
    </div>
  );
}

// --- Mission Card ---
function MissionCard({ learner, nextLesson }: { learner: LearnerProfile; nextLesson: NextLesson | null }) {
  const isPlacementDone = learner.placement_completed === 'done';
  const NextIcon = nextLesson ? (SKILL_ICONS[nextLesson.skill] || Target) : Target;
  return (
    <div className="card" style={{ padding: 'var(--spacing-xl)', borderRadius: 'var(--radius-xl)', display: 'flex', flexDirection: 'column' }}>
      <div className="eyebrow" style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 'var(--spacing-md)' }}>
        <Target size={14} /> Bài học tiếp theo
      </div>

      {!isPlacementDone ? (
        <>
          <h3 style={{ fontSize: '1.5rem', marginBottom: 8 }}>Kiểm tra đầu vào</h3>
          <p style={{ marginBottom: 'var(--spacing-lg)', fontSize: '0.95rem', flex: 1 }}>
            Làm bài kiểm tra đầu vào để AI AGENT ENGLISH tạo lộ trình học riêng cho bạn.
          </p>
          <div>
            <Link href="/placement" className="btn btn-primary">
              Bắt đầu kiểm tra <ArrowRight size={16} />
            </Link>
          </div>
        </>
      ) : nextLesson ? (
        <>
          <h3 style={{ fontSize: '1.5rem', marginBottom: 6, display: 'flex', alignItems: 'center', gap: 10 }}>
            <NextIcon size={22} color="var(--agen-primary)" style={{ flexShrink: 0 }} /> {nextLesson.title}
          </h3>
          <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginBottom: 10 }}>
            {nextLesson.unit_title} · <span style={{ textTransform: 'capitalize' }}>{nextLesson.skill}</span>
          </div>
          <p style={{ marginBottom: 'var(--spacing-lg)', fontSize: '0.95rem', flex: 1 }}>{nextLesson.reason}</p>
          <div>
            <Link href={`/learn?code=${encodeURIComponent(nextLesson.code)}`} className="btn btn-primary">
              Bắt đầu bài học <ArrowRight size={16} />
            </Link>
          </div>
        </>
      ) : (
        <>
          <h3 style={{ fontSize: '1.5rem', marginBottom: 8 }}>Hoàn thành lộ trình</h3>
          <p style={{ marginBottom: 'var(--spacing-lg)', fontSize: '0.95rem', flex: 1 }}>
            Bạn đã hoàn thành toàn bộ lộ trình cấp độ hiện tại. Tự do luyện tập thêm nhé.
          </p>
          <div>
            <Link href="/learn" className="btn btn-primary">
              Luyện tập tự do <ArrowRight size={16} />
            </Link>
          </div>
        </>
      )}
    </div>
  );
}

// --- Review Card (spaced repetition) ---
function ReviewCard({ summary }: { summary: ReviewSummary }) {
  const due = summary.due_count;
  const empty = summary.vocab_total + summary.mistake_total === 0;
  return (
    <div className="card" style={{ padding: 'var(--spacing-xl)', borderRadius: 'var(--radius-xl)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 'var(--spacing-lg)', flexWrap: 'wrap' }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 16, minWidth: 0 }}>
        <span className="icon-tile" style={{ flexShrink: 0, width: 48, height: 48, borderRadius: 16, background: 'color-mix(in srgb, var(--skill-reading) 12%, transparent)', color: 'var(--skill-reading)' }}>
          <Brain size={24} strokeWidth={1.8} />
        </span>
        <div>
          <div className="eyebrow" style={{ marginBottom: 4 }}>Ôn tập thông minh</div>
          {empty ? (
            <div style={{ fontSize: '0.95rem', color: 'var(--text-secondary)' }}>Học xong một bài, từ mới và câu sai sẽ tự vào đây để ôn đúng lúc sắp quên.</div>
          ) : due > 0 ? (
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, flexWrap: 'wrap' }}>
              <span className="review-card-count">{due}</span>
              <span style={{ color: 'var(--text-secondary)' }}>mục cần ôn hôm nay · ~{Math.max(1, Math.round(due * 0.25))} phút</span>
            </div>
          ) : (
            <div style={{ fontSize: '0.95rem', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: 6 }}>
              <CircleCheck size={16} color="var(--agen-success)" /> Đã ôn xong hôm nay · {summary.mastered_count}/{summary.vocab_total + summary.mistake_total} mục đã thuộc
            </div>
          )}
        </div>
      </div>
      <div style={{ display: 'flex', gap: 'var(--spacing-sm)', flexWrap: 'wrap' }}>
        <Link href="/vocabulary" className="btn btn-ghost"><BookMarked size={16} /> Sổ từ vựng</Link>
        {!empty && (
          <Link href="/review" className={due > 0 ? 'btn btn-primary' : 'btn btn-outline'}>
            {due > 0 ? 'Ôn tập ngay' : 'Luyện thêm'} <ArrowRight size={16} />
          </Link>
        )}
      </div>
    </div>
  );
}

// --- Main Dashboard Page ---
export default function DashboardPage() {
  const router = useRouter();
  const { isAuthenticated, learner, setLearner, logout } = useAuthStore();
  const hydrated = useAuthHydrated();
  const [engagement, setEngagement] = useState<Engagement | null>(null);
  const [nextLesson, setNextLesson] = useState<NextLesson | null>(null);
  const [reviewSummary, setReviewSummary] = useState<ReviewSummary | null>(null);

  useEffect(() => {
    if (!hydrated) return;
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }
    // Always fetch fresh profile on mount; challenge + next lesson run after profile
    getMyProfile()
      .then((profile) => {
        setLearner(profile);
        getEngagement().then(setEngagement).catch(console.error);
        getReviewSummary().then(setReviewSummary).catch(console.error);
        // Only fetch the roadmap next lesson once placement is done
        if (profile.placement_completed === 'done') {
          getNextLesson(profile.overall_level).then(setNextLesson).catch(console.error);
        }
      })
      .catch(() => logout());
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hydrated, isAuthenticated]);

  if (!learner) {
    return <PageSkeleton cards={3} />;
  }

  return (
    <main style={{ minHeight: '100vh', padding: 'clamp(24px, 5vw, 48px) var(--page-gutter)' }}>
      <motion.div 
        className="container" 
        style={{ padding: 0 }}
        variants={containerVariants}
        initial="hidden"
        animate="show"
      >
        
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 16, marginBottom: 'var(--spacing-xl)' }}>
          <motion.div variants={itemVariants}>
            <h1 style={{ fontSize: 'clamp(1.9rem, 4vw, 2.5rem)', marginBottom: 6 }}>Xin chào, {learner.display_name}</h1>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)', flexWrap: 'wrap' }}>
              <span className="level-badge">{learner.overall_level}</span>
              <span className="streak-badge"><Flame size={13} /> {engagement?.streak.current ?? learner.current_streak} ngày liên tiếp</span>
              <span className="xp-badge"><Star size={13} fill="currentColor" /> {engagement?.total_xp ?? learner.total_xp} XP</span>
            </div>
          </motion.div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)', flexShrink: 0 }}>
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
        <motion.div variants={itemVariants} className="grid-2" style={{ marginBottom: 'var(--spacing-md)', gap: 'var(--spacing-md)' }}>
          <MissionCard learner={learner} nextLesson={nextLesson} />
          {engagement && <DailyQuests state={engagement} onChange={setEngagement} />}
        </motion.div>

        {(engagement || reviewSummary) && (
          <motion.div variants={itemVariants} className="grid-2" style={{ marginBottom: 'var(--spacing-md)', gap: 'var(--spacing-md)' }}>
            {engagement && <StreakWeekCard state={engagement} onChange={setEngagement} />}
            {reviewSummary && <ReviewCard summary={reviewSummary} />}
          </motion.div>
        )}

        <motion.div variants={itemVariants} style={{ marginBottom: 'var(--spacing-md)' }}>
          <ReminderCard />
        </motion.div>

        {/* Stats Row */}
        <motion.div variants={itemVariants} className="grid-4" style={{ gap: 'var(--spacing-md)', marginBottom: 'var(--spacing-md)' }}>
          <StatCard icon={BookOpen} color="var(--agen-primary)" value={learner.total_lessons_completed} label="Bài đã học" />
          <StatCard icon={Flame} color="var(--agen-secondary)" value={engagement?.streak.current ?? learner.current_streak} label="Ngày liên tiếp" />
          <StatCard icon={Star} color="var(--agen-accent)" value={engagement?.total_xp ?? learner.total_xp} label="Điểm XP" />
          <StatCard icon={GraduationCap} color="var(--skill-writing)" label="Trình độ" value={learner.overall_level} />
        </motion.div>

        {/* 4-Skill Tracker */}
        <motion.div variants={itemVariants} className="card" style={{ marginBottom: 'var(--spacing-2xl)', padding: 'var(--spacing-xl)', borderRadius: 'var(--radius-xl)' }}>
          <h3 style={{ marginBottom: 'var(--spacing-lg)' }}>4 kỹ năng</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 280px), 1fr))', gap: 'var(--spacing-lg) var(--spacing-xl)' }}>
            <SkillBar label="Listening" icon={Headphones} score={learner.listening_score} color="var(--skill-listening)" />
            <SkillBar label="Speaking" icon={Mic} score={learner.speaking_score} color="var(--skill-speaking)" />
            <SkillBar label="Reading" icon={BookOpen} score={learner.reading_score} color="var(--skill-reading)" />
            <SkillBar label="Writing" icon={PenLine} score={learner.writing_score} color="var(--skill-writing)" />
          </div>
        </motion.div>

        {/* Quick Access */}
        <motion.div variants={itemVariants}>
          <h3 style={{ marginBottom: 'var(--spacing-md)' }}>Học nhanh</h3>
          <div className="grid-4" style={{ gap: 'var(--spacing-md)' }}>
            {[
              { icon: Headphones, label: 'Listening', color: 'var(--skill-listening)', href: '/learn' },
              { icon: Mic,        label: 'Speaking',  color: 'var(--skill-speaking)',  href: '/practice/speaking' },
              { icon: BookOpen,   label: 'Reading',   color: 'var(--skill-reading)',   href: '/learn' },
              { icon: PenLine,    label: 'Writing',   color: 'var(--skill-writing)',   href: '/practice/writing' },
            ].map(({ icon: Icon, label, color, href }) => (
              <Link
                key={label}
                href={href}
                className="card card-hover"
                style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, padding: 20, opacity: 1 }}
              >
                <span style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <span className="icon-tile" style={{ background: `color-mix(in srgb, ${color} 12%, transparent)`, color, width: 40, height: 40 }}>
                    <Icon size={20} strokeWidth={1.8} />
                  </span>
                  <span style={{ fontWeight: 500, color: 'var(--text-primary)' }}>{label}</span>
                </span>
                <ChevronRight size={18} color="var(--text-muted)" />
              </Link>
            ))}
          </div>
        </motion.div>

        {/* Parent invite code */}
        {learner.invite_code && (
          <motion.div variants={itemVariants} className="card" style={{ marginTop: 'var(--spacing-2xl)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 16, flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
              <span className="icon-tile"><Users size={20} strokeWidth={1.8} /></span>
              <div>
                <div style={{ fontWeight: 500, marginBottom: 2 }}>Mã liên kết phụ huynh</div>
                <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                  Đưa mã này cho bố mẹ để theo dõi tiến bộ của bạn
                </div>
              </div>
            </div>
            <button
              type="button"
              onClick={() => navigator.clipboard?.writeText(learner.invite_code!)}
              title="Sao chép"
              style={{
                display: 'inline-flex', alignItems: 'center', gap: 10, cursor: 'pointer',
                fontFamily: 'var(--font-mono)', fontSize: '1.15rem', fontWeight: 600, letterSpacing: 2,
                color: 'var(--text-primary)', padding: '10px 16px',
                background: 'var(--bg-elevated)', borderRadius: 12, border: 'none',
              }}
            >
              {learner.invite_code}
              <Copy size={16} color="var(--text-muted)" />
            </button>
          </motion.div>
        )}

        {/* Upgrade Banner for Free users */}
        <motion.div
          variants={itemVariants}
          style={{ marginTop: 'var(--spacing-md)' }}
        >
          <Link href="/upgrade" className="card card-hover" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 16, flexWrap: 'wrap', opacity: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
              <span className="icon-tile" style={{ background: 'var(--bg-tint)', color: 'var(--agen-primary)' }}><Sparkles size={20} strokeWidth={1.8} /></span>
              <div>
                <div style={{ fontWeight: 500, color: 'var(--text-primary)', marginBottom: 2 }}>AI AGENT ENGLISH Premium</div>
                <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Bài học không giới hạn · Báo cáo phụ huynh · Lộ trình cá nhân hóa</div>
              </div>
            </div>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 2, color: 'var(--agen-primary-light)', fontSize: '0.92rem' }}>
              Tìm hiểu thêm <ChevronRight size={16} />
            </span>
          </Link>
        </motion.div>

      </motion.div>
    </main>
  );
}

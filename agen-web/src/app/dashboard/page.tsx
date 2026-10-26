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
import InstallAppCard from '@/components/engagement/InstallAppCard';
import LeagueCard from '@/components/engagement/LeagueCard';
import BlitzCard from '@/components/engagement/BlitzCard';
import FriendsCard from '@/components/engagement/FriendsCard';
import AssignmentsCard from '@/components/engagement/AssignmentsCard';
import Avatar from '@/components/ui/Avatar';
import Mascot from '@/components/ui/Mascot';
import CountUp from '@/components/ui/CountUp';
import SkillRing from '@/components/ui/SkillRing';
import { useSkin } from '@/store/skinStore';
import NotificationBell from '@/components/NotificationBell';
import { PageSkeleton } from '@/components/Skeleton';
import type { LearnerProfile } from '@/types';
import Link from 'next/link';
import {
  ArrowRight, BookMarked, BookOpen, BookText, Brain, ChevronRight, CircleCheck, ClipboardCheck, Copy, Flame, Gem, GraduationCap, Headphones, MessageCircleQuestion,
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

function todayLabel(): string {
  return new Date().toLocaleDateString('vi-VN', { weekday: 'long', day: 'numeric', month: 'long' });
}

function greeting(): string {
  const h = new Date().getHours();
  if (h < 11) return 'Chào buổi sáng';
  if (h < 14) return 'Chào buổi trưa';
  if (h < 18) return 'Chào buổi chiều';
  return 'Chào buổi tối';
}

// --- Sub-components ---

function StatCard({ icon: Icon, color, value, label }: { icon: LucideIcon; color: string; value: string | number; label: string }) {
  return (
    <div className="card stat-card" style={{ '--stat-color': color } as React.CSSProperties}>
      <span className="icon-tile"><Icon size={19} strokeWidth={1.9} /></span>
      <div className="stat-value">{typeof value === 'number' ? <CountUp value={value} /> : value}</div>
      <div className="stat-label">{label}</div>
    </div>
  );
}

// --- Hero: greeting, chips, next lesson and the four skills ---
function Hero({ learner, engagement, nextLesson, skin }: { learner: LearnerProfile; engagement: Engagement | null; nextLesson: NextLesson | null; skin: string }) {
  const isPlacementDone = learner.placement_completed === 'done';
  const NextIcon = nextLesson ? (SKILL_ICONS[nextLesson.skill] || Target) : Target;
  const streak = engagement?.streak.current ?? learner.current_streak;
  const xp = engagement?.total_xp ?? learner.total_xp;
  return (
    <motion.section variants={itemVariants} className="pro-hero">
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 6 }}>
          <Link href="/shop" aria-label="Avatar · Cửa hàng" style={{ flexShrink: 0, opacity: 1 }}>
            <Avatar avatar={learner.avatar} name={learner.display_name} size={skin === 'vivid' ? 60 : 52} />
          </Link>
          <div style={{ minWidth: 0 }}>
            <div className="eyebrow">{todayLabel()}</div>
            <h1 className="dash-greeting" style={{ margin: 0 }}>{greeting()}, {learner.display_name}</h1>
          </div>
        </div>
        <div className="pro-hero-chips">
          <span className="pro-chip"><GraduationCap size={14} /> {learner.overall_level}</span>
          <span className="pro-chip"><Flame size={14} color="#FFB454" /> {streak} ngày liên tiếp</span>
          <span className="pro-chip"><Star size={14} color="#FFD60A" fill="#FFD60A" /> {xp} XP</span>
          <Link href="/shop" className="pro-chip"><Gem size={14} color="#7DD3FC" /> {learner.gems ?? 0}</Link>
        </div>

        <div className="pro-hero-next">
          <div className="eyebrow" style={{ display: 'flex', alignItems: 'center', gap: 6 }}><Target size={13} /> {isPlacementDone ? 'Bài học tiếp theo' : 'Bước đầu tiên'}</div>
          {!isPlacementDone ? (
            <>
              <h3>Kiểm tra đầu vào</h3>
              <p>Làm bài kiểm tra 4 kỹ năng để AI AGENT ENGLISH tạo lộ trình học riêng cho bạn.</p>
              <Link href="/placement" className="btn btn-primary">Bắt đầu kiểm tra <ArrowRight size={16} /></Link>
            </>
          ) : nextLesson ? (
            <>
              <h3><NextIcon size={18} /> {nextLesson.title}</h3>
              <p>{nextLesson.unit_title} · <span style={{ textTransform: 'capitalize' }}>{nextLesson.skill}</span> — {nextLesson.reason}</p>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                <Link href={`/learn?code=${encodeURIComponent(nextLesson.code)}`} className="btn btn-primary">Bắt đầu bài học <ArrowRight size={16} /></Link>
                <Link href="/curriculum" className="btn btn-ghost btn-sm" style={{ alignSelf: 'center' }}>Xem lộ trình</Link>
              </div>
            </>
          ) : (
            <>
              <h3>Hoàn thành lộ trình</h3>
              <p>Bạn đã hoàn thành toàn bộ lộ trình cấp độ hiện tại. Tự do luyện tập thêm nhé.</p>
              <Link href="/learn" className="btn btn-primary">Luyện tập tự do <ArrowRight size={16} /></Link>
            </>
          )}
        </div>
      </div>

      <div>
        <div className="eyebrow" style={{ marginBottom: 12 }}>4 kỹ năng</div>
        <div className="pro-hero-rings">
          <SkillRing label="Nghe" icon={Headphones} score={learner.listening_score} color="#64D2FF" size={88} stroke={8} />
          <SkillRing label="Nói" icon={Mic} score={learner.speaking_score} color="#FF6B9A" size={88} stroke={8} />
          <SkillRing label="Đọc" icon={BookOpen} score={learner.reading_score} color="#4ADE80" size={88} stroke={8} />
          <SkillRing label="Viết" icon={PenLine} score={learner.writing_score} color="#C084FC" size={88} stroke={8} />
        </div>
      </div>
    </motion.section>
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
  const skin = useSkin();

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
        
        {/* Top bar */}
        <div className="dash-head" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12, marginBottom: 'var(--spacing-md)' }}>
          <motion.div variants={itemVariants} className="dash-head-main" style={{ minWidth: 0 }}>
            {skin === 'vivid' && (
              <Mascot size={72} mood={(engagement?.streak.studied_today) ? 'cheer' : 'happy'}
                say={engagement?.streak.studied_today ? `Hôm nay học rồi, giỏi quá! Chuỗi ${engagement.streak.current} ngày.` : (engagement?.streak.current ?? 0) > 0 ? `Học một bài để giữ chuỗi ${engagement?.streak.current} ngày nhé!` : 'Chào bạn! Cùng Bo học một bài hôm nay nào!'} />
            )}
          </motion.div>
          <div className="dash-head-actions" style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)', flexShrink: 0 }}>
            <NotificationBell />
            <button className="btn btn-ghost btn-sm" onClick={() => { logout(); router.push('/'); }}>Đăng xuất</button>
          </div>
        </div>

        <Hero learner={learner} engagement={engagement} nextLesson={nextLesson} skin={skin} />

        {engagement && (
          <motion.div variants={itemVariants} style={{ marginBottom: 'var(--spacing-md)' }}>
            <DailyQuests state={engagement} onChange={setEngagement} />
          </motion.div>
        )}

        {(engagement || reviewSummary) && (
          <motion.div variants={itemVariants} className="grid-2" style={{ marginBottom: 'var(--spacing-md)', gap: 'var(--spacing-md)' }}>
            {engagement && <StreakWeekCard state={engagement} onChange={setEngagement} />}
            {reviewSummary && <ReviewCard summary={reviewSummary} />}
          </motion.div>
        )}

        <motion.div variants={itemVariants} style={{ marginBottom: 'var(--spacing-md)', display: 'flex', flexDirection: 'column', gap: 'var(--spacing-md)' }}>
          <LeagueCard />
          <BlitzCard wordsKnown={reviewSummary?.vocab_total ?? 0} />
          <AssignmentsCard />
          <FriendsCard />
          <InstallAppCard />
          <ReminderCard />
        </motion.div>

        {/* Stats Row */}
        <motion.div variants={itemVariants} className="grid-4" style={{ gap: 'var(--spacing-md)', marginBottom: 'var(--spacing-md)' }}>
          <StatCard icon={BookOpen} color="var(--agen-primary)" value={learner.total_lessons_completed} label="Bài đã học" />
          <StatCard icon={Flame} color="var(--agen-secondary)" value={engagement?.streak.current ?? learner.current_streak} label="Ngày liên tiếp" />
          <StatCard icon={Star} color="var(--agen-accent)" value={engagement?.total_xp ?? learner.total_xp} label="Điểm XP" />
          <StatCard icon={GraduationCap} color="var(--skill-writing)" label="Trình độ" value={learner.overall_level} />
        </motion.div>

        {/* Quick Access */}
        <motion.div variants={itemVariants} style={{ marginBottom: 'var(--spacing-2xl)' }}>
          <div className="section-head"><h3>Luyện nhanh</h3><Link href="/practice/speaking">Tất cả <ChevronRight size={14} /></Link></div>
          <div className="grid-4" style={{ gap: 'var(--spacing-md)' }}>
            {[
              { icon: Headphones, label: 'Listening', sub: 'Nghe & shadowing', a: '#38BDF8', b: '#2563EB', href: '/learn' },
              { icon: Mic,        label: 'Speaking',  sub: 'Roleplay với AI', a: '#F472B6', b: '#E11D48', href: '/practice/speaking' },
              { icon: BookOpen,   label: 'Reading',   sub: 'Bài đọc theo cấp', a: '#34D399', b: '#059669', href: '/learn' },
              { icon: PenLine,    label: 'Writing',   sub: 'Chấm AI · band IELTS', a: '#A78BFA', b: '#7C3AED', href: '/practice/writing' },
              { icon: ClipboardCheck, label: 'Thi thử', sub: 'IELTS · TOEIC mini test', a: '#FBBF24', b: '#D97706', href: '/exams' },
              { icon: MessageCircleQuestion, label: 'Hỏi Bo', sub: 'Giải đáp ngữ pháp', a: '#2DD4BF', b: '#0D9488', href: '/tutor' },
            ].map(({ icon: Icon, label, sub, a, b, href }) => (
              <Link key={label} href={href} className="card card-hover quick-tile" style={{ '--qt-a': a, '--qt-b': b } as React.CSSProperties}>
                <span style={{ display: 'flex', alignItems: 'center', gap: 12, minWidth: 0 }}>
                  <span className="icon-tile"><Icon size={20} strokeWidth={1.9} /></span>
                  <span style={{ minWidth: 0 }}>
                    <span style={{ display: 'block', fontWeight: 600, color: 'var(--text-primary)' }}>{label}</span>
                    <span style={{ display: 'block', fontSize: '0.78rem', color: 'var(--text-muted)' }}>{sub}</span>
                  </span>
                </span>
                <ChevronRight size={18} className="chev" />
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

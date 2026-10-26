'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuthStore } from '@/store/authStore';
import {
  getOverview, getActivity, getCoachAdvice, getWeeklyReport,
  getAssessmentOutcomes, getLeaderboard,
  OverviewData, ActivityData, CoachAdvice, WeeklyReport, AssessmentOutcome, LeaderboardResponse
} from '@/lib/analyticsService';
import { getAchievements } from '@/lib/services';
import type { Achievement } from '@/types';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, BookOpen, BookText, CalendarDays, CircleAlert, CircleCheck, Flame, GraduationCap, Headphones, LoaderCircle, Mic, PenLine, Sparkles, Star, Target, TrendingUp, Trophy, type LucideIcon } from 'lucide-react';

// ── Skill Bar Component ───────────────────────────────────────────────────────
function AnimatedSkillBar({ label, score, color, icon: Icon }: { label: string; score: number; color: string; icon: LucideIcon }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', display: 'inline-flex', alignItems: 'center', gap: 8 }}><Icon size={16} color={color} /> {label}</span>
        <span style={{ fontWeight: 600 }}>{score.toFixed(0)}%</span>
      </div>
      <div className="progress-bar">
        <div className="progress-fill" style={{ width: `${score}%`, background: color }} />
      </div>
    </div>
  );
}

// ── Activity Calendar ─────────────────────────────────────────────────────────
function ActivityCalendar({ days }: { days: ActivityData['days'] }) {
  const last30 = days.slice(-30);

  const getIntensity = (xp: number) => {
    if (xp === 0) return 0;
    if (xp < 20) return 1;
    if (xp < 50) return 2;
    if (xp < 80) return 3;
    return 4;
  };

  const colors = [
    'var(--bg-elevated)',             // 0 - no activity
    'rgba(0,113,227,0.25)',          // 1 - low
    'rgba(0,113,227,0.5)',           // 2 - medium
    'rgba(0,113,227,0.75)',          // 3 - high
    'var(--agen-primary)',            // 4 - max
  ];

  return (
    <div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
        {last30.map((day) => {
          const intensity = getIntensity(day.xp);
          return (
            <div
              key={day.date}
              title={`${day.date}: ${day.xp} XP, ${day.sessions} sessions`}
              style={{
                width: 16, height: 16, borderRadius: 4,
                background: colors[intensity],
                cursor: 'default',
              }}
            />
          );
        })}
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 10, fontSize: '0.75rem', color: 'var(--text-muted)' }}>
        <span>Ít</span>
        {colors.map((c, i) => (
          <div key={i} style={{ width: 12, height: 12, borderRadius: 3, background: c }} />
        ))}
        <span>Nhiều</span>
      </div>
    </div>
  );
}

// ── Main Progress Page ────────────────────────────────────────────────────────
export default function ProgressPage() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();

  const [overview, setOverview] = useState<OverviewData | null>(null);
  const [activity, setActivity] = useState<ActivityData | null>(null);
  const [coach, setCoach] = useState<CoachAdvice | null>(null);
  const [report, setReport] = useState<WeeklyReport | null>(null);
  const [achievements, setAchievements] = useState<Achievement[]>([]);
  const [assessment, setAssessment] = useState<AssessmentOutcome | null>(null);
  const [leaderboard, setLeaderboard] = useState<LeaderboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [coachLoading, setCoachLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState<'progress' | 'leaderboard'>('progress');

  useEffect(() => {
    if (!isAuthenticated) { router.push('/login'); return; }

    // Load overview, activity & achievements first (fast)
    Promise.all([getOverview(), getActivity(30), getAchievements(), getAssessmentOutcomes(), getLeaderboard()])
      .then(([ov, ac, achs, outcome, lb]) => { setOverview(ov); setActivity(ac); setAchievements(achs); setAssessment(outcome); setLeaderboard(lb); })
      .catch(() => setError('Không thể tải dữ liệu tiến bộ'))
      .finally(() => setLoading(false));

    // Load AI coach advice & weekly report (slower — separate)
    Promise.all([getCoachAdvice(), getWeeklyReport()])
      .then(([c, r]) => { setCoach(c); setReport(r); })
      .catch(() => { /* non-critical */ })
      .finally(() => setCoachLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated]);

  if (loading) return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10, color: 'var(--text-muted)' }}>
      <LoaderCircle className="animate-spin" size={20} /> Đang phân tích tiến bộ của bạn…
    </div>
  );

  if (error || !overview) return (
    <div style={{ padding: 40, textAlign: 'center' }}>
      <p style={{ color: 'var(--agen-secondary)', display: 'inline-flex', alignItems: 'center', gap: 8 }}><CircleAlert size={16} /> {error || 'Không thể tải dữ liệu'}</p>
      <div><Link href="/dashboard" className="btn btn-outline" style={{ marginTop: 16 }}><ArrowLeft size={16} /> Về Dashboard</Link></div>
    </div>
  );

  return (
    <main style={{ padding: 'clamp(24px, 5vw, 48px) var(--spacing-lg)', minHeight: '100vh' }}>
      <div className="container" style={{ maxWidth: 980, padding: 0 }}>

        {/* ── Header ── */}
        <div className="animate-fade-in-up" style={{ marginBottom: 'var(--spacing-xl)' }}>
          <Link href="/dashboard" style={{ display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: '0.92rem', marginBottom: 12 }}><ArrowLeft size={16} /> Dashboard</Link>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16 }}>
            <div>
              <h1 style={{ fontSize: 'clamp(1.9rem, 4vw, 2.5rem)' }}>Tiến bộ</h1>
              <p style={{ color: 'var(--text-muted)', marginTop: 6 }}>Phân tích hành trình học và so sánh với cộng đồng.</p>
            </div>
            
            {/* Tabs */}
            <div className="segmented">
              <button
                onClick={() => setActiveTab('progress')}
                aria-pressed={activeTab === 'progress'}
              >
                Tiến bộ cá nhân
              </button>
              <button
                onClick={() => setActiveTab('leaderboard')}
                aria-pressed={activeTab === 'leaderboard'}
              >
                Bảng xếp hạng
              </button>
            </div>
          </div>
        </div>

        {activeTab === 'progress' ? (
          <AnimatePresence mode="wait">
            <motion.div key="progress-tab" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}>
              {/* ── Hero Stats ── */}
        <div className="animate-fade-in-up delay-100" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 'var(--spacing-md)', marginBottom: 'var(--spacing-xl)' }}>
          {[
            { label: 'Trình độ', value: overview.overall_level, icon: GraduationCap, color: 'var(--skill-writing)' },
            { label: 'Tổng XP', value: overview.total_xp, icon: Star, color: 'var(--agen-accent)' },
            { label: 'Chuỗi ngày học', value: `${overview.current_streak} ngày`, icon: Flame, color: 'var(--agen-secondary)' },
            { label: 'Bài học', value: overview.total_lessons_completed, icon: BookOpen, color: 'var(--agen-primary)' },
          ].map((s) => (
            <div key={s.label} className="card" style={{ padding: 20 }}>
              <s.icon size={20} strokeWidth={1.8} color={s.color} style={{ marginBottom: 14 }} />
              <div style={{ fontSize: '1.75rem', fontWeight: 600, letterSpacing: '-0.03em', lineHeight: 1 }}>{s.value}</div>
              <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginTop: 6 }}>{s.label}</div>
            </div>
          ))}
        </div>

        {assessment?.baseline && (
          <div className="animate-fade-in-up delay-175 card" style={{ marginBottom: 'var(--spacing-xl)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
              <div>
                <h3 style={{ marginBottom: 4 }}>Mức tiến bộ đo được</h3>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.82rem', margin: 0 }}>
                  So sánh bài đánh giá đầu vào với lần kiểm tra tiến bộ gần nhất.
                </p>
              </div>
              {assessment.accuracy_delta !== null && (
                <strong style={{ fontSize: '1.4rem', fontWeight: 600, color: assessment.accuracy_delta >= 0 ? 'var(--agen-success)' : 'var(--agen-secondary)' }}>
                  {assessment.accuracy_delta >= 0 ? '+' : ''}{assessment.accuracy_delta.toFixed(1)} điểm
                </strong>
              )}
            </div>
            {assessment.latest_followup ? (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: 10, marginTop: 16 }}>
                {Object.entries(assessment.skill_deltas).map(([skill, delta]) => (
                  <div key={skill} style={{ padding: 12, background: 'var(--bg-elevated)', borderRadius: 12 }}>
                    <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', textTransform: 'capitalize' }}>{skill}</div>
                    <strong style={{ color: delta >= 0 ? 'var(--agen-success)' : 'var(--agen-secondary)' }}>
                      {delta >= 0 ? '+' : ''}{delta.toFixed(1)}
                    </strong>
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: 0 }}>
                Hãy làm bài đánh giá tiến bộ sau một thời gian học để xem mức cải thiện.
              </p>
            )}
          </div>
        )}

        {/* ── XP Progress to Next Level ── */}
        <div className="animate-fade-in-up delay-150 card" style={{ marginBottom: 'var(--spacing-xl)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <span style={{ fontWeight: 600 }}>Tiến độ lên level tiếp theo</span>
            <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>{overview.progress_pct.toFixed(0)}% · cần thêm <b style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{overview.xp_to_next_level} XP</b></span>
          </div>
          <div className="progress-bar" style={{ height: 8 }}>
            <div className="progress-fill" style={{ width: `${overview.progress_pct}%` }} />
          </div>
        </div>

        {/* ── Two Column Grid ── */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 'var(--spacing-lg)', marginBottom: 'var(--spacing-xl)' }}>

          {/* Skill Scores */}
          <div className="animate-fade-in-up delay-200 card">
            <h3 style={{ marginBottom: 'var(--spacing-lg)' }}>Điểm kỹ năng</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-md)' }}>
              <AnimatedSkillBar label="Listening" score={overview.skill_scores.listening} color="var(--skill-listening)" icon={Headphones} />
              <AnimatedSkillBar label="Speaking"  score={overview.skill_scores.speaking}  color="var(--skill-speaking)"  icon={Mic} />
              <AnimatedSkillBar label="Reading"   score={overview.skill_scores.reading}   color="var(--skill-reading)"   icon={BookOpen} />
              <AnimatedSkillBar label="Writing"   score={overview.skill_scores.writing}        color="var(--skill-writing)"   icon={PenLine} />
              <AnimatedSkillBar label="Vocabulary" score={overview.skill_scores.vocabulary} color="var(--agen-accent)"    icon={BookText} />
            </div>
            <Link href="/placement?type=followup" className="btn btn-ghost btn-sm" style={{ marginTop: 'var(--spacing-lg)' }}>
              <TrendingUp size={15} /> Đánh giá tiến bộ
            </Link>
          </div>

          {/* Activity Calendar */}
          <div className="animate-fade-in-up delay-200 card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--spacing-md)' }}>
              <h3>Lịch học tập</h3>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>30 ngày qua</span>
            </div>
            {activity ? <ActivityCalendar days={activity.days} /> : <p style={{ color: 'var(--text-muted)' }}>Đang tải…</p>}
            <div style={{ display: 'flex', gap: 32, marginTop: 20, paddingTop: 16, borderTop: '1px solid var(--border-subtle)' }}>
              <div>
                <div style={{ fontSize: '1.5rem', fontWeight: 600, letterSpacing: '-0.02em' }}>{activity?.total_xp_30d || 0}</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>XP kiếm được</div>
              </div>
              <div>
                <div style={{ fontSize: '1.5rem', fontWeight: 600, letterSpacing: '-0.02em' }}>{activity?.total_sessions_30d || 0}</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Buổi học</div>
              </div>
            </div>
          </div>
        </div>

        {/* ── AI Coach Corner ── */}
        <div className="animate-fade-in-up delay-300" style={{ marginBottom: 'var(--spacing-xl)' }}>
          <div className="card">
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
              <span className="icon-tile" style={{ background: 'var(--bg-tint)', color: 'var(--agen-primary)' }}><Sparkles size={20} strokeWidth={1.8} /></span>
              <div>
                <div style={{ fontWeight: 600 }}>AGEN Coach</div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Lời khuyên học tập hôm nay</div>
              </div>
            </div>

            {coachLoading ? (
              <div style={{ color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 8 }}><LoaderCircle className="animate-spin" size={16} /> Coach đang phân tích dữ liệu học của bạn…</div>
            ) : coach ? (
              <>
                {/* Motivational message */}
                <div style={{ padding: 16, background: 'var(--bg-elevated)', borderRadius: 14, marginBottom: 16, lineHeight: 1.6, fontSize: '1.02rem' }}>
                  {coach.motivational_message}
                </div>

                {/* Study plan */}
                <div style={{ marginBottom: 16 }}>
                  <div style={{ fontWeight: 600, marginBottom: 8 }}>Kế hoạch học hôm nay</div>
                  <div style={{ padding: '12px 16px', background: 'var(--bg-elevated)', borderRadius: 12, fontSize: '0.92rem' }}>
                    {coach.study_plan_today}
                  </div>
                </div>

                {/* Weak/Strong */}
                <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap' }}>
                  {coach.weak_skills.length > 0 && (
                    <div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 500, marginBottom: 6 }}>Cần luyện thêm</div>
                      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                        {coach.weak_skills.map(s => (
                          <span key={s} style={{ padding: '3px 10px', borderRadius: 99, background: 'rgba(255,59,48,0.08)', color: 'var(--agen-secondary)', fontSize: '0.8rem', fontWeight: 500, textTransform: 'capitalize' }}>{s}</span>
                        ))}
                      </div>
                    </div>
                  )}
                  {coach.strong_skills.length > 0 && (
                    <div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 500, marginBottom: 6 }}>Điểm mạnh</div>
                      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                        {coach.strong_skills.map(s => (
                          <span key={s} style={{ padding: '3px 10px', borderRadius: 99, background: 'rgba(52,199,89,0.1)', color: 'var(--agen-success)', fontSize: '0.8rem', fontWeight: 500, textTransform: 'capitalize' }}>{s}</span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* Recommended topics */}
                {coach.recommended_topics?.length > 0 && (
                  <div style={{ marginTop: 16 }}>
                    <div style={{ fontWeight: 600, marginBottom: 10 }}>Bài học gợi ý</div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                      {coach.recommended_topics.map((t, i) => (
                        <Link
                          key={i}
                          href="/learn"
                          className="card card-hover"
                          style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12, padding: '12px 16px', background: 'var(--bg-elevated)', border: 'none', opacity: 1, color: 'var(--text-primary)' }}
                        >
                          <div>
                            <span style={{ textTransform: 'capitalize', color: 'var(--agen-primary-light)', fontWeight: 500, fontSize: '0.92rem' }}>{t.skill}</span>
                            {' · '}
                            <span>{t.topic}</span>
                          </div>
                          <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{t.reason}</span>
                        </Link>
                      ))}
                    </div>
                  </div>
                )}
              </>
            ) : (
              <p style={{ color: 'var(--text-muted)' }}>Coach chưa có dữ liệu để phân tích. Hãy hoàn thành ít nhất 1 bài học!</p>
            )}
          </div>
        </div>

        {/* ── Weekly Report ── */}
        <div className="animate-fade-in-up delay-400">
          <div className="card">
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20 }}>
              <span className="icon-tile"><CalendarDays size={20} strokeWidth={1.8} /></span>
              <div>
                <div style={{ fontWeight: 600 }}>Báo cáo tuần này</div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>AI tổng hợp 7 ngày qua</div>
              </div>
            </div>

            {coachLoading ? (
              <div style={{ color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 8 }}><LoaderCircle className="animate-spin" size={16} /> Đang tạo báo cáo…</div>
            ) : report ? (
              <>
                {/* Stats row */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 12, marginBottom: 20 }}>
                  {[
                    { label: 'Buổi học', value: report.sessions_count, color: 'var(--text-primary)' },
                    { label: 'XP kiếm được', value: `+${report.xp_earned_this_week}`, color: 'var(--text-primary)' },
                    { label: 'Kỹ năng tốt nhất', value: report.best_skill, color: 'var(--agen-success)' },
                  ].map(s => (
                    <div key={s.label} style={{ padding: 14, background: 'var(--bg-elevated)', borderRadius: 12 }}>
                      <div style={{ fontSize: '1.35rem', fontWeight: 600, letterSpacing: '-0.02em', color: s.color, textTransform: 'capitalize' }}>{s.value}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 4 }}>{s.label}</div>
                    </div>
                  ))}
                </div>

                {/* Highlight */}
                <div style={{ padding: 14, background: 'rgba(52,199,89,0.08)', borderRadius: 12, marginBottom: 14 }}>
                  <b style={{ fontWeight: 600 }}>Điểm nổi bật:</b> {report.highlight}
                </div>

                {/* Areas to improve */}
                {report.areas_to_improve?.length > 0 && (
                  <div style={{ marginBottom: 14 }}>
                    <div style={{ fontWeight: 600, marginBottom: 8 }}>Cần cải thiện tuần tới</div>
                    <ul style={{ paddingLeft: 20, color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                      {report.areas_to_improve.map((a, i) => <li key={i}>{a}</li>)}
                    </ul>
                  </div>
                )}

                {/* Goal & encouragement */}
                <div style={{ padding: 14, background: 'var(--bg-tint)', borderRadius: 12, display: 'flex', gap: 8, alignItems: 'flex-start' }}>
                  <Target size={16} color="var(--agen-primary)" style={{ flexShrink: 0, marginTop: 3 }} /><span><b style={{ fontWeight: 600 }}>Mục tiêu tuần tới:</b> {report.next_week_goal}</span>
                </div>
                <div style={{ marginTop: 12, color: 'var(--text-secondary)' }}>
                  {report.encouragement}
                </div>
              </>
            ) : (
              <p style={{ color: 'var(--text-muted)' }}>Hoàn thành ít nhất 1 bài học để xem báo cáo tuần của bạn.</p>
            )}
          </div>
        </div>

        {/* ── Achievements ── */}
        <div className="animate-fade-in-up delay-500" style={{ marginTop: 'var(--spacing-xl)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 'var(--spacing-lg)' }}>
            <div>
              <h3 style={{ margin: 0 }}>Thành tựu</h3>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Thu thập tất cả huy hiệu trên hành trình học.</div>
            </div>
          </div>
          
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 'var(--spacing-md)' }}>
            {achievements.map((ach) => (
              <div
                key={ach.id}
                className="card"
                style={{
                  textAlign: 'center',
                  padding: 'var(--spacing-lg) var(--spacing-md)',
                  opacity: ach.earned ? 1 : 0.45,
                  filter: ach.earned ? 'none' : 'grayscale(100%)',
                  position: 'relative'
                }}
              >
                {ach.earned && (
                  <CircleCheck size={16} color="var(--agen-success)" style={{ position: 'absolute', top: 12, right: 12 }} />
                )}
                <div style={{ fontSize: '2.4rem', marginBottom: 12 }}>{ach.icon}</div>
                <div style={{ fontWeight: 600, marginBottom: 4 }}>{ach.name}</div>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>{ach.description}</div>
                <div className="xp-badge" style={{ marginTop: 12, fontSize: '0.72rem', padding: '2px 8px' }}>
                  +{ach.xp_reward} XP
                </div>
              </div>
            ))}
          </div>
        </div>
            </motion.div>
          </AnimatePresence>
        ) : (
          <AnimatePresence mode="wait">
            <motion.div key="leaderboard-tab" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}>
              
              <div className="card" style={{ marginBottom: 'var(--spacing-xl)', padding: 'var(--spacing-xl)' }}>
                <div style={{ textAlign: 'center', marginBottom: 24 }}>
                  <Trophy size={32} strokeWidth={1.6} color="var(--agen-accent)" style={{ marginBottom: 12 }} />
                  <h3>Top 10 học viên AGEN</h3>
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Bảng xếp hạng vinh danh những học viên chăm chỉ nhất</p>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column' }}>
                  {leaderboard?.entries?.map((entry, idx) => (
                    <div 
                      key={entry.learner_id} 
                      style={{ 
                        display: 'flex', alignItems: 'center', padding: '14px 16px', borderRadius: 12,
                        background: entry.is_current_user ? 'var(--bg-tint)' : 'transparent',
                        borderTop: idx && !entry.is_current_user ? '1px solid var(--border-subtle)' : '1px solid transparent'
                      }}
                    >
                      <div style={{ width: 32, fontWeight: 600, color: idx < 3 ? 'var(--text-primary)' : 'var(--text-muted)' }}>
                        {idx + 1}
                      </div>
                      <div style={{ fontSize: '1.4rem', marginRight: 14 }}>{entry.avatar}</div>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontWeight: 500, display: 'flex', alignItems: 'center', gap: 8 }}>
                          {entry.display_name} 
                          {entry.is_current_user && <span style={{ fontSize: '0.7rem', background: 'var(--agen-primary)', color: 'white', padding: '2px 8px', borderRadius: 99, fontWeight: 500 }}>Bạn</span>}
                        </div>
                        <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Level: {entry.level}</div>
                      </div>
                      <div style={{ fontWeight: 600 }}>
                        {entry.xp} XP
                      </div>
                    </div>
                  ))}
                  
                  {(!leaderboard || leaderboard.entries.length === 0) && (
                    <p style={{ textAlign: 'center', color: 'var(--text-muted)' }}>Chưa có dữ liệu xếp hạng.</p>
                  )}
                </div>
              </div>
              
              {/* 30 days summary */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: 16 }}>
                 <div className="card text-center">
                    <h4>Bạn đã học được gì trong 30 ngày qua?</h4>
                    <p style={{ color: 'var(--text-secondary)', marginTop: 8, fontSize: '0.9rem' }}>
                      Bạn đã hoàn thành <b>{activity?.total_sessions_30d || 0} buổi học</b> và kiếm được <b>{activity?.total_xp_30d || 0} XP</b>.
                      <br/>
                      Mỗi nỗ lực nhỏ đều dẫn đến kết quả lớn. Tiếp tục phát huy nhé!
                    </p>
                 </div>
              </div>

            </motion.div>
          </AnimatePresence>
        )}
      </div>
    </main>
  );
}

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

// ── Skill Bar Component ───────────────────────────────────────────────────────
function AnimatedSkillBar({ label, score, color, icon }: { label: string; score: number; color: string; icon: string }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>{icon} {label}</span>
        <span style={{ fontWeight: 800, color, fontSize: '1.1rem' }}>{score.toFixed(0)}<span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>%</span></span>
      </div>
      <div style={{ height: 10, background: 'var(--bg-base)', borderRadius: 99, overflow: 'hidden' }}>
        <div
          className="animate-progress"
          style={{
            height: '100%', borderRadius: 99,
            background: `linear-gradient(90deg, ${color}aa, ${color})`,
            width: `${score}%`,
            transition: 'width 1s ease-out',
            boxShadow: `0 0 8px ${color}66`,
          }}
        />
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
    'rgba(108,99,255,0.25)',          // 1 - low
    'rgba(108,99,255,0.50)',          // 2 - medium
    'rgba(108,99,255,0.75)',          // 3 - high
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
                width: 16, height: 16, borderRadius: 3,
                background: colors[intensity],
                border: '1px solid rgba(255,255,255,0.05)',
                cursor: 'default',
              }}
            />
          );
        })}
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 10, fontSize: '0.75rem', color: 'var(--text-muted)' }}>
        <span>Ít</span>
        {colors.map((c, i) => (
          <div key={i} style={{ width: 12, height: 12, borderRadius: 2, background: c, border: '1px solid rgba(255,255,255,0.05)' }} />
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
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ textAlign: 'center' }}>
        <div style={{ fontSize: '2.5rem', marginBottom: 16 }}>📊</div>
        <p>Đang phân tích tiến bộ của bạn...</p>
      </div>
    </div>
  );

  if (error || !overview) return (
    <div style={{ padding: 40, textAlign: 'center' }}>
      <p style={{ color: 'var(--agen-secondary)' }}>⚠️ {error || 'Không thể tải dữ liệu'}</p>
      <Link href="/dashboard" className="btn btn-outline" style={{ marginTop: 16 }}>← Về Dashboard</Link>
    </div>
  );

  return (
    <main style={{ padding: 'var(--spacing-lg)', minHeight: '100vh' }}>
      <div className="container" style={{ maxWidth: 900 }}>

        {/* ── Header ── */}
        <div className="animate-fade-in-up" style={{ marginBottom: 'var(--spacing-xl)' }}>
          <Link href="/dashboard" style={{ color: 'var(--text-muted)', display: 'inline-block', marginBottom: 16 }}>← Dashboard</Link>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16 }}>
            <div>
              <h2>📊 Báo cáo & Xếp hạng</h2>
              <p style={{ color: 'var(--text-muted)' }}>Phân tích hành trình học và so sánh với cộng đồng</p>
            </div>
            
            {/* Tabs */}
            <div style={{ display: 'flex', background: 'var(--bg-elevated)', borderRadius: 99, padding: 4 }}>
              <button 
                onClick={() => setActiveTab('progress')}
                style={{ padding: '8px 20px', borderRadius: 99, border: 'none', background: activeTab === 'progress' ? 'var(--gradient-primary)' : 'transparent', color: activeTab === 'progress' ? 'white' : 'var(--text-muted)', fontWeight: 600, cursor: 'pointer', transition: 'all 0.2s' }}
              >
                Tiến bộ cá nhân
              </button>
              <button 
                onClick={() => setActiveTab('leaderboard')}
                style={{ padding: '8px 20px', borderRadius: 99, border: 'none', background: activeTab === 'leaderboard' ? 'var(--gradient-primary)' : 'transparent', color: activeTab === 'leaderboard' ? 'white' : 'var(--text-muted)', fontWeight: 600, cursor: 'pointer', transition: 'all 0.2s' }}
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
            { label: 'Trình độ', value: overview.overall_level, emoji: '🎯', color: 'var(--agen-primary-light)' },
            { label: 'Tổng XP', value: overview.total_xp, emoji: '⭐', color: 'var(--agen-accent)' },
            { label: 'Streak', value: `${overview.current_streak} ngày`, emoji: '🔥', color: '#FF6B35' },
            { label: 'Bài học', value: overview.total_lessons_completed, emoji: '📚', color: 'var(--agen-success)' },
          ].map((s) => (
            <div key={s.label} className="card" style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '2rem', marginBottom: 6 }}>{s.emoji}</div>
              <div style={{ fontSize: '1.6rem', fontWeight: 900, color: s.color }}>{s.value}</div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: 4 }}>{s.label}</div>
            </div>
          ))}
        </div>

        {assessment?.baseline && (
          <div className="animate-fade-in-up delay-175 card" style={{ marginBottom: 'var(--spacing-xl)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
              <div>
                <h3 style={{ marginBottom: 4 }}>📐 Mức tiến bộ đo được</h3>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.82rem', margin: 0 }}>
                  So sánh bài đánh giá đầu vào với lần kiểm tra tiến bộ gần nhất.
                </p>
              </div>
              {assessment.accuracy_delta !== null && (
                <strong style={{ fontSize: '1.4rem', color: assessment.accuracy_delta >= 0 ? 'var(--agen-success)' : 'var(--agen-secondary)' }}>
                  {assessment.accuracy_delta >= 0 ? '+' : ''}{assessment.accuracy_delta.toFixed(1)} điểm
                </strong>
              )}
            </div>
            {assessment.latest_followup ? (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: 10, marginTop: 16 }}>
                {Object.entries(assessment.skill_deltas).map(([skill, delta]) => (
                  <div key={skill} style={{ padding: 10, background: 'var(--bg-elevated)', borderRadius: 8 }}>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{skill}</div>
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
            <span style={{ fontWeight: 600 }}>⬆️ Tiến độ lên Level tiếp theo</span>
            <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Cần thêm <b style={{ color: 'var(--agen-accent)' }}>{overview.xp_to_next_level} XP</b></span>
          </div>
          <div style={{ height: 14, background: 'var(--bg-base)', borderRadius: 99, overflow: 'hidden' }}>
            <div style={{
              height: '100%', borderRadius: 99, transition: 'width 1.2s ease-out',
              background: 'linear-gradient(90deg, var(--agen-primary), var(--agen-accent))',
              width: `${overview.progress_pct}%`,
              boxShadow: '0 0 12px rgba(108,99,255,0.5)',
              position: 'relative'
            }}>
              <div style={{ position: 'absolute', right: 8, top: '50%', transform: 'translateY(-50%)', fontSize: '0.6rem', fontWeight: 800, color: 'white' }}>
                {overview.progress_pct.toFixed(0)}%
              </div>
            </div>
          </div>
        </div>

        {/* ── Two Column Grid ── */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--spacing-lg)', marginBottom: 'var(--spacing-xl)' }}>

          {/* Skill Scores */}
          <div className="animate-fade-in-up delay-200 card">
            <h3 style={{ marginBottom: 'var(--spacing-lg)' }}>📈 Điểm 4 Kỹ năng</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-md)' }}>
              <AnimatedSkillBar label="Listening" score={overview.skill_scores.listening} color="var(--skill-listening)" icon="🎧" />
              <AnimatedSkillBar label="Speaking"  score={overview.skill_scores.speaking}  color="var(--skill-speaking)"  icon="🗣️" />
              <AnimatedSkillBar label="Reading"   score={overview.skill_scores.reading}   color="var(--skill-reading)"   icon="📖" />
              <AnimatedSkillBar label="Writing"   score={overview.skill_scores.writing}        color="var(--skill-writing)"   icon="✍️" />
              <AnimatedSkillBar label="Vocabulary" score={overview.skill_scores.vocabulary} color="var(--agen-accent)"    icon="📚" />
            </div>
            <Link href="/placement?type=followup" className="btn btn-ghost btn-sm" style={{ marginTop: 'var(--spacing-lg)' }}>
              📈 Đánh giá tiến bộ
            </Link>
          </div>

          {/* Activity Calendar */}
          <div className="animate-fade-in-up delay-200 card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--spacing-md)' }}>
              <h3>🗓️ Lịch học tập</h3>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>30 ngày qua</span>
            </div>
            {activity ? <ActivityCalendar days={activity.days} /> : <p style={{ color: 'var(--text-muted)' }}>Đang tải...</p>}
            <div style={{ display: 'flex', gap: 16, marginTop: 20, paddingTop: 16, borderTop: '1px solid var(--border-subtle)' }}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--agen-accent)' }}>{activity?.total_xp_30d || 0}</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>XP earned</div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--agen-success)' }}>{activity?.total_sessions_30d || 0}</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Buổi học</div>
              </div>
            </div>
          </div>
        </div>

        {/* ── AI Coach Corner ── */}
        <div className="animate-fade-in-up delay-300" style={{ marginBottom: 'var(--spacing-xl)' }}>
          <div className="card" style={{ background: 'linear-gradient(135deg, rgba(108,99,255,0.08), rgba(255,158,64,0.08))', borderColor: 'rgba(108,99,255,0.3)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
              <span style={{ fontSize: '1.8rem' }}>🤖</span>
              <div>
                <div style={{ fontWeight: 700, color: 'var(--agen-primary-light)' }}>AGEN Coach</div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Lời khuyên học tập hôm nay</div>
              </div>
            </div>

            {coachLoading ? (
              <div style={{ color: 'var(--text-muted)', fontStyle: 'italic' }}>🧠 Coach đang phân tích dữ liệu học của bạn...</div>
            ) : coach ? (
              <>
                {/* Motivational message */}
                <div style={{ padding: 16, background: 'rgba(108,99,255,0.06)', borderRadius: 8, marginBottom: 16, borderLeft: '3px solid var(--agen-primary)', lineHeight: 1.6 }}>
                  💬 {coach.motivational_message}
                </div>

                {/* Study plan */}
                <div style={{ marginBottom: 16 }}>
                  <div style={{ fontWeight: 600, marginBottom: 8 }}>📅 Kế hoạch học hôm nay:</div>
                  <div style={{ padding: '10px 14px', background: 'var(--bg-elevated)', borderRadius: 8, fontFamily: 'monospace', fontSize: '0.9rem' }}>
                    {coach.study_plan_today}
                  </div>
                </div>

                {/* Weak/Strong */}
                <div style={{ display: 'flex', gap: 16 }}>
                  {coach.weak_skills.length > 0 && (
                    <div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--agen-secondary)', fontWeight: 600, marginBottom: 6 }}>⚠️ Cần luyện thêm</div>
                      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                        {coach.weak_skills.map(s => (
                          <span key={s} style={{ padding: '3px 10px', borderRadius: 99, background: 'rgba(255,107,107,0.1)', color: 'var(--agen-secondary)', fontSize: '0.8rem', fontWeight: 600 }}>{s}</span>
                        ))}
                      </div>
                    </div>
                  )}
                  {coach.strong_skills.length > 0 && (
                    <div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--agen-success)', fontWeight: 600, marginBottom: 6 }}>✅ Điểm mạnh</div>
                      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                        {coach.strong_skills.map(s => (
                          <span key={s} style={{ padding: '3px 10px', borderRadius: 99, background: 'rgba(6,214,160,0.1)', color: 'var(--agen-success)', fontSize: '0.8rem', fontWeight: 600 }}>{s}</span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* Recommended topics */}
                {coach.recommended_topics?.length > 0 && (
                  <div style={{ marginTop: 16 }}>
                    <div style={{ fontWeight: 600, marginBottom: 10 }}>🎯 Bài học gợi ý:</div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                      {coach.recommended_topics.map((t, i) => (
                        <Link
                          key={i}
                          href="/learn"
                          className="card card-hover"
                          style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 14px', background: 'var(--bg-elevated)' }}
                        >
                          <div>
                            <span style={{ textTransform: 'capitalize', color: 'var(--agen-primary-light)', fontWeight: 600, fontSize: '0.9rem' }}>{t.skill}</span>
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
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 20 }}>
              <span style={{ fontSize: '1.8rem' }}>🗓️</span>
              <div>
                <div style={{ fontWeight: 700 }}>Báo cáo tuần này</div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>AI tổng hợp 7 ngày qua</div>
              </div>
            </div>

            {coachLoading ? (
              <div style={{ color: 'var(--text-muted)', fontStyle: 'italic' }}>🧠 Đang tạo báo cáo AI...</div>
            ) : report ? (
              <>
                {/* Stats row */}
                <div style={{ display: 'flex', gap: 16, marginBottom: 20 }}>
                  {[
                    { label: 'Buổi học', value: report.sessions_count, color: 'var(--agen-primary-light)' },
                    { label: 'XP kiếm được', value: `+${report.xp_earned_this_week}`, color: 'var(--agen-accent)' },
                    { label: 'Kỹ năng tốt nhất', value: report.best_skill, color: 'var(--agen-success)' },
                  ].map(s => (
                    <div key={s.label} style={{ flex: 1, textAlign: 'center', padding: 12, background: 'var(--bg-elevated)', borderRadius: 8 }}>
                      <div style={{ fontSize: '1.3rem', fontWeight: 800, color: s.color }}>{s.value}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 4 }}>{s.label}</div>
                    </div>
                  ))}
                </div>

                {/* Highlight */}
                <div style={{ padding: 14, background: 'rgba(6,214,160,0.06)', borderRadius: 8, marginBottom: 14, borderLeft: '3px solid var(--agen-success)' }}>
                  🌟 <b>Điểm nổi bật:</b> {report.highlight}
                </div>

                {/* Areas to improve */}
                {report.areas_to_improve?.length > 0 && (
                  <div style={{ marginBottom: 14 }}>
                    <div style={{ fontWeight: 600, marginBottom: 8 }}>⚠️ Cần cải thiện tuần tới:</div>
                    <ul style={{ paddingLeft: 20, color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                      {report.areas_to_improve.map((a, i) => <li key={i}>{a}</li>)}
                    </ul>
                  </div>
                )}

                {/* Goal & encouragement */}
                <div style={{ padding: 14, background: 'rgba(108,99,255,0.06)', borderRadius: 8, borderLeft: '3px solid var(--agen-primary)' }}>
                  🎯 <b>Mục tiêu tuần tới:</b> {report.next_week_goal}
                </div>
                <div style={{ marginTop: 12, fontStyle: 'italic', color: 'var(--text-secondary)' }}>
                  💪 {report.encouragement}
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
            <span style={{ fontSize: '1.8rem' }}>🏆</span>
            <div>
              <h3 style={{ margin: 0 }}>Thành tựu & Danh hiệu</h3>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Cố gắng thu thập tất cả huy hiệu nhé!</div>
            </div>
          </div>
          
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 'var(--spacing-md)' }}>
            {achievements.map((ach) => (
              <div
                key={ach.id}
                className="card"
                style={{
                  textAlign: 'center',
                  padding: 'var(--spacing-md)',
                  opacity: ach.earned ? 1 : 0.5,
                  filter: ach.earned ? 'none' : 'grayscale(100%)',
                  background: ach.earned ? 'var(--bg-elevated)' : 'transparent',
                  border: `1px solid ${ach.earned ? 'var(--agen-accent)' : 'var(--border-subtle)'}`,
                  position: 'relative'
                }}
              >
                {ach.earned && (
                  <div style={{ position: 'absolute', top: 8, right: 8, color: '#4caf50', fontSize: '1rem' }}>✅</div>
                )}
                <div style={{ fontSize: '3rem', marginBottom: 12 }}>{ach.icon}</div>
                <div style={{ fontWeight: 700, marginBottom: 4, color: ach.earned ? 'var(--agen-primary-light)' : 'var(--text-primary)' }}>{ach.name}</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{ach.description}</div>
                <div style={{ marginTop: 12, fontSize: '0.7rem', fontWeight: 'bold', color: 'var(--agen-accent)', background: 'rgba(255, 152, 0, 0.1)', padding: '2px 8px', borderRadius: 12, display: 'inline-block' }}>
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
              
              <div className="card" style={{ marginBottom: 'var(--spacing-xl)', background: 'linear-gradient(135deg, rgba(108,99,255,0.08), rgba(255,107,107,0.08))', border: '1px solid rgba(108,99,255,0.3)' }}>
                <div style={{ textAlign: 'center', marginBottom: 24 }}>
                  <div style={{ fontSize: '3rem', marginBottom: 12 }}>🏆</div>
                  <h3>Top 10 AGEN Learners</h3>
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Bảng xếp hạng vinh danh những học viên chăm chỉ nhất</p>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {leaderboard?.entries?.map((entry, idx) => (
                    <div 
                      key={entry.learner_id} 
                      style={{ 
                        display: 'flex', alignItems: 'center', padding: '16px', borderRadius: 12, 
                        background: entry.is_current_user ? 'rgba(108,99,255,0.15)' : 'var(--bg-elevated)',
                        border: entry.is_current_user ? '1px solid var(--agen-primary)' : '1px solid var(--border-subtle)'
                      }}
                    >
                      <div style={{ width: 30, fontWeight: 800, color: idx < 3 ? 'var(--agen-accent)' : 'var(--text-muted)', fontSize: idx < 3 ? '1.2rem' : '1rem' }}>
                        #{idx + 1}
                      </div>
                      <div style={{ fontSize: '1.6rem', marginRight: 16 }}>{entry.avatar}</div>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontWeight: 700, display: 'flex', alignItems: 'center', gap: 8 }}>
                          {entry.display_name} 
                          {entry.is_current_user && <span style={{ fontSize: '0.7rem', background: 'var(--agen-primary)', color: 'white', padding: '2px 8px', borderRadius: 99 }}>Bạn</span>}
                        </div>
                        <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Level: {entry.level}</div>
                      </div>
                      <div style={{ fontWeight: 900, color: 'var(--agen-accent)' }}>
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
                    <div style={{ fontSize: '2rem', marginBottom: 8 }}>🏅</div>
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

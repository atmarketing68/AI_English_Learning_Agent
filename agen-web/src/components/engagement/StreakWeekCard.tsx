'use client';

import { useState } from 'react';
import confetti from 'canvas-confetti';
import { CircleCheck, Flame, Gem, Gift, Snowflake, Wrench } from 'lucide-react';
import { claimWeeklyReward, repairStreak, setWeeklyGoal, type Engagement } from '@/lib/engagementService';
import { playSound } from '@/lib/soundEffects';
import { track } from '@/lib/analytics';

/** Streak, streak freezes and the Mon–Sun weekly goal. */
export default function StreakWeekCard({
  state, onChange,
}: {
  state: Engagement;
  onChange: (next: Engagement) => void;
}) {
  const { streak, weekly } = state;
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const changeGoal = async (days: number) => {
    if (days === weekly.goal_days || busy) return;
    setBusy(true);
    setError('');
    try {
      onChange(await setWeeklyGoal(days));
      track('weekly_goal_set', { days });
    } catch {
      setError('Không đổi được mục tiêu, thử lại nhé.');
    } finally {
      setBusy(false);
    }
  };

  const claim = async () => {
    setBusy(true);
    setError('');
    try {
      const res = await claimWeeklyReward();
      playSound('success');
      confetti({ particleCount: 90, spread: 80, origin: { y: 0.6 }, colors: ['#0071E3', '#64D2FF', '#D97A00'] });
      track('weekly_goal_claimed', { goal: weekly.goal_days, freeze: res.freeze_awarded });
      onChange(res.state);
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(detail || 'Không nhận được thưởng, thử lại nhé.');
    } finally {
      setBusy(false);
    }
  };

  // G14 · sửa chuỗi trong 24 giờ
  const repair = async () => {
    setBusy(true);
    setError('');
    try {
      const next = await repairStreak();
      playSound('success');
      track('streak_repaired', { restored: next.streak.current });
      onChange(next);
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(detail || 'Chưa sửa được chuỗi, thử lại nhé.');
    } finally {
      setBusy(false);
    }
  };

  const status = streak.freeze_used_today
    ? 'Bảo vệ chuỗi đã giữ chuỗi cho những ngày bạn vắng.'
    : streak.studied_today
    ? 'Đã học hôm nay — chuỗi được giữ.'
    : streak.protected
    ? `Bạn vắng ${streak.missed_days} ngày, bảo vệ chuỗi sẽ giữ chuỗi khi bạn học hôm nay.`
    : streak.current > 0
    ? 'Học 1 bài hôm nay để giữ chuỗi.'
    : 'Học hôm nay để bắt đầu chuỗi mới.';

  return (
    <div className="card streak-card">
      <div className="streak-top">
        <div className="streak-flame" data-active={streak.studied_today}>
          <Flame size={30} strokeWidth={1.8} />
        </div>
        <div style={{ minWidth: 0 }}>
          <div className="streak-number">{streak.current} <span>ngày liên tiếp</span></div>
          <div className="streak-status">{status}</div>
        </div>
      </div>

      {streak.repair && (
        <div className="streak-repair">
          <Wrench size={18} />
          <div style={{ flex: 1, minWidth: 0 }}>
            <b>Chuỗi {streak.repair.lost} ngày vừa bị đứt</b>
            <div>Sửa ngay hôm nay để giữ lại {streak.repair.restored} ngày liên tiếp.</div>
          </div>
          <button type="button" className="btn btn-primary btn-sm" onClick={repair} disabled={busy}>
            Sửa · {streak.repair.cost} <Gem size={13} />
          </button>
        </div>
      )}

      <div className="freeze-row" title="Mỗi bảo vệ chuỗi giữ chuỗi khi bạn lỡ 1 ngày. Nhận thêm khi đạt mục tiêu tuần.">
        <span className="freeze-icons" aria-label={`${streak.freezes}/${streak.max_freezes} bảo vệ chuỗi`}>
          {Array.from({ length: streak.max_freezes }, (_, i) => (
            <span key={i} className="freeze" data-on={i < streak.freezes}><Snowflake size={15} /></span>
          ))}
        </span>
        <span>Bảo vệ chuỗi · {streak.freezes}/{streak.max_freezes}</span>
      </div>

      <div className="week-head">
        <span className="eyebrow">Mục tiêu tuần</span>
        <div className="segmented" role="group" aria-label="Số ngày học mỗi tuần">
          {weekly.options.map(d => (
            <button key={d} type="button" aria-pressed={d === weekly.goal_days} onClick={() => changeGoal(d)} disabled={busy}>
              {d} ngày
            </button>
          ))}
        </div>
      </div>

      <div className="week-days">
        {weekly.days.map(d => (
          <div key={d.date} className="week-day" data-done={d.done} data-today={d.is_today} data-future={d.is_future}>
            <span className="week-dot">{d.done ? <Flame size={14} /> : null}</span>
            <span className="week-label">{d.label}</span>
          </div>
        ))}
      </div>

      <div className="week-foot">
        <span><strong>{Math.min(weekly.days_done, 7)}</strong>/{weekly.goal_days} ngày tuần này</span>
        {weekly.claimed ? (
          <span className="quest-claimed"><CircleCheck size={16} /> Đã đạt mục tiêu tuần</span>
        ) : weekly.completed ? (
          <button type="button" className="btn btn-primary btn-sm" onClick={claim} disabled={busy}>
            <Gift size={15} /> Nhận +{weekly.reward_xp} XP{streak.freezes < streak.max_freezes ? ' & 1 bảo vệ' : ''}
          </button>
        ) : (
          <span className="week-reward"><Gift size={14} /> +{weekly.reward_xp} XP{streak.freezes < streak.max_freezes ? ' & 1 bảo vệ chuỗi' : ''}</span>
        )}
      </div>
      {error && <div className="alert-error" style={{ marginTop: 10 }}>{error}</div>}
    </div>
  );
}

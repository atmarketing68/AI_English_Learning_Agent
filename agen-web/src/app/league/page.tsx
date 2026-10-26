'use client';

/** G3 · Giải đấu tuần — Mon–Sun XP leaderboard with a reward for last week's top 10. */
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import confetti from 'canvas-confetti';
import { ArrowLeft, CircleAlert, Crown, Gift, LoaderCircle, Medal, Star, Trophy } from 'lucide-react';
import { useAuthHydrated, useAuthStore } from '@/store/authStore';
import { claimLeagueReward, getLeague, type League } from '@/lib/engagementService';
import { getMyProfile } from '@/lib/services';
import { PageSkeleton } from '@/components/Skeleton';
import { playSound } from '@/lib/soundEffects';
import { track } from '@/lib/analytics';

const TIER_COLOR: Record<string, string> = { 'Vàng': '#D4A017', 'Bạc': '#8E8E93', 'Đồng': '#B5651D' };

function daysLeft(endsOn: string): number {
  const end = new Date(`${endsOn}T23:59:59`);
  return Math.max(0, Math.ceil((end.getTime() - Date.now()) / 86_400_000));
}

export default function LeaguePage() {
  const router = useRouter();
  const hydrated = useAuthHydrated();
  const { isAuthenticated, setLearner } = useAuthStore();
  const [league, setLeague] = useState<League | null>(null);
  const [error, setError] = useState('');
  const [claiming, setClaiming] = useState(false);
  const [claimed, setClaimed] = useState<number | null>(null);

  useEffect(() => {
    if (!hydrated) return;
    if (!isAuthenticated) { router.push('/login'); return; }
    getLeague().then(l => { setLeague(l); track('league_opened', { rank: l.me.rank }); }).catch(() => setError('Không tải được bảng xếp hạng.'));
  }, [hydrated, isAuthenticated, router]);

  const claim = async () => {
    setClaiming(true);
    try {
      const res = await claimLeagueReward();
      setClaimed(res.xp_awarded);
      setLeague(l => (l ? { ...l, last_week: { ...l.last_week, claimed: true, claimable: false } } : l));
      setLearner(await getMyProfile());
      track('league_reward_claimed', { xp: res.xp_awarded });
      playSound('success');
      confetti({ particleCount: 80, spread: 70, origin: { y: 0.4 }, colors: ['#D4A017', '#0071E3', '#1F9D55'] });
    } catch (err: unknown) {
      setError((err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Không nhận được thưởng.');
    } finally {
      setClaiming(false);
    }
  };

  if (!league) {
    return (
      <main className="league-page">
        {error ? <div className="alert-error"><CircleAlert size={16} /> {error}</div> : <PageSkeleton cards={2} />}
      </main>
    );
  }

  const left = daysLeft(league.ends_on);
  const lw = league.last_week;

  return (
    <main className="league-page">
      <div className="league-column">
        <Link href="/dashboard" style={{ display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: '0.92rem', marginBottom: 12 }}><ArrowLeft size={16} /> Trang chủ</Link>
        <div className="league-hero card">
          <span className="icon-tile league-hero-icon"><Trophy size={28} strokeWidth={1.6} /></span>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div className="eyebrow">Giải đấu tuần · {league.week}</div>
            <h1 style={{ fontSize: 'clamp(1.6rem, 4vw, 2.1rem)', margin: '4px 0 6px' }}>
              {league.me.rank ? `Bạn đang hạng ${league.me.rank}` : 'Bạn chưa có XP tuần này'}
            </h1>
            <div style={{ color: 'var(--text-secondary)', fontSize: '0.92rem' }}>
              {league.me.xp} XP tuần này · {league.me.participants} người tham gia · còn {left} ngày
            </div>
          </div>
        </div>

        {error && <div className="alert-error" style={{ marginBottom: 16 }}><CircleAlert size={16} /> {error}</div>}

        {(lw.claimable || claimed !== null || (lw.rank && lw.rank <= 10)) && (
          <div className="card league-reward" data-claimed={lw.claimed || claimed !== null}>
            <Gift size={22} />
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 600 }}>
                Tuần trước bạn hạng {lw.rank}{lw.tier ? ` · hạng ${lw.tier}` : ''}
              </div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                {claimed !== null ? `Đã nhận +${claimed} XP. Tuần này cố gắng giữ hạng nhé!` : lw.claimed ? 'Đã nhận thưởng tuần trước.' : `Phần thưởng: +${lw.reward_xp} XP`}
              </div>
            </div>
            {lw.claimable && claimed === null && (
              <button className="btn btn-primary btn-sm" onClick={claim} disabled={claiming}>
                {claiming ? <LoaderCircle className="animate-spin" size={14} /> : <Star size={14} fill="currentColor" />} Nhận thưởng
              </button>
            )}
          </div>
        )}

        <div className="league-rewards">
          {league.rewards.map((r, i) => (
            <span key={r.up_to_rank} className="league-reward-chip" style={{ color: Object.values(TIER_COLOR)[i] }}>
              <Medal size={14} /> Top {r.up_to_rank}: +{r.xp} XP
            </span>
          ))}
        </div>

        <ol className="league-board card">
          {league.entries.length === 0 && <li className="league-empty">Chưa ai có XP tuần này. Học một bài để dẫn đầu!</li>}
          {league.entries.map(e => (
            <li key={e.learner_id} className="league-row" data-me={e.is_me} data-tier={e.tier ?? ''}>
              <span className="league-rank" style={{ color: e.tier ? TIER_COLOR[e.tier] : undefined }}>
                {e.rank === 1 ? <Crown size={18} /> : e.rank}
              </span>
              <span className="avatar">{e.display_name.slice(0, 1).toUpperCase()}</span>
              <span className="league-name">{e.display_name}{e.is_me && <small> (bạn)</small>}</span>
              <span className="level-badge">{e.level}</span>
              <span className="league-xp"><Star size={13} fill="currentColor" /> {e.xp}</span>
            </li>
          ))}
          {league.me.rank && league.me.rank > league.entries.length && (
            <li className="league-row" data-me="true">
              <span className="league-rank">{league.me.rank}</span>
              <span className="avatar">?</span>
              <span className="league-name">Bạn</span>
              <span />
              <span className="league-xp"><Star size={13} fill="currentColor" /> {league.me.xp}</span>
            </li>
          )}
        </ol>
        <p className="league-note">Bảng xếp hạng tính XP kiếm được từ thứ Hai đến Chủ nhật. Top 10 nhận thưởng vào tuần sau.</p>
      </div>
    </main>
  );
}

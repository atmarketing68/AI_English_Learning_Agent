'use client';

/** G3/G4 · Giải đấu tuần — a group of 30 in your tier; top 7 go up, bottom 5 go down. */
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import confetti from 'canvas-confetti';
import { ArrowDown, ArrowLeft, ArrowUp, CircleAlert, Crown, Gem, Gift, LoaderCircle, Medal, Minus, Star, Trophy } from 'lucide-react';
import { useAuthHydrated, useAuthStore } from '@/store/authStore';
import { claimLeagueReward, getLeague, type League, type LeagueMovement } from '@/lib/engagementService';
import { getMyProfile } from '@/lib/services';
import { PageSkeleton } from '@/components/Skeleton';
import Avatar from '@/components/ui/Avatar';
import Mascot from '@/components/ui/Mascot';
import { playSound } from '@/lib/soundEffects';
import { track } from '@/lib/analytics';
import { apiErrorMessage } from '@/lib/apiError';

const TIER_COLORS = ['#B5651D', '#8E8E93', '#D4A017', '#38BDF8'];   // Đồng · Bạc · Vàng · Kim cương
const MOVE_LABEL: Record<LeagueMovement, string> = {
  new: 'Tuần đầu tiên', promoted: 'Thăng hạng', relegated: 'Xuống hạng', stay: 'Giữ hạng', inactive: 'Nghỉ tuần trước',
};

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
  const [claimed, setClaimed] = useState<{ xp: number; gems: number } | null>(null);

  useEffect(() => {
    if (!hydrated) return;
    if (!isAuthenticated) { router.push('/login'); return; }
    getLeague().then(l => { setLeague(l); track('league_opened', { rank: l.me.rank, tier: l.tier }); }).catch(() => setError('Không tải được bảng xếp hạng.'));
  }, [hydrated, isAuthenticated, router]);

  const claim = async () => {
    setClaiming(true);
    try {
      const res = await claimLeagueReward();
      setClaimed({ xp: res.xp_awarded, gems: res.gems_awarded });
      setLeague(l => (l ? { ...l, last_week: { ...l.last_week, claimed: true, claimable: false } } : l));
      setLearner(await getMyProfile());
      track('league_reward_claimed', { xp: res.xp_awarded, gems: res.gems_awarded });
      playSound('success');
      confetti({ particleCount: 80, spread: 70, origin: { y: 0.4 }, colors: ['#D4A017', '#0071E3', '#1F9D55'] });
    } catch (err: unknown) {
      setError(apiErrorMessage(err, 'Không nhận được thưởng.'));
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
  const tierColor = TIER_COLORS[league.tier] || TIER_COLORS[0];
  const myZone = league.entries.find(e => e.is_me)?.zone;
  const size = league.entries.length;
  const relegateFrom = size >= 10 ? size - league.relegate_bottom : Infinity;

  return (
    <main className="league-page">
      <div className="league-column">
        <Link href="/dashboard" style={{ display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: '0.92rem', marginBottom: 12 }}><ArrowLeft size={16} /> Trang chủ</Link>
        <div className="league-hero card">
          <span className="icon-tile league-hero-icon" style={{ background: `color-mix(in srgb, ${tierColor} 16%, transparent)`, color: tierColor }}><Trophy size={28} strokeWidth={1.6} /></span>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div className="eyebrow">Giải {league.tier_name} · nhóm {league.group_no} · {league.week}</div>
            <h1 style={{ fontSize: 'clamp(1.6rem, 4vw, 2.1rem)', margin: '4px 0 6px' }}>
              {league.me.rank ? `Bạn đang hạng ${league.me.rank}` : 'Bạn chưa có XP tuần này'}
            </h1>
            <div style={{ color: 'var(--text-secondary)', fontSize: '0.92rem' }}>
              {league.me.xp} XP tuần này · {league.me.participants}/{league.group_size} người trong nhóm · còn {left} ngày
            </div>
          </div>
        </div>

        <Mascot size={64} mood={myZone === 'promote' ? 'cheer' : myZone === 'relegate' ? 'think' : 'happy'}
          say={myZone === 'promote' ? `Giữ top ${league.promote_top} đến Chủ nhật là thăng hạng!` : myZone === 'relegate' ? 'Học thêm một bài để thoát vùng xuống hạng nhé!' : `Vào top ${league.promote_top} để lên giải ${league.tiers[Math.min(league.tier + 1, league.tiers.length - 1)]}!`}
          className="league-mascot" />

        <div className="league-tiers" style={{ marginTop: 14 }} aria-label="Các hạng giải">
          {league.tiers.map((name, i) => (
            <div key={name} className="league-tier" data-active={i === league.tier} style={{ '--tier-color': TIER_COLORS[i] } as React.CSSProperties}>
              <span className="league-tier-gem" />
              {name}
            </div>
          ))}
        </div>

        {error && <div className="alert-error" style={{ marginBottom: 16 }}><CircleAlert size={16} /> {error}</div>}

        {lw.movement !== 'new' && (
          <div className="card league-reward" data-claimed={lw.claimed || claimed !== null}>
            <Gift size={22} />
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 600, display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                Tuần trước{lw.rank ? ` hạng ${lw.rank}` : ''}{lw.tier_name ? ` · giải ${lw.tier_name}` : ''}
                <span className="league-move" data-move={lw.movement}>
                  {lw.movement === 'promoted' ? <ArrowUp size={14} /> : lw.movement === 'relegated' || lw.movement === 'inactive' ? <ArrowDown size={14} /> : <Minus size={14} />}
                  {MOVE_LABEL[lw.movement]}
                </span>
              </div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                {claimed ? `Đã nhận +${claimed.xp} XP và +${claimed.gems} đá quý. Tuần này cố gắng giữ hạng nhé!`
                  : lw.claimed ? 'Đã nhận thưởng tuần trước.'
                  : lw.reward_xp > 0 ? `Phần thưởng: +${lw.reward_xp} XP · +${lw.reward_gems} đá quý`
                  : 'Vào top 10 tuần này để có thưởng.'}
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
            <span key={r.up_to_rank} className="league-reward-chip" style={{ color: TIER_COLORS[2 - Math.min(i, 2)] }}>
              <Medal size={14} /> Top {r.up_to_rank}: +{r.xp} XP <Gem size={12} />
            </span>
          ))}
        </div>

        <ol className="league-board card">
          {league.entries.length === 0 && <li className="league-empty">Chưa ai có XP tuần này. Học một bài để dẫn đầu!</li>}
          {league.entries.map((e, i) => (
            <li key={e.learner_id} style={{ display: 'contents' }}>
              {i === 0 && size > 1 && <div className="league-zone-sep" data-zone="promote"><ArrowUp size={12} /> Vùng thăng hạng</div>}
              {i === league.promote_top && <div className="league-zone-sep" data-zone="stay">Giữ hạng</div>}
              {i === relegateFrom && <div className="league-zone-sep" data-zone="relegate"><ArrowDown size={12} /> Vùng xuống hạng</div>}
              <div className="league-row" data-me={e.is_me} data-zone={e.zone}>
                <span className="league-rank">{e.rank === 1 ? <Crown size={18} color="#D4A017" /> : e.rank}</span>
                <Avatar avatar={e.avatar} name={e.display_name} size={36} />
                <span className="league-name">{e.display_name}{e.is_me && <small> (bạn)</small>}</span>
                <span className="level-badge">{e.level}</span>
                <span className="league-xp"><Star size={13} fill="currentColor" /> {e.xp}</span>
              </div>
            </li>
          ))}
        </ol>
        <p className="league-note">
          Mỗi tuần bạn thi đua với tối đa {league.group_size} bạn cùng giải. Top {league.promote_top} thăng hạng, {league.relegate_bottom} người cuối (nhóm từ 10 người) xuống hạng. Top 10 nhận XP và đá quý vào tuần sau.
        </p>
      </div>
    </main>
  );
}

'use client';

/** G3 · Dashboard card: my rank in this week's league. */
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { ChevronRight, Trophy } from 'lucide-react';
import { getLeague, type League } from '@/lib/engagementService';

export default function LeagueCard() {
  const [league, setLeague] = useState<League | null>(null);
  useEffect(() => { getLeague().then(setLeague).catch(() => null); }, []);
  if (!league) return null;
  const { me, last_week } = league;
  const tierColor = ['#B5651D', '#8E8E93', '#D4A017', '#38BDF8'][league.tier] || '#D4A017';
  return (
    <Link href="/league" className="card card-hover" style={{ display: 'flex', alignItems: 'center', gap: 16, padding: 'var(--spacing-lg)', borderRadius: 'var(--radius-xl)', opacity: 1 }}>
      <span className="icon-tile" style={{ flexShrink: 0, width: 48, height: 48, borderRadius: 16, background: `color-mix(in srgb, ${tierColor} 14%, transparent)`, color: tierColor }}>
        <Trophy size={24} strokeWidth={1.8} />
      </span>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div className="eyebrow" style={{ marginBottom: 4 }}>Giải {league.tier_name} · nhóm {league.group_no}</div>
        <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
          {me.rank ? `Hạng ${me.rank} · ${me.xp} XP` : 'Học một bài để vào bảng xếp hạng'}
        </div>
        <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
          {last_week.claimable ? `Tuần trước bạn hạng ${last_week.rank} — có thưởng chờ nhận!` : `${me.participants} bạn trong nhóm · top ${league.promote_top} thăng hạng`}
        </div>
      </div>
      <ChevronRight size={18} color="var(--text-muted)" />
    </Link>
  );
}

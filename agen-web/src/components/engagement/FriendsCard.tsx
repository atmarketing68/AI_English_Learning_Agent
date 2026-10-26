'use client';

/** G6 · Dashboard card: duo quest status with friends. */
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { ChevronRight, Users } from 'lucide-react';
import { getFriends, type Friends } from '@/lib/friendsService';

export default function FriendsCard() {
  const [data, setData] = useState<Friends | null>(null);
  useEffect(() => { getFriends().then(setData).catch(() => null); }, []);
  if (!data) return null;
  const claimable = data.friends.filter(f => f.quest.claimable).length;
  const best = [...data.friends].sort((a, b) => (b.quest.my_xp + b.quest.friend_xp) - (a.quest.my_xp + a.quest.friend_xp))[0];
  return (
    <Link href="/friends" className="card card-hover" style={{ display: 'flex', alignItems: 'center', gap: 16, padding: 'var(--spacing-lg)', borderRadius: 'var(--radius-xl)', opacity: 1 }}>
      <span className="icon-tile" style={{ flexShrink: 0, width: 48, height: 48, borderRadius: 16, background: 'color-mix(in srgb, var(--skill-listening) 14%, transparent)', color: 'var(--skill-listening)' }}>
        <Users size={24} strokeWidth={1.8} />
      </span>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div className="eyebrow" style={{ marginBottom: 4 }}>Thử thách bạn bè</div>
        <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
          {claimable ? `${claimable} thử thách đã xong — nhận thưởng!` : best ? `Cùng ${best.display_name}: ${best.quest.my_xp + best.quest.friend_xp}/${data.goal} XP tuần này` : `Kết bạn để cùng kiếm ${data.goal} XP mỗi tuần`}
        </div>
        <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
          {data.friends.length ? `${data.friends.length} bạn học · +${data.reward_xp} XP và +${data.reward_gems} đá quý mỗi thử thách` : 'Gửi mã của bạn cho bạn bè'}
        </div>
      </div>
      <ChevronRight size={18} color="var(--text-muted)" />
    </Link>
  );
}

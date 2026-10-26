'use client';

/** G6 · Bạn học — add friends by code and clear a weekly duo quest together. */
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import confetti from 'canvas-confetti';
import { ArrowLeft, Check, CircleAlert, Copy, Flame, Gem, Gift, LoaderCircle, Star, UserPlus, Users, X } from 'lucide-react';
import { useAuthHydrated, useAuthStore } from '@/store/authStore';
import { addFriend, claimDuoQuest, getFriends, removeFriend, type Friend, type Friends } from '@/lib/friendsService';
import { getMyProfile } from '@/lib/services';
import { PageSkeleton } from '@/components/Skeleton';
import Avatar from '@/components/ui/Avatar';
import Mascot from '@/components/ui/Mascot';
import { playSound } from '@/lib/soundEffects';
import { track } from '@/lib/analytics';

function DuoBar({ f, goal }: { f: Friend; goal: number }) {
  const mine = Math.min(100, (f.quest.my_xp / goal) * 100);
  const theirs = Math.min(100 - mine, (f.quest.friend_xp / goal) * 100);
  return (
    <div className="duo-bar" aria-label={`Tiến độ ${f.quest.my_xp + f.quest.friend_xp}/${goal} XP`}>
      <span style={{ width: `${mine}%` }} />
      <span style={{ width: `${theirs}%` }} data-friend />
    </div>
  );
}

export default function FriendsPage() {
  const router = useRouter();
  const hydrated = useAuthHydrated();
  const { isAuthenticated, setLearner } = useAuthStore();
  const [data, setData] = useState<Friends | null>(null);
  const [code, setCode] = useState('');
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!hydrated) return;
    if (!isAuthenticated) { router.push('/login'); return; }
    getFriends().then(setData).catch(() => setError('Không tải được danh sách bạn học.'));
  }, [hydrated, isAuthenticated, router]);

  const onAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!code.trim()) return;
    setBusy('add'); setError('');
    try {
      setData(await addFriend(code));
      setCode('');
      track('friend_added');
      playSound('pop');
    } catch (err: unknown) {
      setError((err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Không thêm được bạn.');
    } finally { setBusy(null); }
  };

  const onClaim = async (f: Friend) => {
    setBusy(f.learner_id); setError('');
    try {
      const res = await claimDuoQuest(f.learner_id);
      setData(await getFriends());
      setLearner(await getMyProfile());
      track('duo_quest_claimed', { xp: res.xp, gems: res.gems });
      playSound('success');
      confetti({ particleCount: 90, spread: 70, origin: { y: 0.5 }, colors: ['#0EA5E9', '#22C55E', '#F59E0B'] });
    } catch (err: unknown) {
      setError((err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Không nhận được thưởng.');
    } finally { setBusy(null); }
  };

  const onRemove = async (f: Friend) => {
    if (!confirm(`Bỏ kết bạn với ${f.display_name}?`)) return;
    setBusy(f.learner_id);
    try { setData(await removeFriend(f.learner_id)); } finally { setBusy(null); }
  };

  if (!data) return <main className="friends-page">{error ? <div className="alert-error"><CircleAlert size={16} /> {error}</div> : <PageSkeleton cards={2} />}</main>;

  return (
    <main className="friends-page">
      <div className="friends-column">
        <Link href="/dashboard" style={{ display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: '0.92rem', marginBottom: 12 }}><ArrowLeft size={16} /> Trang chủ</Link>
        <section className="card friends-hero">
          <span className="icon-tile" style={{ width: 56, height: 56, borderRadius: 18, background: 'color-mix(in srgb, var(--skill-listening) 14%, transparent)', color: 'var(--skill-listening)' }}><Users size={28} strokeWidth={1.7} /></span>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div className="eyebrow">Thử thách bạn bè</div>
            <h1 style={{ fontSize: 'clamp(1.5rem, 4vw, 2rem)', margin: '2px 0 4px' }}>Cùng bạn kiếm {data.goal} XP mỗi tuần</h1>
            <p style={{ margin: 0, fontSize: '0.9rem' }}>Mỗi người góp ít nhất {data.min_each} XP. Xong là cả hai cùng nhận +{data.reward_xp} XP và +{data.reward_gems} đá quý.</p>
          </div>
        </section>

        <Mascot size={64} mood={data.friends.some(f => f.quest.claimable) ? 'cheer' : 'happy'}
          say={data.friends.some(f => f.quest.claimable) ? 'Xong thử thách rồi, nhận thưởng thôi!' : data.friends.length ? 'Rủ bạn học mỗi ngày để xong thử thách sớm nhé!' : 'Gửi mã của bạn cho bạn bè để cùng học nào!'} className="league-mascot" />

        <section className="card" style={{ marginTop: 14, display: 'grid', gap: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
            <div>
              <div style={{ fontWeight: 600 }}>Mã của bạn</div>
              <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>Bạn bè nhập mã này để kết bạn (cũng là mã liên kết phụ huynh).</div>
            </div>
            <button type="button" className="code-chip" onClick={() => { if (data.my_code) { navigator.clipboard?.writeText(data.my_code); setCopied(true); setTimeout(() => setCopied(false), 1500); } }}>
              {data.my_code || '—'} {copied ? <Check size={15} /> : <Copy size={15} />}
            </button>
          </div>
          <form onSubmit={onAdd} style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            <input className="form-input" placeholder="Nhập mã của bạn bè (AGEN-XXXX)" value={code} onChange={e => setCode(e.target.value.toUpperCase())} style={{ flex: '1 1 200px', textTransform: 'uppercase', letterSpacing: 1 }} maxLength={20} aria-label="Mã bạn bè" />
            <button type="submit" className="btn btn-primary" disabled={busy === 'add' || !code.trim()}>
              {busy === 'add' ? <LoaderCircle className="animate-spin" size={16} /> : <UserPlus size={16} />} Kết bạn
            </button>
          </form>
          {error && <div className="alert-error"><CircleAlert size={16} /> {error}</div>}
        </section>

        <h3 style={{ margin: '24px 0 10px' }}>Bạn học ({data.friends.length}/{data.max_friends})</h3>
        {data.friends.length === 0 && <div className="card" style={{ textAlign: 'center', color: 'var(--text-muted)', padding: 28 }}>Chưa có bạn học nào. Gửi mã của bạn cho một người bạn để bắt đầu thử thách tuần.</div>}
        <div style={{ display: 'grid', gap: 12 }}>
          {data.friends.map(f => (
            <div key={f.learner_id} className="card friend-card" data-done={f.quest.done}>
              <div className="friend-head">
                <Avatar avatar={f.avatar} name={f.display_name} size={44} />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontWeight: 600, display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                    {f.display_name} <span className="level-badge">{f.level}</span>
                    {f.studied_today && <span className="skill-badge" style={{ background: 'color-mix(in srgb, var(--agen-success) 12%, transparent)', color: 'var(--agen-success)' }}>Đã học hôm nay</span>}
                  </div>
                  <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)', display: 'inline-flex', alignItems: 'center', gap: 4 }}><Flame size={13} color="var(--agen-secondary)" /> {f.streak} ngày liên tiếp</div>
                </div>
                <button type="button" className="icon-btn" aria-label="Bỏ kết bạn" onClick={() => onRemove(f)} disabled={busy === f.learner_id}><X size={16} /></button>
              </div>
              <div className="friend-quest">
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: 6 }}>
                  <span>Tuần này: <strong>{f.quest.my_xp + f.quest.friend_xp}</strong>/{data.goal} XP</span>
                  <span style={{ color: 'var(--text-muted)' }}>Bạn {f.quest.my_xp} · {f.display_name} {f.quest.friend_xp}</span>
                </div>
                <DuoBar f={f} goal={data.goal} />
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 10, marginTop: 10, flexWrap: 'wrap' }}>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    {f.quest.claimed ? 'Đã nhận thưởng tuần này.' : f.quest.done ? 'Xong rồi! Nhận thưởng nào.' : f.quest.my_xp < data.min_each ? `Bạn cần thêm ${data.min_each - f.quest.my_xp} XP cho phần của mình.` : f.quest.friend_xp < data.min_each ? `${f.display_name} cần thêm ${data.min_each - f.quest.friend_xp} XP.` : `Còn ${Math.max(0, data.goal - f.quest.my_xp - f.quest.friend_xp)} XP nữa.`}
                  </span>
                  {f.quest.claimable ? (
                    <button type="button" className="btn btn-primary btn-sm" onClick={() => onClaim(f)} disabled={busy === f.learner_id}>
                      {busy === f.learner_id ? <LoaderCircle className="animate-spin" size={14} /> : <Gift size={14} />} Nhận +{data.reward_xp} XP · +{data.reward_gems} <Gem size={12} />
                    </button>
                  ) : f.quest.claimed ? (
                    <span className="xp-badge"><Star size={13} fill="currentColor" /> +{data.reward_xp} XP đã nhận</span>
                  ) : null}
                </div>
              </div>
            </div>
          ))}
        </div>
        <p className="league-note">Thử thách làm mới vào thứ Hai hằng tuần. XP tính từ mọi hoạt động học của hai bạn.</p>
      </div>
    </main>
  );
}

'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  BookOpen, Briefcase, Check, Copy, Download, Flame, Gem, GraduationCap, LogOut, Pencil, ShoppingBag, Smile, Sparkles, Star, Trash2, Trophy, Users, X,
} from 'lucide-react';
import Avatar from '@/components/ui/Avatar';
import { skinForLearner, useSkinStore } from '@/store/skinStore';
import { track } from '@/lib/analytics';
import api from '@/lib/api';
import { useAuthHydrated, useAuthStore } from '@/store/authStore';
import { getAchievements, getMe, getMyProfile, updateMyProfile } from '@/lib/services';
import { getSubscription, type SubscriptionInfo } from '@/lib/billingService';
import { getEngagement, type Engagement } from '@/lib/engagementService';
import { getReviewSummary, type ReviewSummary } from '@/lib/reviewService';
import { PageSkeleton } from '@/components/Skeleton';
import ReminderCard from '@/components/engagement/ReminderCard';
import InstallAppCard from '@/components/engagement/InstallAppCard';
import CertificatesCard from '@/components/profile/CertificatesCard';
import type { Achievement, User } from '@/types';

const GOALS = [
  { id: 'giao_tiep', label: 'Giao tiếp hằng ngày' },
  { id: 'hoc_thuat', label: 'Học thuật / Trường lớp' },
  { id: 'cong_viec', label: 'Công việc / Đi làm' },
  { id: 'luyen_thi', label: 'Luyện thi (IELTS, TOEIC)' },
];
const MINUTES = [5, 10, 15, 30];

export default function ProfilePage() {
  const router = useRouter();
  const hydrated = useAuthHydrated();
  const { isAuthenticated, learner, setLearner, logout } = useAuthStore();
  const [user, setUser] = useState<User | null>(null);
  const [plan, setPlan] = useState<SubscriptionInfo | null>(null);
  const [engagement, setEngagement] = useState<Engagement | null>(null);
  const [review, setReview] = useState<ReviewSummary | null>(null);
  const [achievements, setAchievements] = useState<Achievement[]>([]);
  const [editingName, setEditingName] = useState(false);
  const [name, setName] = useState('');
  const [copied, setCopied] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [password, setPassword] = useState('');
  const [deleteError, setDeleteError] = useState('');
  const setSkin = useSkinStore((s) => s.setSkin);

  useEffect(() => {
    if (!hydrated) return;
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }
    getMyProfile().then(setLearner).catch(() => logout());
    getMe().then(setUser).catch(() => undefined);
    getSubscription().then(setPlan).catch(() => undefined);
    getEngagement().then(setEngagement).catch(() => undefined);
    getReviewSummary().then(setReview).catch(() => undefined);
    getAchievements().then(setAchievements).catch(() => undefined);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hydrated, isAuthenticated]);

  if (!learner) return <PageSkeleton maxWidth={880} cards={3} />;

  const save = async (patch: Parameters<typeof updateMyProfile>[0]) => {
    setSaving(true);
    setError('');
    try {
      setLearner(await updateMyProfile(patch));
      return true;
    } catch {
      setError('Không lưu được, thử lại nhé.');
      return false;
    } finally {
      setSaving(false);
    }
  };

  const saveName = async () => {
    const trimmed = name.trim();
    if (!trimmed || trimmed === learner.display_name) { setEditingName(false); return; }
    if (await save({ display_name: trimmed })) setEditingName(false);
  };

  const exportData = async () => {
    try {
      const { data } = await api.get('/privacy/export');
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'ai-agent-english-du-lieu-cua-toi.json';
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      setError('Không tải được dữ liệu, thử lại nhé.');
    }
  };

  const deleteAccount = async () => {
    setDeleteError('');
    try {
      await api.delete('/privacy/account', { data: { password } });
      logout();
      router.push('/');
    } catch (err: unknown) {
      const status = (err as { response?: { status?: number } })?.response?.status;
      setDeleteError(status === 401 ? 'Mật khẩu không đúng.' : 'Không xoá được tài khoản, thử lại sau.');
    }
  };

  const currentSkin = skinForLearner(learner);
  const changeSkin = async (skin: 'vivid' | 'classic') => {
    if (skin === currentSkin) return;
    setSkin(skin);                       // instant, before the request returns
    if (await save({ ui_skin: skin })) track('ui_skin_changed', { skin });
  };

  const earned = achievements.filter(a => a.earned);
  const isPremium = plan?.is_premium;

  return (
    <main className="profile-page">
      <div className="container" style={{ padding: 0, maxWidth: 880 }}>
        {/* Header */}
        <section className="card profile-head">
          <Link href="/shop" aria-label="Đổi avatar ở Cửa hàng" style={{ flexShrink: 0, opacity: 1 }}>
            <Avatar avatar={learner.avatar} name={learner.display_name} size={72} className="profile-avatar" />
          </Link>
          <div style={{ flex: 1, minWidth: 0 }}>
            {editingName ? (
              <form className="profile-name-edit" onSubmit={(e) => { e.preventDefault(); saveName(); }}>
                <input className="form-input" value={name} onChange={(e) => setName(e.target.value)} maxLength={100} autoFocus aria-label="Tên hiển thị" />
                <button type="submit" className="icon-btn" aria-label="Lưu" disabled={saving}><Check size={18} /></button>
                <button type="button" className="icon-btn" aria-label="Huỷ" onClick={() => setEditingName(false)}><X size={18} /></button>
              </form>
            ) : (
              <h1 className="profile-name">
                {learner.display_name}
                <button type="button" className="icon-btn" aria-label="Đổi tên" onClick={() => { setName(learner.display_name); setEditingName(true); }}>
                  <Pencil size={15} />
                </button>
              </h1>
            )}
            <div className="profile-meta">
              {user?.email && <span>{user.email}</span>}
              <span className="level-badge">{learner.overall_level}</span>
              <span className={isPremium ? 'plan-chip is-premium' : 'plan-chip'}>{isPremium ? 'Premium' : 'Gói miễn phí'}</span>
              <Link href="/shop" className="gems-badge"><Gem size={13} /> {learner.gems ?? 0} · Cửa hàng</Link>
            </div>
          </div>
        </section>

        {/* Stats */}
        <section className="profile-stats">
          <div className="card"><Flame size={18} color="var(--agen-secondary)" /><strong>{engagement?.streak.current ?? learner.current_streak}</strong><span>ngày liên tiếp · dài nhất {engagement?.streak.longest ?? '–'}</span></div>
          <div className="card"><Star size={18} color="var(--agen-accent)" /><strong>{learner.total_xp}</strong><span>điểm XP · <Gem size={11} style={{ verticalAlign: -1 }} /> {learner.gems ?? 0} đá quý</span></div>
          <div className="card"><BookOpen size={18} color="var(--agen-primary)" /><strong>{learner.total_lessons_completed}</strong><span>bài đã học</span></div>
          <div className="card"><GraduationCap size={18} color="var(--skill-reading)" /><strong>{review?.mastered_count ?? 0}<small>/{review?.vocab_total ?? 0}</small></strong><span>từ đã thuộc</span></div>
        </section>

        {/* Achievements */}
        <section className="card profile-section">
          <div className="profile-section-head">
            <h2><Trophy size={18} color="var(--agen-accent)" /> Huy hiệu</h2>
            <span>{earned.length}/{achievements.length}</span>
          </div>
          <div className="badge-grid">
            {achievements.map(a => (
              <div key={a.id} className="badge" data-earned={a.earned} title={a.description}>
                <span className="badge-icon">{a.icon}</span>
                <span className="badge-name">{a.name}</span>
                <span className="badge-desc">{a.description}</span>
              </div>
            ))}
            {!achievements.length && <p className="profile-muted">Hoàn thành bài học đầu tiên để nhận huy hiệu.</p>}
          </div>
        </section>

        <CertificatesCard />

        {/* Learning settings */}
        <section className="card profile-section">
          <div className="profile-section-head"><h2>Cài đặt học tập</h2></div>
          <label className="profile-field">
            <span>Mục tiêu</span>
            <select className="form-input" value={learner.learning_goal || ''} disabled={saving}
              onChange={(e) => save({ learning_goal: e.target.value })}>
              <option value="" disabled>Chọn mục tiêu</option>
              {GOALS.map(g => <option key={g.id} value={g.id}>{g.label}</option>)}
            </select>
          </label>
          <div className="profile-field">
            <span>Giao diện</span>
            <div className="skin-switch" role="group" aria-label="Giao diện">
              <button type="button" className="skin-option" aria-pressed={currentSkin === 'vivid'} disabled={saving} onClick={() => changeSkin('vivid')}>
                <strong><Smile size={16} color="#6C5CE7" /> Vui nhộn</strong>
                <span className="skin-option-swatch"><i style={{ background: '#6C5CE7' }} /><i style={{ background: '#F59E0B' }} /><i style={{ background: '#22C55E' }} /><i style={{ background: '#EC4899' }} /></span>
                <span>Màu sắc tươi, mascot Bo, nút to — hợp với học sinh.</span>
              </button>
              <button type="button" className="skin-option" aria-pressed={currentSkin === 'classic'} disabled={saving} onClick={() => changeSkin('classic')}>
                <strong><Briefcase size={16} color="#0071E3" /> Chuyên nghiệp</strong>
                <span className="skin-option-swatch"><i style={{ background: '#0071E3' }} /><i style={{ background: '#1D1D1F' }} /><i style={{ background: '#86868B' }} /><i style={{ background: '#1F9D55' }} /></span>
                <span>Gọn gàng, hiện đại — cho người đi làm và phụ huynh.</span>
              </button>
            </div>
          </div>
          <div className="profile-field">
            <span>Thời gian mỗi ngày</span>
            <div className="segmented" role="group" aria-label="Phút học mỗi ngày">
              {MINUTES.map(m => (
                <button key={m} type="button" aria-pressed={learner.daily_study_minutes === m} disabled={saving}
                  onClick={() => save({ daily_study_minutes: m })}>{m} phút</button>
              ))}
            </div>
          </div>
        </section>

        <div className="profile-stack">
          <ReminderCard />
          <InstallAppCard />
        </div>

        {/* Parent link */}
        {learner.invite_code && (
          <section className="card profile-section profile-row">
            <span className="icon-tile"><Users size={20} strokeWidth={1.8} /></span>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontWeight: 600 }}>Mã liên kết phụ huynh</div>
              <div className="profile-muted">Đưa mã này cho bố mẹ để theo dõi tiến bộ của bạn.</div>
            </div>
            <button type="button" className="code-chip" onClick={() => {
              navigator.clipboard?.writeText(learner.invite_code!);
              setCopied(true);
              setTimeout(() => setCopied(false), 1500);
            }}>
              {learner.invite_code} {copied ? <Check size={15} /> : <Copy size={15} />}
            </button>
          </section>
        )}

        {/* Account */}
        <section className="card profile-section">
          <div className="profile-section-head"><h2>Tài khoản</h2></div>
          <div className="profile-actions">
            {!isPremium && (
              <Link href="/upgrade" className="btn btn-primary"><Sparkles size={16} /> Nâng cấp Premium</Link>
            )}
            <Link href="/shop" className="btn btn-ghost"><ShoppingBag size={16} /> Cửa hàng avatar</Link>
            <button type="button" className="btn btn-ghost" onClick={exportData}><Download size={16} /> Tải dữ liệu của tôi</button>
            <button type="button" className="btn btn-ghost" onClick={() => { logout(); router.push('/'); }}><LogOut size={16} /> Đăng xuất</button>
            <button type="button" className="btn btn-ghost profile-danger" onClick={() => setDeleteOpen(true)}><Trash2 size={16} /> Xoá tài khoản</button>
          </div>
          {deleteOpen && (
            <form className="profile-delete" onSubmit={(e) => { e.preventDefault(); deleteAccount(); }}>
              <p>Toàn bộ tiến độ, sổ từ vựng và lịch sử học sẽ bị xoá vĩnh viễn. Nhập mật khẩu để xác nhận.</p>
              <input className="form-input" type="password" value={password} onChange={(e) => setPassword(e.target.value)}
                placeholder="Mật khẩu" autoComplete="current-password" aria-label="Mật khẩu" />
              {deleteError && <div className="alert-error">{deleteError}</div>}
              <div style={{ display: 'flex', gap: 8 }}>
                <button type="submit" className="btn btn-primary profile-danger-solid" disabled={!password}>Xoá vĩnh viễn</button>
                <button type="button" className="btn btn-ghost" onClick={() => { setDeleteOpen(false); setPassword(''); }}>Huỷ</button>
              </div>
            </form>
          )}
        </section>

        {error && <div className="alert-error" style={{ marginTop: 12 }}>{error}</div>}
      </div>
    </main>
  );
}

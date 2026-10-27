'use client';

/** G4 · Cửa hàng — spend gems on avatars, colours and frames. */
import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import confetti from 'canvas-confetti';
import { ArrowLeft, Check, CircleAlert, Gem, Lock, LoaderCircle, Sparkles, Star, Trophy, Zap } from 'lucide-react';
import { useAuthHydrated, useAuthStore } from '@/store/authStore';
import { buyShopItem, equipShopItem, getShop, type Shop, type ShopItem, type ShopItemKind } from '@/lib/gamificationService';
import { getMyProfile } from '@/lib/services';
import { PageSkeleton } from '@/components/Skeleton';
import Avatar from '@/components/ui/Avatar';
import Mascot from '@/components/ui/Mascot';
import { playSound } from '@/lib/soundEffects';
import { track } from '@/lib/analytics';
import { apiErrorMessage } from '@/lib/apiError';

const TABS: { kind: ShopItemKind; label: string }[] = [
  { kind: 'avatar', label: 'Nhân vật' },
  { kind: 'color', label: 'Màu nền' },
  { kind: 'frame', label: 'Khung' },
];

const SWATCH: Record<string, string> = {
  sky: 'linear-gradient(135deg, #BAE6FD, #7DD3FC)', mint: 'linear-gradient(135deg, #BBF7D0, #6EE7B7)',
  peach: 'linear-gradient(135deg, #FED7AA, #FDBA74)', lilac: 'linear-gradient(135deg, #E9D5FF, #C4B5FD)',
  lemon: 'linear-gradient(135deg, #FEF08A, #FDE047)', galaxy: 'radial-gradient(circle at 30% 30%, #818CF8, #312E81 70%)',
};

function ItemPreview({ item, avatar }: { item: ShopItem; avatar: Shop['avatar'] }) {
  if (item.kind === 'avatar') return <Avatar avatar={{ emoji: item.value, color: avatar.color, frame: 'none' }} size={56} raw />;
  if (item.kind === 'color') return <span className="shop-swatch" style={{ background: SWATCH[item.value] }} />;
  return <Avatar avatar={{ emoji: avatar.emoji, color: avatar.color, frame: item.value }} size={52} raw />;
}

export default function ShopPage() {
  const router = useRouter();
  const hydrated = useAuthHydrated();
  const { isAuthenticated, learner, setLearner } = useAuthStore();
  const [shop, setShop] = useState<Shop | null>(null);
  const [tab, setTab] = useState<ShopItemKind>('avatar');
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState('');
  const [toast, setToast] = useState('');

  useEffect(() => {
    if (!hydrated) return;
    if (!isAuthenticated) { router.push('/login'); return; }
    getShop().then(s => { setShop(s); track('shop_opened', { gems: s.gems }); }).catch(() => setError('Không tải được cửa hàng.'));
    if (!learner) getMyProfile().then(setLearner).catch(() => undefined);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hydrated, isAuthenticated, router]);

  const items = useMemo(() => (shop?.items || []).filter(i => i.kind === tab), [shop, tab]);

  const act = async (item: ShopItem) => {
    if (!shop || busy) return;
    setError('');
    if (item.equipped) return;
    if (!item.owned && shop.gems < item.price) {
      setError(`Cần thêm ${item.price - shop.gems} đá quý nữa. Học bài, làm nhiệm vụ hoặc chơi Blitz để kiếm thêm nhé!`);
      playSound('error');
      return;
    }
    setBusy(item.id);
    try {
      const next = item.owned ? await equipShopItem(item.id) : await buyShopItem(item.id);
      setShop(next);
      if (item.owned) {
        track('shop_item_equipped', { item: item.id });
        playSound('pop');
        setToast(`Đã đổi sang ${item.name_vi}.`);
      } else {
        track('shop_item_bought', { item: item.id, price: item.price });
        playSound('success');
        confetti({ particleCount: 70, spread: 60, origin: { y: 0.5 }, colors: ['#0EA5E9', '#6C5CE7', '#F59E0B'] });
        setToast(`Tuyệt! ${item.name_vi} là của bạn.`);
      }
      setTimeout(() => setToast(''), 2500);
      if (learner) setLearner({ ...learner, gems: next.gems, avatar: next.avatar });
      getMyProfile().then(setLearner).catch(() => undefined);
    } catch (err: unknown) {
      setError(apiErrorMessage(err, 'Không thực hiện được, thử lại nhé.'));
    } finally {
      setBusy(null);
    }
  };

  if (!shop) {
    return <main className="shop-page">{error ? <div className="alert-error"><CircleAlert size={16} /> {error}</div> : <PageSkeleton cards={2} />}</main>;
  }

  return (
    <main className="shop-page">
      <div className="shop-column">
        <Link href="/dashboard" style={{ display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: '0.92rem', marginBottom: 12 }}><ArrowLeft size={16} /> Trang chủ</Link>

        <section className="card shop-hero">
          <div className="shop-preview">
            <Avatar avatar={shop.avatar} name={learner?.display_name} size={84} raw />
            <div style={{ minWidth: 0 }}>
              <div className="eyebrow">Cửa hàng</div>
              <h1 style={{ fontSize: 'clamp(1.5rem, 4vw, 2rem)', margin: '2px 0 4px' }}>{learner?.display_name || 'Bạn'}</h1>
              <div style={{ fontSize: '0.88rem', color: 'var(--text-secondary)' }}>Đổi đá quý lấy nhân vật, màu nền và khung avatar.</div>
            </div>
          </div>
          <span className="shop-balance"><Gem size={20} /> {shop.gems}</span>
        </section>

        <Mascot mood={shop.gems >= 30 ? 'cheer' : 'happy'} size={72} say={shop.gems >= 30 ? 'Bạn đủ đá quý để mua món mới rồi đó!' : 'Học bài hoặc chơi Blitz để kiếm đá quý nhé!'} className="shop-mascot" />

        <div className="shop-tabs" role="tablist" style={{ marginTop: 16 }}>
          {TABS.map(t => (
            <button key={t.kind} role="tab" aria-selected={tab === t.kind} onClick={() => setTab(t.kind)}>{t.label}</button>
          ))}
        </div>

        {error && <div className="alert-error" style={{ marginBottom: 12 }}><CircleAlert size={16} /> {error}</div>}
        {toast && <div className="alert-success" style={{ marginBottom: 12 }} role="status"><Check size={16} /> {toast}</div>}

        <div className="shop-grid">
          {items.map(item => {
            const locked = !item.owned && shop.gems < item.price;
            return (
              <button
                key={item.id} type="button" className="shop-item"
                data-equipped={item.equipped} data-locked={locked}
                disabled={busy !== null || item.equipped}
                onClick={() => act(item)}
                aria-label={`${item.name_vi}${item.equipped ? ' (đang dùng)' : item.owned ? ' (đã có)' : ` · ${item.price} đá quý`}`}
              >
                <ItemPreview item={item} avatar={shop.avatar} />
                <span className="shop-item-name">{item.name_vi}</span>
                {busy === item.id ? <LoaderCircle className="animate-spin" size={16} />
                  : item.equipped ? <span className="shop-item-owned"><Check size={14} /> Đang dùng</span>
                  : item.owned ? <span className="shop-item-owned">Đã có · nhấn để dùng</span>
                  : <span className="shop-item-price" data-free={item.price === 0}>{locked && <Lock size={12} />}<Gem size={13} /> {item.price}</span>}
              </button>
            );
          })}
        </div>

        <h3 style={{ marginTop: 28, marginBottom: 4 }}>Kiếm đá quý thế nào?</h3>
        <div className="shop-earn">
          <div><Star size={16} color="var(--agen-accent)" /> Xong 1 bài học: <strong>3–15</strong></div>
          <div><Sparkles size={16} color="var(--agen-primary)" /> Nhận thưởng nhiệm vụ: <strong>+3</strong></div>
          <div><Zap size={16} color="var(--skill-listening)" /> Blitz 60 giây: <strong>tới 10</strong></div>
          <div><Trophy size={16} color="#D4A017" /> Top 10 giải đấu: <strong>20–40</strong></div>
        </div>
      </div>
    </main>
  );
}

'use client';

/** G3 · "Học thử ngay" — creates a guest learner and opens the app, no sign-up. */
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { LoaderCircle, Zap } from 'lucide-react';
import { getMyProfile, startGuestTrial } from '@/lib/services';
import { useAuthStore } from '@/store/authStore';
import { track } from '@/lib/analytics';

interface Props {
  className?: string;
  label?: string;
  /** Where the guest lands; the dashboard shows the placement + quick lessons. */
  to?: string;
}

export default function GuestTrialButton({ className = 'btn btn-outline btn-lg', label = 'Học thử ngay, không cần đăng ký', to = '/dashboard' }: Props) {
  const router = useRouter();
  const { setAuth, setLearner, setUserRole, setGuest } = useAuthStore();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const start = async () => {
    setLoading(true);
    setError('');
    try {
      const token = await startGuestTrial();
      setAuth(token.access_token, token.refresh_token);
      setUserRole('learner');
      setGuest(true);
      setLearner(await getMyProfile());
      track('guest_trial_started');
      router.push(to);
    } catch {
      setError('Chưa mở được phiên học thử. Hãy thử lại.');
      setLoading(false);
    }
  };

  return (
    <>
      <button type="button" className={className} onClick={start} disabled={loading}>
        {loading ? <LoaderCircle className="animate-spin" size={18} /> : <Zap size={18} />} {loading ? 'Đang mở…' : label}
      </button>
      {error && <span style={{ color: 'var(--agen-secondary)', fontSize: '0.85rem' }}>{error}</span>}
    </>
  );
}

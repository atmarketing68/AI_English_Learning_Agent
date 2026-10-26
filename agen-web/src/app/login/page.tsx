'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { login, getMyProfile, getMe } from '@/lib/services';
import { useAuthStore } from '@/store/authStore';

export default function LoginPage() {
  const router = useRouter();
  const { setAuth, setLearner, setUserRole } = useAuthStore();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const token = await login({ username: email, password });
      setAuth(token.access_token, token.refresh_token);
      const me = await getMe();
      setUserRole(me.role);
      if (me.role === 'parent') {
        router.push('/parent');
      } else {
        const profile = await getMyProfile();
        setLearner(profile);
        router.push('/dashboard');
      }
    } catch (err: unknown) {
      setError((err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Email hoặc mật khẩu không đúng.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 'var(--spacing-lg)' }}>
      <div className="card animate-fade-in-up" style={{ width: '100%', maxWidth: 440 }}>
        
        {/* Header */}
        <div className="text-center" style={{ marginBottom: 'var(--spacing-xl)' }}>
          <div style={{ fontSize: '2.5rem', marginBottom: 'var(--spacing-sm)' }}>🎓</div>
          <h2>Chào mừng trở lại!</h2>
          <p style={{ marginTop: 8 }}>Tiếp tục hành trình học tiếng Anh của bạn</p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-md)' }}>
          <div className="form-group">
            <label className="form-label">Email</label>
            <input
              className="form-input"
              type="email"
              placeholder="email@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label">Mật khẩu</label>
            <input
              className="form-input"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          {error && (
            <div style={{ padding: '10px 14px', borderRadius: 'var(--radius-sm)', background: 'rgba(255,107,107,0.1)', color: 'var(--agen-secondary)', fontSize: '0.875rem' }}>
              ⚠️ {error}
            </div>
          )}

          <button type="submit" className="btn btn-primary btn-full btn-lg" disabled={loading} style={{ marginTop: 8 }}>
            {loading ? '⏳ Đang đăng nhập...' : '🚀 Đăng nhập'}
          </button>
        </form>

        {/* Footer */}
        <div className="text-center" style={{ marginTop: 'var(--spacing-lg)', fontSize: '0.9rem', color: 'var(--text-muted)' }}>
          Chưa có tài khoản?{' '}
          <Link href="/register" style={{ color: 'var(--agen-primary-light)', fontWeight: 600 }}>
            Đăng ký miễn phí
          </Link>
        </div>
      </div>
    </main>
  );
}

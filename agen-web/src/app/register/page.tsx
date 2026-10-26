'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { register, login, getMyProfile } from '@/lib/services';
import { useAuthStore } from '@/store/authStore';
import Logo from '@/components/ui/Logo';
import { CircleAlert, GraduationCap, Users } from 'lucide-react';
import { identifyUser, track } from '@/lib/analytics';
import { apiErrorMessage } from '@/lib/apiError';

const GRADES = [
  { value: 'grade_1', label: 'Lớp 1' }, { value: 'grade_2', label: 'Lớp 2' },
  { value: 'grade_3', label: 'Lớp 3' }, { value: 'grade_4', label: 'Lớp 4' },
  { value: 'grade_5', label: 'Lớp 5' }, { value: 'grade_6', label: 'Lớp 6' },
  { value: 'grade_7', label: 'Lớp 7' }, { value: 'grade_8', label: 'Lớp 8' },
  { value: 'grade_9', label: 'Lớp 9' }, { value: 'grade_10', label: 'Lớp 10' },
  { value: 'grade_11', label: 'Lớp 11' }, { value: 'grade_12', label: 'Lớp 12' },
  { value: 'university', label: 'Đại học / Sinh viên' }, { value: 'adult', label: 'Người đi làm' },
];

export default function RegisterPage() {
  const router = useRouter();
  const { setAuth, setLearner, setUserRole } = useAuthStore();
  const [role, setRole] = useState<'learner' | 'parent'>('learner');
  const [form, setForm] = useState({
    full_name: '', display_name: '', email: '', password: '', age: '', grade: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm((f) => ({ ...f, [e.target.name]: e.target.value }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (!/[A-Za-z]/.test(form.password) || !/\d/.test(form.password)) {
      setError('Mật khẩu cần có cả chữ cái và chữ số (ví dụ: hocTiengAnh2026).');
      return;
    }
    setLoading(true);
    let accountCreated = false;
    try {
      const created = await register({
        ...form,
        age: role === 'learner' && form.age ? parseInt(form.age) : undefined,
        role,
      });
      accountCreated = true;
      // Auto-login after register
      const token = await login({ username: form.email, password: form.password });
      setAuth(token.access_token, token.refresh_token);
      setUserRole(role);
      identifyUser(created.id, { role });
      track('signup_completed', { role });

      if (role === 'parent') {
        // Parents have no learner profile — go straight to parent dashboard
        router.push('/parent');
      } else {
        const profile = await getMyProfile();
        setLearner(profile);
        router.push('/onboarding');
      }
    } catch (err: unknown) {
      const message = apiErrorMessage(err, 'Đã có lỗi xảy ra. Vui lòng thử lại.');
      setError(accountCreated ? `Tài khoản đã được tạo. ${message} Hãy thử Đăng nhập.` : message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 'var(--spacing-lg)' }}>
      <div className="animate-fade-in-up" style={{ width: '100%', maxWidth: 480 }}>
        <Link href="/" aria-label="AI AGENT ENGLISH — trang chủ" style={{ display: 'flex', justifyContent: 'center', marginBottom: 28, opacity: 1 }}><Logo size={64} wordmark={false} /></Link>
        <div className="card" style={{ padding: 'clamp(24px, 5vw, 40px)', boxShadow: 'var(--shadow-md)', border: 'none' }}>

          <div className="text-center" style={{ marginBottom: 'var(--spacing-xl)' }}>
            <h2 style={{ fontSize: '1.75rem' }}>Tạo tài khoản AI AGENT ENGLISH</h2>
            <p style={{ marginTop: 8, fontSize: '0.95rem' }}>Bắt đầu hành trình tiếng Anh cá nhân hóa của bạn.</p>
          </div>

          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-md)' }}>
            {/* Role selector */}
            <div className="form-group">
              <label className="form-label">Bạn là</label>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                {([
                  { value: 'learner', icon: GraduationCap, label: 'Học viên' },
                  { value: 'parent', icon: Users, label: 'Phụ huynh' },
                ] as const).map((r) => (
                  <button
                    key={r.value}
                    type="button"
                    onClick={() => setRole(r.value)}
                    style={{
                      padding: '12px', borderRadius: 'var(--radius-md)', cursor: 'pointer',
                      border: `1.5px solid ${role === r.value ? 'var(--agen-primary)' : 'var(--border-medium)'}`,
                      background: role === r.value ? 'var(--bg-tint)' : 'transparent',
                      color: role === r.value ? 'var(--agen-primary)' : 'var(--text-primary)', fontWeight: 500,
                      fontFamily: 'inherit',
                      display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6,
                      transition: 'all 0.15s',
                    }}
                  >
                    <r.icon size={22} strokeWidth={1.8} />
                    <span style={{ fontSize: '0.85rem' }}>{r.label}</span>
                  </button>
                ))}
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--spacing-md)' }}>
              <div className="form-group">
                <label className="form-label">Họ và tên</label>
                <input className="form-input" name="full_name" placeholder="Nguyễn Văn A" value={form.full_name} onChange={handleChange} required />
              </div>
              <div className="form-group">
                <label className="form-label">Tên hiển thị</label>
                <input className="form-input" name="display_name" placeholder={role === 'parent' ? 'Bố Minh' : 'Minh'} value={form.display_name} onChange={handleChange} required />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Email</label>
              <input className="form-input" type="email" name="email" placeholder="email@example.com" value={form.email} onChange={handleChange} required />
            </div>

            <div className="form-group">
              <label className="form-label">Mật khẩu</label>
              <input className="form-input" type="password" name="password" placeholder="Tối thiểu 8 ký tự, gồm chữ và số" value={form.password} onChange={handleChange} required minLength={8} />
            </div>

            {role === 'learner' && (
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: 'var(--spacing-md)' }}>
                <div className="form-group">
                  <label className="form-label">Tuổi</label>
                  <input className="form-input" type="number" name="age" placeholder="Tuổi" value={form.age} onChange={handleChange} min={5} max={80} />
                </div>
                <div className="form-group">
                  <label className="form-label">Lớp / Cấp học</label>
                  <select className="form-input" name="grade" value={form.grade} onChange={handleChange} style={{ cursor: 'pointer' }}>
                    <option value="">Chọn cấp học</option>
                    {GRADES.map((g) => <option key={g.value} value={g.value}>{g.label}</option>)}
                  </select>
                </div>
              </div>
            )}

            {error && (
              <div className="alert-error">
                <CircleAlert size={16} style={{ flexShrink: 0 }} /> {error}
              </div>
            )}

            <button type="submit" className="btn btn-primary btn-full btn-lg" disabled={loading} style={{ marginTop: 8 }}>
              {loading ? 'Đang tạo tài khoản…' : role === 'parent' ? 'Tạo tài khoản phụ huynh' : 'Bắt đầu học ngay'}
            </button>
          </form>

          <div className="text-center" style={{ marginTop: 'var(--spacing-lg)', fontSize: '0.9rem', color: 'var(--text-muted)' }}>
            Đã có tài khoản?{' '}
            <Link href="/login" style={{ color: 'var(--agen-primary-light)', fontWeight: 500 }}>Đăng nhập</Link>
          </div>
        </div>
      </div>
    </main>
  );
}

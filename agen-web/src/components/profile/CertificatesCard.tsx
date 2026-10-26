'use client';

/** G10 · Chứng nhận của tôi: xem / in chứng nhận và nhận chứng nhận khi hoàn thành lộ trình mục tiêu. */
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Award, ExternalLink, LoaderCircle } from 'lucide-react';
import { claimTrackCertificate, getMyCertificates, type MyCertificates } from '@/lib/certificatesService';
import { track } from '@/lib/analytics';

export default function CertificatesCard() {
  const [data, setData] = useState<MyCertificates | null>(null);
  const [busy, setBusy] = useState('');
  const [error, setError] = useState('');

  useEffect(() => { getMyCertificates().then(setData).catch(() => setData(null)); }, []);
  if (!data) return null;

  const claimable = data.tracks.filter(t => t.completed && !t.claimed_code);
  const claim = async (trackId: string) => {
    setBusy(trackId); setError('');
    try {
      const c = await claimTrackCertificate(trackId);
      track('certificate_claimed', { track: trackId });
      setData(d => (d ? { certificates: [c, ...d.certificates], tracks: d.tracks.map(t => (t.track_id === trackId ? { ...t, claimed_code: c.code } : t)) } : d));
    } catch (err) {
      setError((err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Chưa nhận được chứng nhận.');
    } finally { setBusy(''); }
  };

  return (
    <section className="card profile-section">
      <div className="profile-section-head">
        <h2><Award size={18} color="var(--agen-accent)" /> Chứng nhận</h2>
        <span>{data.certificates.length}</span>
      </div>
      {claimable.map(t => (
        <div key={t.track_id} className="member-cert" style={{ justifyContent: 'space-between' }}>
          <span>🎉 Bạn đã hoàn thành <b>{t.title}</b></span>
          <button type="button" className="btn btn-primary btn-sm" disabled={!!busy} onClick={() => claim(t.track_id)}>{busy === t.track_id ? <LoaderCircle className="animate-spin" size={14} /> : <Award size={14} />} Nhận chứng nhận</button>
        </div>
      ))}
      {data.certificates.map(c => (
        <a key={c.code} href={`/certificate/${c.code}`} target="_blank" rel="noreferrer" className="member-cert">
          <Award size={16} color="var(--agen-accent)" />
          <span style={{ flex: 1, minWidth: 0 }}><b>{c.title}</b><br /><small style={{ color: 'var(--text-muted)' }}>{c.issuer_name} · mã {c.code}</small></span>
          <ExternalLink size={14} />
        </a>
      ))}
      {data.certificates.length === 0 && claimable.length === 0 && (
        <p className="profile-muted" style={{ margin: 0 }}>Hoàn thành một <Link href="/tracks">lộ trình mục tiêu</Link> (IELTS, TOEIC, phỏng vấn…) để nhận chứng nhận có mã xác thực, in được ra PDF.</p>
      )}
      {error && <div className="alert-error" style={{ marginTop: 8 }}>{error}</div>}
    </section>
  );
}

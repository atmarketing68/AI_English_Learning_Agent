'use client';

/** G10 · Chứng nhận hoàn thành: trang công khai để xác thực bằng mã và in / lưu PDF. */
import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { Award, CircleAlert, LoaderCircle, Printer, ShieldCheck } from 'lucide-react';
import { verifyCertificate, type Certificate } from '@/lib/certificatesService';

const SKILL_VI: Record<string, string> = { listening: 'Nghe', speaking: 'Nói', reading: 'Đọc', writing: 'Viết', vocabulary: 'Từ vựng', grammar: 'Ngữ pháp' };

export default function CertificatePage() {
  const { code } = useParams<{ code: string }>();
  const [cert, setCert] = useState<Certificate | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    verifyCertificate(code).then(setCert).catch(() => setError('Không tìm thấy chứng nhận với mã này.'));
  }, [code]);

  if (!cert) {
    return (
      <main className="report-page" style={{ display: 'grid', placeItems: 'center' }}>
        {error ? <div className="alert-error"><CircleAlert size={16} /> {error}</div> : <LoaderCircle className="animate-spin" size={22} />}
      </main>
    );
  }
  const issued = new Date(cert.issued_at.endsWith('Z') ? cert.issued_at : `${cert.issued_at}Z`).toLocaleDateString('vi-VN', { day: '2-digit', month: 'long', year: 'numeric' });
  const verifyUrl = typeof window !== 'undefined' ? window.location.href : `/certificate/${cert.code}`;
  const skills = Object.entries(cert.details.skills ?? {}).filter(([, v]) => v > 0);

  return (
    <main className="report-page cert-page">
      <div className="no-print cert-toolbar">
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, color: cert.revoked ? 'var(--agen-secondary)' : 'var(--agen-success)', fontWeight: 600 }}>
          <ShieldCheck size={18} /> {cert.revoked ? 'Chứng nhận đã bị thu hồi' : 'Chứng nhận hợp lệ'}
        </span>
        <span style={{ flex: 1 }} />
        <button type="button" className="btn btn-primary btn-sm" onClick={() => window.print()}><Printer size={14} /> In / Lưu PDF</button>
      </div>

      <article className="cert-sheet" data-revoked={cert.revoked}>
        <div className="cert-border">
          <div className="cert-brand">AI AGENT ENGLISH</div>
          <div className="cert-seal" aria-hidden><Award size={34} /></div>
          <div className="cert-kicker">Chứng nhận hoàn thành · Certificate of Completion</div>
          <p className="cert-small">Chứng nhận rằng · This is to certify that</p>
          <h1 className="cert-name">{cert.recipient_name}</h1>
          <p className="cert-small">đã hoàn thành · has successfully completed</p>
          <h2 className="cert-title">{cert.title}</h2>
          {cert.note && <p className="cert-note">{cert.note}</p>}
          <div className="cert-stats">
            {cert.details.level && <div><strong>{cert.details.level.replace('PRE_', 'Pre-')}</strong><span>Trình độ CEFR</span></div>}
            {cert.details.lessons != null && <div><strong>{cert.details.lessons}</strong><span>Bài đã học</span></div>}
            {cert.details.total_xp != null && <div><strong>{cert.details.total_xp.toLocaleString('vi-VN')}</strong><span>XP</span></div>}
            {cert.details.longest_streak != null && <div><strong>{cert.details.longest_streak}</strong><span>Chuỗi dài nhất</span></div>}
          </div>
          {skills.length > 0 && (
            <div className="cert-skills">{skills.map(([k, v]) => <span key={k}>{SKILL_VI[k] ?? k} {v}</span>)}</div>
          )}
          <div className="cert-foot">
            <div><div className="cert-sign">{cert.issuer_name}</div><span>Đơn vị cấp · Issued by</span></div>
            <div><div className="cert-sign">{issued}</div><span>Ngày cấp · Date</span></div>
          </div>
          <div className="cert-verify">Mã xác thực <b>{cert.code}</b> · kiểm tra tại {verifyUrl}</div>
        </div>
      </article>
      <p className="no-print" style={{ textAlign: 'center', fontSize: '0.8rem', color: 'var(--text-muted)' }}><Link href="/">AI AGENT ENGLISH</Link> — học tiếng Anh cùng AI</p>
    </main>
  );
}

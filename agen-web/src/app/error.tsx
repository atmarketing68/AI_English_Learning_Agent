'use client';

import { useEffect } from 'react';
import Link from 'next/link';
import { errorDetail, reloadOnceForChunkError } from '@/lib/errorRecovery';

/** Friendly fallback when a page throws; shows a technical line the user can screenshot for support. */
export default function Error({ error, retry }: { error: Error & { digest?: string }; retry: () => void }) {
  useEffect(() => {
    console.error(error);
    reloadOnceForChunkError(error);
  }, [error]);

  return (
    <main style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 'var(--spacing-lg)' }}>
      <div className="card" style={{ maxWidth: 460, width: '100%', textAlign: 'center', padding: 28 }}>
        <h2 style={{ marginBottom: 8 }}>Trang chưa tải được</h2>
        <p style={{ marginBottom: 20 }}>Có trục trặc nhỏ khi hiển thị trang này. Bạn thử tải lại nhé — tiến trình học của bạn không bị mất.</p>
        <div style={{ display: 'flex', gap: 10, justifyContent: 'center', flexWrap: 'wrap' }}>
          <button type="button" className="btn btn-primary" onClick={() => retry()}>Thử lại</button>
          <button type="button" className="btn btn-ghost" onClick={() => window.location.reload()}>Tải lại trang</button>
          <Link href="/" className="btn btn-ghost">Về trang chủ</Link>
        </div>
        <details style={{ marginTop: 18, textAlign: 'left', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
          <summary style={{ cursor: 'pointer' }}>Chi tiết kỹ thuật (gửi cho hỗ trợ nếu lỗi lặp lại)</summary>
          <p style={{ marginTop: 8, wordBreak: 'break-word' }}>{errorDetail(error)}</p>
        </details>
      </div>
    </main>
  );
}

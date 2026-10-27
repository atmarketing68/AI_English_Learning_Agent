'use client';

import { useEffect } from 'react';
import { errorDetail, reloadOnceForChunkError } from '@/lib/errorRecovery';

/** Last-resort fallback for errors in the root layout (replaces <html>, so it is self-contained). */
export default function GlobalError({ error }: { error: Error & { digest?: string } }) {
  useEffect(() => {
    console.error(error);
    reloadOnceForChunkError(error);
  }, [error]);

  return (
    <html lang="vi">
      <body style={{ margin: 0, fontFamily: 'system-ui, -apple-system, Segoe UI, Roboto, sans-serif', background: '#F5F5F7', color: '#1D1D1F' }}>
        <main style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}>
          <div style={{ maxWidth: 460, width: '100%', textAlign: 'center', background: '#fff', borderRadius: 24, padding: 28, boxShadow: '0 4px 24px rgba(0,0,0,0.08)' }}>
            <h2 style={{ margin: '0 0 8px' }}>Trang chưa tải được</h2>
            <p style={{ margin: '0 0 20px', color: '#6E6E73' }}>Có trục trặc nhỏ khi hiển thị trang. Bạn thử tải lại nhé — tiến trình học của bạn không bị mất.</p>
            <div style={{ display: 'flex', gap: 10, justifyContent: 'center', flexWrap: 'wrap' }}>
              <button type="button" onClick={() => window.location.reload()} style={{ padding: '12px 22px', borderRadius: 999, border: 0, background: '#0071E3', color: '#fff', fontSize: 16, fontWeight: 600 }}>Tải lại trang</button>
              {/* eslint-disable-next-line @next/next/no-html-link-for-pages -- the router is unavailable in the global error UI */}
              <a href="/" style={{ padding: '12px 22px', borderRadius: 999, border: '1px solid #D2D2D7', color: '#1D1D1F', textDecoration: 'none', fontSize: 16 }}>Về trang chủ</a>
            </div>
            <details style={{ marginTop: 18, textAlign: 'left', fontSize: 12, color: '#6E6E73' }}>
              <summary style={{ cursor: 'pointer' }}>Chi tiết kỹ thuật (gửi cho hỗ trợ nếu lỗi lặp lại)</summary>
              <p style={{ marginTop: 8, wordBreak: 'break-word' }}>{errorDetail(error)}</p>
            </details>
          </div>
        </main>
      </body>
    </html>
  );
}

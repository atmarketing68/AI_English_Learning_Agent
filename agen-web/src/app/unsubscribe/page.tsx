'use client';

import { Suspense, useEffect, useState } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { CircleAlert, CircleCheck } from 'lucide-react';
import { unsubscribeEmail } from '@/lib/reminderService';

function UnsubscribeContent() {
  const token = useSearchParams().get('token');
  const [status, setStatus] = useState<'working' | 'done' | 'error'>(token ? 'working' : 'error');

  useEffect(() => {
    if (!token) return;
    unsubscribeEmail(token).then(() => setStatus('done')).catch(() => setStatus('error'));
  }, [token]);

  return (
    <main className="review-shell">
      <div className="card review-end">
        {status === 'working' && <p>Đang xử lý…</p>}
        {status === 'done' && (
          <>
            <CircleCheck size={40} strokeWidth={1.5} color="var(--agen-success)" />
            <h2>Đã tắt email nhắc học</h2>
            <p>Bạn sẽ không nhận email nhắc học nữa. Có thể bật lại bất cứ lúc nào trong mục Nhắc học trên trang chủ.</p>
          </>
        )}
        {status === 'error' && (
          <>
            <CircleAlert size={40} strokeWidth={1.5} color="var(--agen-secondary)" />
            <h2>Liên kết không hợp lệ</h2>
            <p>Đăng nhập và tắt email trong mục Nhắc học trên trang chủ nhé.</p>
          </>
        )}
        <Link href="/dashboard" className="btn btn-primary btn-full">Về trang chủ</Link>
      </div>
    </main>
  );
}

// useSearchParams requires a Suspense boundary in the App Router
export default function UnsubscribePage() {
  return (
    <Suspense fallback={null}>
      <UnsubscribeContent />
    </Suspense>
  );
}

'use client';

import { useEffect, useState } from 'react';
import { LoaderCircle } from 'lucide-react';

/**
 * Full-screen overlay shown while AGEN generates a lesson live (the fallback
 * path when there is no pre-cached content). Communicates progress with an
 * indeterminate-but-reassuring bar and rotating encouraging messages so the
 * wait (which can be 30-120s on the free LLM tier) never feels frozen.
 */
const MESSAGES = [
  'AI AGENT ENGLISH đang thiết kế bài học riêng cho bạn…',
  'Chọn từ vựng và ví dụ phù hợp trình độ…',
  'Tạo câu hỏi luyện tập…',
  'Kiểm tra chất lượng nội dung…',
  'Sắp xong rồi, chuẩn bị học thôi.',
];

export default function LessonGeneratingOverlay({ skillLabel }: { skillLabel?: string }) {
  const [msgIndex, setMsgIndex] = useState(0);
  const [pct, setPct] = useState(8);

  useEffect(() => {
    // Rotate messages every 4s.
    const msgTimer = setInterval(() => {
      setMsgIndex((i) => Math.min(i + 1, MESSAGES.length - 1));
    }, 4000);
    // Creep the bar toward ~90% so it always feels alive, never reaching 100
    // until the real result arrives and the overlay unmounts.
    const barTimer = setInterval(() => {
      setPct((p) => (p < 90 ? p + Math.max(1, Math.round((90 - p) / 12)) : p));
    }, 900);
    return () => { clearInterval(msgTimer); clearInterval(barTimer); };
  }, []);

  return (
    <main
      style={{
        minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
        padding: 'var(--spacing-lg)',
      }}
    >
      <div className="card animate-fade-in-up" style={{ maxWidth: 440, width: '100%', textAlign: 'center', padding: 40, border: 'none', boxShadow: 'var(--shadow-md)' }}>
        <LoaderCircle className="animate-spin" size={36} strokeWidth={1.6} color="var(--agen-primary)" style={{ margin: '0 auto var(--spacing-lg)', display: 'block' }} />

        <h3 style={{ marginBottom: 8 }}>
          Đang tạo bài học{skillLabel ? ` ${skillLabel}` : ''}
        </h3>
        <p style={{ color: 'var(--text-secondary)', minHeight: 44, marginBottom: 'var(--spacing-lg)' }}>
          {MESSAGES[msgIndex]}
        </p>

        <div className="progress-bar" style={{ height: 8, marginBottom: 12 }}>
          <div className="progress-fill" style={{ width: `${pct}%` }} />
        </div>
        <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
          Lần đầu tạo bài có thể mất tới một phút. Những lần sau sẽ nhanh hơn.
        </p>
      </div>
    </main>
  );
}

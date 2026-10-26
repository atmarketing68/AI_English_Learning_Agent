'use client';

/** G11 · Bài viết gần đây: điểm AI, và điểm + nhận xét của giáo viên khi đã chấm lại. */
import { useEffect, useState } from 'react';
import { GraduationCap, PenLine } from 'lucide-react';
import { getWritingHistory, type WritingHistoryItem } from '@/lib/writingApiService';

const day = (s: string) => new Date(/(?:[zZ]|[+-]\d\d:\d\d)$/.test(s) ? s : `${s}Z`).toLocaleDateString('vi-VN');

export default function WritingHistoryCard() {
  const [items, setItems] = useState<WritingHistoryItem[] | null>(null);
  useEffect(() => { getWritingHistory(8).then(setItems).catch(() => setItems([])); }, []);
  if (!items?.length) return null;
  return (
    <section style={{ marginTop: 8 }}>
      <div className="section-head"><h3>Bài viết gần đây</h3></div>
      <div className="card" style={{ padding: '4px 18px' }}>
        {items.map(w => (
          <div key={w.id} className="member-cert" style={{ alignItems: 'flex-start' }}>
            <PenLine size={15} color="var(--skill-writing)" style={{ marginTop: 3 }} />
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontWeight: 600 }}>{w.prompt_title}</div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{day(w.created_at)} · {w.word_count} từ · AI: {w.band != null ? `band ${w.band}` : w.overall_score != null ? Math.round(w.overall_score) : '—'}</div>
              {w.teacher_comment && <div style={{ fontSize: '0.85rem', marginTop: 4, whiteSpace: 'pre-line' }}>“{w.teacher_comment}”</div>}
            </div>
            {w.teacher_score != null
              ? <span className="teacher-score" title="Giáo viên đã chấm lại"><GraduationCap size={13} /> {w.teacher_band != null ? `${w.teacher_band}` : `${w.teacher_score}`}</span>
              : <span style={{ fontWeight: 600 }}>{w.overall_score != null ? Math.round(w.overall_score) : '—'}</span>}
          </div>
        ))}
      </div>
    </section>
  );
}

'use client';

/** G7 · Dashboard card: pending class/company assignments. */
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { ChevronRight, School } from 'lucide-react';
import { getMyGroups, type LearnerGroup } from '@/lib/groupsService';

export default function AssignmentsCard() {
  const [groups, setGroups] = useState<LearnerGroup[] | null>(null);
  useEffect(() => { getMyGroups().then(r => setGroups(r.groups)).catch(() => null); }, []);
  if (!groups || groups.length === 0) return null;
  const pending = groups.flatMap(g => g.assignments.filter(a => !a.done).map(a => ({ group: g.group.name, a })));
  const next = pending[0];
  return (
    <Link href={next ? `/learn?assignment=${next.a.id}` : '/classes'} className="card card-hover" style={{ display: 'flex', alignItems: 'center', gap: 16, padding: 'var(--spacing-lg)', borderRadius: 'var(--radius-xl)', opacity: 1 }}>
      <span className="icon-tile" style={{ flexShrink: 0, width: 48, height: 48, borderRadius: 16, background: 'var(--bg-tint)', color: 'var(--agen-primary)' }}>
        <School size={24} strokeWidth={1.8} />
      </span>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div className="eyebrow" style={{ marginBottom: 4 }}>Bài tập được giao</div>
        <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{next ? `${next.a.title} · ${next.group}` : 'Đã làm xong hết bài tập'}</div>
        <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>{next ? `${pending.length} bài đang chờ${next.a.due_on ? ` · hạn gần nhất ${new Date(next.a.due_on).toLocaleDateString('vi-VN')}` : ''}` : `${groups.length} lớp/nhóm của bạn`}</div>
      </div>
      <ChevronRight size={18} color="var(--text-muted)" />
    </Link>
  );
}

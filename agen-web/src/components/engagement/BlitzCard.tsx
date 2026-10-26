'use client';

/** G4 · Dashboard card: jump into a 60-second blitz round. */
import Link from 'next/link';
import { ChevronRight, Zap } from 'lucide-react';

export default function BlitzCard({ wordsKnown }: { wordsKnown: number }) {
  return (
    <Link href="/blitz" className="card card-hover blitz-card-link">
      <span className="icon-tile" style={{ flexShrink: 0, width: 48, height: 48, borderRadius: 16, background: 'color-mix(in srgb, var(--skill-listening) 14%, transparent)', color: 'var(--skill-listening)' }}>
        <Zap size={24} strokeWidth={1.8} />
      </span>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div className="eyebrow" style={{ marginBottom: 4 }}>Blitz 60 giây</div>
        <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Đoán nghĩa 15 từ trong 1 phút</div>
        <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
          {wordsKnown > 0 ? `Có ${wordsKnown} từ trong sổ của bạn · +XP và đá quý` : 'Từ trong lộ trình · +XP và đá quý mỗi câu đúng'}
        </div>
      </div>
      <ChevronRight size={18} color="var(--text-muted)" />
    </Link>
  );
}

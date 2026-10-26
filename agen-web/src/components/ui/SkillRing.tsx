'use client';

/** Circular progress ring with an animated stroke, used for the 4 skills and goal progress. */
import { motion } from 'framer-motion';
import type { LucideIcon } from 'lucide-react';
import CountUp from '@/components/ui/CountUp';

export default function SkillRing({ score, color, label, icon: Icon, size = 104, stroke = 9 }: {
  score: number; color: string; label: string; icon?: LucideIcon; size?: number; stroke?: number;
}) {
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const pct = Math.max(0, Math.min(100, score));
  return (
    <div className="skill-ring" style={{ width: size }}>
      <div style={{ position: 'relative', width: size, height: size }}>
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} aria-hidden="true">
          <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="var(--ring-track)" strokeWidth={stroke} />
          <motion.circle
            cx={size / 2} cy={size / 2} r={r} fill="none" stroke={color} strokeWidth={stroke} strokeLinecap="round"
            strokeDasharray={c}
            initial={{ strokeDashoffset: c }}
            animate={{ strokeDashoffset: c * (1 - pct / 100) }}
            transition={{ duration: 1.1, ease: [0.25, 0.1, 0.25, 1], delay: 0.15 }}
            style={{ rotate: -90, transformOrigin: '50% 50%', filter: `drop-shadow(0 0 6px color-mix(in srgb, ${color} 45%, transparent))` }}
          />
        </svg>
        <div className="skill-ring-center">
          {Icon && <Icon size={16} color={color} strokeWidth={2} />}
          <strong><CountUp value={pct} suffix="%" /></strong>
        </div>
      </div>
      <span className="skill-ring-label">{label}</span>
    </div>
  );
}

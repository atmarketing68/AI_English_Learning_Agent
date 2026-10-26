'use client';

/**
 * G4 · Bo — the friendly robot mascot of the playful ("vivid") look.
 * Renders nothing on the classic skin, so adult learners and parents keep a
 * clean, professional interface. Pass `always` to show it regardless.
 */
import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Volume2 } from 'lucide-react';
import { useSkin } from '@/store/skinStore';

import { playVietnamese, vietnameseVoiceAvailable } from '@/lib/speechService';

export type MascotMood = 'happy' | 'cheer' | 'think' | 'sad' | 'sleepy' | 'wow';

interface Props {
  mood?: MascotMood;
  size?: number;
  /** Speech bubble next to Bo. */
  say?: string;
  /** Where the bubble sits. */
  bubble?: 'right' | 'top';
  always?: boolean;
  className?: string;
}

const EYE: Record<MascotMood, { ry: number; dy: number }> = {
  happy: { ry: 5, dy: 0 }, cheer: { ry: 2.4, dy: 1 }, think: { ry: 5, dy: -1 },
  sad: { ry: 5.5, dy: 2 }, sleepy: { ry: 1.2, dy: 2 }, wow: { ry: 7, dy: 0 },
};

const MOUTH: Record<MascotMood, string> = {
  happy: 'M40 60 Q52 70 64 60',
  cheer: 'M38 58 Q52 76 66 58 Z',
  think: 'M42 63 L62 63',
  sad: 'M40 66 Q52 57 64 66',
  sleepy: 'M46 63 Q52 67 58 63',
  wow: 'M46 58 Q52 52 58 58 Q64 66 52 70 Q40 66 46 58 Z',
};

const BOUNCE: Record<MascotMood, { y?: number[]; rotate?: number[]; duration: number }> = {
  happy: { y: [0, -4, 0], duration: 2.4 },
  cheer: { y: [0, -10, 0], rotate: [0, -6, 6, 0], duration: 0.7 },
  think: { rotate: [0, 4, 0], duration: 2 },
  sad: { y: [0, 2, 0], duration: 2.6 },
  sleepy: { y: [0, 1, 0], duration: 3.2 },
  wow: { y: [0, -6, 0], duration: 1.2 },
};

export default function Mascot({ mood = 'happy', size = 96, say, bubble = 'right', always, className }: Props) {
  const skin = useSkin();
  const [canSpeak, setCanSpeak] = useState(false);
  useEffect(() => {
    const check = () => setCanSpeak(vietnameseVoiceAvailable());
    check();
    if (typeof window !== 'undefined' && window.speechSynthesis) {
      window.speechSynthesis.addEventListener?.('voiceschanged', check);
      return () => window.speechSynthesis.removeEventListener?.('voiceschanged', check);
    }
  }, []);
  if (skin !== 'vivid' && !always) return null;
  const eye = EYE[mood];
  const anim = BOUNCE[mood];
  const blush = mood === 'cheer' || mood === 'happy' || mood === 'wow';

  return (
    <div className={`mascot${className ? ` ${className}` : ''}`} data-bubble={bubble} data-mood={mood}>
      {say && (
        <div className="mascot-bubble" role="status">
          {say}
          {canSpeak && (
            <button type="button" className="mascot-speak" aria-label="Nghe Bo nói" onClick={() => void playVietnamese(say)}><Volume2 size={14} /></button>
          )}
        </div>
      )}
      <motion.svg
        width={size} height={size} viewBox="0 0 104 104" aria-hidden="true"
        animate={{ y: anim.y, rotate: anim.rotate }}
        transition={{ duration: anim.duration, repeat: Infinity, ease: 'easeInOut' }}
      >
        {/* antenna */}
        <line x1="52" y1="14" x2="52" y2="4" stroke="var(--mascot-dark)" strokeWidth="4" strokeLinecap="round" />
        <circle cx="52" cy="4" r="4.5" fill="var(--mascot-accent)" />
        {/* ears */}
        <rect x="4" y="38" width="10" height="20" rx="5" fill="var(--mascot-dark)" />
        <rect x="90" y="38" width="10" height="20" rx="5" fill="var(--mascot-dark)" />
        {/* head */}
        <rect x="12" y="14" width="80" height="72" rx="26" fill="var(--mascot-body)" />
        <rect x="20" y="24" width="64" height="54" rx="20" fill="var(--mascot-face)" />
        {/* eyes */}
        <ellipse cx="38" cy={48 + eye.dy} rx="6" ry={eye.ry} fill="var(--mascot-dark)" />
        <ellipse cx="66" cy={48 + eye.dy} rx="6" ry={eye.ry} fill="var(--mascot-dark)" />
        {mood !== 'sleepy' && (
          <>
            <circle cx="40" cy={45 + eye.dy} r="1.8" fill="#fff" />
            <circle cx="68" cy={45 + eye.dy} r="1.8" fill="#fff" />
          </>
        )}
        {/* cheeks */}
        {blush && (
          <>
            <circle cx="30" cy="59" r="4" fill="var(--mascot-blush)" opacity="0.8" />
            <circle cx="74" cy="59" r="4" fill="var(--mascot-blush)" opacity="0.8" />
          </>
        )}
        {/* mouth */}
        <path d={MOUTH[mood]} fill={mood === 'cheer' || mood === 'wow' ? 'var(--mascot-dark)' : 'none'} stroke="var(--mascot-dark)" strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round" />
        {/* body */}
        <rect x="30" y="86" width="44" height="14" rx="7" fill="var(--mascot-dark)" />
        <circle cx="52" cy="93" r="3" fill="var(--mascot-accent)" />
        {mood === 'think' && <text x="84" y="22" fontSize="18" fontWeight="800" fill="var(--mascot-dark)">?</text>}
        {mood === 'sleepy' && <text x="80" y="22" fontSize="16" fontWeight="800" fill="var(--mascot-dark)">z</text>}
      </motion.svg>
    </div>
  );
}

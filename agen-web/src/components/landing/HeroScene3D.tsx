'use client';

/**
 * Landing hero · "Vũ trụ tri thức" — a CSS-3D scene (no WebGL): a glowing
 * knowledge core with orbiting rings, six vocabulary cards circling it while
 * always facing the viewer, a staircase of CEFR levels with a light climbing
 * it, a grid floor flying toward the viewer and drifting letters. The whole
 * stage tilts with the pointer (springs), so every depth layer parallaxes.
 * Honors prefers-reduced-motion (static pose, no spin).
 */
import { useEffect } from 'react';
import { motion, useMotionValue, useSpring, useTransform } from 'framer-motion';
import { BookOpen, Compass, Flame, Lightbulb, Mic, Sparkles, Star, Trophy, type LucideIcon } from 'lucide-react';

const WORDS: { word: string; ipa: string; vi: string; icon: LucideIcon; a: string; b: string }[] = [
  { word: 'knowledge', ipa: '/ˈnɒl.ɪdʒ/', vi: 'tri thức', icon: BookOpen, a: '#38BDF8', b: '#2563EB' },
  { word: 'fluent', ipa: '/ˈfluː.ənt/', vi: 'lưu loát', icon: Mic, a: '#F472B6', b: '#E11D48' },
  { word: 'confident', ipa: '/ˈkɒn.fɪ.dənt/', vi: 'tự tin', icon: Sparkles, a: '#FBBF24', b: '#F97316' },
  { word: 'achieve', ipa: '/əˈtʃiːv/', vi: 'đạt được', icon: Trophy, a: '#34D399', b: '#059669' },
  { word: 'explore', ipa: '/ɪkˈsplɔːr/', vi: 'khám phá', icon: Compass, a: '#A78BFA', b: '#7C3AED' },
  { word: 'inspire', ipa: '/ɪnˈspaɪər/', vi: 'truyền cảm hứng', icon: Lightbulb, a: '#2DD4BF', b: '#0D9488' },
];

const LEVELS = ['A1', 'A2', 'B1', 'B2', 'C1'];

// Deterministic "random" letters so SSR and client render the same scene.
const LETTERS = 'ABCDEFGHKLMNPRSTUWY'.split('').map((ch, i) => {
  const t = (i * 137.508) % 360;                       // golden-angle spread
  return {
    ch,
    x: Math.round(Math.cos((t * Math.PI) / 180) * (170 + (i % 4) * 55)),
    y: Math.round(Math.sin((t * Math.PI) / 180) * (120 + (i % 3) * 40)),
    z: -320 + ((i * 97) % 520),
    size: 12 + (i % 5) * 4,
    delay: (i % 7) * -1.3,
    dur: 7 + (i % 5) * 1.5,
  };
});

export default function HeroScene3D() {
  const mx = useMotionValue(0);
  const my = useMotionValue(0);
  const rotateY = useSpring(useTransform(mx, [-0.5, 0.5], [-14, 14]), { stiffness: 50, damping: 18, mass: 0.6 });
  const rotateX = useSpring(useTransform(my, [-0.5, 0.5], [10, -10]), { stiffness: 50, damping: 18, mass: 0.6 });

  useEffect(() => {
    if (typeof window === 'undefined' || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    const onMove = (e: PointerEvent) => {
      mx.set(e.clientX / window.innerWidth - 0.5);
      my.set(e.clientY / window.innerHeight - 0.5);
    };
    const onLeave = () => { mx.set(0); my.set(0); };
    window.addEventListener('pointermove', onMove, { passive: true });
    document.addEventListener('pointerleave', onLeave);
    return () => { window.removeEventListener('pointermove', onMove); document.removeEventListener('pointerleave', onLeave); };
  }, [mx, my]);

  return (
    <div className="h3d" aria-hidden="true">
      <motion.div className="h3d-stage" style={{ rotateX, rotateY }}>
        {/* Space floor flying toward the viewer */}
        <div className="h3d-floor" />
        <div className="h3d-glow" />

        {/* Drifting letters at many depths */}
        {LETTERS.map(l => (
          <span key={l.ch} className="h3d-letter" style={{ '--x': `${l.x}px`, '--y': `${l.y}px`, '--z': `${l.z}px`, '--d': `${l.delay}s`, '--t': `${l.dur}s`, fontSize: l.size } as React.CSSProperties}>{l.ch}</span>
        ))}

        {/* Knowledge core: orb + three gyroscope rings */}
        <div className="h3d-core">
          <div className="h3d-ring h3d-ring-a" />
          <div className="h3d-ring h3d-ring-b" />
          <div className="h3d-ring h3d-ring-c" />
          <div className="h3d-orb"><BookOpen size={40} strokeWidth={1.6} /></div>
          <div className="h3d-xp">+25 XP</div>
        </div>

        {/* Vocabulary cards orbiting the core, always facing the viewer */}
        <div className="h3d-orbit-tilt">
          <div className="h3d-orbit-spin">
            {WORDS.map((w, i) => {
              const Icon = w.icon;
              const angle = (360 / WORDS.length) * i;
              return (
                <div key={w.word} className="h3d-orbit-item" style={{ '--a': `${angle}deg` } as React.CSSProperties}>
                  <div className="h3d-orbit-unspin">
                    <div className="h3d-orbit-untilt">
                      <div className="h3d-word" style={{ '--d': `${i * -0.9}s`, '--ca': w.a, '--cb': w.b } as React.CSSProperties}>
                        <span className="h3d-word-icon"><Icon size={16} strokeWidth={2} /></span>
                        <span>
                          <b>{w.word}</b>
                          <small>{w.ipa}</small>
                          <em>{w.vi}</em>
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Staircase of levels with a light climbing it */}
        <div className="h3d-steps">
          {LEVELS.map((lv, i) => (
            <div key={lv} className="h3d-step" style={{ '--i': i } as React.CSSProperties}><span>{lv}</span></div>
          ))}
          <div className="h3d-climber" />
          <div className="h3d-goal"><Trophy size={18} strokeWidth={2} /></div>
        </div>

        {/* Product moments floating in space */}
        <div className="h3d-chip h3d-chip-band"><Star size={14} fill="#FFD60A" color="#FFD60A" /> Band 7.0 <i>IELTS ↑</i></div>
        <div className="h3d-chip h3d-chip-streak"><Flame size={14} color="#FFB454" /> 12 ngày liên tiếp</div>
        <div className="h3d-chip h3d-chip-speak"><Mic size={14} color="#FF6B9A" /> Speaking · 92%</div>
      </motion.div>
    </div>
  );
}

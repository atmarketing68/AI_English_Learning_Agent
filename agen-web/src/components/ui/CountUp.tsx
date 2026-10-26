'use client';

/** Animated number: counts from 0 (or the previous value) to `value` with an ease-out curve. */
import { useEffect, useRef, useState } from 'react';

export default function CountUp({ value, duration = 900, decimals = 0, suffix = '', prefix = '' }: {
  value: number; duration?: number; decimals?: number; suffix?: string; prefix?: string;
}) {
  const [shown, setShown] = useState(0);
  const from = useRef(0);

  useEffect(() => {
    const start = performance.now();
    const begin = from.current;
    const reduce = typeof window !== 'undefined' && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
    let raf = 0;
    const tick = (now: number) => {
      const t = reduce ? 1 : Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - t, 3);
      setShown(begin + (value - begin) * eased);
      if (t < 1) raf = requestAnimationFrame(tick);
      else from.current = value;
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [value, duration]);

  return <>{prefix}{shown.toFixed(decimals)}{suffix}</>;
}

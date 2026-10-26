'use client';

import type { CSSProperties } from 'react';

/** A single shimmering skeleton block. */
export function Skeleton({
  width = '100%',
  height = 16,
  radius = 'var(--radius-md)',
  style,
}: {
  width?: number | string;
  height?: number | string;
  radius?: number | string;
  style?: CSSProperties;
}) {
  return (
    <div
      className="skeleton"
      aria-hidden="true"
      style={{ width, height, borderRadius: radius, ...style }}
    />
  );
}

/** A skeleton shaped like a .card with a few text lines. */
export function SkeletonCard({ lines = 3 }: { lines?: number }) {
  return (
    <div className="card" aria-hidden="true">
      <Skeleton width="45%" height={20} style={{ marginBottom: 16 }} />
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton
          key={i}
          width={i === lines - 1 ? '60%' : '100%'}
          height={12}
          style={{ marginBottom: 10 }}
        />
      ))}
    </div>
  );
}

/**
 * A full-page loading placeholder: a header block plus a few cards.
 * Used in place of a bare spinner while a page's data loads.
 */
export function PageSkeleton({
  maxWidth = 900,
  cards = 3,
}: {
  maxWidth?: number;
  cards?: number;
}) {
  return (
    <main style={{ minHeight: '100vh', padding: 'var(--spacing-lg)' }}>
      <div className="container" style={{ maxWidth }}>
        {/* Header */}
        <div style={{ marginBottom: 'var(--spacing-xl)' }}>
          <Skeleton width={220} height={14} style={{ marginBottom: 12 }} />
          <Skeleton width="55%" height={28} style={{ marginBottom: 8 }} />
          <Skeleton width={160} height={12} />
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-md)' }}>
          {Array.from({ length: cards }).map((_, i) => (
            <SkeletonCard key={i} lines={i === 0 ? 4 : 2} />
          ))}
        </div>
      </div>
    </main>
  );
}

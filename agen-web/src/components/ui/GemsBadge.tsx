'use client';

/** G4 · Đá quý: the shop currency, linked to the shop. */
import Link from 'next/link';
import { Gem } from 'lucide-react';

export default function GemsBadge({ gems, link = true, size = 13 }: { gems: number; link?: boolean; size?: number }) {
  const inner = <><Gem size={size} /> {gems}</>;
  if (!link) return <span className="gems-badge" title="Đá quý">{inner}</span>;
  return <Link href="/shop" className="gems-badge" title="Đá quý · Cửa hàng">{inner}</Link>;
}

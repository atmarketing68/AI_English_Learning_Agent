'use client';

/** G3 · Reminds a guest to save their account so progress is not lost. */
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { UserPlus } from 'lucide-react';
import { useAuthHydrated, useAuthStore } from '@/store/authStore';
import { showsAppShell } from '@/components/ui/navigation';

export default function GuestBanner() {
  const pathname = usePathname();
  const hydrated = useAuthHydrated();
  const { isAuthenticated, isGuest } = useAuthStore();
  if (!hydrated || !isAuthenticated || !isGuest || !showsAppShell(pathname)) return null;
  return (
    <div className="guest-banner" role="status">
      <span>Bạn đang <strong>học thử</strong>. Lưu tài khoản để giữ XP, chuỗi ngày và sổ từ.</span>
      <Link href="/register?claim=1" className="btn btn-sm btn-primary"><UserPlus size={14} /> Lưu tài khoản</Link>
    </div>
  );
}

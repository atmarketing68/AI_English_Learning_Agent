'use client';

/**
 * G4 · Keeps <html data-skin> in sync with who is logged in.
 * Parents, admins and signed-out visitors always see the professional look.
 */
import { useEffect } from 'react';
import { usePathname } from 'next/navigation';
import { useAuthHydrated, useAuthStore } from '@/store/authStore';
import { skinForLearner, useSkinStore } from '@/store/skinStore';

// SEO content pages are marketing: always the professional look.
const ALWAYS_CLASSIC = ['/parent', '/admin', '/teacher', '/login', '/register', '/unsubscribe', '/certificate', '/receipt',
  '/luyen-thi-ielts', '/luyen-thi-toeic', '/tieng-anh-cho-tre-em', '/tieng-anh-giao-tiep', '/lop-hoc-va-doanh-nghiep'];

export default function SkinProvider() {
  const pathname = usePathname();
  const hydrated = useAuthHydrated();
  const { isAuthenticated, userRole, learner } = useAuthStore();
  const setSkin = useSkinStore((s) => s.setSkin);

  useEffect(() => {
    if (!hydrated) return;
    const forcedClassic = !isAuthenticated || userRole === 'parent' || userRole === 'teacher' || ALWAYS_CLASSIC.some(p => pathname === p || pathname.startsWith(`${p}/`));
    if (forcedClassic) { setSkin('classic'); return; }
    if (!learner) return;   // profile still loading: keep whatever the inline script applied
    setSkin(skinForLearner(learner));
  }, [hydrated, isAuthenticated, userRole, learner, pathname, setSkin]);

  return null;
}

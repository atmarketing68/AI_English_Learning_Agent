'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { motion } from 'framer-motion';
import { useAuthHydrated, useAuthStore } from '@/store/authStore';
import { TAB_ITEMS, isActive, showsAppShell } from '@/components/ui/navigation';

/** Bottom tab bar on phones (hidden by CSS on wider screens). */
export default function MobileNav() {
  const pathname = usePathname();
  const hydrated = useAuthHydrated();
  const { isAuthenticated, userRole } = useAuthStore();

  if (!hydrated || !isAuthenticated || userRole === 'parent' || !showsAppShell(pathname)) return null;

  return (
    <motion.nav
      className="app-tabbar"
      aria-label="Điều hướng"
      initial={{ y: 80 }}
      animate={{ y: 0 }}
      transition={{ duration: 0.35, ease: [0.25, 0.1, 0.25, 1] }}
    >
      {TAB_ITEMS.map((item) => {
        const active = isActive(item, pathname);
        const Icon = item.icon;
        return (
          <Link key={item.href} href={item.href} className="app-tab" data-active={active} aria-current={active ? 'page' : undefined}>
            <Icon size={22} strokeWidth={active ? 2.2 : 1.8} />
            <span>{item.label}</span>
          </Link>
        );
      })}
    </motion.nav>
  );
}

'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuthStore } from '@/store/authStore';
import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { House, Mic, ChartColumn, Sparkles } from 'lucide-react';

export default function MobileNav() {
  const pathname = usePathname();
  const { isAuthenticated, userRole } = useAuthStore();
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth <= 768);
    };
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Hide nav on certain routes (like login, register, onboarding) or if not logged in
  const hideNavRoutes = ['/login', '/register', '/onboarding', '/placement'];
  if (!isAuthenticated || hideNavRoutes.includes(pathname) || !isMobile) return null;
  if (userRole === 'parent' && pathname !== '/parent') return null; // Parents don't need this bottom nav for now

  const NAV_ITEMS = [
    { href: '/dashboard', match: '/dashboard', label: 'Học', icon: House },
    { href: '/practice/speaking', match: '/practice', label: 'Luyện tập', icon: Mic },
    { href: '/progress', match: '/progress', label: 'Tiến bộ', icon: ChartColumn },
    { href: '/upgrade', match: '/upgrade', label: 'Pro', icon: Sparkles },
  ];

  return (
    <AnimatePresence>
      <motion.nav
        initial={{ y: 100 }}
        animate={{ y: 0 }}
        transition={{ duration: 0.35, ease: [0.25, 0.1, 0.25, 1] }}
        style={{
          position: 'fixed',
          bottom: 0,
          left: 0,
          right: 0,
          height: 'calc(60px + env(safe-area-inset-bottom))',
          paddingBottom: 'env(safe-area-inset-bottom)',
          background: 'var(--bg-nav)',
          backdropFilter: 'saturate(180%) blur(20px)',
          WebkitBackdropFilter: 'saturate(180%) blur(20px)',
          borderTop: '1px solid var(--border-subtle)',
          display: 'flex',
          justifyContent: 'space-around',
          alignItems: 'center',
          zIndex: 1000,
        }}
      >
        {NAV_ITEMS.map((item) => {
          const isActive = pathname.startsWith(item.match);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: 3,
                padding: '6px 12px',
                color: isActive ? 'var(--agen-primary)' : 'var(--text-muted)',
                transition: 'color 0.2s',
                textDecoration: 'none',
                opacity: 1,
              }}
            >
              <Icon size={22} strokeWidth={isActive ? 2.2 : 1.8} />
              <span style={{ fontSize: '0.68rem', fontWeight: 500 }}>
                {item.label}
              </span>
            </Link>
          );
        })}
      </motion.nav>
    </AnimatePresence>
  );
}

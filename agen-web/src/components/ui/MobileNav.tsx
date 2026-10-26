'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuthStore } from '@/store/authStore';
import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

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
    { href: '/dashboard', label: 'Học', icon: '🏠' },
    { href: '/practice', label: 'Luyện tập', icon: '🗣️' },
    { href: '/progress', label: 'Tiến bộ', icon: '📊' },
    { href: '/upgrade', label: 'Pro', icon: '⚡' },
  ];

  return (
    <AnimatePresence>
      <motion.nav
        initial={{ y: 100 }}
        animate={{ y: 0 }}
        style={{
          position: 'fixed',
          bottom: 0,
          left: 0,
          right: 0,
          height: 64,
          background: 'rgba(26, 24, 39, 0.85)',
          backdropFilter: 'blur(12px)',
          borderTop: '1px solid var(--border-medium)',
          display: 'flex',
          justifyContent: 'space-around',
          alignItems: 'center',
          zIndex: 1000,
          paddingBottom: 'safe-area-inset-bottom', // For iOS
        }}
      >
        {NAV_ITEMS.map((item) => {
          const isActive = pathname.startsWith(item.href);
          return (
            <Link 
              key={item.href} 
              href={item.href}
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: 4,
                padding: '8px 12px',
                color: isActive ? 'var(--agen-primary-light)' : 'var(--text-muted)',
                transition: 'color 0.2s',
                textDecoration: 'none'
              }}
            >
              <span style={{ fontSize: '1.2rem', filter: isActive ? 'none' : 'grayscale(100%)', opacity: isActive ? 1 : 0.6 }}>
                {item.icon}
              </span>
              <span style={{ fontSize: '0.7rem', fontWeight: isActive ? 700 : 500 }}>
                {item.label}
              </span>
            </Link>
          );
        })}
      </motion.nav>
    </AnimatePresence>
  );
}

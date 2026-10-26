'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Flame, Gem, Star } from 'lucide-react';
import Avatar from '@/components/ui/Avatar';
import Logo from '@/components/ui/Logo';
import MobileNav from '@/components/ui/MobileNav';
import GuestBanner from '@/components/GuestBanner';
import { useAuthHydrated, useAuthStore } from '@/store/authStore';
import { SIDEBAR_ITEMS, isActive, showsAppShell } from '@/components/ui/navigation';

/** Learner app frame: a sidebar on desktop and the tab bar on phones. */
export default function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const hydrated = useAuthHydrated();
  const { isAuthenticated, userRole, learner } = useAuthStore();
  const shell = hydrated && isAuthenticated && userRole !== 'parent' && showsAppShell(pathname);

  return (
    <>
      {shell && (
        <aside className="app-sidebar" aria-label="Điều hướng chính">
          <Link href="/dashboard" className="app-sidebar-brand"><Logo size={26} /></Link>
          <nav>
            {SIDEBAR_ITEMS.map((group, gi) => (
              <ul key={gi} className="app-sidebar-group">
                {group.map(item => {
                  const Icon = item.icon;
                  const active = isActive(item, pathname);
                  return (
                    <li key={item.href}>
                      <Link href={item.href} className="app-sidebar-link" data-active={active} aria-current={active ? 'page' : undefined}>
                        <Icon size={19} strokeWidth={active ? 2.2 : 1.8} /> {item.label}
                      </Link>
                    </li>
                  );
                })}
              </ul>
            ))}
          </nav>
          {learner && (
            <Link href="/profile" className="app-sidebar-me">
              <Avatar avatar={learner.avatar} name={learner.display_name} size={38} />
              <span style={{ minWidth: 0 }}>
                <span className="app-sidebar-name">{learner.display_name}</span>
                <span className="app-sidebar-stats">
                  <Flame size={12} /> {learner.current_streak} · <Star size={12} /> {learner.total_xp} · <Gem size={12} /> {learner.gems ?? 0}
                </span>
              </span>
            </Link>
          )}
        </aside>
      )}
      <div className={shell ? 'app-content with-shell' : 'app-content'}><GuestBanner />{children}</div>
      <MobileNav />
    </>
  );
}

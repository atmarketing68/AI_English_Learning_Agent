/** Shared navigation for the learner app shell (desktop sidebar + mobile tab bar). */
import {
  BookMarked, BookOpen, Brain, ChartColumn, House, Map as MapIcon, Mic, PenLine, ShoppingBag, Sparkles, Target, Trophy, UserRound, Users, Zap, type LucideIcon,
} from 'lucide-react';

export interface NavItem {
  href: string;
  label: string;
  icon: LucideIcon;
  /** Path prefixes that mark this item as active. */
  match: string[];
}

export const SIDEBAR_ITEMS: NavItem[][] = [
  [
    { href: '/dashboard', label: 'Trang chủ', icon: House, match: ['/dashboard'] },
    { href: '/curriculum', label: 'Lộ trình', icon: MapIcon, match: ['/curriculum'] },
    { href: '/learn', label: 'Bài học', icon: BookOpen, match: ['/learn'] },
    { href: '/review', label: 'Ôn tập', icon: Brain, match: ['/review'] },
    { href: '/blitz', label: 'Blitz 60s', icon: Zap, match: ['/blitz'] },
    { href: '/vocabulary', label: 'Sổ từ vựng', icon: BookMarked, match: ['/vocabulary'] },
  ],
  [
    { href: '/practice/speaking', label: 'Luyện nói', icon: Mic, match: ['/practice/speaking'] },
    { href: '/practice/writing', label: 'Luyện viết', icon: PenLine, match: ['/practice/writing'] },
    { href: '/tracks', label: 'Mục tiêu', icon: Target, match: ['/tracks'] },
    { href: '/league', label: 'Giải đấu', icon: Trophy, match: ['/league'] },
    { href: '/friends', label: 'Bạn học', icon: Users, match: ['/friends'] },
    { href: '/progress', label: 'Tiến bộ', icon: ChartColumn, match: ['/progress'] },
  ],
  [
    { href: '/shop', label: 'Cửa hàng', icon: ShoppingBag, match: ['/shop'] },
    { href: '/profile', label: 'Hồ sơ', icon: UserRound, match: ['/profile'] },
    { href: '/upgrade', label: 'Premium', icon: Sparkles, match: ['/upgrade'] },
  ],
];

export const TAB_ITEMS: NavItem[] = [
  { href: '/dashboard', label: 'Học', icon: House, match: ['/dashboard', '/learn', '/curriculum'] },
  { href: '/review', label: 'Ôn tập', icon: Brain, match: ['/review', '/vocabulary', '/blitz'] },
  { href: '/practice/speaking', label: 'Luyện tập', icon: Mic, match: ['/practice'] },
  { href: '/progress', label: 'Tiến bộ', icon: ChartColumn, match: ['/progress', '/league', '/tracks', '/friends'] },
  { href: '/profile', label: 'Hồ sơ', icon: UserRound, match: ['/profile', '/upgrade', '/shop'] },
];

const SHELL_PREFIXES = ['/dashboard', '/curriculum', '/learn', '/vocabulary', '/practice', '/progress', '/profile', '/upgrade', '/league', '/tracks', '/shop', '/blitz', '/friends'];

/**
 * Pages that show the app navigation. Focus modes keep the whole screen:
 * the lesson player (/learn/<id>) and a review session (/review).
 */
export function showsAppShell(pathname: string): boolean {
  if (/^\/learn\/[^/]+/.test(pathname)) return false;
  return SHELL_PREFIXES.some(p => pathname === p || pathname.startsWith(`${p}/`));
}

export const isActive = (item: NavItem, pathname: string) =>
  item.match.some(p => pathname === p || pathname.startsWith(`${p}/`));

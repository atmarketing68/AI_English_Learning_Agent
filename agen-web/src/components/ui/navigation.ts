/** Shared navigation for the learner app shell (desktop sidebar + mobile tab bar). */
import {
  BookMarked, BookOpen, Brain, ChartColumn, House, Map as MapIcon, Mic, PenLine, Sparkles, UserRound, type LucideIcon,
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
    { href: '/vocabulary', label: 'Sổ từ vựng', icon: BookMarked, match: ['/vocabulary'] },
  ],
  [
    { href: '/practice/speaking', label: 'Luyện nói', icon: Mic, match: ['/practice/speaking'] },
    { href: '/practice/writing', label: 'Luyện viết', icon: PenLine, match: ['/practice/writing'] },
    { href: '/progress', label: 'Tiến bộ', icon: ChartColumn, match: ['/progress'] },
  ],
  [
    { href: '/profile', label: 'Hồ sơ', icon: UserRound, match: ['/profile'] },
    { href: '/upgrade', label: 'Premium', icon: Sparkles, match: ['/upgrade'] },
  ],
];

export const TAB_ITEMS: NavItem[] = [
  { href: '/dashboard', label: 'Học', icon: House, match: ['/dashboard', '/learn', '/curriculum'] },
  { href: '/review', label: 'Ôn tập', icon: Brain, match: ['/review', '/vocabulary'] },
  { href: '/practice/speaking', label: 'Luyện tập', icon: Mic, match: ['/practice'] },
  { href: '/progress', label: 'Tiến bộ', icon: ChartColumn, match: ['/progress'] },
  { href: '/profile', label: 'Hồ sơ', icon: UserRound, match: ['/profile', '/upgrade'] },
];

const SHELL_PREFIXES = ['/dashboard', '/curriculum', '/learn', '/vocabulary', '/practice', '/progress', '/profile', '/upgrade'];

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

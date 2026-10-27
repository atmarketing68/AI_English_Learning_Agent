import { Baby, Briefcase, GraduationCap, MessagesSquare, School, type LucideIcon } from 'lucide-react';
import type { SeoIcon } from '@/lib/seo/pages';

export const SEO_ICONS: Record<SeoIcon, { icon: LucideIcon; colors: [string, string] }> = {
  ielts: { icon: GraduationCap, colors: ['#2F80FF', '#06B6D4'] },
  toeic: { icon: Briefcase, colors: ['#8B5CF6', '#6366F1'] },
  kids: { icon: Baby, colors: ['#EC4899', '#F97316'] },
  talk: { icon: MessagesSquare, colors: ['#10B981', '#14B8A6'] },
  class: { icon: School, colors: ['#F59E0B', '#F97316'] },
};

/** SEO · Kiểu dữ liệu cho cẩm nang học (bài viết dài theo từ khoá) — server-rendered tại /cam-nang/<slug>. */
export type ArticleCategory = 'ielts' | 'toeic' | 'giao-tiep' | 'tu-vung' | 'phu-huynh' | 'nen-tang';

export const ARTICLE_CATEGORIES: Record<ArticleCategory, string> = {
  ielts: 'IELTS',
  toeic: 'TOEIC',
  'giao-tiep': 'Giao tiếp & phát âm',
  'tu-vung': 'Từ vựng',
  'phu-huynh': 'Dành cho phụ huynh',
  'nen-tang': 'Nền tảng',
};

export interface ArticleBlock {
  id: string;                 // anchor for the table of contents
  h2: string;
  paras?: string[];
  bullets?: string[];
  numbered?: string[];
  table?: { caption?: string; head: string[]; rows: string[][] };
  tip?: string;               // highlighted "mẹo" box
  after?: string[];           // paragraphs after the list/table
}

export interface Article {
  slug: string;
  category: ArticleCategory;
  title: string;              // <title>, ≤ ~60 ký tự trước hậu tố thương hiệu
  description: string;        // meta description ~150–160 ký tự
  h1: string;
  lead: string;
  published: string;          // YYYY-MM-DD
  updated: string;
  blocks: ArticleBlock[];
  faqs: { q: string; a: string }[];
  goal: string;               // slug of the related goal page (lib/seo/pages.ts)
  related: string[];          // other article slugs
}

/** Rough reading time at ~200 words a minute (Vietnamese prose). */
export function readingMinutes(a: Article): number {
  const text = [a.lead, ...a.blocks.flatMap(b => [b.h2, ...(b.paras ?? []), ...(b.bullets ?? []), ...(b.numbered ?? []), ...(b.after ?? []), b.tip ?? '',
    ...(b.table ? b.table.rows.flat() : [])]), ...a.faqs.flatMap(f => [f.q, f.a])].join(' ');
  return Math.max(3, Math.round(text.split(/\s+/).filter(Boolean).length / 200));
}

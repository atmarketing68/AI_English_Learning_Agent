import type { MetadataRoute } from 'next';
import { ARTICLES } from '@/lib/seo/articles';
import { GUIDES } from '@/lib/seo/guides';
import { SEO_PAGES } from '@/lib/seo/pages';
import { CONTENT_UPDATED, SITE_URL } from '@/lib/seo/site';

export default function sitemap(): MetadataRoute.Sitemap {
  const lastModified = new Date(CONTENT_UPDATED);
  return [
    { url: SITE_URL, lastModified, changeFrequency: 'weekly', priority: 1 },
    ...SEO_PAGES.map(p => ({ url: `${SITE_URL}/${p.slug}`, lastModified, changeFrequency: 'monthly' as const, priority: 0.8 })),
    { url: `${SITE_URL}/cam-nang`, lastModified, changeFrequency: 'weekly', priority: 0.7 },
    ...ARTICLES.map(a => ({ url: `${SITE_URL}/cam-nang/${a.slug}`, lastModified: new Date(a.updated), changeFrequency: 'monthly' as const, priority: 0.7 })),
    { url: `${SITE_URL}/huong-dan-su-dung`, lastModified, changeFrequency: 'monthly', priority: 0.6 },
    ...GUIDES.map(g => ({ url: `${SITE_URL}/huong-dan-su-dung/${g.slug}`, lastModified, changeFrequency: 'monthly' as const, priority: 0.6 })),
  ];
}

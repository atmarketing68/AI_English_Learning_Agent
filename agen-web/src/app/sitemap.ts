import type { MetadataRoute } from 'next';
import { SEO_PAGES } from '@/lib/seo/pages';
import { CONTENT_UPDATED, SITE_URL } from '@/lib/seo/site';

export default function sitemap(): MetadataRoute.Sitemap {
  const lastModified = new Date(CONTENT_UPDATED);
  return [
    { url: SITE_URL, lastModified, changeFrequency: 'weekly', priority: 1 },
    ...SEO_PAGES.map(p => ({ url: `${SITE_URL}/${p.slug}`, lastModified, changeFrequency: 'monthly' as const, priority: 0.8 })),
  ];
}

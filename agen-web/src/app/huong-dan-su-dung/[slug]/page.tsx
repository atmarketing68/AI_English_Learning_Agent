import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import GuideView from '@/components/seo/GuideView';
import { GUIDES, GUIDE_BY_SLUG } from '@/lib/seo/guides';
import { SITE_NAME } from '@/lib/seo/site';

export const dynamicParams = false;

export function generateStaticParams() {
  return GUIDES.map(g => ({ slug: g.slug }));
}

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }): Promise<Metadata> {
  const g = GUIDE_BY_SLUG[(await params).slug];
  if (!g) return {};
  const image = g.steps.flatMap(s => s.images ?? []).find(i => !i.mobile);
  const images = image ? [{ url: image.src, width: 1440, height: 900, alt: image.alt }] : undefined;
  return {
    title: g.title,
    description: g.description,
    alternates: { canonical: `/huong-dan-su-dung/${g.slug}` },
    openGraph: { type: 'article', url: `/huong-dan-su-dung/${g.slug}`, title: g.title, description: g.description, siteName: SITE_NAME, locale: 'vi_VN', images },
    twitter: { card: 'summary_large_image', title: g.title, description: g.description, images: image ? [image.src] : undefined },
  };
}

export default async function Page({ params }: { params: Promise<{ slug: string }> }) {
  const g = GUIDE_BY_SLUG[(await params).slug];
  if (!g) notFound();
  return <GuideView guide={g} />;
}

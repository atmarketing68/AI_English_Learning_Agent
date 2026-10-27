import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import ArticleView from '@/components/seo/ArticleView';
import { ARTICLES, ARTICLE_BY_SLUG } from '@/lib/seo/articles';
import { OG_IMAGE, SITE_NAME } from '@/lib/seo/site';

export const dynamicParams = false;

export function generateStaticParams() {
  return ARTICLES.map(a => ({ slug: a.slug }));
}

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }): Promise<Metadata> {
  const a = ARTICLE_BY_SLUG[(await params).slug];
  if (!a) return {};
  return {
    title: a.title,
    description: a.description,
    alternates: { canonical: `/cam-nang/${a.slug}` },
    openGraph: { type: 'article', url: `/cam-nang/${a.slug}`, title: a.title, description: a.description, siteName: SITE_NAME, locale: 'vi_VN',
      images: [OG_IMAGE], publishedTime: a.published, modifiedTime: a.updated },
    twitter: { card: 'summary_large_image', title: a.title, description: a.description, images: [OG_IMAGE.url] },
  };
}

export default async function Page({ params }: { params: Promise<{ slug: string }> }) {
  const a = ARTICLE_BY_SLUG[(await params).slug];
  if (!a) notFound();
  return <ArticleView article={a} />;
}

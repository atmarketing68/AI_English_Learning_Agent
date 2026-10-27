/** Cẩm nang học tiếng Anh: danh sách bài viết theo chủ đề + lối vào hướng dẫn sử dụng. */
import type { Metadata } from 'next';
import SeoHeroArt from '@/components/seo/SeoHeroArt';
import Link from 'next/link';
import { BookOpen, ChevronRight, Clock, LifeBuoy } from 'lucide-react';
import { SiteFooter, SiteHeader } from '@/components/landing/SiteChrome';
import { ARTICLES } from '@/lib/seo/articles';
import { ARTICLE_CATEGORIES, readingMinutes, type ArticleCategory } from '@/lib/seo/articleTypes';
import { OG_IMAGE, SITE_NAME, SITE_URL, jsonLd } from '@/lib/seo/site';

const TITLE = 'Cẩm nang học tiếng Anh: IELTS, TOEIC, giao tiếp';
const DESCRIPTION = 'Cẩm nang học tiếng Anh cho người Việt: cấu trúc đề IELTS, TOEIC, lộ trình tự học, cách luyện nói một mình, học từ vựng nhớ lâu, khung CEFR và hướng dẫn cho phụ huynh.';

export const metadata: Metadata = {
  title: TITLE,
  description: DESCRIPTION,
  alternates: { canonical: '/cam-nang' },
  openGraph: { type: 'website', url: '/cam-nang', title: TITLE, description: DESCRIPTION, siteName: SITE_NAME, locale: 'vi_VN', images: [OG_IMAGE] },
  twitter: { card: 'summary_large_image', title: TITLE, description: DESCRIPTION, images: [OG_IMAGE.url] },
};

const ORDER: ArticleCategory[] = ['ielts', 'toeic', 'giao-tiep', 'tu-vung', 'phu-huynh', 'nen-tang'];

export default function CamNangPage() {
  const ld = [
    {
      '@context': 'https://schema.org', '@type': 'CollectionPage', url: `${SITE_URL}/cam-nang`, name: TITLE, description: DESCRIPTION, inLanguage: 'vi-VN',
      hasPart: ARTICLES.map(a => ({ '@type': 'Article', headline: a.h1, url: `${SITE_URL}/cam-nang/${a.slug}` })),
    },
    {
      '@context': 'https://schema.org', '@type': 'BreadcrumbList',
      itemListElement: [
        { '@type': 'ListItem', position: 1, name: 'Trang chủ', item: SITE_URL },
        { '@type': 'ListItem', position: 2, name: 'Cẩm nang', item: `${SITE_URL}/cam-nang` },
      ],
    },
  ];
  return (
    <main style={{ minHeight: '100vh', overflowX: 'hidden', background: 'var(--bg-surface)' }}>
      {ld.map((d, i) => <script key={i} type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLd(d) }} />)}
      <SiteHeader />
      <section className="seo-hero lp-tinted">
        <div className="seo-hero-inner">
          <nav className="seo-crumbs" aria-label="Breadcrumb"><Link href="/">Trang chủ</Link><span aria-hidden="true">/</span><span>Cẩm nang</span></nav>
          <span className="hero-badge"><BookOpen size={14} /> Cẩm nang học tiếng Anh</span>
          <h1>Học tiếng Anh đúng cách, từng bước một</h1>
          <p>Kiến thức nền về các kỳ thi, phương pháp luyện nói và học từ vựng, cùng hướng dẫn cho phụ huynh — viết ngắn gọn, áp dụng được ngay.</p>
          <div className="hero-actions" style={{ justifyContent: 'center' }}>
            <Link href="/huong-dan-su-dung" className="btn btn-ghost btn-lg"><LifeBuoy size={18} /> Hướng dẫn dùng ứng dụng</Link>
          </div>
        </div>
        <SeoHeroArt name="seo-cam-nang" />
      </section>

      {ORDER.map(cat => {
        const items = ARTICLES.filter(a => a.category === cat);
        if (!items.length) return null;
        return (
          <section key={cat} className="lp-section" style={{ paddingTop: 48, paddingBottom: 8 }}>
            <div className="article-list">
              <h2 className="article-list-title">{ARTICLE_CATEGORIES[cat]}</h2>
              <div className="seo-related" style={{ maxWidth: 'none' }}>
                {items.map(a => (
                  <Link key={a.slug} href={`/cam-nang/${a.slug}`} className="lp-card lp-goal">
                    <span className="article-cat"><Clock size={13} /> {readingMinutes(a)} phút đọc</span>
                    <h3 style={{ marginTop: 10 }}>{a.h1}</h3>
                    <p>{a.description}</p>
                    <span className="lp-goal-more">Đọc bài <ChevronRight size={15} /></span>
                  </Link>
                ))}
              </div>
            </div>
          </section>
        );
      })}
      <div style={{ height: 72 }} />
      <SiteFooter />
    </main>
  );
}

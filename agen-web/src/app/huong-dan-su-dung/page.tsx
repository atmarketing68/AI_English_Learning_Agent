/** Hướng dẫn sử dụng: chọn đối tượng (người học, học sinh, phụ huynh, giáo viên) + lối vào cẩm nang học. */
import type { Metadata } from 'next';
import SeoHeroArt from '@/components/seo/SeoHeroArt';
import Link from 'next/link';
import { BookOpen, ChevronRight, LifeBuoy } from 'lucide-react';
import { SiteFooter, SiteHeader } from '@/components/landing/SiteChrome';
import { SEO_ICONS } from '@/components/seo/seoIcons';
import { GUIDES } from '@/lib/seo/guides';
import { OG_IMAGE, SITE_NAME, SITE_URL, jsonLd } from '@/lib/seo/site';

const TITLE = 'Hướng dẫn sử dụng AI AGENT ENGLISH';
const DESCRIPTION = 'Hướng dẫn dùng AI AGENT ENGLISH từng bước, có ảnh minh hoạ, cho người học, học sinh, phụ huynh và giáo viên / trung tâm.';

export const metadata: Metadata = {
  title: TITLE,
  description: DESCRIPTION,
  alternates: { canonical: '/huong-dan-su-dung' },
  openGraph: { type: 'website', url: '/huong-dan-su-dung', title: TITLE, description: DESCRIPTION, siteName: SITE_NAME, locale: 'vi_VN', images: [OG_IMAGE] },
  twitter: { card: 'summary_large_image', title: TITLE, description: DESCRIPTION, images: [OG_IMAGE.url] },
};

export default function GuidesHub() {
  const ld = [
    {
      '@context': 'https://schema.org', '@type': 'CollectionPage', url: `${SITE_URL}/huong-dan-su-dung`, name: TITLE, description: DESCRIPTION, inLanguage: 'vi-VN',
      hasPart: GUIDES.map(g => ({ '@type': 'Article', headline: g.h1, url: `${SITE_URL}/huong-dan-su-dung/${g.slug}` })),
    },
    {
      '@context': 'https://schema.org', '@type': 'BreadcrumbList',
      itemListElement: [
        { '@type': 'ListItem', position: 1, name: 'Trang chủ', item: SITE_URL },
        { '@type': 'ListItem', position: 2, name: 'Hướng dẫn sử dụng', item: `${SITE_URL}/huong-dan-su-dung` },
      ],
    },
  ];
  return (
    <main style={{ minHeight: '100vh', overflowX: 'hidden', background: 'var(--bg-surface)' }}>
      {ld.map((d, i) => <script key={i} type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLd(d) }} />)}
      <SiteHeader />
      <section className="seo-hero lp-tinted">
        <div className="seo-hero-inner">
          <nav className="seo-crumbs" aria-label="Breadcrumb"><Link href="/">Trang chủ</Link><span aria-hidden="true">/</span><span>Hướng dẫn sử dụng</span></nav>
          <span className="hero-badge"><LifeBuoy size={14} /> Hướng dẫn sử dụng</span>
          <h1>Bắt đầu với AI AGENT ENGLISH</h1>
          <p>Chọn vai trò của bạn để xem từng bước, kèm ảnh chụp màn hình thật của ứng dụng.</p>
        </div>
        <SeoHeroArt name="seo-huong-dan" />
      </section>

      <section className="lp-section" style={{ paddingTop: 48 }}>
        <div className="guide-hub">
          {GUIDES.map(g => {
            const { icon: Icon, colors } = SEO_ICONS[g.icon];
            return (
              <Link key={g.slug} href={`/huong-dan-su-dung/${g.slug}`} className="lp-card lp-goal">
                <span className="lp-icon" style={{ width: 48, height: 48, borderRadius: 14, background: `linear-gradient(135deg, ${colors[0]}, ${colors[1]})` }}><Icon size={23} color="#fff" /></span>
                <h3>{g.cardTitle}</h3>
                <p>{g.cardDesc}</p>
                <span className="lp-goal-more">{g.steps.length} bước · Xem hướng dẫn <ChevronRight size={15} /></span>
              </Link>
            );
          })}
        </div>
        <div style={{ textAlign: 'center', marginTop: 40 }}>
          <Link href="/cam-nang" className="btn btn-ghost btn-lg"><BookOpen size={18} /> Đọc cẩm nang học tiếng Anh</Link>
        </div>
      </section>
      <div style={{ height: 48 }} />
      <SiteFooter />
    </main>
  );
}

/**
 * SEO · Khung trang nội dung theo mục tiêu (server component): hero, điểm nổi bật, bài viết,
 * các bước, hỏi đáp, CTA, trang liên quan + JSON-LD (WebPage, BreadcrumbList, FAQPage).
 */
import type { Metadata } from 'next';
import SeoHeroArt from '@/components/seo/SeoHeroArt';
import Link from 'next/link';
import { ArrowRight, BadgeCheck, Check, ChevronDown, ChevronRight, Trophy } from 'lucide-react';
import { SiteFooter, SiteHeader } from '@/components/landing/SiteChrome';
import { SEO_ICONS } from '@/components/seo/seoIcons';
import { SEO_PAGE_BY_SLUG, type SeoPage } from '@/lib/seo/pages';
import { OG_IMAGE, ORGANIZATION_LD, SITE_NAME, SITE_URL, jsonLd } from '@/lib/seo/site';

export function seoMetadata(slug: string): Metadata {
  const p = SEO_PAGE_BY_SLUG[slug];
  return {
    title: p.title,
    description: p.description,
    alternates: { canonical: `/${p.slug}` },
    openGraph: { type: 'article', url: `/${p.slug}`, title: p.title, description: p.description, siteName: SITE_NAME, locale: 'vi_VN', images: [OG_IMAGE] },
    twitter: { card: 'summary_large_image', title: p.title, description: p.description, images: [OG_IMAGE.url] },
  };
}

function structuredData(p: SeoPage) {
  const url = `${SITE_URL}/${p.slug}`;
  return [
    {
      '@context': 'https://schema.org', '@type': 'WebPage', '@id': `${url}#webpage`, url, name: p.title, description: p.description,
      inLanguage: 'vi-VN', isPartOf: { '@id': `${SITE_URL}/#website` }, publisher: { '@id': ORGANIZATION_LD['@id'] },
    },
    {
      '@context': 'https://schema.org', '@type': 'BreadcrumbList',
      itemListElement: [
        { '@type': 'ListItem', position: 1, name: 'Trang chủ', item: SITE_URL },
        { '@type': 'ListItem', position: 2, name: p.cardTitle, item: url },
      ],
    },
    {
      '@context': 'https://schema.org', '@type': 'FAQPage',
      mainEntity: p.faqs.map(f => ({ '@type': 'Question', name: f.q, acceptedAnswer: { '@type': 'Answer', text: f.a } })),
    },
  ];
}

export default function SeoLanding({ slug }: { slug: string }) {
  const p = SEO_PAGE_BY_SLUG[slug];
  const { icon: Icon, colors } = SEO_ICONS[p.icon];
  return (
    <main style={{ minHeight: '100vh', overflowX: 'hidden', background: 'var(--bg-surface)' }}>
      {structuredData(p).map((d, i) => <script key={i} type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLd(d) }} />)}
      <SiteHeader />

      <section className="seo-hero lp-tinted">
        <div className="seo-hero-inner">
          <nav className="seo-crumbs" aria-label="Breadcrumb"><Link href="/">Trang chủ</Link><span aria-hidden="true">/</span><span>{p.cardTitle}</span></nav>
          <span className="hero-badge"><Icon size={14} /> {p.eyebrow}</span>
          <h1>{p.h1}</h1>
          <p>{p.lead}</p>
          <div className="hero-actions" style={{ justifyContent: 'center' }}>
            <Link href={p.cta.href} className="btn btn-primary btn-lg btn-shine">{p.cta.label} <ArrowRight size={18} /></Link>
            <Link href="/#bang-gia" className="hero-link">Xem bảng giá <ChevronRight size={18} /></Link>
          </div>
        </div>
        <SeoHeroArt name={({ 'luyen-thi-ielts': 'seo-ielts', 'luyen-thi-toeic': 'seo-toeic', 'tieng-anh-cho-tre-em': 'seo-kids', 'tieng-anh-giao-tiep': 'seo-speaking', 'lop-hoc-va-doanh-nghiep': 'seo-business' } as Record<string, string>)[slug] ?? 'seo-cam-nang'} />
      </section>

      <section className="lp-section" style={{ paddingTop: 56 }}>
        <div className="seo-highlights">
          {p.highlights.map(h => (
            <div key={h.title} className="lp-card">
              <span className="lp-icon" style={{ width: 44, height: 44, borderRadius: 13, background: `linear-gradient(135deg, ${colors[0]}, ${colors[1]})` }}><Check size={22} color="#fff" /></span>
              <h3>{h.title}</h3>
              <p>{h.desc}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="lp-section" style={{ paddingTop: 0 }}>
        <article className="seo-article">
          {p.sections.map(s => (
            <div key={s.h2}>
              <h2>{s.h2}</h2>
              {s.body.map((para, i) => <p key={i}>{para}</p>)}
              {s.bullets && <ul className="lp-checks">{s.bullets.map(b => <li key={b}><Check size={16} /> {b}</li>)}</ul>}
            </div>
          ))}
        </article>
      </section>

      <section className="lp-section lp-tinted">
        <div className="lp-heading"><span className="lp-eyebrow">Bắt đầu thế nào?</span><h2>3 bước để bắt đầu</h2></div>
        <ol className="lp-steps grid-3" style={{ gap: 24, listStyle: 'none', padding: 0, margin: 0 }}>
          {p.steps.map((s, i) => (
            <li key={s.title} className="lp-card lp-step">
              <div className="lp-step-top"><span className="lp-step-num">0{i + 1}</span></div>
              <h3>{s.title}</h3>
              <p>{s.desc}</p>
            </li>
          ))}
        </ol>
      </section>

      <section className="lp-section">
        <div className="lp-heading"><span className="lp-eyebrow">Hỏi đáp</span><h2>Câu hỏi thường gặp</h2></div>
        <div className="lp-faq">
          {p.faqs.map(f => (
            <details key={f.q} className="lp-faq-item">
              <summary>{f.q}<ChevronDown size={20} /></summary>
              <p>{f.a}</p>
            </details>
          ))}
        </div>
      </section>

      <section className="lp-section" style={{ paddingTop: 0 }}>
        <div className="lp-heading"><h2 style={{ fontSize: 'clamp(1.5rem, 3.4vw, 2.1rem)' }}>Có thể bạn quan tâm</h2></div>
        <div className="seo-related">
          {p.related.map(slug => {
            const r = SEO_PAGE_BY_SLUG[slug];
            return (
              <Link key={slug} href={`/${slug}`} className="lp-card lp-goal">
                <h3 style={{ marginTop: 0 }}>{r.cardTitle}</h3>
                <p>{r.cardDesc}</p>
                <span className="lp-goal-more">Xem chi tiết <ChevronRight size={15} /></span>
              </Link>
            );
          })}
        </div>
      </section>

      <section className="lp-section" style={{ paddingTop: 0 }}>
        <div className="lp-cta">
          <span className="lp-blob lp-blob-1" aria-hidden="true" />
          <span className="lp-blob lp-blob-2" aria-hidden="true" />
          <div className="lp-cta-inner">
            <Trophy size={40} strokeWidth={1.6} />
            <h2>{p.cta.title}</h2>
            <p>{p.cta.desc}</p>
            <Link href={p.cta.href} className="btn btn-lg lp-cta-btn btn-shine">{p.cta.label} <ArrowRight size={18} /></Link>
            <div className="lp-cta-points">
              {['Không cần thẻ tín dụng', 'Học trên điện thoại và máy tính', 'Giải thích bằng tiếng Việt'].map(x => <span key={x}><BadgeCheck size={16} /> {x}</span>)}
            </div>
          </div>
        </div>
      </section>

      <SiteFooter />
    </main>
  );
}

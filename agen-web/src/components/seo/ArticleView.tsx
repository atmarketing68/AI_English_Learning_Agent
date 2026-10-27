/** Cẩm nang · một bài viết: mục lục, nội dung, mẹo, bảng, hỏi đáp, CTA + JSON-LD (Article, BreadcrumbList, FAQPage). */
import Link from 'next/link';
import SeoHeroArt from '@/components/seo/SeoHeroArt';
import { ArrowRight, BookOpen, ChevronDown, ChevronRight, Clock, Lightbulb } from 'lucide-react';
import { SiteFooter, SiteHeader } from '@/components/landing/SiteChrome';
import { ARTICLE_BY_SLUG } from '@/lib/seo/articles';
import { ARTICLE_CATEGORIES, readingMinutes, type Article } from '@/lib/seo/articleTypes';
import { SEO_PAGE_BY_SLUG } from '@/lib/seo/pages';
import { OG_IMAGE, ORGANIZATION_LD, SITE_NAME, SITE_URL, jsonLd } from '@/lib/seo/site';

const fmt = (d: string) => new Date(`${d}T00:00:00`).toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric' });

function structuredData(a: Article) {
  const url = `${SITE_URL}/cam-nang/${a.slug}`;
  return [
    {
      '@context': 'https://schema.org', '@type': 'Article', '@id': `${url}#article`, mainEntityOfPage: url, headline: a.h1, description: a.description,
      inLanguage: 'vi-VN', datePublished: a.published, dateModified: a.updated, image: `${SITE_URL}${OG_IMAGE.url}`,
      author: { '@type': 'Organization', name: SITE_NAME, url: SITE_URL }, publisher: { '@id': ORGANIZATION_LD['@id'] },
    },
    {
      '@context': 'https://schema.org', '@type': 'BreadcrumbList',
      itemListElement: [
        { '@type': 'ListItem', position: 1, name: 'Trang chủ', item: SITE_URL },
        { '@type': 'ListItem', position: 2, name: 'Cẩm nang', item: `${SITE_URL}/cam-nang` },
        { '@type': 'ListItem', position: 3, name: a.h1, item: url },
      ],
    },
    {
      '@context': 'https://schema.org', '@type': 'FAQPage',
      mainEntity: a.faqs.map(f => ({ '@type': 'Question', name: f.q, acceptedAnswer: { '@type': 'Answer', text: f.a } })),
    },
  ];
}

export default function ArticleView({ article: a }: { article: Article }) {
  const goal = SEO_PAGE_BY_SLUG[a.goal];
  return (
    <main style={{ minHeight: '100vh', overflowX: 'hidden', background: 'var(--bg-surface)' }}>
      {structuredData(a).map((d, i) => <script key={i} type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLd(d) }} />)}
      <SiteHeader />

      <section className="seo-hero lp-tinted" style={{ paddingBottom: 40 }}>
        <div className="seo-hero-inner">
          <nav className="seo-crumbs" aria-label="Breadcrumb">
            <Link href="/">Trang chủ</Link><span aria-hidden="true">/</span><Link href="/cam-nang">Cẩm nang</Link>
            <span aria-hidden="true">/</span><span>{ARTICLE_CATEGORIES[a.category]}</span>
          </nav>
          <h1>{a.h1}</h1>
          <p>{a.lead}</p>
          <div className="article-meta">
            <span><Clock size={14} /> {readingMinutes(a)} phút đọc</span>
            <span>Cập nhật {fmt(a.updated)}</span>
            <span>{SITE_NAME}</span>
          </div>
        </div>
        <SeoHeroArt name="seo-cam-nang" />
      </section>

      <section className="lp-section" style={{ paddingTop: 40 }}>
        <div className="article-layout">
          <nav className="article-toc" aria-label="Mục lục">
            <b>Mục lục</b>
            <ol>{a.blocks.map(b => <li key={b.id}><a href={`#${b.id}`}>{b.h2}</a></li>)}<li><a href="#hoi-dap">Hỏi đáp</a></li></ol>
          </nav>
          <article className="seo-article article-body">
            {a.blocks.map(b => (
              <section key={b.id} id={b.id}>
                <h2>{b.h2}</h2>
                {b.paras?.map((p, i) => <p key={i}>{p}</p>)}
                {b.bullets && <ul>{b.bullets.map(x => <li key={x}>{x}</li>)}</ul>}
                {b.numbered && <ol>{b.numbered.map(x => <li key={x}>{x}</li>)}</ol>}
                {b.table && (
                  <div className="article-table">
                    <table>
                      {b.table.caption && <caption>{b.table.caption}</caption>}
                      <thead><tr>{b.table.head.map(h => <th key={h} scope="col">{h}</th>)}</tr></thead>
                      <tbody>{b.table.rows.map((r, i) => <tr key={i}>{r.map((c, j) => <td key={j}>{c}</td>)}</tr>)}</tbody>
                    </table>
                  </div>
                )}
                {b.after?.map((p, i) => <p key={`a${i}`}>{p}</p>)}
                {b.tip && <aside className="article-tip"><Lightbulb size={18} /><div><b>Mẹo</b><p>{b.tip}</p></div></aside>}
              </section>
            ))}

            <section id="hoi-dap">
              <h2>Hỏi đáp</h2>
              <div className="lp-faq" style={{ maxWidth: 'none' }}>
                {a.faqs.map(f => (
                  <details key={f.q} className="lp-faq-item">
                    <summary>{f.q}<ChevronDown size={20} /></summary>
                    <p>{f.a}</p>
                  </details>
                ))}
              </div>
            </section>

            {goal && (
              <aside className="article-cta">
                <div>
                  <b>{goal.cardTitle} với AI AGENT ENGLISH</b>
                  <p>{goal.cardDesc}</p>
                </div>
                <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                  <Link href="/register" className="btn btn-primary">Học thử miễn phí <ArrowRight size={16} /></Link>
                  <Link href={`/${goal.slug}`} className="btn btn-ghost">Xem chi tiết <ChevronRight size={16} /></Link>
                </div>
              </aside>
            )}
          </article>
        </div>
      </section>

      <section className="lp-section lp-tinted" style={{ paddingTop: 56, paddingBottom: 72 }}>
        <div className="lp-heading" style={{ marginBottom: 28 }}><h2 style={{ fontSize: 'clamp(1.5rem, 3.4vw, 2.1rem)' }}>Bài viết liên quan</h2></div>
        <div className="seo-related">
          {a.related.map(s => ARTICLE_BY_SLUG[s]).filter(Boolean).map(r => (
            <Link key={r.slug} href={`/cam-nang/${r.slug}`} className="lp-card lp-goal">
              <span className="article-cat"><BookOpen size={13} /> {ARTICLE_CATEGORIES[r.category]}</span>
              <h3 style={{ marginTop: 10 }}>{r.h1}</h3>
              <span className="lp-goal-more">Đọc bài <ChevronRight size={15} /></span>
            </Link>
          ))}
        </div>
      </section>

      <SiteFooter />
    </main>
  );
}

/** Hướng dẫn sử dụng · một đối tượng: các bước có ảnh chụp thật, mẹo, hỏi đáp + JSON-LD (Article, BreadcrumbList, FAQPage). */
import Image from 'next/image';
import Link from 'next/link';
import { ArrowRight, BookOpen, ChevronDown, ChevronRight, Lightbulb } from 'lucide-react';
import { SiteFooter, SiteHeader } from '@/components/landing/SiteChrome';
import { SEO_ICONS } from '@/components/seo/seoIcons';
import { GUIDE_BY_SLUG, type Guide, type GuideImage } from '@/lib/seo/guides';
import { ORGANIZATION_LD, SITE_NAME, SITE_URL, jsonLd } from '@/lib/seo/site';

function structuredData(g: Guide) {
  const url = `${SITE_URL}/huong-dan-su-dung/${g.slug}`;
  const first = g.steps.flatMap(s => s.images ?? [])[0];
  return [
    {
      '@context': 'https://schema.org', '@type': 'Article', '@id': `${url}#article`, mainEntityOfPage: url, headline: g.h1, description: g.description,
      inLanguage: 'vi-VN', image: first ? `${SITE_URL}${first.src}` : undefined,
      author: { '@type': 'Organization', name: SITE_NAME, url: SITE_URL }, publisher: { '@id': ORGANIZATION_LD['@id'] },
    },
    {
      '@context': 'https://schema.org', '@type': 'BreadcrumbList',
      itemListElement: [
        { '@type': 'ListItem', position: 1, name: 'Trang chủ', item: SITE_URL },
        { '@type': 'ListItem', position: 2, name: 'Hướng dẫn sử dụng', item: `${SITE_URL}/huong-dan-su-dung` },
        { '@type': 'ListItem', position: 3, name: g.cardTitle, item: url },
      ],
    },
    {
      '@context': 'https://schema.org', '@type': 'FAQPage',
      mainEntity: g.faqs.map(f => ({ '@type': 'Question', name: f.q, acceptedAnswer: { '@type': 'Answer', text: f.a } })),
    },
  ];
}

function Shot({ image, priority }: { image: GuideImage; priority?: boolean }) {
  const [w, h] = image.mobile ? [720, 1558] : [1440, 900];
  return (
    <figure className={`guide-shot${image.mobile ? ' guide-shot-mobile' : ''}`}>
      <a href={image.src} target="_blank" rel="noopener" title="Mở ảnh cỡ lớn">
        <Image src={image.src} alt={image.alt} width={w} height={h} priority={priority}
          sizes={image.mobile ? '(max-width: 600px) 70vw, 300px' : '(max-width: 900px) 100vw, 760px'} />
      </a>
      {image.caption && <figcaption>{image.caption}</figcaption>}
    </figure>
  );
}

export default function GuideView({ guide: g }: { guide: Guide }) {
  const { icon: Icon, colors } = SEO_ICONS[g.icon];
  return (
    <main style={{ minHeight: '100vh', overflowX: 'hidden', background: 'var(--bg-surface)' }}>
      {structuredData(g).map((d, i) => <script key={i} type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLd(d) }} />)}
      <SiteHeader />

      <section className="seo-hero lp-tinted" style={{ paddingBottom: 40 }}>
        <div className="seo-hero-inner">
          <nav className="seo-crumbs" aria-label="Breadcrumb">
            <Link href="/">Trang chủ</Link><span aria-hidden="true">/</span><Link href="/huong-dan-su-dung">Hướng dẫn sử dụng</Link>
            <span aria-hidden="true">/</span><span>{g.cardTitle}</span>
          </nav>
          <span className="lp-icon guide-badge" style={{ background: `linear-gradient(135deg, ${colors[0]}, ${colors[1]})` }}><Icon size={26} color="#fff" /></span>
          <h1>{g.h1}</h1>
          <p>{g.lead}</p>
        </div>
      </section>

      <section className="lp-section" style={{ paddingTop: 40 }}>
        <div className="article-layout">
          <nav className="article-toc" aria-label="Các bước">
            <b>Các bước</b>
            <ol>{g.steps.map(s => <li key={s.id}><a href={`#${s.id}`}>{s.title}</a></li>)}<li><a href="#hoi-dap">Hỏi đáp</a></li></ol>
          </nav>
          <article className="seo-article article-body">
            {g.steps.map((s, si) => {
              const mobiles = s.images?.filter(i => i.mobile) ?? [];
              const wides = s.images?.filter(i => !i.mobile) ?? [];
              return (
                <section key={s.id} id={s.id} className="guide-step">
                  <h2>{s.title}</h2>
                  {s.text.map((p, i) => <p key={i}>{p}</p>)}
                  {s.bullets && <ul>{s.bullets.map(x => <li key={x}>{x}</li>)}</ul>}
                  {wides.map((im, i) => <Shot key={im.src} image={im} priority={si === 0 && i === 0} />)}
                  {mobiles.length > 0 && <div className="guide-shot-row">{mobiles.map(im => <Shot key={im.src} image={im} />)}</div>}
                  {s.tip && <aside className="article-tip"><Lightbulb size={18} /><div><b>Mẹo</b><p>{s.tip}</p></div></aside>}
                </section>
              );
            })}

            <section id="hoi-dap">
              <h2>Hỏi đáp</h2>
              <div className="lp-faq" style={{ maxWidth: 'none' }}>
                {g.faqs.map(f => (
                  <details key={f.q} className="lp-faq-item">
                    <summary>{f.q}<ChevronDown size={20} /></summary>
                    <p>{f.a}</p>
                  </details>
                ))}
              </div>
            </section>

            <aside className="article-cta">
              <div>
                <b>Sẵn sàng bắt đầu?</b>
                <p>Tạo tài khoản miễn phí trong một phút, hoặc học thử ngay không cần đăng ký.</p>
              </div>
              <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                <Link href="/register" className="btn btn-primary">Tạo tài khoản miễn phí <ArrowRight size={16} /></Link>
                <Link href="/cam-nang" className="btn btn-ghost"><BookOpen size={16} /> Cẩm nang học</Link>
              </div>
            </aside>
          </article>
        </div>
      </section>

      <section className="lp-section lp-tinted" style={{ paddingTop: 56, paddingBottom: 72 }}>
        <div className="lp-heading" style={{ marginBottom: 28 }}><h2 style={{ fontSize: 'clamp(1.5rem, 3.4vw, 2.1rem)' }}>Hướng dẫn cho đối tượng khác</h2></div>
        <div className="seo-related">
          {g.related.map(s => GUIDE_BY_SLUG[s]).filter(Boolean).map(r => {
            const { icon: RIcon, colors: rc } = SEO_ICONS[r.icon];
            return (
              <Link key={r.slug} href={`/huong-dan-su-dung/${r.slug}`} className="lp-card lp-goal">
                <span className="lp-icon" style={{ width: 48, height: 48, borderRadius: 14, background: `linear-gradient(135deg, ${rc[0]}, ${rc[1]})` }}><RIcon size={23} color="#fff" /></span>
                <h3>{r.cardTitle}</h3>
                <p>{r.cardDesc}</p>
                <span className="lp-goal-more">Xem hướng dẫn <ChevronRight size={15} /></span>
              </Link>
            );
          })}
        </div>
      </section>

      <SiteFooter />
    </main>
  );
}

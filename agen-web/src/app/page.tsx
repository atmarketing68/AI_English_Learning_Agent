/** Trang chủ (landing): metadata + dữ liệu có cấu trúc ở server, phần giao diện động trong LandingPage. */
import type { Metadata } from 'next';
import LandingPage from '@/components/landing/LandingPage';
import { LANDING_FAQS } from '@/lib/seo/landingFaqs';
import { OG_IMAGE, ORGANIZATION_LD, SITE_DESCRIPTION, SITE_NAME, SITE_URL, jsonLd } from '@/lib/seo/site';

const TITLE = 'AI AGENT ENGLISH — Học tiếng Anh cùng AI Coach cá nhân cho người Việt';

export const metadata: Metadata = {
  title: { absolute: TITLE },
  description: SITE_DESCRIPTION,
  alternates: { canonical: '/' },
  openGraph: { type: 'website', url: '/', title: TITLE, description: SITE_DESCRIPTION, siteName: SITE_NAME, locale: 'vi_VN', images: [OG_IMAGE] },
  twitter: { card: 'summary_large_image', title: TITLE, description: SITE_DESCRIPTION, images: [OG_IMAGE.url] },
};

const STRUCTURED = [
  ORGANIZATION_LD,
  {
    '@context': 'https://schema.org', '@type': 'WebSite', '@id': `${SITE_URL}/#website`, url: SITE_URL, name: SITE_NAME,
    inLanguage: 'vi-VN', publisher: { '@id': ORGANIZATION_LD['@id'] },
  },
  {
    '@context': 'https://schema.org', '@type': 'WebApplication', name: SITE_NAME, url: SITE_URL, description: SITE_DESCRIPTION,
    applicationCategory: 'EducationalApplication', operatingSystem: 'Web, Android, iOS', inLanguage: 'vi-VN',
    offers: { '@type': 'Offer', price: '0', priceCurrency: 'VND', description: 'Gói miễn phí' },
    publisher: { '@id': ORGANIZATION_LD['@id'] },
  },
  {
    '@context': 'https://schema.org', '@type': 'FAQPage',
    mainEntity: LANDING_FAQS.map(f => ({ '@type': 'Question', name: f.q, acceptedAnswer: { '@type': 'Answer', text: f.a } })),
  },
];

export default function HomePage() {
  return (
    <>
      {STRUCTURED.map((d, i) => <script key={i} type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLd(d) }} />)}
      <LandingPage />
    </>
  );
}

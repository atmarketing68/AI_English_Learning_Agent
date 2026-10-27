/**
 * SEO · địa chỉ gốc và thông tin chung của trang công khai.
 * Tên miền chính: https://aiagentenglish.com. Có thể đè bằng `NEXT_PUBLIC_SITE_URL` (vd. khi thử trên tên miền khác).
 */
export const SITE_URL = (process.env.NEXT_PUBLIC_SITE_URL || 'https://aiagentenglish.com').replace(/\/+$/, '');

export const SITE_NAME = 'AI AGENT ENGLISH';
export const SITE_TAGLINE = 'Học tiếng Anh cùng AI Coach cá nhân';
export const SITE_DESCRIPTION =
  'Ứng dụng học tiếng Anh với AI cho người Việt: luyện nói có chấm phát âm, chấm bài viết theo band IELTS/TOEIC, thi thử, lộ trình theo trình độ CEFR và báo cáo cho phụ huynh. Học thử miễn phí, không cần thẻ.';
export const OG_IMAGE = { url: '/og.png', width: 1200, height: 630, alt: 'AI AGENT ENGLISH — Học tiếng Anh cùng AI' };
/** Ngày cập nhật nội dung các trang công khai (sitemap lastmod). */
export const CONTENT_UPDATED = '2026-10-27';

/** JSON for a <script type="application/ld+json"> tag, with "<" escaped (Next.js JSON-LD guide). */
export function jsonLd(data: unknown): string {
  return JSON.stringify(data).replace(/</g, '\\u003c');
}

export const ORGANIZATION_LD = {
  '@context': 'https://schema.org',
  '@type': 'Organization',
  '@id': `${SITE_URL}/#organization`,
  name: SITE_NAME,
  url: SITE_URL,
  logo: `${SITE_URL}/logo.png`,
};

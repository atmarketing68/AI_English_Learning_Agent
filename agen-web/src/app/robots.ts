import type { MetadataRoute } from 'next';
import { SITE_URL } from '@/lib/seo/site';

/** Trang công khai được lập chỉ mục; khu vực sau đăng nhập (nội dung riêng của từng người) thì không. */
const PRIVATE = [
  '/admin', '/dashboard', '/curriculum', '/learn', '/vocabulary', '/practice', '/progress', '/profile', '/upgrade', '/league',
  '/tracks', '/shop', '/blitz', '/friends', '/classes', '/exams', '/tutor', '/plan', '/listen', '/club', '/review', '/onboarding',
  '/placement', '/parent', '/teacher', '/receipt', '/certificate', '/unsubscribe',
];

export default function robots(): MetadataRoute.Robots {
  return {
    rules: { userAgent: '*', allow: '/', disallow: PRIVATE },
    sitemap: `${SITE_URL}/sitemap.xml`,
    host: SITE_URL,
  };
}

import type { MetadataRoute } from 'next';

export default function manifest(): MetadataRoute.Manifest {
  return {
    id: '/',
    name: 'AI AGENT ENGLISH',
    short_name: 'AI English',
    description: 'Học tiếng Anh cùng AI Coach cá nhân — mỗi ngày 15 phút.',
    lang: 'vi',
    start_url: '/dashboard?source=pwa',
    scope: '/',
    display: 'standalone',
    orientation: 'portrait',
    background_color: '#F5F5F7',
    theme_color: '#F5F5F7',
    categories: ['education'],
    icons: [
      { src: '/icons/icon-192.png', sizes: '192x192', type: 'image/png', purpose: 'any' },
      { src: '/icons/icon-512.png', sizes: '512x512', type: 'image/png', purpose: 'any' },
      { src: '/icons/maskable-192.png', sizes: '192x192', type: 'image/png', purpose: 'maskable' },
      { src: '/icons/maskable-512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
    ],
    shortcuts: [
      { name: 'Ôn tập hôm nay', short_name: 'Ôn tập', url: '/review', icons: [{ src: '/icons/icon-192.png', sizes: '192x192' }] },
      { name: 'Học bài mới', short_name: 'Học', url: '/learn', icons: [{ src: '/icons/icon-192.png', sizes: '192x192' }] },
      { name: 'Sổ từ vựng', short_name: 'Sổ từ', url: '/vocabulary', icons: [{ src: '/icons/icon-192.png', sizes: '192x192' }] },
    ],
  };
}

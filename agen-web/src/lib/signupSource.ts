/**
 * G14 · Nguồn đăng ký (first-touch): utm_source / ?ref= trên link, nếu không có thì tên miền trang giới thiệu.
 * Lưu một lần trong trình duyệt, gửi kèm khi đăng ký hoặc học thử để admin xem hiệu quả từng kênh.
 */
const KEY = 'agen-src';

export function captureSignupSource(): void {
  if (typeof window === 'undefined') return;
  try {
    if (localStorage.getItem(KEY)) return;
    const params = new URLSearchParams(window.location.search);
    let source = params.get('utm_source') || params.get('ref') || '';
    if (!source && document.referrer) {
      const host = new URL(document.referrer).hostname.replace(/^www\./, '');
      if (host && host !== window.location.hostname.replace(/^www\./, '')) source = host;
    }
    if (source) localStorage.setItem(KEY, source.slice(0, 60));
  } catch { /* private mode / bad referrer */ }
}

export function signupSource(): string | undefined {
  try { return localStorage.getItem(KEY) || undefined; } catch { return undefined; }
}

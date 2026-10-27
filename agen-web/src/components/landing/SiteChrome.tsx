/** Header + footer of the public pages (landing and SEO pages). Plain links, no client state. */
import Link from 'next/link';
import { Menu } from 'lucide-react';
import Logo from '@/components/ui/Logo';
import { SEO_PAGES } from '@/lib/seo/pages';

export function SiteHeader({ home = false }: { home?: boolean }) {
  const anchor = (id: string) => (home ? `#${id}` : `/#${id}`);
  const links = [
    { href: anchor('muc-tieu'), label: 'Mục tiêu học' },
    { href: '/cam-nang', label: 'Cẩm nang' },
    { href: '/huong-dan-su-dung', label: 'Hướng dẫn' },
    { href: anchor('bang-gia'), label: 'Bảng giá' },
    { href: anchor('hoi-dap'), label: 'Hỏi đáp' },
  ];
  return (
    <header className="lp-nav">
      <div className="lp-nav-inner">
        <Link href="/" aria-label="AI AGENT ENGLISH — trang chủ" style={{ display: 'inline-flex', opacity: 1 }}><Logo size={30} /></Link>
        <nav className="lp-nav-links" aria-label="Điều hướng trang">
          {links.map(l => <a key={l.href} href={l.href}>{l.label}</a>)}
        </nav>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16, fontSize: '0.88rem' }}>
          <Link href="/login" className="lp-nav-login" style={{ color: 'var(--text-secondary)' }}>Đăng nhập</Link>
          <Link href="/register" className="btn btn-primary btn-sm" style={{ whiteSpace: 'nowrap' }}>Học miễn phí</Link>
          {/* Phone: the same links in a no-JS dropdown */}
          <details className="lp-nav-menu">
            <summary aria-label="Mở menu"><Menu size={20} /></summary>
            <nav aria-label="Menu">
              {links.map(l => <a key={l.href} href={l.href}>{l.label}</a>)}
              <Link href="/login">Đăng nhập</Link>
            </nav>
          </details>
        </div>
      </div>
    </header>
  );
}

export function SiteFooter({ home = false }: { home?: boolean }) {
  const anchor = (id: string) => (home ? `#${id}` : `/#${id}`);
  return (
    <footer className="lp-footer">
      <div className="lp-footer-top">
        <div style={{ maxWidth: 360 }}>
          <Logo size={32} />
          <p>AI English Learning Agent — người thầy, người bạn và huấn luyện viên tiếng Anh đồng hành lâu dài.</p>
        </div>
        <div className="lp-footer-cols">
          <div>
            <b>Học theo mục tiêu</b>
            {SEO_PAGES.map(p => <Link key={p.slug} href={`/${p.slug}`}>{p.cardTitle}</Link>)}
          </div>
          <div>
            <b>Tài nguyên</b>
            <Link href="/cam-nang">Cẩm nang học</Link>
            <Link href="/huong-dan-su-dung">Hướng dẫn sử dụng</Link>
          </div>
          <div>
            <b>Sản phẩm</b>
            <a href={anchor('ky-nang')}>4 kỹ năng</a>
            <a href={anchor('tinh-nang')}>Tính năng</a>
            <a href={anchor('bang-gia')}>Bảng giá</a>
          </div>
          <div>
            <b>Tài khoản</b>
            <Link href="/register">Đăng ký</Link>
            <Link href="/login">Đăng nhập</Link>
            <a href={anchor('hoi-dap')}>Hỏi đáp</a>
          </div>
        </div>
      </div>
      <div className="lp-footer-bottom">
        <span>© {new Date().getFullYear()} AI AGENT ENGLISH. Bảo lưu mọi quyền.</span>
        <span>Học tiếng Anh cùng AI</span>
      </div>
    </footer>
  );
}

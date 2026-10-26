'use client';

import Image from 'next/image';
import Link from 'next/link';
import { motion } from 'framer-motion';
import {
  ArrowRight, ChevronRight, Brain, Mic, TrendingUp, Flame, Users, Route,
  Check, type LucideIcon,
} from 'lucide-react';
import Logo from '@/components/ui/Logo';

const STATS = [
  { value: '1,247', label: 'Học viên đang học' },
  { value: '4.9', label: 'Đánh giá trung bình' },
  { value: '98%', label: 'Hài lòng sau 30 ngày' },
];

const FEATURES: { icon: LucideIcon; title: string; desc: string }[] = [
  { icon: Brain, title: 'AI Coach cá nhân', desc: 'Hệ thống AI đa tác tử phân tích điểm mạnh, điểm yếu và tạo bài học riêng — như gia sư 1-1 bản xứ.' },
  { icon: Mic, title: 'Luyện nói với AI', desc: 'Roleplay tình huống thực tế. Nhận phản hồi chi tiết về ngữ pháp và gợi ý cải thiện ngay tức thì.' },
  { icon: TrendingUp, title: 'Thích ứng thông minh', desc: 'Độ khó tự động điều chỉnh theo kết quả thực tế. Học đúng thứ bạn cần, không lãng phí thời gian.' },
  { icon: Flame, title: 'Động lực mỗi ngày', desc: 'XP, chuỗi ngày học, thành tựu và bảng xếp hạng giúp bạn duy trì thói quen.' },
  { icon: Users, title: 'Báo cáo phụ huynh', desc: 'Báo cáo hằng tuần bằng ngôn ngữ dễ hiểu, giúp phụ huynh biết con cần cải thiện điều gì.' },
  { icon: Route, title: 'Lộ trình CEFR riêng', desc: 'Từ bài kiểm tra đầu vào đến lộ trình chuẩn CEFR. Biết chính xác cần học gì, theo thứ tự nào.' },
];

const TESTIMONIALS = [
  { name: 'Minh Anh', meta: '16 tuổi · B2', quote: 'AGEN giúp mình từ B1 lên B2 chỉ trong 2 tháng. Phần luyện nói với AI là phần mình thích nhất.' },
  { name: 'Bố của Hùng', meta: 'Phụ huynh', quote: 'Báo cáo hằng tuần rất rõ ràng. Biết chính xác con cần cải thiện kỹ năng nào, không phải đoán mò.' },
  { name: 'Lan Phương', meta: '28 tuổi · B1', quote: '15 phút mỗi ngày với AGEN hiệu quả hơn cả buổi học 2 tiếng. Rất hợp với người đi làm.' },
];

const STEPS = [
  { n: '1', title: 'Tạo tài khoản miễn phí', desc: 'Chỉ cần email — không cần thẻ tín dụng.' },
  { n: '2', title: 'Kiểm tra đầu vào 5 phút', desc: 'AGEN xác định trình độ hiện tại của bạn.' },
  { n: '3', title: 'Nhận lộ trình và học ngay', desc: 'Bài học được tạo riêng theo mục tiêu của bạn.' },
];

const reveal = {
  initial: { opacity: 0, y: 24 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, margin: '-60px' },
  transition: { duration: 0.6, ease: [0.25, 0.1, 0.25, 1] as const },
};

function SectionHeading({ eyebrow, title, sub }: { eyebrow: string; title: string; sub?: string }) {
  return (
    <motion.div {...reveal} style={{ textAlign: 'center', marginBottom: 56 }}>
      <div className="eyebrow" style={{ marginBottom: 10 }}>{eyebrow}</div>
      <h2 style={{ fontSize: 'clamp(2rem, 4.5vw, 3rem)', fontWeight: 700, letterSpacing: '-0.03em' }}>{title}</h2>
      {sub && <p style={{ fontSize: '1.1rem', maxWidth: 560, margin: '14px auto 0' }}>{sub}</p>}
    </motion.div>
  );
}

export default function HomePage() {
  return (
    <main style={{ minHeight: '100vh', overflowX: 'hidden', background: 'var(--bg-surface)' }}>

      {/* ─── NAV ──────────────────────────────────────────────────────── */}
      <header style={{
        position: 'sticky', top: 0, zIndex: 100, height: 52,
        background: 'var(--bg-nav)', backdropFilter: 'saturate(180%) blur(20px)', WebkitBackdropFilter: 'saturate(180%) blur(20px)',
        borderBottom: '1px solid var(--border-subtle)',
      }}>
        <div style={{ height: '100%', padding: '0 var(--page-gutter)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Link href="/" aria-label="AGEN — trang chủ" style={{ display: 'inline-flex', opacity: 1 }}><Logo size={28} /></Link>
          <nav style={{ display: 'flex', alignItems: 'center', gap: 20, fontSize: '0.85rem' }}>
            <Link href="/login" style={{ color: 'var(--text-secondary)' }}>Đăng nhập</Link>
            <Link href="/register" className="btn btn-primary btn-sm" style={{ padding: '6px 14px', fontSize: '0.8rem' }}>Bắt đầu</Link>
          </nav>
        </div>
      </header>

      {/* ─── HERO ─────────────────────────────────────────────────────── */}
      <section className="hero">
        <div className="hero-media">
          <Image
            src="/hero-banner.webp"
            alt="Robot AI Coach của AGEN đọc sách tiếng Anh, xung quanh là biểu tượng luyện nghe, nói, viết"
            fill
            priority
            sizes="100vw"
            style={{ objectFit: 'cover' }}
          />
        </div>
        <motion.div
          className="hero-content"
          initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: [0.25, 0.1, 0.25, 1] }}
        >
          <div className="hero-eyebrow">AI English Learning Agent</div>
          <h1><span className="nowrap">Học tiếng Anh</span> <span className="nowrap">cùng AI.</span><br /><span className="nowrap">Theo cách của</span> <span className="nowrap">riêng bạn.</span></h1>
          <p>
            Người thầy, người bạn và huấn luyện viên tiếng Anh — đồng hành từ nền tảng đến nâng cao, theo đúng tốc độ của bạn.
          </p>
          <div className="hero-actions">
            <Link href="/register" className="btn btn-primary btn-lg">Bắt đầu học miễn phí</Link>
            <Link href="/login" className="hero-link">
              Đăng nhập <ChevronRight size={18} />
            </Link>
          </div>
        </motion.div>
      </section>

      {/* ─── STATS ────────────────────────────────────────────────────── */}
      <section style={{ padding: '56px var(--page-gutter)', borderBottom: '1px solid var(--border-subtle)' }}>
        <div style={{ display: 'flex', gap: 'clamp(32px, 8vw, 120px)', justifyContent: 'center', flexWrap: 'wrap', textAlign: 'center' }}>
          {STATS.map(s => (
            <div key={s.label}>
              <div style={{ fontSize: 'clamp(1.8rem, 4vw, 2.5rem)', fontWeight: 700, letterSpacing: '-0.03em', color: 'var(--text-primary)' }}>{s.value}</div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: 2 }}>{s.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* ─── FEATURES ─────────────────────────────────────────────────── */}
      <section style={{ padding: '100px var(--page-gutter)', background: 'var(--bg-base)' }}>
        <div>
          <SectionHeading eyebrow="Tất cả trong một" title="Vì sao chọn AGEN?" sub="Mọi thứ bạn cần để tiến bộ đều đặn — gói gọn trong một ứng dụng." />
          <div className="grid-3" style={{ gap: 20 }}>
            {FEATURES.map(({ icon: Icon, title, desc }, i) => (
              <motion.div
                key={title}
                {...reveal}
                transition={{ ...reveal.transition, delay: (i % 3) * 0.06 }}
                style={{ padding: 32, borderRadius: 24, background: 'var(--bg-surface)' }}
              >
                <Icon size={30} strokeWidth={1.6} color="var(--agen-primary)" style={{ marginBottom: 20 }} />
                <h3 style={{ fontSize: '1.2rem', marginBottom: 8 }}>{title}</h3>
                <p style={{ fontSize: '0.95rem', lineHeight: 1.55 }}>{desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── HOW IT WORKS ─────────────────────────────────────────────── */}
      <section style={{ padding: '100px var(--page-gutter)' }}>
        <div>
          <SectionHeading eyebrow="Bắt đầu trong 30 giây" title="Cách hoạt động" />
          <div className="grid-3" style={{ gap: 40 }}>
            {STEPS.map((step, i) => (
              <motion.div key={step.n} {...reveal} transition={{ ...reveal.transition, delay: i * 0.08 }} style={{ textAlign: 'center' }}>
                <div style={{
                  width: 48, height: 48, borderRadius: '50%', margin: '0 auto 20px',
                  border: '1.5px solid var(--text-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontWeight: 600, fontSize: '1.1rem',
                }}>
                  {step.n}
                </div>
                <h3 style={{ fontSize: '1.2rem', marginBottom: 8 }}>{step.title}</h3>
                <p style={{ fontSize: '0.95rem', maxWidth: 260, margin: '0 auto' }}>{step.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── TESTIMONIALS ─────────────────────────────────────────────── */}
      <section style={{ padding: '100px var(--page-gutter)', background: 'var(--bg-base)' }}>
        <div>
          <SectionHeading eyebrow="Câu chuyện thật" title="Học viên nói gì?" />
          <div className="grid-3" style={{ gap: 20 }}>
            {TESTIMONIALS.map((t, i) => (
              <motion.figure
                key={t.name}
                {...reveal}
                transition={{ ...reveal.transition, delay: i * 0.06 }}
                style={{ padding: 32, borderRadius: 24, background: 'var(--bg-surface)', display: 'flex', flexDirection: 'column', gap: 24 }}
              >
                <blockquote style={{ fontSize: '1.05rem', lineHeight: 1.55, color: 'var(--text-primary)', flex: 1 }}>
                  “{t.quote}”
                </blockquote>
                <figcaption>
                  <div style={{ fontWeight: 600, fontSize: '0.95rem' }}>{t.name}</div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>{t.meta}</div>
                </figcaption>
              </motion.figure>
            ))}
          </div>
        </div>
      </section>

      {/* ─── CTA BOTTOM ───────────────────────────────────────────────── */}
      <section style={{ padding: '120px var(--page-gutter)', textAlign: 'center' }}>
        <motion.div {...reveal} style={{ maxWidth: 680, margin: '0 auto' }}>
          <h2 style={{ fontSize: 'clamp(2rem, 5vw, 3.25rem)', fontWeight: 700, letterSpacing: '-0.035em', marginBottom: 16 }}>
            Sẵn sàng bắt đầu?
          </h2>
          <p style={{ fontSize: '1.15rem', maxWidth: 480, margin: '0 auto 36px' }}>
            Chỉ mất 5 phút để kiểm tra đầu vào và nhận lộ trình học của riêng bạn.
          </p>
          <Link href="/register" className="btn btn-primary btn-lg">
            Tạo tài khoản miễn phí <ArrowRight size={18} />
          </Link>
          <div style={{ marginTop: 28, display: 'flex', gap: 24, justifyContent: 'center', flexWrap: 'wrap', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            {['Không cần thẻ tín dụng', 'Bắt đầu ngay hôm nay', 'Hủy bất cứ lúc nào'].map(x => (
              <span key={x} style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                <Check size={14} /> {x}
              </span>
            ))}
          </div>
        </motion.div>
      </section>

      {/* ─── FOOTER ───────────────────────────────────────────────────── */}
      <footer style={{ background: 'var(--bg-base)', borderTop: '1px solid var(--border-subtle)', padding: '24px var(--page-gutter)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12, fontSize: '0.78rem', color: 'var(--text-muted)' }}>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 10 }}><Logo size={20} wordmark={false} /> © {new Date().getFullYear()} AGEN. Bảo lưu mọi quyền.</span>
          <span>AI English Learning Agent</span>
        </div>
      </footer>
    </main>
  );
}

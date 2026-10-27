'use client';

import Image from 'next/image';
import Link from 'next/link';
import { useEffect, useRef, useState } from 'react';
import { motion, useInView } from 'framer-motion';
import {
  ArrowRight, BadgeCheck, BookOpen, Brain, Briefcase, Check, ChevronDown, ChevronRight,
  ClipboardCheck, Clock, Coffee, Crown, Flame, GraduationCap, Headphones, Hotel,
  MessageCircle, Mic, PenLine, Plane, Presentation, Rocket, Route, ShieldCheck,
  Smartphone, Sparkles, Target, TrendingUp, Trophy, UserPlus, Users, Utensils, Zap,
  type LucideIcon,
} from 'lucide-react';
import GuestTrialButton from '@/components/GuestTrialButton';
import HeroScene3D from '@/components/landing/HeroScene3D';
import { SiteFooter, SiteHeader } from '@/components/landing/SiteChrome';
import { LANDING_FAQS as FAQS } from '@/lib/seo/landingFaqs';
import { SEO_PAGES, type SeoIcon } from '@/lib/seo/pages';
import { SEO_ICONS } from '@/components/seo/seoIcons';

// ─── Palette for icon tiles ──────────────────────────────────────────────────
const G = {
  blue:   ['#2F80FF', '#06B6D4'],
  pink:   ['#EC4899', '#F97316'],
  green:  ['#10B981', '#14B8A6'],
  purple: ['#8B5CF6', '#6366F1'],
  orange: ['#F59E0B', '#F97316'],
  sky:    ['#0EA5E9', '#2563EB'],
} as const;
type Tone = keyof typeof G;

// ─── Content ─────────────────────────────────────────────────────────────────
const STATS: { value: number; decimals?: number; suffix?: string; label: string; icon: LucideIcon; tone: Tone }[] = [
  { value: 4, label: 'Kỹ năng Nghe – Nói – Đọc – Viết trong một lộ trình', icon: Target, tone: 'blue' },
  { value: 10, suffix: ' phút', label: 'Kiểm tra trình độ, có lộ trình riêng ngay', icon: Clock, tone: 'orange' },
  { value: 24, suffix: '/7', label: 'Gia sư AI Bo giải đáp bằng tiếng Việt', icon: MessageCircle, tone: 'pink' },
];

const SKILLS: { icon: LucideIcon; tone: Tone; title: string; desc: string; img: string }[] = [
  { icon: Headphones, tone: 'sky', title: 'Listening', desc: 'Nghe hội thoại thật với giọng đọc tự nhiên, kèm transcript.', img: 'skill-listening' },
  { icon: Mic, tone: 'pink', title: 'Speaking', desc: 'Nhập vai cùng AI, được sửa câu và gợi ý ngay khi nói.', img: 'skill-speaking' },
  { icon: BookOpen, tone: 'green', title: 'Reading', desc: 'Bài đọc theo trình độ, từ vựng nổi bật và câu hỏi hiểu bài.', img: 'skill-reading' },
  { icon: PenLine, tone: 'purple', title: 'Writing', desc: 'Viết đoạn văn, email và nhận chấm điểm chi tiết từng lỗi.', img: 'skill-writing' },
];

const FEATURES: { icon: LucideIcon; tone: Tone; title: string; desc: string; img?: string }[] = [
  { icon: TrendingUp, tone: 'green', title: 'Thích ứng thông minh', desc: 'Độ khó tự điều chỉnh theo kết quả thực tế. Học đúng thứ bạn cần.', img: 'feature-adaptive' },
  { icon: Flame, tone: 'orange', title: 'Động lực mỗi ngày', desc: 'XP, chuỗi ngày học, thành tựu và bảng xếp hạng giữ bạn đều đặn.', img: 'feature-motivation' },
  { icon: Users, tone: 'purple', title: 'Báo cáo phụ huynh', desc: 'Báo cáo hằng tuần dễ hiểu, biết rõ con cần cải thiện điều gì.', img: 'feature-parent' },
];

const LEVELS = ['Pre-A1', 'A1', 'A2', 'B1', 'B2'];

const TOPICS: { icon: LucideIcon; label: string }[] = [
  { icon: Coffee, label: 'Gọi món ở quán cà phê' },
  { icon: Plane, label: 'Làm thủ tục sân bay' },
  { icon: Briefcase, label: 'Phỏng vấn xin việc' },
  { icon: Hotel, label: 'Nhận phòng khách sạn' },
  { icon: Presentation, label: 'Thuyết trình công việc' },
  { icon: Utensils, label: 'Đặt bàn nhà hàng' },
  { icon: GraduationCap, label: 'Luyện thi IELTS, TOEIC' },
  { icon: MessageCircle, label: 'Giao tiếp hằng ngày' },
];

const STEPS: { icon: LucideIcon; tone: Tone; title: string; desc: string; img: string }[] = [
  { icon: UserPlus, tone: 'blue', title: 'Học thử hoặc tạo tài khoản', desc: 'Học thử ngay không cần đăng ký; lưu tài khoản bằng email khi muốn giữ tiến bộ.', img: 'step-1' },
  { icon: ClipboardCheck, tone: 'purple', title: 'Kiểm tra đầu vào 8 phút', desc: '14 câu hỏi về đọc, nghe và nói để AI AGENT ENGLISH xác định đúng trình độ của bạn.', img: 'step-2' },
  { icon: Rocket, tone: 'pink', title: 'Nhận lộ trình và học ngay', desc: 'Bài học được tạo riêng theo mục tiêu và thời gian của bạn.', img: 'step-3' },
];

// Who it is for — each card opens the matching usage guide (no invented testimonials or numbers on the landing page).
const AUDIENCES: { slug: string; icon: SeoIcon; title: string; desc: string }[] = [
  { slug: 'nguoi-hoc', icon: 'talk', title: 'Người học & người đi làm', desc: 'Lộ trình theo trình độ, 15 phút mỗi ngày, luyện nói với AI, chấm viết theo band và thi thử IELTS/TOEIC.' },
  { slug: 'hoc-sinh', icon: 'kids', title: 'Học sinh', desc: 'Giao diện vui cùng Bo: đá quý, Blitz 60 giây, giải đấu tuần — tạo thói quen học mỗi ngày.' },
  { slug: 'phu-huynh', icon: 'ielts', title: 'Phụ huynh', desc: 'Liên kết tài khoản của con, báo cáo hằng tuần dễ hiểu, được nhắc khi con nghỉ học.' },
  { slug: 'giao-vien', icon: 'class', title: 'Giáo viên & trung tâm', desc: 'Tạo lớp, giao bài và bài kiểm tra, xem tiến bộ từng học viên, in bảng điểm.' },
];

const PLANS = [
  {
    name: 'Miễn phí', price: '0₫', period: 'mãi mãi', highlight: false, cta: 'Bắt đầu miễn phí',
    features: ['3 bài học AI mỗi ngày', 'Luyện nói roleplay với AI', 'Luyện viết và chấm điểm AI', 'Bài kiểm tra đầu vào', 'XP, chuỗi ngày học, thành tựu'],
  },
  {
    name: 'Premium', price: '67K₫', period: '/tháng · gói 12 tháng', highlight: true, cta: 'Dùng thử 7 ngày',
    features: ['Mọi thứ trong gói Miễn phí', 'Bài học không giới hạn', 'Báo cáo tiến bộ cho phụ huynh', 'Lộ trình IELTS / TOEIC / phỏng vấn', 'Chấm viết theo band IELTS/TOEIC'],
  },
  {
    name: 'Gia đình', price: '124K₫', period: '/tháng · gói 12 tháng · tối đa 4 con', highlight: false, cta: 'Tạo tài khoản phụ huynh',
    features: ['Một lần thanh toán cho cả nhà', 'Mỗi con đều là Premium', 'Báo cáo tuần + cảnh báo nghỉ học qua email', 'Báo cáo PDF để in', 'Giao diện vui nhộn cho bé, chuyên nghiệp cho người lớn'],
  },
];


// ─── Building blocks ─────────────────────────────────────────────────────────
const EASE = [0.25, 0.1, 0.25, 1] as const;
const reveal = {
  initial: { opacity: 0, y: 28 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, margin: '-60px' },
  transition: { duration: 0.7, ease: EASE },
};
const stagger = (i: number) => ({ ...reveal, transition: { ...reveal.transition, delay: i * 0.08 } });

function IconTile({ icon: Icon, tone, size = 52 }: { icon: LucideIcon; tone: Tone; size?: number }) {
  const [a, b] = G[tone];
  return (
    <span
      className="lp-icon"
      style={{
        width: size, height: size, borderRadius: size * 0.3,
        background: `linear-gradient(135deg, ${a}, ${b})`,
        boxShadow: `0 10px 24px -8px ${a}99`,
      }}
    >
      <Icon size={size * 0.48} strokeWidth={2} color="#fff" />
    </span>
  );
}

function Media({ name, children }: { name: string; children?: React.ReactNode }) {
  return (
    <div className="lp-media">
      <Image src={`/img/${name}.webp`} alt="" fill sizes="(max-width: 700px) 90vw, 360px" />
      {children}
    </div>
  );
}

function SectionHeading({ eyebrow, title, sub, icon: Icon }: { eyebrow: string; title: string; sub?: string; icon: LucideIcon }) {
  return (
    <motion.div {...reveal} className="lp-heading">
      <span className="lp-eyebrow"><Icon size={14} /> {eyebrow}</span>
      <h2>{title}</h2>
      {sub && <p>{sub}</p>}
    </motion.div>
  );
}

/** Counts up from 0 the first time the number scrolls into view. */
function CountUp({ value, decimals = 0, suffix = '' }: { value: number; decimals?: number; suffix?: string }) {
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true, margin: '-40px' });
  const [n, setN] = useState(0);

  useEffect(() => {
    if (!inView) return;
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    let raf = 0;
    const start = performance.now();
    const tick = (t: number) => {
      const p = reduce ? 1 : Math.min(1, (t - start) / 1400);
      setN(value * (1 - Math.pow(1 - p, 3)));
      if (p < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [inView, value]);

  return <span ref={ref}>{n.toLocaleString('en-US', { minimumFractionDigits: decimals, maximumFractionDigits: decimals })}{suffix}</span>;
}

/** Mini chat mock shown inside the AI Coach bento card. */
function ChatMock() {
  return (
    <div className="lp-chat" aria-hidden="true">
      <div className="lp-bubble lp-bubble-ai">Hi! What would you like to order today?</div>
      <div className="lp-bubble lp-bubble-me">I want a coffee, please.</div>
      <div className="lp-bubble lp-bubble-tip"><Sparkles size={13} /> Lịch sự hơn: <b>&ldquo;I&apos;d like a coffee, please.&rdquo;</b></div>
    </div>
  );
}

/** Animated voice waveform for the speaking bento card. */
function Waveform() {
  return (
    <div className="lp-wave" aria-hidden="true">
      {Array.from({ length: 28 }).map((_, i) => (
        <span key={i} style={{ animationDelay: `${(i % 7) * 0.12}s`, height: `${30 + ((i * 37) % 60)}%` }} />
      ))}
    </div>
  );
}

// ─── Page ────────────────────────────────────────────────────────────────────
export default function LandingPage() {
  return (
    <main style={{ minHeight: '100vh', overflowX: 'hidden', background: 'var(--bg-surface)' }}>
      <SiteHeader home />

      {/* ─── HERO ─────────────────────────────────────────────────────── */}
      <section className="lp-hero">
        <span className="lp-hero-orb lp-hero-orb-a" aria-hidden="true" />
        <span className="lp-hero-orb lp-hero-orb-b" aria-hidden="true" />
        <span className="lp-hero-orb lp-hero-orb-c" aria-hidden="true" />
        <div className="lp-hero-inner">
          <motion.div
            className="lp-hero-copy"
            initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, ease: EASE }}
          >
            <span className="hero-badge"><Sparkles size={14} /> AI Coach tiếng Anh cá nhân cho người Việt</span>
            <h1 className="lp-hero-title"><span className="lp-hero-title-main">Học tiếng Anh cùng AI</span><span className="lp-hero-title-sub">Theo cách của riêng bạn.</span></h1>
            <p>
              Người thầy, người bạn và huấn luyện viên tiếng Anh — đồng hành từ nền tảng đến nâng cao, theo đúng tốc độ của bạn.
            </p>
            <div className="hero-actions">
              <Link href="/register" className="btn btn-primary btn-lg btn-shine">
                Bắt đầu học miễn phí <ArrowRight size={18} />
              </Link>
              <GuestTrialButton className="btn btn-lg hero-guest-btn" label="Học thử ngay" />
              <Link href="/login" className="hero-link">
                Đăng nhập <ChevronRight size={18} />
              </Link>
            </div>
            <div className="hero-trust">
              <span className="lp-icon" style={{ width: 40, height: 40, borderRadius: 12, background: `linear-gradient(135deg, ${G.green[0]}, ${G.green[1]})` }} aria-hidden="true">
                <ShieldCheck size={20} color="#fff" />
              </span>
              <div>
                <div className="stars"><b>Miễn phí để bắt đầu</b></div>
                <div className="hero-trust-text">Học thử ngay, không cần đăng ký</div>
              </div>
            </div>
          </motion.div>

          {/* 3D "knowledge universe" scene */}
          <motion.div
            className="lp-hero-scene"
            initial={{ opacity: 0, scale: 0.92 }} animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 1.1, ease: EASE, delay: 0.1 }}
          >
            <HeroScene3D />
          </motion.div>
        </div>
      </section>

      {/* ─── STATS ────────────────────────────────────────────────────── */}
      <section className="lp-section lp-stats">
        <div className="grid-3" style={{ gap: 20 }}>
          {STATS.map((s, i) => (
            <motion.div key={s.label} {...stagger(i)} className="lp-card lp-stat" style={{ '--i': i } as React.CSSProperties}>
              <IconTile icon={s.icon} tone={s.tone} size={48} />
              <div>
                <div className="lp-stat-value"><CountUp value={s.value} decimals={s.decimals} suffix={s.suffix} /></div>
                <div className="lp-stat-label">{s.label}</div>
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ─── 4 SKILLS ─────────────────────────────────────────────────── */}
      <section id="ky-nang" className="lp-section lp-tinted">
        <SectionHeading icon={Target} eyebrow="4 kỹ năng · 1 lộ trình" title="Giỏi đều cả nghe, nói, đọc, viết" sub="Mỗi ngày một bài học ngắn, kết hợp đủ 4 kỹ năng để bạn tiến bộ toàn diện." />
        <div className="grid-4" style={{ gap: 20 }}>
          {SKILLS.map((s, i) => (
            <motion.div key={s.title} {...stagger(i)} className="lp-card lp-skill" style={{ ['--tone' as string]: G[s.tone][0] }}>
              <Media name={s.img}><span className="lp-media-icon"><IconTile icon={s.icon} tone={s.tone} size={44} /></span></Media>
              <h3>{s.title}</h3>
              <p>{s.desc}</p>
              <span className="lp-skill-glow" aria-hidden="true" />
            </motion.div>
          ))}
        </div>
      </section>

      {/* ─── FEATURES (bento) ─────────────────────────────────────────── */}
      <section id="tinh-nang" className="lp-section">
        <SectionHeading icon={Zap} eyebrow="Tất cả trong một" title="Vì sao học viên chọn AI AGENT ENGLISH?" sub="Mọi thứ bạn cần để tiến bộ đều đặn — gói gọn trong một ứng dụng." />
        <div className="lp-bento">
          <motion.div {...stagger(0)} className="lp-card lp-bento-wide lp-bento-coach">
            <div>
              <IconTile icon={Brain} tone="blue" />
              <h3>AI Coach cá nhân 1-1</h3>
              <p>Hệ thống AI đa tác tử phân tích điểm mạnh, điểm yếu của bạn và tạo bài học riêng — như có gia sư bản xứ bên cạnh mọi lúc.</p>
              <ul className="lp-checks">
                <li><Check size={16} /> Sửa lỗi ngay trong câu trả lời</li>
                <li><Check size={16} /> Gợi ý cách nói tự nhiên hơn</li>
                <li><Check size={16} /> Giải thích bằng tiếng Việt</li>
              </ul>
            </div>
            <ChatMock />
          </motion.div>

          <motion.div {...stagger(1)} className="lp-card lp-bento-speak">
            <IconTile icon={Mic} tone="pink" />
            <h3>Luyện nói không ngại</h3>
            <p>Nhập vai tình huống thật. Nhấn giữ để nói, AI phản hồi ngay.</p>
            <Waveform />
          </motion.div>

          {FEATURES.map((f, i) => (
            <motion.div key={f.title} {...stagger(i + 2)} className="lp-card lp-feature">
              <IconTile icon={f.icon} tone={f.tone} />
              <h3>{f.title}</h3>
              <p>{f.desc}</p>
              {f.img && <Media name={f.img} />}
            </motion.div>
          ))}

          <motion.div {...stagger(5)} className="lp-card lp-bento-wide lp-bento-route">
            <div>
              <IconTile icon={Route} tone="sky" />
              <h3>Lộ trình CEFR của riêng bạn</h3>
              <p>Bắt đầu từ đúng trình độ sau bài kiểm tra đầu vào, rồi mở khoá từng chặng theo chuẩn CEFR.</p>
            </div>
            <div className="lp-levels" aria-hidden="true">
              <div className="lp-levels-track">
                <motion.span
                  className="lp-levels-fill"
                  initial={{ width: '0%' }}
                  whileInView={{ width: '62%' }}
                  viewport={{ once: true }}
                  transition={{ duration: 1.6, ease: EASE, delay: 0.3 }}
                />
              </div>
              <div className="lp-levels-row">
                {LEVELS.map((l, i) => (
                  <span key={l} className={i <= 2 ? 'done' : i === 3 ? 'current' : ''}>{l}</span>
                ))}
              </div>
            </div>
          </motion.div>

          <motion.div {...stagger(6)} className="lp-card lp-feature">
            <IconTile icon={Smartphone} tone="blue" />
            <h3>Học mọi lúc, mọi nơi</h3>
            <p>Chỉ cần trình duyệt trên điện thoại hoặc máy tính. Mỗi ngày 5–30 phút là đủ.</p>
            <Media name="feature-anywhere" />
          </motion.div>
        </div>
      </section>

      {/* ─── TOPICS MARQUEE ───────────────────────────────────────────── */}
      <section className="lp-marquee-wrap" aria-label="Chủ đề luyện tập">
        <div className="lp-marquee">
          {[...TOPICS, ...TOPICS].map(({ icon: Icon, label }, i) => (
            <span key={i} className="lp-chip" aria-hidden={i >= TOPICS.length}><Icon size={16} /> {label}</span>
          ))}
        </div>
      </section>

      {/* ─── HOW IT WORKS ─────────────────────────────────────────────── */}
      <section className="lp-section lp-tinted">
        <SectionHeading icon={Clock} eyebrow="Bắt đầu trong 30 giây" title="3 bước để bắt đầu" />
        <div className="lp-steps grid-3" style={{ gap: 24 }}>
          {STEPS.map((s, i) => (
            <motion.div key={s.title} {...stagger(i)} className="lp-card lp-step">
              <Media name={s.img} />
              <div className="lp-step-top">
                <IconTile icon={s.icon} tone={s.tone} size={60} />
                <span className="lp-step-num">0{i + 1}</span>
              </div>
              <h3>{s.title}</h3>
              <p>{s.desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ─── GOALS (links to the SEO pages) ───────────────────────────── */}
      <section id="muc-tieu" className="lp-section">
        <SectionHeading icon={Target} eyebrow="Học theo mục tiêu" title="Bạn học tiếng Anh để làm gì?" sub="Chọn mục tiêu để xem AI AGENT ENGLISH giúp bạn thế nào." />
        <div className="lp-goals">
          {SEO_PAGES.map((p, i) => {
            const { icon: Icon, colors } = SEO_ICONS[p.icon];
            return (
              <motion.div key={p.slug} {...stagger(i)}>
                <Link href={`/${p.slug}`} className="lp-card lp-goal">
                  <span className="lp-icon" style={{ width: 48, height: 48, borderRadius: 14, background: `linear-gradient(135deg, ${colors[0]}, ${colors[1]})`, boxShadow: `0 10px 24px -8px ${colors[0]}99` }}>
                    <Icon size={23} strokeWidth={2} color="#fff" />
                  </span>
                  <h3>{p.cardTitle}</h3>
                  <p>{p.cardDesc}</p>
                  <span className="lp-goal-more">Xem chi tiết <ChevronRight size={15} /></span>
                </Link>
              </motion.div>
            );
          })}
        </div>
      </section>

      {/* ─── WHO IT IS FOR (links to the usage guides) ─────────────── */}
      <section className="lp-section">
        <SectionHeading icon={Users} eyebrow="Dành cho ai" title="Một ứng dụng cho cả nhà và cả lớp" sub="Chọn vai trò để xem hướng dẫn từng bước, có ảnh chụp màn hình thật." />
        <div className="guide-hub">
          {AUDIENCES.map((a, i) => {
            const { icon: Icon, colors } = SEO_ICONS[a.icon];
            return (
              <motion.div key={a.slug} {...stagger(i)}>
                <Link href={`/huong-dan-su-dung/${a.slug}`} className="lp-card lp-goal">
                  <span className="lp-icon" style={{ width: 48, height: 48, borderRadius: 14, background: `linear-gradient(135deg, ${colors[0]}, ${colors[1]})` }}>
                    <Icon size={23} strokeWidth={2} color="#fff" />
                  </span>
                  <h3>{a.title}</h3>
                  <p>{a.desc}</p>
                  <span className="lp-goal-more">Xem hướng dẫn <ChevronRight size={15} /></span>
                </Link>
              </motion.div>
            );
          })}
        </div>
      </section>

      {/* ─── PRICING ──────────────────────────────────────────────────── */}
      <section id="bang-gia" className="lp-section lp-tinted">
        <SectionHeading icon={Crown} eyebrow="Bảng giá" title="Bắt đầu miễn phí, nâng cấp khi sẵn sàng" />
        <div className="lp-pricing">
          {PLANS.map((p, i) => (
            <motion.div key={p.name} {...stagger(i)} className={`lp-card lp-plan${p.highlight ? ' lp-plan-pro' : ''}`}>
              {p.highlight && <span className="lp-plan-badge"><Crown size={13} /> Phổ biến nhất</span>}
              <h3>{p.name}</h3>
              <div className="lp-price"><b>{p.price}</b> <span>{p.period}</span></div>
              <ul className="lp-checks">
                {p.features.map(f => <li key={f}><Check size={16} /> {f}</li>)}
              </ul>
              <Link href="/register" className={`btn btn-lg btn-full ${p.highlight ? 'btn-primary btn-shine' : 'btn-ghost'}`}>
                {p.cta}
              </Link>
            </motion.div>
          ))}
        </div>
        <p className="lp-note"><ShieldCheck size={15} /> Không cần thẻ tín dụng · Hủy bất cứ lúc nào</p>
      </section>

      {/* ─── FAQ ──────────────────────────────────────────────────────── */}
      <section id="hoi-dap" className="lp-section">
        <SectionHeading icon={MessageCircle} eyebrow="Hỏi đáp" title="Câu hỏi thường gặp" />
        <div className="lp-faq">
          {FAQS.map((f, i) => (
            <motion.details key={f.q} {...stagger(i)} className="lp-faq-item">
              <summary>{f.q}<ChevronDown size={20} /></summary>
              <p>{f.a}</p>
            </motion.details>
          ))}
        </div>
      </section>

      {/* ─── CTA ──────────────────────────────────────────────────────── */}
      <section className="lp-section" style={{ paddingTop: 0 }}>
        <motion.div {...reveal} className="lp-cta">
          <div className="lp-cta-media" aria-hidden="true">
            <Image src="/img/cta-banner.webp" alt="" fill sizes="(max-width: 1200px) 100vw, 1200px" />
          </div>
          <span className="lp-blob lp-blob-1" aria-hidden="true" />
          <span className="lp-blob lp-blob-2" aria-hidden="true" />
          <span className="lp-blob lp-blob-3" aria-hidden="true" />
          <div className="lp-cta-inner">
            <Trophy size={40} strokeWidth={1.6} />
            <h2>Sẵn sàng nói tiếng Anh tự tin?</h2>
            <p>Chỉ mất 5 phút để kiểm tra trình độ và nhận lộ trình học của riêng bạn.</p>
            <Link href="/register" className="btn btn-lg lp-cta-btn btn-shine">
              Tạo tài khoản miễn phí <ArrowRight size={18} />
            </Link>
            <div className="lp-cta-points">
              {['Miễn phí trọn đời gói cơ bản', 'Không cần thẻ tín dụng', 'Bắt đầu ngay hôm nay'].map(x => (
                <span key={x}><BadgeCheck size={16} /> {x}</span>
              ))}
            </div>
          </div>
        </motion.div>
      </section>

      <SiteFooter home />
    </main>
  );
}

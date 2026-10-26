'use client';

import Image from 'next/image';
import Link from 'next/link';
import { useEffect, useRef, useState } from 'react';
import { motion, useInView } from 'framer-motion';
import {
  ArrowRight, BadgeCheck, BookOpen, Brain, Briefcase, Check, ChevronDown, ChevronRight,
  ClipboardCheck, Clock, Coffee, Crown, Flame, GraduationCap, Headphones, Heart, Hotel,
  MessageCircle, Mic, PenLine, Plane, Presentation, Quote, Rocket, Route, ShieldCheck,
  Smartphone, Sparkles, Star, Target, TrendingUp, Trophy, UserPlus, Users, Utensils, Zap,
  type LucideIcon,
} from 'lucide-react';
import Logo from '@/components/ui/Logo';

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
  { value: 1247, label: 'Học viên đang học', icon: Users, tone: 'blue' },
  { value: 4.9, decimals: 1, suffix: '/5', label: 'Đánh giá trung bình', icon: Star, tone: 'orange' },
  { value: 98, suffix: '%', label: 'Hài lòng sau 30 ngày', icon: Heart, tone: 'pink' },
];

const SKILLS: { icon: LucideIcon; tone: Tone; title: string; desc: string }[] = [
  { icon: Headphones, tone: 'sky', title: 'Listening', desc: 'Nghe hội thoại thật với giọng đọc tự nhiên, kèm transcript.' },
  { icon: Mic, tone: 'pink', title: 'Speaking', desc: 'Nhập vai cùng AI, được sửa câu và gợi ý ngay khi nói.' },
  { icon: BookOpen, tone: 'green', title: 'Reading', desc: 'Bài đọc theo trình độ, từ vựng nổi bật và câu hỏi hiểu bài.' },
  { icon: PenLine, tone: 'purple', title: 'Writing', desc: 'Viết đoạn văn, email và nhận chấm điểm chi tiết từng lỗi.' },
];

const FEATURES: { icon: LucideIcon; tone: Tone; title: string; desc: string }[] = [
  { icon: TrendingUp, tone: 'green', title: 'Thích ứng thông minh', desc: 'Độ khó tự điều chỉnh theo kết quả thực tế. Học đúng thứ bạn cần.' },
  { icon: Flame, tone: 'orange', title: 'Động lực mỗi ngày', desc: 'XP, chuỗi ngày học, thành tựu và bảng xếp hạng giữ bạn đều đặn.' },
  { icon: Users, tone: 'purple', title: 'Báo cáo phụ huynh', desc: 'Báo cáo hằng tuần dễ hiểu, biết rõ con cần cải thiện điều gì.' },
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

const STEPS: { icon: LucideIcon; tone: Tone; title: string; desc: string }[] = [
  { icon: UserPlus, tone: 'blue', title: 'Tạo tài khoản miễn phí', desc: 'Chỉ cần email, không cần thẻ tín dụng.' },
  { icon: ClipboardCheck, tone: 'purple', title: 'Kiểm tra đầu vào 5 phút', desc: '10 câu hỏi để AGEN xác định đúng trình độ của bạn.' },
  { icon: Rocket, tone: 'pink', title: 'Nhận lộ trình và học ngay', desc: 'Bài học được tạo riêng theo mục tiêu và thời gian của bạn.' },
];

const TESTIMONIALS: { name: string; meta: string; quote: string; tone: Tone }[] = [
  { name: 'Minh Anh', meta: '16 tuổi · B2', quote: 'AGEN giúp mình từ B1 lên B2 chỉ trong 2 tháng. Phần luyện nói với AI là phần mình thích nhất.', tone: 'pink' },
  { name: 'Bố của Hùng', meta: 'Phụ huynh', quote: 'Báo cáo hằng tuần rất rõ ràng. Biết chính xác con cần cải thiện kỹ năng nào, không phải đoán mò.', tone: 'blue' },
  { name: 'Lan Phương', meta: '28 tuổi · B1', quote: '15 phút mỗi ngày với AGEN hiệu quả hơn cả buổi học 2 tiếng. Rất hợp với người đi làm.', tone: 'green' },
];

const PLANS = [
  {
    name: 'Miễn phí', price: '0₫', period: 'mãi mãi', highlight: false, cta: 'Bắt đầu miễn phí',
    features: ['3 bài học AI mỗi ngày', 'Luyện nói roleplay với AI', 'Luyện viết và chấm điểm AI', 'Bài kiểm tra đầu vào', 'XP, chuỗi ngày học, thành tựu'],
  },
  {
    name: 'Premium', price: '67K₫', period: '/tháng · gói 12 tháng', highlight: true, cta: 'Dùng thử ngay',
    features: ['Mọi thứ trong gói Miễn phí', 'Bài học không giới hạn', 'Báo cáo tiến bộ cho phụ huynh', 'Lộ trình học cá nhân hoá', 'Ưu tiên hỗ trợ'],
  },
];

const FAQS = [
  { q: 'AGEN có miễn phí không?', a: 'Có. Gói miễn phí gồm 3 bài học AI mỗi ngày, luyện nói nhập vai, luyện viết có chấm điểm, bài kiểm tra đầu vào và hệ thống XP, chuỗi ngày học. Bạn không cần thẻ tín dụng để bắt đầu.' },
  { q: 'Bài kiểm tra đầu vào mất bao lâu?', a: 'Khoảng 5–8 phút với 10 câu hỏi về từ vựng, ngữ pháp và đọc hiểu. Kết quả dùng để xếp trình độ theo chuẩn CEFR và tạo lộ trình học riêng cho bạn.' },
  { q: 'Mỗi ngày nên học bao nhiêu phút?', a: 'Bạn tự chọn 5, 10, 15 hoặc 30 phút mỗi ngày. AGEN chia nhỏ bài học cho vừa lịch của bạn; 15 phút mỗi ngày là mức được khuyên dùng.' },
  { q: 'Phụ huynh theo dõi việc học của con như thế nào?', a: 'Con chia sẻ mã liên kết có trong ứng dụng. Phụ huynh tạo tài khoản phụ huynh, nhập mã và xem báo cáo hằng tuần: con đã tiến bộ gì, cần hỗ trợ gì và phụ huynh nên làm gì.' },
  { q: 'Gói Premium khác gì gói miễn phí?', a: 'Premium mở khoá bài học không giới hạn, báo cáo cho phụ huynh, lộ trình cá nhân hoá và ưu tiên hỗ trợ. Giá từ 99.000₫/tháng, hoặc chỉ khoảng 67.000₫/tháng khi chọn gói 12 tháng.' },
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
export default function HomePage() {
  const faqJsonLd = {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: FAQS.map(f => ({ '@type': 'Question', name: f.q, acceptedAnswer: { '@type': 'Answer', text: f.a } })),
  };

  return (
    <main style={{ minHeight: '100vh', overflowX: 'hidden', background: 'var(--bg-surface)' }}>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(faqJsonLd) }} />

      {/* ─── NAV ──────────────────────────────────────────────────────── */}
      <header className="lp-nav">
        <div className="lp-nav-inner">
          <Link href="/" aria-label="AGEN — trang chủ" style={{ display: 'inline-flex', opacity: 1 }}><Logo size={30} /></Link>
          <nav className="lp-nav-links" aria-label="Điều hướng trang">
            <a href="#ky-nang">Kỹ năng</a>
            <a href="#tinh-nang">Tính năng</a>
            <a href="#bang-gia">Bảng giá</a>
            <a href="#hoi-dap">Hỏi đáp</a>
          </nav>
          <div style={{ display: 'flex', alignItems: 'center', gap: 16, fontSize: '0.88rem' }}>
            <Link href="/login" style={{ color: 'var(--text-secondary)' }}>Đăng nhập</Link>
            <Link href="/register" className="btn btn-primary btn-sm">Học miễn phí</Link>
          </div>
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
          transition={{ duration: 0.8, ease: EASE }}
        >
          <span className="hero-badge"><Sparkles size={14} /> AI Coach tiếng Anh cá nhân cho người Việt</span>
          <h1><span className="nowrap">Học tiếng Anh</span> <span className="nowrap">cùng AI.</span><br /><span className="nowrap">Theo cách của</span> <span className="nowrap">riêng bạn.</span></h1>
          <p>
            Người thầy, người bạn và huấn luyện viên tiếng Anh — đồng hành từ nền tảng đến nâng cao, theo đúng tốc độ của bạn.
          </p>
          <div className="hero-actions">
            <Link href="/register" className="btn btn-primary btn-lg btn-shine">
              Bắt đầu học miễn phí <ArrowRight size={18} />
            </Link>
            <Link href="/login" className="hero-link">
              Đăng nhập <ChevronRight size={18} />
            </Link>
          </div>
          <div className="hero-trust">
            <div className="avatar-stack" aria-hidden="true">
              {(['pink', 'blue', 'green', 'orange'] as Tone[]).map((t, i) => (
                <span key={t} style={{ background: `linear-gradient(135deg, ${G[t][0]}, ${G[t][1]})` }}>{'MLHT'[i]}</span>
              ))}
            </div>
            <div>
              <div className="stars" aria-label="4.9 trên 5 sao">
                {Array.from({ length: 5 }).map((_, i) => <Star key={i} size={14} fill="#F59E0B" color="#F59E0B" />)}
                <b>4.9</b>
              </div>
              <div className="hero-trust-text">1,247 học viên đang học cùng AGEN</div>
            </div>
          </div>
        </motion.div>
      </section>

      {/* ─── STATS ────────────────────────────────────────────────────── */}
      <section className="lp-section" style={{ paddingTop: 56, paddingBottom: 56 }}>
        <div className="grid-3" style={{ gap: 20 }}>
          {STATS.map((s, i) => (
            <motion.div key={s.label} {...stagger(i)} className="lp-card lp-stat">
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
              <IconTile icon={s.icon} tone={s.tone} size={56} />
              <h3>{s.title}</h3>
              <p>{s.desc}</p>
              <span className="lp-skill-glow" aria-hidden="true" />
            </motion.div>
          ))}
        </div>
      </section>

      {/* ─── FEATURES (bento) ─────────────────────────────────────────── */}
      <section id="tinh-nang" className="lp-section">
        <SectionHeading icon={Zap} eyebrow="Tất cả trong một" title="Vì sao học viên chọn AGEN?" sub="Mọi thứ bạn cần để tiến bộ đều đặn — gói gọn trong một ứng dụng." />
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

      {/* ─── TESTIMONIALS ─────────────────────────────────────────────── */}
      <section className="lp-section">
        <SectionHeading icon={Heart} eyebrow="Câu chuyện thật" title="Học viên nói gì về AGEN?" />
        <div className="grid-3" style={{ gap: 20 }}>
          {TESTIMONIALS.map((t, i) => (
            <motion.figure key={t.name} {...stagger(i)} className="lp-card lp-quote">
              <Quote size={28} color={G[t.tone][0]} style={{ opacity: 0.9 }} />
              <div className="stars" aria-label="5 sao">
                {Array.from({ length: 5 }).map((_, k) => <Star key={k} size={15} fill="#F59E0B" color="#F59E0B" />)}
              </div>
              <blockquote>{t.quote}</blockquote>
              <figcaption>
                <span className="lp-avatar" style={{ background: `linear-gradient(135deg, ${G[t.tone][0]}, ${G[t.tone][1]})` }}>{t.name.charAt(0)}</span>
                <span>
                  <b>{t.name}</b>
                  <small>{t.meta}</small>
                </span>
              </figcaption>
            </motion.figure>
          ))}
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

      {/* ─── FOOTER ───────────────────────────────────────────────────── */}
      <footer className="lp-footer">
        <div className="lp-footer-top">
          <div style={{ maxWidth: 360 }}>
            <Logo size={32} />
            <p>AI English Learning Agent — người thầy, người bạn và huấn luyện viên tiếng Anh đồng hành lâu dài.</p>
          </div>
          <div className="lp-footer-cols">
            <div>
              <b>Sản phẩm</b>
              <a href="#ky-nang">4 kỹ năng</a>
              <a href="#tinh-nang">Tính năng</a>
              <a href="#bang-gia">Bảng giá</a>
            </div>
            <div>
              <b>Tài khoản</b>
              <Link href="/register">Đăng ký</Link>
              <Link href="/login">Đăng nhập</Link>
              <a href="#hoi-dap">Hỏi đáp</a>
            </div>
          </div>
        </div>
        <div className="lp-footer-bottom">
          <span>© {new Date().getFullYear()} AGEN. Bảo lưu mọi quyền.</span>
          <span>Học tiếng Anh cùng AI</span>
        </div>
      </footer>
    </main>
  );
}

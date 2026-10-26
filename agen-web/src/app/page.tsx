'use client';

import Link from 'next/link';
import { motion, Variants } from 'framer-motion';
import { useState, useEffect } from 'react';

const STATS = [
  { value: '1,247', label: 'Học viên đang học', icon: '👥' },
  { value: '4.9★', label: 'Đánh giá trung bình', icon: '⭐' },
  { value: '98%', label: 'Hài lòng sau 30 ngày', icon: '💚' },
];

const FEATURES = [
  {
    icon: '🤖',
    color: '#6C63FF',
    title: 'AI Coach cá nhân',
    desc: 'Hệ thống AI đa tác tử phân tích điểm mạnh/yếu của bạn và tạo bài học riêng — như gia sư 1-1 bản xứ.',
  },
  {
    icon: '🗣️',
    color: '#F472B6',
    title: 'Luyện Nói với AI',
    desc: 'Roleplay tình huống thực tế với AI. Nhận phản hồi chi tiết về ngữ pháp và gợi ý cải thiện ngay tức thì.',
  },
  {
    icon: '📈',
    color: '#06D6A0',
    title: 'Thích ứng thông minh',
    desc: 'Bài học tự động điều chỉnh độ khó dựa trên kết quả thực tế của bạn. Học hiệu quả hơn, không lãng phí thời gian.',
  },
  {
    icon: '🔥',
    color: '#FF6B6B',
    title: 'Gamification sâu',
    desc: 'XP, Streak hằng ngày, Thành tựu và Bảng xếp hạng. Học như chơi game — không thể bỏ cuộc!',
  },
  {
    icon: '👨‍👩‍👧',
    color: '#FFD93D',
    title: 'Báo cáo Phụ huynh',
    desc: 'Phụ huynh theo dõi tiến bộ con qua báo cáo hằng tuần với ngôn ngữ đơn giản, không phải bảng điểm khô khan.',
  },
  {
    icon: '🎯',
    color: '#38BDF8',
    title: 'Lộ trình cá nhân hóa',
    desc: 'Từ Placement Test đến lộ trình CEFR riêng biệt. Biết chính xác bạn cần học gì, theo thứ tự nào.',
  },
];

const TESTIMONIALS = [
  { name: 'Minh Anh', age: 16, quote: 'AGEN giúp mình từ B1 lên B2 chỉ trong 2 tháng! Phần luyện nói với AI đặc biệt thích.', level: 'B2', emoji: '🎓' },
  { name: 'Bố của Hùng', role: 'Phụ huynh', quote: 'Báo cáo hàng tuần rất rõ ràng. Biết chính xác con cần cải thiện kỹ năng nào, không phải đoán mò.', level: 'Parent', emoji: '👨' },
  { name: 'Lan Phương', age: 28, quote: 'Dân đi làm như mình không có nhiều thời gian. 15 phút/ngày với AGEN hiệu quả hơn cả lớp học 2 tiếng.', level: 'B1', emoji: '💼' },
];

const STEPS = [
  { n: '01', title: 'Tạo tài khoản miễn phí', desc: 'Chỉ cần email — không cần thẻ tín dụng.', icon: '✨' },
  { n: '02', title: 'Kiểm tra đầu vào 5 phút', desc: 'AGEN phân tích trình độ hiện tại của bạn.', icon: '🧭' },
  { n: '03', title: 'Nhận lộ trình riêng & học ngay', desc: 'AI tạo bài học phù hợp — bắt đầu học ngay hôm nay.', icon: '🚀' },
];

// Floating particle animation (CSS only)
function FloatingParticles() {
  return (
    <div style={{ position: 'absolute', inset: 0, overflow: 'hidden', pointerEvents: 'none' }}>
      {[...Array(12)].map((_, i) => (
        <div
          key={i}
          style={{
            position: 'absolute',
            width: `${4 + (i % 4) * 3}px`,
            height: `${4 + (i % 4) * 3}px`,
            borderRadius: '50%',
            background: i % 3 === 0 ? 'rgba(108,99,255,0.4)' : i % 3 === 1 ? 'rgba(255,107,107,0.3)' : 'rgba(255,217,61,0.3)',
            left: `${(i * 8.5) % 100}%`,
            top: `${(i * 13.7) % 80}%`,
            animation: `float-${i % 3} ${3 + i * 0.5}s ease-in-out infinite`,
            animationDelay: `${i * 0.4}s`,
          }}
        />
      ))}
      <style>{`
        @keyframes float-0 { 0%,100%{transform:translateY(0px) rotate(0deg)} 50%{transform:translateY(-18px) rotate(180deg)} }
        @keyframes float-1 { 0%,100%{transform:translateY(0px) rotate(0deg)} 50%{transform:translateY(-12px) rotate(-180deg)} }
        @keyframes float-2 { 0%,100%{transform:translateY(0px) rotate(0deg)} 50%{transform:translateY(-24px) rotate(90deg)} }
      `}</style>
    </div>
  );
}


export default function HomePage() {
  const [activeTestimonial, setActiveTestimonial] = useState(0);

  useEffect(() => {
    const t = setInterval(() => setActiveTestimonial(p => (p + 1) % TESTIMONIALS.length), 4000);
    return () => clearInterval(t);
  }, []);

  const containerVariants: Variants = {
    hidden: { opacity: 0 },
    show: { opacity: 1, transition: { staggerChildren: 0.12 } },
  };
  const itemVariants: Variants = {
    hidden: { opacity: 0, y: 30 },
    show: { opacity: 1, y: 0, transition: { type: 'spring', stiffness: 260, damping: 22 } },
  };

  return (
    <main style={{ minHeight: '100vh', overflow: 'hidden' }}>

      {/* ─── HERO ─────────────────────────────────────────────────────── */}
      <section style={{ position: 'relative', minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', textAlign: 'center', padding: '80px 24px' }}>
        {/* Background gradient mesh */}
        <div style={{ position: 'absolute', inset: 0, background: 'radial-gradient(ellipse 70% 60% at 50% 0%, rgba(108,99,255,0.2) 0%, transparent 70%), radial-gradient(ellipse 50% 40% at 80% 80%, rgba(255,107,107,0.12) 0%, transparent 60%)', pointerEvents: 'none' }} />
        <FloatingParticles />

        <motion.div
          variants={containerVariants} initial="hidden" animate="show"
          style={{ maxWidth: 720, position: 'relative', zIndex: 1 }}
        >
          {/* Badge */}
          <motion.div variants={itemVariants}>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8, padding: '6px 18px', borderRadius: 99, background: 'rgba(108,99,255,0.15)', border: '1px solid rgba(108,99,255,0.35)', fontSize: '0.82rem', fontWeight: 700, color: 'var(--agen-primary-light)', marginBottom: 28, letterSpacing: 0.5 }}>
              ✨ Nền tảng AI học tiếng Anh thế hệ mới
            </span>
          </motion.div>

          {/* Headline */}
          <motion.h1 variants={itemVariants} style={{ fontSize: 'clamp(2.4rem, 7vw, 4.2rem)', fontWeight: 900, lineHeight: 1.1, marginBottom: 28 }}>
            <span style={{ background: 'linear-gradient(135deg, #6C63FF, #F472B6, #FFD93D)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text' }}>
              AI English
            </span>
            <br />
            Learning Agent
          </motion.h1>

          {/* Subtitle */}
          <motion.p variants={itemVariants} style={{ fontSize: '1.2rem', lineHeight: 1.75, color: 'var(--text-secondary)', maxWidth: 560, margin: '0 auto 40px', fontWeight: 400 }}>
            Người thầy, người bạn và huấn luyện viên tiếng Anh AI — đồng hành từ nền tảng đến nâng cao theo tốc độ của <em>riêng bạn</em>.
          </motion.p>

          {/* CTA Buttons */}
          <motion.div variants={itemVariants} style={{ display: 'flex', gap: 16, flexWrap: 'wrap', justifyContent: 'center', marginBottom: 48 }}>
            <Link href="/register">
              <motion.span
                whileHover={{ scale: 1.05, y: -2 }}
                whileTap={{ scale: 0.97 }}
                style={{ display: 'inline-flex', alignItems: 'center', gap: 8, padding: '16px 36px', borderRadius: 14, background: 'linear-gradient(135deg, #6C63FF, #8B85FF)', color: 'white', fontWeight: 700, fontSize: '1.05rem', boxShadow: '0 8px 32px rgba(108,99,255,0.45)', cursor: 'pointer' }}
              >
                🚀 Bắt đầu học miễn phí
              </motion.span>
            </Link>
            <Link href="/login">
              <motion.span
                whileHover={{ scale: 1.03 }}
                style={{ display: 'inline-flex', alignItems: 'center', gap: 8, padding: '16px 28px', borderRadius: 14, background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.14)', color: 'var(--text-primary)', fontWeight: 600, cursor: 'pointer' }}
              >
                Đăng nhập
              </motion.span>
            </Link>
          </motion.div>

          {/* Skill Pills */}
          <motion.div variants={itemVariants} style={{ display: 'flex', gap: 10, flexWrap: 'wrap', justifyContent: 'center', marginBottom: 56 }}>
            {[
              { label: '🎧 Listening', color: 'var(--skill-listening)' },
              { label: '🗣️ Speaking', color: 'var(--skill-speaking)' },
              { label: '📖 Reading', color: 'var(--skill-reading)' },
              { label: '✍️ Writing', color: 'var(--skill-writing)' },
            ].map(s => (
              <span key={s.label} style={{ padding: '7px 16px', borderRadius: 99, background: `${s.color}18`, border: `1px solid ${s.color}40`, color: s.color, fontWeight: 600, fontSize: '0.85rem' }}>
                {s.label}
              </span>
            ))}
          </motion.div>

          {/* Social Proof */}
          <motion.div variants={itemVariants} style={{ display: 'flex', gap: 24, justifyContent: 'center', flexWrap: 'wrap' }}>
            {STATS.map(s => (
              <div key={s.label} style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '0.9rem' }}>{s.icon}</div>
                <div style={{ fontSize: '1.4rem', fontWeight: 900, color: 'var(--agen-primary-light)' }}>{s.value}</div>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{s.label}</div>
              </div>
            ))}
          </motion.div>
        </motion.div>
      </section>

      {/* ─── HOW IT WORKS ─────────────────────────────────────────────── */}
      <section style={{ padding: '80px 24px', maxWidth: 900, margin: '0 auto' }}>
        <motion.div initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} style={{ textAlign: 'center', marginBottom: 56 }}>
          <div style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--agen-accent)', letterSpacing: 1.5, textTransform: 'uppercase', marginBottom: 12 }}>Bắt đầu trong 30 giây</div>
          <h2 style={{ fontSize: 'clamp(1.8rem, 4vw, 2.5rem)', fontWeight: 900 }}>Cách hoạt động</h2>
        </motion.div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 24 }}>
          {STEPS.map((step, i) => (
            <motion.div
              key={step.n}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.12 }}
              whileHover={{ y: -4, boxShadow: '0 16px 40px rgba(108,99,255,0.2)' }}
              style={{ padding: '32px 28px', borderRadius: 20, background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)', position: 'relative', overflow: 'hidden' }}
            >
              <div style={{ position: 'absolute', top: -10, right: -10, fontSize: '4rem', opacity: 0.07, fontWeight: 900, color: 'var(--agen-primary-light)', lineHeight: 1 }}>{step.n}</div>
              <div style={{ fontSize: '2rem', marginBottom: 16 }}>{step.icon}</div>
              <h3 style={{ fontSize: '1.05rem', marginBottom: 8, fontWeight: 700 }}>{step.title}</h3>
              <p style={{ fontSize: '0.88rem', lineHeight: 1.65 }}>{step.desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ─── FEATURES ─────────────────────────────────────────────────── */}
      <section style={{ padding: '80px 24px', maxWidth: 1100, margin: '0 auto' }}>
        <motion.div initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} style={{ textAlign: 'center', marginBottom: 56 }}>
          <div style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--agen-primary-light)', letterSpacing: 1.5, textTransform: 'uppercase', marginBottom: 12 }}>Tất cả trong một</div>
          <h2 style={{ fontSize: 'clamp(1.8rem, 4vw, 2.5rem)', fontWeight: 900 }}>Vì sao chọn AGEN?</h2>
        </motion.div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 20 }}>
          {FEATURES.map((f, i) => (
            <motion.div
              key={f.title}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.08 }}
              whileHover={{ y: -4, borderColor: `${f.color}60` }}
              style={{ padding: '28px 24px', borderRadius: 20, background: 'var(--bg-surface)', border: `1px solid ${f.color}20`, cursor: 'default', transition: 'all 0.25s' }}
            >
              <div style={{ width: 52, height: 52, borderRadius: 14, background: `${f.color}18`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.6rem', marginBottom: 18, border: `1px solid ${f.color}30` }}>
                {f.icon}
              </div>
              <h3 style={{ fontSize: '1.05rem', fontWeight: 700, marginBottom: 10, color: 'var(--text-primary)' }}>{f.title}</h3>
              <p style={{ fontSize: '0.88rem', lineHeight: 1.7, color: 'var(--text-secondary)' }}>{f.desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ─── TESTIMONIALS ─────────────────────────────────────────────── */}
      <section style={{ padding: '80px 24px' }}>
        <div style={{ maxWidth: 680, margin: '0 auto', textAlign: 'center' }}>
          <motion.div initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} style={{ marginBottom: 40 }}>
            <div style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--agen-success)', letterSpacing: 1.5, textTransform: 'uppercase', marginBottom: 12 }}>Câu chuyện thật</div>
            <h2 style={{ fontSize: 'clamp(1.8rem, 4vw, 2.5rem)', fontWeight: 900 }}>Học viên nói gì?</h2>
          </motion.div>

          <div style={{ position: 'relative', minHeight: 180 }}>
            {TESTIMONIALS.map((t, i) => (
              <motion.div
                key={t.name}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: activeTestimonial === i ? 1 : 0, scale: activeTestimonial === i ? 1 : 0.95, position: 'absolute' }}
                style={{ padding: '32px', borderRadius: 20, background: 'var(--bg-surface)', border: '1px solid var(--border-medium)', textAlign: 'left', width: '100%', top: 0 }}
              >
                <div style={{ fontSize: '1.4rem', marginBottom: 16 }}>❝</div>
                <p style={{ fontSize: '1rem', lineHeight: 1.75, color: 'var(--text-primary)', marginBottom: 20, fontStyle: 'italic' }}>{t.quote}</p>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <div style={{ width: 44, height: 44, borderRadius: '50%', background: 'rgba(108,99,255,0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.4rem' }}>{t.emoji}</div>
                  <div>
                    <div style={{ fontWeight: 700 }}>{t.name}</div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{t.role || `${t.age} tuổi`} · Level {t.level}</div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>

          <div style={{ display: 'flex', gap: 8, justifyContent: 'center', marginTop: 200 }}>
            {TESTIMONIALS.map((_, i) => (
              <button key={i} onClick={() => setActiveTestimonial(i)} style={{ width: activeTestimonial === i ? 24 : 8, height: 8, borderRadius: 99, background: activeTestimonial === i ? 'var(--agen-primary)' : 'var(--border-medium)', border: 'none', cursor: 'pointer', transition: 'all 0.3s', padding: 0 }} />
            ))}
          </div>
        </div>
      </section>

      {/* ─── CTA BOTTOM ───────────────────────────────────────────────── */}
      <section style={{ padding: '80px 24px 100px' }}>
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          style={{ maxWidth: 680, margin: '0 auto', textAlign: 'center', padding: '60px 40px', borderRadius: 28, background: 'linear-gradient(135deg, rgba(108,99,255,0.18), rgba(255,107,107,0.1))', border: '1px solid rgba(108,99,255,0.3)', position: 'relative', overflow: 'hidden' }}
        >
          <div style={{ position: 'absolute', top: -60, right: -60, width: 200, height: 200, borderRadius: '50%', background: 'radial-gradient(circle, rgba(108,99,255,0.3) 0%, transparent 70%)', pointerEvents: 'none' }} />
          <div style={{ fontSize: '3rem', marginBottom: 20 }}>🎓</div>
          <h2 style={{ fontSize: 'clamp(1.6rem, 3.5vw, 2.2rem)', fontWeight: 900, marginBottom: 16 }}>Sẵn sàng bắt đầu hành trình?</h2>
          <p style={{ color: 'var(--text-secondary)', marginBottom: 36, fontSize: '1rem', maxWidth: 420, margin: '0 auto 36px' }}>
            Chỉ mất 5 phút để kiểm tra đầu vào và nhận lộ trình học riêng của bạn. Miễn phí, không cần thẻ tín dụng.
          </p>
          <Link href="/register">
            <motion.span
              whileHover={{ scale: 1.05, y: -2 }}
              whileTap={{ scale: 0.97 }}
              style={{ display: 'inline-flex', alignItems: 'center', gap: 10, padding: '18px 42px', borderRadius: 14, background: 'linear-gradient(135deg, #6C63FF, #8B85FF)', color: 'white', fontWeight: 800, fontSize: '1.1rem', boxShadow: '0 8px 32px rgba(108,99,255,0.5)', cursor: 'pointer' }}
            >
              🚀 Tạo tài khoản miễn phí
            </motion.span>
          </Link>
          <div style={{ marginTop: 20, fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            ✓ Không cần thẻ tín dụng &nbsp;·&nbsp; ✓ Bắt đầu ngay hôm nay &nbsp;·&nbsp; ✓ Hủy bất cứ lúc nào
          </div>
        </motion.div>
      </section>

    </main>
  );
}

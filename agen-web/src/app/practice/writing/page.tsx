'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  getWritingPrompt, submitWriting, EXAM_GENRES,
  WritingPromptResponse, WritingEvaluationResponse, type ExamBand,
} from '@/lib/writingApiService';
import { notifyActivityCompleted } from '@/lib/services';
import { useAuthStore } from '@/store/authStore';
import { getMyProfile } from '@/lib/services';
import { ArrowLeft, Award, BookText, Briefcase, CircleAlert, Feather, GraduationCap, Lightbulb, LoaderCircle, Mail, MessageSquareQuote, Palette, Sparkles, Star, TrendingUp } from 'lucide-react';
import { track } from '@/lib/analytics';
import WritingHistoryCard from '@/components/writing/WritingHistoryCard';

interface GenreCard { id: string; label: string; sub?: string; icon: typeof Mail }
const GENERAL_GENRES: GenreCard[] = [
  { id: 'opinion', label: 'Ý kiến / Quan điểm', icon: MessageSquareQuote },
  { id: 'narrative', label: 'Kể chuyện', icon: Feather },
  { id: 'descriptive', label: 'Miêu tả', icon: Palette },
  { id: 'email', label: 'Viết thư / Email', icon: Mail },
];

/** G5 · đề thi thật, chấm theo band. */
const EXAM_CARDS: GenreCard[] = [
  { id: 'ielts_task2', label: 'IELTS Task 2 · Essay 250 từ', sub: 'Chấm band 0–9 theo 4 tiêu chí', icon: GraduationCap },
  { id: 'ielts_task1', label: 'IELTS Task 1 · Thư (General)', sub: 'Thư 150 từ, 3 ý bắt buộc', icon: Mail },
  { id: 'toeic_email', label: 'TOEIC Writing · Trả lời email', sub: 'Câu 6–7, điểm 0–200', icon: Briefcase },
  { id: 'toeic_essay', label: 'TOEIC Writing · Opinion essay', sub: 'Câu 8, 300 từ', icon: Award },
];

const IELTS_LABELS: Record<string, string> = {
  task_response: 'Task Response', coherence_cohesion: 'Coherence & Cohesion', lexical_resource: 'Lexical Resource', grammatical_range: 'Grammar Range & Accuracy',
};
const TOEIC_LABELS: Record<string, string> = {
  task_completion: 'Hoàn thành yêu cầu', organisation: 'Tổ chức ý', vocabulary: 'Từ vựng', grammar: 'Ngữ pháp',
};

function BandCard({ band }: { band: ExamBand }) {
  const ielts = band.exam === 'ielts';
  const labels = ielts ? IELTS_LABELS : TOEIC_LABELS;
  const max = ielts ? 9 : 5;
  return (
    <div className="card band-card">
      <div className="eyebrow" style={{ marginBottom: 6 }}>{ielts ? 'IELTS Writing · Band ước tính' : 'TOEIC Writing · Điểm ước tính'}</div>
      <div className="band-score text-gradient">{ielts ? band.overall.toFixed(1) : Math.round(band.overall)}<small>{ielts ? '/9' : '/200'}</small></div>
      <div className="band-criteria">
        {Object.entries(band.criteria).map(([k, v]) => (
          <div key={k}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.82rem', marginBottom: 4 }}>
              <span style={{ color: 'var(--text-secondary)' }}>{labels[k] || k}</span><strong>{ielts ? v.toFixed(1) : v}</strong>
            </div>
            <div className="progress-bar"><div className="progress-fill" style={{ width: `${(v / max) * 100}%`, background: 'var(--agen-primary)' }} /></div>
          </div>
        ))}
      </div>
      {band.next_band_tips.length > 0 && (
        <div style={{ marginTop: 14 }}>
          <div style={{ fontWeight: 600, fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6 }}><TrendingUp size={15} color="var(--agen-success)" /> Để lên {ielts ? 'band tiếp theo' : 'điểm cao hơn'}</div>
          <ul style={{ paddingLeft: 18, fontSize: '0.88rem', color: 'var(--text-secondary)', display: 'grid', gap: 4 }}>
            {band.next_band_tips.map((t, i) => <li key={i}>{t}</li>)}
          </ul>
        </div>
      )}
      <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 12 }}>Ước tính của AI theo thang điểm công bố; kết quả thi thật có thể khác.</p>
    </div>
  );
}

export default function WritingPracticePage() {
  const { setLearner, learner } = useAuthStore();
  const examFirst = learner?.learning_goal === 'luyen_thi' || learner?.learning_goal === 'cong_viec';
  useEffect(() => { if (!learner) getMyProfile().then(setLearner).catch(() => undefined); }, [learner, setLearner]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [promptData, setPromptData] = useState<WritingPromptResponse | null>(null);
  const [userText, setUserText] = useState('');
  
  const [evaluation, setEvaluation] = useState<WritingEvaluationResponse | null>(null);
  const [evalLoading, setEvalLoading] = useState(false);

  // Stats for the editor
  const wordCount = userText.trim() === '' ? 0 : userText.trim().split(/\s+/).length;

  const handleGetPrompt = async (genre: string) => {
    setLoading(true);
    setError('');
    setEvaluation(null);
    setUserText('');
    try {
      const res = await getWritingPrompt(genre);
      setPromptData(res);
    } catch (err: unknown) {
      setError((err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Lỗi lấy đề tài viết.');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (!promptData || wordCount < 10) return;
    setEvalLoading(true);
    setError('');
    try {
      const res = await submitWriting(
        promptData.title,
        promptData.prompt,
        promptData.genre,
        userText
      );
      setEvaluation(res);
      track('writing_submitted', { genre: promptData.genre, score: res.overall_score, words: wordCount, band: res.exam_band?.overall });

      // Update streak + daily challenge + refresh profile
      await notifyActivityCompleted('writing');
      const freshProfile = await getMyProfile();
      setLearner(freshProfile);
    } catch (err: unknown) {
      setError((err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Lỗi khi nộp bài.');
    } finally {
      setEvalLoading(false);
    }
  };

  if (!promptData) {
    return (
      <main style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 'var(--spacing-lg)' }}>
        <div style={{ maxWidth: 600, width: '100%' }}>
          <Link href="/dashboard" style={{ display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: '0.92rem', marginBottom: 20 }}><ArrowLeft size={16} /> Dashboard</Link>
          <h1 style={{ fontSize: 'clamp(1.9rem, 4vw, 2.5rem)', marginBottom: 10 }}>Luyện viết</h1>
          <p style={{ color: 'var(--text-secondary)', marginBottom: 28 }}>
            Chọn một chủ đề để bắt đầu. AI sẽ tạo đề bài phù hợp với trình độ của bạn và chấm điểm chi tiết.
          </p>
          
          {error && <div className="alert-error" style={{ marginBottom: 16 }}><CircleAlert size={16} style={{ flexShrink: 0 }} /> {error}</div>}

          {[examFirst ? 'exam' : 'general', examFirst ? 'general' : 'exam'].map(group => (
            <div key={group} style={{ marginBottom: 24 }}>
              <div className="section-head"><h3>{group === 'exam' ? 'Luyện thi · chấm theo band' : 'Viết tự do'}</h3></div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 12 }}>
                {(group === 'exam' ? EXAM_CARDS : GENERAL_GENRES).map(g => (
                  <button
                    key={g.id}
                    className="card card-hover"
                    style={{ display: 'flex', alignItems: 'center', gap: 14, padding: 18, textAlign: 'left', fontFamily: 'inherit', fontSize: '1rem' }}
                    onClick={() => handleGetPrompt(g.id)}
                    disabled={loading}
                  >
                    <span className="icon-tile" style={{ background: group === 'exam' ? 'color-mix(in srgb, var(--agen-primary) 12%, transparent)' : 'color-mix(in srgb, var(--skill-writing) 12%, transparent)', color: group === 'exam' ? 'var(--agen-primary)' : 'var(--skill-writing)', width: 40, height: 40 }}><g.icon size={20} strokeWidth={1.8} /></span>
                    <span style={{ minWidth: 0 }}>
                      <span style={{ display: 'block', fontWeight: 600, fontSize: '0.95rem' }}>{g.label}</span>
                      {g.sub && <span style={{ display: 'block', fontSize: '0.78rem', color: 'var(--text-muted)' }}>{g.sub}</span>}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          ))}
          {loading && <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 8, marginTop: 24, color: 'var(--text-muted)', fontSize: '0.9rem' }}><LoaderCircle className="animate-spin" size={16} /> Đang chuẩn bị đề bài…</div>}
          <WritingHistoryCard />
        </div>
      </main>
    );
  }

  return (
    <main style={{ minHeight: '100vh', padding: 'clamp(24px, 4vw, 40px) var(--page-gutter)' }}>
      <div className="container" style={{ padding: 0 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
          <button className="btn btn-ghost btn-sm" onClick={() => setPromptData(null)}><ArrowLeft size={16} /> Đổi đề tài</button>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            {EXAM_GENRES.includes(promptData.genre as typeof EXAM_GENRES[number]) && <span className="skill-badge" style={{ background: 'var(--bg-tint)', color: 'var(--agen-primary)' }}><GraduationCap size={13} /> Đề thi {promptData.genre.startsWith('ielts') ? 'IELTS' : 'TOEIC'}</span>}
            <div className="level-badge">{promptData.level}</div>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: evaluation ? 'repeat(auto-fit, minmax(340px, 1fr))' : '1fr', gap: 'var(--spacing-lg)' }}>
          
          {/* Left Column: Prompt & Editor */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-md)' }}>
            
            {/* Prompt Box */}
            <div className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
                <span className="eyebrow" style={{ textTransform: 'capitalize' }}>{promptData.genre}</span>
                <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Mục tiêu: {promptData.word_target}</span>
              </div>
              <h3 style={{ marginBottom: 12, fontSize: '1.5rem' }}>{promptData.title}</h3>
              <p style={{ marginBottom: 20, fontSize: '1.1rem', lineHeight: 1.6 }}>{promptData.prompt}</p>
              
              <div style={{ padding: 16, background: 'var(--bg-elevated)', borderRadius: 14 }}>
                <div style={{ fontWeight: 600, marginBottom: 8, fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: 6 }}><Lightbulb size={15} color="var(--agen-accent)" /> Hướng dẫn</div>
                <ul style={{ paddingLeft: 20, fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: 12 }}>
                  {promptData.guide_steps.map((step, i) => <li key={i}>{step}</li>)}
                </ul>
                <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                  <b>Ví dụ mở bài:</b> &quot;{promptData.example_opening}&quot;
                </div>
              </div>
            </div>

            {/* Editor Box */}
            <div className="card" style={{ display: 'flex', flexDirection: 'column', flex: 1, minHeight: 400 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
                <div style={{ fontWeight: 600 }}>Bài làm của bạn</div>
                <div style={{ fontSize: '0.85rem', color: wordCount < 10 ? 'var(--agen-secondary)' : 'var(--text-muted)' }}>
                  {wordCount} từ
                </div>
              </div>
              
              <textarea
                value={userText}
                onChange={(e) => setUserText(e.target.value)}
                disabled={evalLoading || !!evaluation}
                placeholder="Bắt đầu viết tại đây…"
                style={{
                  flex: 1,
                  width: '100%',
                  padding: 16,
                  borderRadius: 12,
                  border: '1px solid var(--border-subtle)',
                  outline: 'none',
                  background: 'var(--bg-elevated)',
                  color: 'var(--text-primary)',
                  fontSize: '1rem',
                  lineHeight: 1.6,
                  resize: 'none',
                  fontFamily: 'inherit'
                }}
              />

              {!evaluation && (
                <div style={{ marginTop: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ color: 'var(--agen-secondary)', fontSize: '0.85rem' }}>{error}</div>
                  <button 
                    className="btn btn-primary" 
                    onClick={handleSubmit} 
                    disabled={evalLoading || wordCount < 10}
                  >
                    {evalLoading ? 'Đang chấm điểm…' : 'Nộp bài'}
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Right Column: AI Evaluation (Only visible after submit) */}
          {evaluation && (
            <div className="animate-fade-in-up" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-md)' }}>
              
              {/* Score Card */}
              <div className="card" style={{ textAlign: 'center', padding: 'var(--spacing-xl)' }}>
                <div className="eyebrow" style={{ marginBottom: 8 }}>Xếp loại {evaluation.grade}</div>
                <div style={{ fontSize: '4rem', fontWeight: 700, letterSpacing: '-0.04em', lineHeight: 1, marginBottom: 12 }}>{evaluation.overall_score}<span style={{ fontSize: '1.5rem', color: 'var(--text-muted)', fontWeight: 500 }}>/100</span></div>
                <span className="xp-badge"><Star size={13} fill="currentColor" /> +{evaluation.xp_earned} XP</span>
                <p style={{ marginTop: 16, fontSize: '0.95rem' }}>“{evaluation.encouragement}”</p>
              </div>

              {evaluation.exam_band && <BandCard band={evaluation.exam_band} />}

              {/* Sub-scores */}
              <div className="card" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                <div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Grammar</div>
                  <div style={{ fontWeight: 600, fontSize: '1.4rem', letterSpacing: '-0.02em' }}>{evaluation.scores.grammar}/100</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Vocabulary</div>
                  <div style={{ fontWeight: 600, fontSize: '1.4rem', letterSpacing: '-0.02em' }}>{evaluation.scores.vocabulary}/100</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Coherence</div>
                  <div style={{ fontWeight: 600, fontSize: '1.4rem', letterSpacing: '-0.02em' }}>{evaluation.scores.coherence}/100</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Task Achievement</div>
                  <div style={{ fontWeight: 600, fontSize: '1.4rem', letterSpacing: '-0.02em' }}>{evaluation.scores.task_achievement}/100</div>
                </div>
              </div>

              {/* Detailed Feedback */}
              <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
                
                {evaluation.grammar_errors.length > 0 && (
                  <div>
                    <h4 style={{ marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}><CircleAlert size={17} color="var(--agen-secondary)" /> Lỗi ngữ pháp & sửa lỗi</h4>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                      {evaluation.grammar_errors.map((err, i) => (
                        <div key={i} style={{ padding: 14, background: 'var(--bg-elevated)', borderRadius: 12 }}>
                          <div style={{ textDecoration: 'line-through', color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: 4 }}>{err.original}</div>
                          <div style={{ color: 'var(--agen-success)', fontWeight: 600, fontSize: '0.95rem', marginBottom: 8 }}>{err.corrected}</div>
                          <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{err.explanation_vi}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div>
                  <h4 style={{ marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}><BookText size={17} color="var(--agen-primary)" /> Từ vựng & mạch lạc</h4>
                  <div style={{ padding: 14, background: 'var(--bg-elevated)', borderRadius: 12, marginBottom: 12, fontSize: '0.95rem', lineHeight: 1.5 }}>
                    <b>Từ vựng:</b> {evaluation.vocabulary_feedback}
                  </div>
                  <div style={{ padding: 14, background: 'var(--bg-elevated)', borderRadius: 12, fontSize: '0.95rem', lineHeight: 1.5 }}>
                    <b>Mạch lạc:</b> {evaluation.coherence_feedback}
                  </div>
                </div>

                <div>
                  <h4 style={{ marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}><Sparkles size={17} color="var(--agen-success)" /> Bản sửa hoàn chỉnh (tham khảo)</h4>
                  <div style={{ padding: 16, background: 'var(--bg-elevated)', borderRadius: 12, fontSize: '0.95rem', lineHeight: 1.6 }}>
                    {evaluation.corrected_version}
                  </div>
                </div>

                <Link href="/dashboard" className="btn btn-primary" style={{ textAlign: 'center', marginTop: 16 }}>
                  Hoàn thành & Về Dashboard
                </Link>
              </div>

            </div>
          )}

        </div>
      </div>
    </main>
  );
}

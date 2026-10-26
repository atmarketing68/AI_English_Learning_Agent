'use client';

import { useState } from 'react';
import Link from 'next/link';
import {
  getWritingPrompt, submitWriting,
  WritingPromptResponse, WritingEvaluationResponse
} from '@/lib/writingApiService';
import { notifyActivityCompleted } from '@/lib/services';
import { useAuthStore } from '@/store/authStore';
import { getMyProfile } from '@/lib/services';

export default function WritingPracticePage() {
  const { setLearner } = useAuthStore();
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
        <div className="card" style={{ maxWidth: 600, width: '100%' }}>
          <Link href="/dashboard" style={{ color: 'var(--text-muted)', display: 'block', marginBottom: 24 }}>← Về Dashboard</Link>
          <h2 style={{ marginBottom: 16 }}>✍️ Luyện Viết (AI Coach)</h2>
          <p style={{ color: 'var(--text-secondary)', marginBottom: 32 }}>
            Chọn một chủ đề để bắt đầu. AI sẽ tạo đề bài phù hợp với trình độ của bạn và chấm điểm chi tiết.
          </p>
          
          {error && <div style={{ color: 'var(--agen-secondary)', marginBottom: 16 }}>{error}</div>}
          
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            {[
              { id: 'opinion', label: 'Ý kiến / Quan điểm', emoji: '🗣️' },
              { id: 'narrative', label: 'Kể chuyện', emoji: '📖' },
              { id: 'descriptive', label: 'Miêu tả', emoji: '🎨' },
              { id: 'email', label: 'Viết thư / Email', emoji: '✉️' },
            ].map(g => (
              <button 
                key={g.id}
                className="btn btn-outline"
                style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: 24, gap: 12, height: 'auto' }}
                onClick={() => handleGetPrompt(g.id)}
                disabled={loading}
              >
                <div style={{ fontSize: '2rem' }}>{g.emoji}</div>
                <div style={{ fontWeight: 600 }}>{g.label}</div>
              </button>
            ))}
          </div>
          {loading && <div style={{ textAlign: 'center', marginTop: 24, fontStyle: 'italic', color: 'var(--text-muted)' }}>🤖 AI đang chuẩn bị đề bài...</div>}
        </div>
      </main>
    );
  }

  return (
    <main style={{ minHeight: '100vh', padding: 'var(--spacing-lg)' }}>
      <div className="container" style={{ maxWidth: 1200 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
          <button className="btn btn-ghost" onClick={() => setPromptData(null)}>← Đổi đề tài</button>
          <div className="level-badge">{promptData.level}</div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: evaluation ? '1fr 1fr' : '1fr', gap: 'var(--spacing-lg)' }}>
          
          {/* Left Column: Prompt & Editor */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-md)' }}>
            
            {/* Prompt Box */}
            <div className="card" style={{ background: 'var(--bg-elevated)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
                <span style={{ fontSize: '0.8rem', color: 'var(--agen-primary)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: 1 }}>{promptData.genre}</span>
                <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Mục tiêu: {promptData.word_target}</span>
              </div>
              <h3 style={{ marginBottom: 12, color: 'var(--agen-primary-light)' }}>{promptData.title}</h3>
              <p style={{ marginBottom: 20, fontSize: '1.1rem', lineHeight: 1.6 }}>{promptData.prompt}</p>
              
              <div style={{ padding: 16, background: 'rgba(108,99,255,0.06)', borderRadius: 8, borderLeft: '3px solid var(--agen-primary)' }}>
                <div style={{ fontWeight: 600, marginBottom: 8, fontSize: '0.9rem' }}>💡 Hướng dẫn (Scaffolding):</div>
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
                  {wordCount} words
                </div>
              </div>
              
              <textarea
                value={userText}
                onChange={(e) => setUserText(e.target.value)}
                disabled={evalLoading || !!evaluation}
                placeholder="Bắt đầu viết tại đây..."
                style={{
                  flex: 1,
                  width: '100%',
                  padding: 16,
                  borderRadius: 8,
                  border: '1px solid var(--border-subtle)',
                  background: 'var(--bg-base)',
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
                    {evalLoading ? '🤖 AI đang chấm điểm...' : '✅ Nộp bài'}
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Right Column: AI Evaluation (Only visible after submit) */}
          {evaluation && (
            <div className="animate-fade-in-up" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-md)' }}>
              
              {/* Score Card */}
              <div className="card-gradient" style={{ textAlign: 'center', padding: 'var(--spacing-xl)' }}>
                <div style={{ fontSize: '1.2rem', fontWeight: 600, color: 'var(--agen-primary-light)', marginBottom: 8 }}>{evaluation.grade} Grade</div>
                <div style={{ fontSize: '3rem', fontWeight: 900, marginBottom: 8 }}>{evaluation.overall_score}<span style={{ fontSize: '1.5rem', color: 'var(--text-muted)' }}>/100</span></div>
                <div style={{ fontSize: '1.1rem' }}>⭐ +{evaluation.xp_earned} XP</div>
                <div style={{ marginTop: 16, fontStyle: 'italic', fontSize: '0.95rem' }}>&quot;{evaluation.encouragement}&quot;</div>
              </div>

              {/* Sub-scores */}
              <div className="card" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                <div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Grammar</div>
                  <div style={{ fontWeight: 700, color: 'var(--agen-primary)' }}>{evaluation.scores.grammar}/100</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Vocabulary</div>
                  <div style={{ fontWeight: 700, color: 'var(--agen-primary)' }}>{evaluation.scores.vocabulary}/100</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Coherence</div>
                  <div style={{ fontWeight: 700, color: 'var(--agen-primary)' }}>{evaluation.scores.coherence}/100</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Task Achievement</div>
                  <div style={{ fontWeight: 700, color: 'var(--agen-primary)' }}>{evaluation.scores.task_achievement}/100</div>
                </div>
              </div>

              {/* Detailed Feedback */}
              <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
                
                {evaluation.grammar_errors.length > 0 && (
                  <div>
                    <h4 style={{ marginBottom: 12, color: 'var(--agen-secondary)', display: 'flex', alignItems: 'center', gap: 8 }}><span>⚠️</span> Lỗi Ngữ pháp & Sửa lỗi</h4>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                      {evaluation.grammar_errors.map((err, i) => (
                        <div key={i} style={{ padding: 12, background: 'var(--bg-elevated)', borderRadius: 8, borderLeft: '3px solid var(--agen-secondary)' }}>
                          <div style={{ textDecoration: 'line-through', color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: 4 }}>{err.original}</div>
                          <div style={{ color: 'var(--agen-success)', fontWeight: 600, fontSize: '0.95rem', marginBottom: 8 }}>{err.corrected}</div>
                          <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>💡 {err.explanation_vi}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div>
                  <h4 style={{ marginBottom: 12, color: 'var(--agen-primary-light)', display: 'flex', alignItems: 'center', gap: 8 }}><span>📚</span> Từ vựng & Mạch lạc</h4>
                  <div style={{ padding: 12, background: 'rgba(108,99,255,0.05)', borderRadius: 8, marginBottom: 12, fontSize: '0.95rem', lineHeight: 1.5 }}>
                    <b>Từ vựng:</b> {evaluation.vocabulary_feedback}
                  </div>
                  <div style={{ padding: 12, background: 'rgba(108,99,255,0.05)', borderRadius: 8, fontSize: '0.95rem', lineHeight: 1.5 }}>
                    <b>Mạch lạc:</b> {evaluation.coherence_feedback}
                  </div>
                </div>

                <div>
                  <h4 style={{ marginBottom: 12, color: 'var(--agen-success)', display: 'flex', alignItems: 'center', gap: 8 }}><span>✨</span> Bản sửa hoàn chỉnh (Tham khảo)</h4>
                  <div style={{ padding: 16, background: 'var(--bg-elevated)', borderRadius: 8, fontSize: '0.95rem', lineHeight: 1.6, fontStyle: 'italic', border: '1px solid var(--border-subtle)' }}>
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

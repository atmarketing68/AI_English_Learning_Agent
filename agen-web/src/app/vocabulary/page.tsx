'use client';

import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { motion } from 'framer-motion';
import {
  ArrowLeft, ArrowRight, BookMarked, CircleAlert, CircleCheck, Search, Trash2, Volume2,
} from 'lucide-react';
import { useAuthStore, useAuthHydrated } from '@/store/authStore';
import { PageSkeleton } from '@/components/Skeleton';
import { speakText } from '@/lib/speechService';
import { track } from '@/lib/analytics';
import {
  deleteNotebookItem, getNotebook, getReviewSummary, parseUtc,
  type NotebookItem, type NotebookKind, type ReviewSummary,
} from '@/lib/reviewService';

function strengthInfo(item: NotebookItem): { label: string; color: string; value: number } {
  if (item.mastered) return { label: 'Đã thuộc', color: 'var(--agen-success)', value: 100 };
  if (item.reps === 0) return { label: 'Mới', color: 'var(--text-muted)', value: 4 };
  const value = Math.max(item.mastery, 8);
  if (item.strength < 80) return { label: 'Sắp quên', color: 'var(--agen-secondary)', value };
  if (item.mastery >= 40) return { label: 'Nhớ tốt', color: 'var(--agen-primary)', value };
  return { label: 'Đang học', color: 'var(--agen-accent)', value };
}

function dueLabel(dueAt: string): string {
  const due = parseUtc(dueAt);
  const days = Math.ceil((due.getTime() - Date.now()) / 86_400_000);
  if (days <= 0) return 'Cần ôn hôm nay';
  if (days === 1) return 'Ôn ngày mai';
  return `Ôn sau ${days} ngày`;
}

export default function VocabularyPage() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();
  const hydrated = useAuthHydrated();

  const [kind, setKind] = useState<NotebookKind>('vocab');
  const [query, setQuery] = useState('');
  const [items, setItems] = useState<NotebookItem[] | null>(null);
  const [summary, setSummary] = useState<ReviewSummary | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!hydrated) return;
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }
    track('notebook_opened');
    getReviewSummary().then(setSummary).catch(() => undefined);
  }, [hydrated, isAuthenticated, router]);

  useEffect(() => {
    if (!hydrated || !isAuthenticated) return;
    let cancelled = false;
    getNotebook(kind)
      .then((page) => { if (!cancelled) { setItems(page.items); setError(''); } })
      .catch(() => { if (!cancelled) setError('Không tải được sổ. Vui lòng thử lại.'); });
    return () => { cancelled = true; };
  }, [hydrated, isAuthenticated, kind]);

  const visible = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!items || !q) return items ?? [];
    return items.filter((it) => it.front.toLowerCase().includes(q) || it.back.toLowerCase().includes(q));
  }, [items, query]);

  const remove = async (item: NotebookItem) => {
    if (!window.confirm(`Xoá “${item.front}” khỏi sổ? Mục này sẽ không xuất hiện khi ôn tập nữa.`)) return;
    try {
      await deleteNotebookItem(item.id);
      setItems((list) => list?.filter((it) => it.id !== item.id) ?? null);
    } catch {
      setError('Không xoá được. Vui lòng thử lại.');
    }
  };

  if (!summary && !items && !error) return <PageSkeleton maxWidth={880} cards={3} />;

  const switchKind = (k: NotebookKind) => { setItems(null); setKind(k); };

  return (
    <main className="notebook-page">
      <div className="container" style={{ padding: 0, maxWidth: 880 }}>
        <Link href="/dashboard" className="back-link"><ArrowLeft size={16} /> Trang chủ</Link>

        <div className="notebook-head">
          <div>
            <h1 style={{ fontSize: 'clamp(1.8rem, 4vw, 2.4rem)', marginBottom: 6 }}>Sổ từ vựng</h1>
            <p style={{ margin: 0 }}>Từ mới và câu làm sai được lưu tự động sau mỗi bài học.</p>
          </div>
          {summary && (
            <Link href="/review" className="btn btn-primary">
              {summary.due_count > 0 ? <>Ôn tập ngay · {summary.due_count}</> : 'Luyện tập'} <ArrowRight size={16} />
            </Link>
          )}
        </div>

        {summary && (
          <div className="notebook-stats">
            <div className="card"><strong>{summary.vocab_total}</strong><span>từ đã lưu</span></div>
            <div className="card"><strong>{summary.mastered_count}</strong><span>đã thuộc</span></div>
            <div className="card"><strong>{summary.due_count}</strong><span>cần ôn hôm nay</span></div>
          </div>
        )}

        <div className="notebook-toolbar">
          <div className="segmented" role="group" aria-label="Loại mục">
            <button type="button" aria-pressed={kind === 'vocab'} onClick={() => switchKind('vocab')}>
              Từ vựng{summary ? ` · ${summary.vocab_total}` : ''}
            </button>
            <button type="button" aria-pressed={kind === 'mistake'} onClick={() => switchKind('mistake')}>
              Lỗi sai{summary ? ` · ${summary.mistake_total}` : ''}
            </button>
          </div>
          <label className="notebook-search">
            <Search size={16} />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={kind === 'vocab' ? 'Tìm từ hoặc nghĩa…' : 'Tìm câu hỏi…'}
              aria-label="Tìm trong sổ"
            />
          </label>
        </div>

        {error && <div className="alert-error" style={{ marginBottom: 16 }}><CircleAlert size={16} /> {error}</div>}

        {!items ? (
          <PageSkeleton maxWidth={880} cards={2} />
        ) : visible.length === 0 ? (
          <div className="card notebook-empty">
            {kind === 'vocab' ? <BookMarked size={36} strokeWidth={1.5} /> : <CircleCheck size={36} strokeWidth={1.5} />}
            <h3>{query ? 'Không tìm thấy' : kind === 'vocab' ? 'Sổ từ vựng đang trống' : 'Chưa có lỗi sai nào'}</h3>
            <p>
              {query
                ? 'Thử từ khoá khác nhé.'
                : kind === 'vocab'
                ? 'Hoàn thành một bài học, các từ mới sẽ được lưu vào đây để ôn đúng lúc.'
                : 'Câu nào bạn trả lời sai trong bài học sẽ được lưu lại để luyện cho đến khi đúng.'}
            </p>
            {!query && <Link href="/learn" className="btn btn-primary">Học bài mới <ArrowRight size={16} /></Link>}
          </div>
        ) : (
          <motion.ul className="notebook-list" initial="hidden" animate="show" variants={{ show: { transition: { staggerChildren: 0.03 } } }}>
            {visible.map((item) => {
              const s = strengthInfo(item);
              return (
                <motion.li
                  key={item.id}
                  className="card notebook-item"
                  variants={{ hidden: { opacity: 0, y: 8 }, show: { opacity: 1, y: 0 } }}
                >
                  <div className="notebook-item-main">
                    {item.kind === 'vocab' ? (
                      <>
                        <div className="notebook-word">
                          <strong>{item.front}</strong>
                          {item.phonetic && <span className="notebook-phonetic">{item.phonetic}</span>}
                          <button type="button" className="icon-btn" aria-label={`Nghe “${item.front}”`} onClick={() => speakText(item.front)}>
                            <Volume2 size={16} />
                          </button>
                        </div>
                        <div className="notebook-meaning">{item.back}</div>
                        {item.example && <div className="notebook-example">“{item.example}”</div>}
                      </>
                    ) : (
                      <>
                        <div className="notebook-question">{item.front}</div>
                        <div className="notebook-answer"><CircleCheck size={15} /> {item.back}</div>
                        {item.last_wrong_answer && <div className="notebook-wrong">Bạn đã chọn: {item.last_wrong_answer}</div>}
                        {item.explanation && <div className="notebook-example">{item.explanation}</div>}
                      </>
                    )}
                  </div>
                  <div className="notebook-item-side">
                    <div className="notebook-strength">
                      <span style={{ color: s.color }}>{s.label}</span>
                      <div className="progress-bar"><div className="progress-fill" style={{ width: `${s.value}%`, background: s.color }} /></div>
                    </div>
                    <span className="notebook-due">{dueLabel(item.due_at)}</span>
                    <button type="button" className="icon-btn" aria-label="Xoá khỏi sổ" onClick={() => remove(item)}>
                      <Trash2 size={15} />
                    </button>
                  </div>
                </motion.li>
              );
            })}
          </motion.ul>
        )}
      </div>
    </main>
  );
}

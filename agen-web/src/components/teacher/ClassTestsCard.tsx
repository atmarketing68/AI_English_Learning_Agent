'use client';

/** G13 · Bài kiểm tra lớp: giao một đề thi thử cho cả lớp trong khoảng ngày, xem điểm từng học viên. */
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { ChevronDown, ChevronUp, CircleAlert, ClipboardCheck, LoaderCircle, Plus, Printer, Repeat, Trash2 } from 'lucide-react';
import Avatar from '@/components/ui/Avatar';
import {
  createGroupTest, deleteGroupTest, setGroupTestRepeat, getGroupTestResults, getGroupTests, getTestCatalogue, testScoreLabel,
  type ClassTest, type ClassTestResults, type TestCatalogueItem,
} from '@/lib/groupsService';
import { track } from '@/lib/analytics';

const SKILL_VI: Record<string, string> = { listening: 'Nghe', reading: 'Đọc', speaking: 'Nói' };
const STATUS_VI: Record<ClassTest['status'], string> = { upcoming: 'Sắp mở', open: 'Đang mở', closed: 'Đã đóng' };

const fmtDay = (iso: string) => new Date(`${iso}T00:00:00`).toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit' });
const isoDay = (d: Date) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;

function avgLabel(t: ClassTest): string {
  if (t.avg_estimate == null) return 'Chưa có bài';
  return `TB ${testScoreLabel(t.exam, { estimate: t.avg_estimate, pct: t.avg_pct })}`;
}

export default function ClassTestsCard({ groupId }: { groupId: string }) {
  const [tests, setTests] = useState<ClassTest[] | null>(null);
  const [catalogue, setCatalogue] = useState<TestCatalogueItem[]>([]);
  const [pick, setPick] = useState('');
  const [opensOn, setOpensOn] = useState('');
  const [dueOn, setDueOn] = useState('');
  const [note, setNote] = useState('');
  const [monthly, setMonthly] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [open, setOpen] = useState<string | null>(null);
  const [results, setResults] = useState<Record<string, ClassTestResults>>({});

  const load = () => getGroupTests(groupId).then(setTests).catch(() => setTests([]));
  useEffect(() => {
    load();
    getTestCatalogue().then(setCatalogue).catch(() => undefined);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [groupId]);

  const toggle = async (id: string) => {
    if (open === id) { setOpen(null); return; }
    setOpen(id);
    try {
      const r = await getGroupTestResults(groupId, id);
      setResults(prev => ({ ...prev, [id]: r }));
    } catch { /* the row still shows its summary */ }
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    const item = catalogue.find(c => `${c.kind}:${c.id}` === pick);
    if (!item || !dueOn) return;
    setBusy(true); setError('');
    try {
      await createGroupTest(groupId, { kind: item.kind, exam_id: item.id, due_on: dueOn, opens_on: opensOn || null, note: note || null, repeat: monthly ? 'monthly' : null });
      track('class_test_created', { kind: item.kind, exam: item.exam });
      setPick(''); setOpensOn(''); setDueOn(''); setNote(''); setMonthly(false);
      await load();
    } catch (err: unknown) {
      setError((err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Không giao được bài kiểm tra.');
    } finally { setBusy(false); }
  };

  const toggleRepeat = async (t: ClassTest) => {
    try {
      const next = await setGroupTestRepeat(groupId, t.id, t.repeat ? null : 'monthly');
      track('class_test_repeat_set', { on: !!next.repeat });
      setTests(prev => prev?.map(x => (x.id === t.id ? { ...x, repeat: next.repeat } : x)) ?? prev);
    } catch { setError('Chưa đổi được chế độ lặp lại.'); }
  };

  const remove = async (t: ClassTest) => {
    if (!confirm(`Xoá bài kiểm tra "${t.title}"? Bài làm vẫn còn trong lịch sử của học viên.`)) return;
    await deleteGroupTest(groupId, t.id);
    await load();
  };

  const groups: { label: string; items: TestCatalogueItem[] }[] = [
    { label: 'Nghe / Đọc', items: catalogue.filter(c => c.kind === 'mock') },
    { label: 'Nói (Speaking)', items: catalogue.filter(c => c.kind === 'speaking') },
  ];

  return (
    <>
      <h3 style={{ margin: '0 0 10px', display: 'flex', alignItems: 'center', gap: 8 }}><ClipboardCheck size={20} /> Bài kiểm tra lớp</h3>
      <form onSubmit={submit} className="card" style={{ display: 'grid', gap: 10, marginBottom: 'var(--spacing-md)' }}>
        <div className="class-test-form">
          <select className="form-input" value={pick} onChange={e => setPick(e.target.value)} aria-label="Đề thi" required>
            <option value="">Chọn đề thi thử…</option>
            {groups.map(g => g.items.length > 0 && (
              <optgroup key={g.label} label={g.label}>
                {g.items.map(c => <option key={`${c.kind}:${c.id}`} value={`${c.kind}:${c.id}`}>{c.title} · {c.minutes} phút</option>)}
              </optgroup>
            ))}
          </select>
          <label className="test-date-field"><span>Mở từ</span>
            <input className="form-input" type="date" value={opensOn} min={isoDay(new Date())} onChange={e => setOpensOn(e.target.value)} aria-label="Ngày mở đề" />
          </label>
          <label className="test-date-field"><span>Hạn nộp</span>
            <input className="form-input" type="date" value={dueOn} min={opensOn || isoDay(new Date())} onChange={e => setDueOn(e.target.value)} aria-label="Hạn nộp bài kiểm tra" required />
          </label>
        </div>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <input className="form-input" placeholder="Ghi chú (Kiểm tra tháng 11 — làm trong 1 lần)" value={note} onChange={e => setNote(e.target.value)} maxLength={500} style={{ flex: '1 1 240px' }} />
          <label className="test-repeat-toggle"><input type="checkbox" checked={monthly} onChange={e => setMonthly(e.target.checked)} /> <Repeat size={14} /> Lặp lại hằng tháng</label>
          <button type="submit" className="btn btn-primary" disabled={busy || !pick || !dueOn}>{busy ? <LoaderCircle className="animate-spin" size={16} /> : <Plus size={16} />} Giao bài kiểm tra</button>
        </div>
        {error && <div className="alert-error"><CircleAlert size={16} /> {error}</div>}
        <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Cả lớp nhận thông báo; lần làm đầu tiên trong thời hạn được tính điểm và không trừ lượt thi miễn phí. Sáng ngày hết hạn, ai chưa làm sẽ được nhắc. Chọn “Lặp lại hằng tháng” để hệ thống tự giao đề mới (đề chưa làm) cùng khung ngày vào tháng sau.</div>
      </form>

      {tests && tests.length > 0 && (
        <div className="card" style={{ padding: 0, marginBottom: 'var(--spacing-lg)', overflow: 'hidden' }}>
          {tests.map((t, i) => {
            const r = results[t.id];
            return (
              <div key={t.id} style={{ borderTop: i ? '1px solid var(--border-subtle)' : 'none' }}>
                <div className="class-test-row">
                  <button type="button" className="class-test-main" onClick={() => toggle(t.id)} aria-expanded={open === t.id}>
                    <span style={{ fontWeight: 600 }}>{t.title}</span>
                    <span className="class-test-meta">
                      <span className={`plan-chip test-status-${t.status}`}>{STATUS_VI[t.status]}</span>
                      {t.skill && <span>{SKILL_VI[t.skill] ?? t.skill}</span>}
                      {t.repeat && <span style={{ display: 'inline-flex', alignItems: 'center', gap: 3 }}><Repeat size={12} /> hằng tháng</span>}
                      <span>{fmtDay(t.opens_on)} → {fmtDay(t.due_on)}</span>
                      <span>{avgLabel(t)}</span>
                    </span>
                  </button>
                  <div style={{ textAlign: 'right', fontSize: '0.85rem', flexShrink: 0 }}>
                    <strong>{t.done_count}/{t.member_count}</strong><div style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>đã làm</div>
                  </div>
                  {open === t.id ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                  <button type="button" className="icon-btn" aria-label="Xoá bài kiểm tra" onClick={() => remove(t)}><Trash2 size={15} /></button>
                </div>
                {open === t.id && (
                  <div style={{ padding: '0 16px 14px' }}>
                    {t.note && <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: 8 }}>{t.note}</div>}
                    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 10 }}>
                      <Link href={`/teacher/${groupId}/tests/${t.id}`} className="btn btn-outline btn-sm" onClick={() => track('class_test_sheet_printed')}><Printer size={14} /> In bảng điểm</Link>
                      {!t.next_test_id && (
                        <button type="button" className="btn btn-ghost btn-sm" onClick={() => toggleRepeat(t)}>
                          <Repeat size={14} /> {t.repeat ? 'Đang lặp hằng tháng · Dừng' : 'Lặp lại hằng tháng'}
                        </button>
                      )}
                    </div>
                    {!r ? <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}><LoaderCircle className="animate-spin" size={14} /> Đang tải điểm…</div> : (
                      <div style={{ overflowX: 'auto' }}>
                        {r.max_estimate != null && (
                          <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginBottom: 6 }}>
                            Cao nhất {testScoreLabel(r.exam, { estimate: r.max_estimate, pct: null })} · thấp nhất {testScoreLabel(r.exam, { estimate: r.min_estimate, pct: null })}
                          </div>
                        )}
                        <table className="teacher-table">
                          <thead><tr><th>Học viên</th><th>Kết quả</th><th>Thời gian</th><th>Nộp lúc</th></tr></thead>
                          <tbody>
                            {r.results.map(row => (
                              <tr key={row.learner_id}>
                                <td><span className="teacher-member-link"><Avatar avatar={row.avatar} name={row.display_name} size={24} /> {row.display_name}</span></td>
                                <td>{row.done ? <strong>{testScoreLabel(r.exam, row)}</strong> : <span style={{ color: 'var(--text-muted)' }}>Chưa làm</span>}</td>
                                <td>{row.seconds ? `${Math.round(row.seconds / 60)} phút` : '—'}</td>
                                <td>{row.submitted_at ? new Date(`${row.submitted_at}Z`).toLocaleString('vi-VN', { timeZone: 'Asia/Ho_Chi_Minh', day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }) : '—'}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </>
  );
}

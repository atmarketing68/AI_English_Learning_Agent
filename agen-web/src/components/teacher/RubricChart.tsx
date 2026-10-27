'use client';

/**
 * G13 · Tiến bộ band IELTS Writing theo thời gian (giáo viên xem một học viên).
 * Overall in ink, the four criteria in the validated categorical slots; crosshair tooltip on hover,
 * legend toggles, and a table view (two criteria colours sit under 3:1 on the light surface).
 */
import { useMemo, useState } from 'react';
import { IELTS_CRITERIA, type IeltsRubric, type RubricPoint } from '@/lib/groupsService';

type Key = 'overall' | keyof IeltsRubric;
const SERIES: { key: Key; label: string; color: string; width: number }[] = [
  { key: 'overall', label: 'Overall', color: 'var(--rv-overall)', width: 2.5 },
  ...IELTS_CRITERIA.map(c => ({ key: c.key as Key, label: c.label, color: `var(--rv-${c.key})`, width: 2 })),
];

const W = 640, H = 220, PAD = { l: 34, r: 16, t: 14, b: 28 };
const shortDay = (s: string) => new Date(s.endsWith('Z') ? s : `${s}Z`).toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit' });
const value = (p: RubricPoint, k: Key) => (k === 'overall' ? p.overall : p.criteria[k] ?? null);

export default function RubricChart({ points, onOpen }: { points: RubricPoint[]; onOpen?: (submissionId: string) => void }) {
  const [hidden, setHidden] = useState<Set<Key>>(new Set());
  const [hover, setHover] = useState<number | null>(null);
  const [table, setTable] = useState(false);

  const { lo, hi } = useMemo(() => {
    const vals = points.flatMap(p => SERIES.map(s => value(p, s.key)).filter((v): v is number => v != null));
    let lo = Math.max(0, Math.floor(Math.min(...vals)) - 0.5), hi = Math.min(9, Math.ceil(Math.max(...vals)) + 0.5);
    if (hi - lo < 2) { lo = Math.max(0, hi - 2); hi = Math.min(9, lo + 2); }
    return { lo, hi };
  }, [points]);

  const x = (i: number) => PAD.l + (points.length === 1 ? (W - PAD.l - PAD.r) / 2 : (i * (W - PAD.l - PAD.r)) / (points.length - 1));
  const y = (v: number) => PAD.t + ((hi - v) * (H - PAD.t - PAD.b)) / (hi - lo);
  const ticks: number[] = [];
  for (let v = Math.ceil(lo); v <= hi; v += 1) ticks.push(v);
  const labelEvery = Math.max(1, Math.ceil(points.length / 6));
  const first = points[0], last = points[points.length - 1];
  const delta = points.length > 1 ? last.overall - first.overall : 0;

  const pick = (e: React.PointerEvent<SVGRectElement>) => {
    const rect = e.currentTarget.ownerSVGElement!.getBoundingClientRect();
    const px = ((e.clientX - rect.left) / rect.width) * W;
    let best = 0;
    points.forEach((_, i) => { if (Math.abs(x(i) - px) < Math.abs(x(best) - px)) best = i; });
    setHover(best);
  };

  return (
    <section className="card" style={{ marginTop: 14 }}>
      <div className="section-head" style={{ display: 'flex', alignItems: 'baseline', gap: 10, flexWrap: 'wrap' }}>
        <h3 style={{ margin: 0, flex: 1 }}>Tiến bộ IELTS Writing</h3>
        <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
          Gần nhất <strong style={{ color: 'var(--text-primary)' }}>band {last.overall.toFixed(1)}</strong>
          {points.length > 1 && <> · {delta >= 0 ? '+' : ''}{delta.toFixed(1)} so với bài đầu</>}
        </span>
        <button type="button" className="btn btn-outline btn-sm" onClick={() => setTable(t => !t)}>{table ? 'Xem biểu đồ' : 'Xem bảng'}</button>
      </div>

      {table ? (
        <div style={{ overflowX: 'auto' }}>
          <table className="teacher-table">
            <thead><tr><th>Bài</th><th>Ngày</th><th>Nguồn</th>{SERIES.map(s => <th key={s.key}>{s.label}</th>)}</tr></thead>
            <tbody>{[...points].reverse().map(p => (
              <tr key={p.submission_id}>
                <td>{onOpen ? <button type="button" className="teacher-member-link" onClick={() => onOpen(p.submission_id)}>{p.title}</button> : p.title}</td>
                <td>{shortDay(p.created_at)}</td><td>{p.source === 'teacher' ? 'Giáo viên' : 'AI'}</td>
                {SERIES.map(s => <td key={s.key}>{value(p, s.key)?.toFixed(1) ?? '—'}</td>)}
              </tr>
            ))}</tbody>
          </table>
        </div>
      ) : (
        <div className="rubric-viz">
          <svg viewBox={`0 0 ${W} ${H}`} className="rubric-chart" role="img" aria-label={`Band IELTS Writing qua ${points.length} bài, gần nhất ${last.overall}`}>
            {ticks.map(t => (
              <g key={t}>
                <line className="grid-line" x1={PAD.l} x2={W - PAD.r} y1={y(t)} y2={y(t)} />
                <text x={PAD.l - 8} y={y(t) + 4} textAnchor="end">{t}</text>
              </g>
            ))}
            {points.map((p, i) => (i % labelEvery === 0 || i === points.length - 1) && (
              <text key={p.submission_id} x={x(i)} y={H - 8} textAnchor="middle">{shortDay(p.created_at)}</text>
            ))}
            {hover != null && <line x1={x(hover)} x2={x(hover)} y1={PAD.t} y2={H - PAD.b} stroke="var(--text-muted)" strokeDasharray="3 3" />}
            {SERIES.filter(s => !hidden.has(s.key)).map(s => {
              const pts = points.map((p, i) => [i, value(p, s.key)] as const).filter((v): v is readonly [number, number] => v[1] != null);
              return (
                <g key={s.key}>
                  {pts.length > 1 && <polyline fill="none" stroke={s.color} strokeWidth={s.width} strokeLinejoin="round" strokeLinecap="round" points={pts.map(([i, v]) => `${x(i)},${y(v)}`).join(' ')} />}
                  {pts.map(([i, v]) => (
                    <circle key={i} cx={x(i)} cy={y(v)} r={hover === i ? 5 : 4} fill={s.color} stroke="var(--bg-surface)" strokeWidth={2}>
                      {points[i].source === 'teacher' && s.key === 'overall' ? <title>Giáo viên chấm</title> : null}
                    </circle>
                  ))}
                </g>
              );
            })}
            {!hidden.has('overall') && <text x={x(points.length - 1)} y={y(last.overall) - 10} textAnchor="middle" style={{ fill: 'var(--text-primary)', fontWeight: 600 }}>{last.overall.toFixed(1)}</text>}
            <rect x={PAD.l - 10} y={0} width={W - PAD.l - PAD.r + 20} height={H} fill="transparent"
              onPointerMove={pick} onPointerLeave={() => setHover(null)}
              onClick={() => { if (hover != null && onOpen) onOpen(points[hover].submission_id); }}
              style={{ cursor: onOpen ? 'pointer' : 'default' }} />
          </svg>
          {hover != null && (
            <div className="rubric-tip" style={{ left: `clamp(0px, calc(${(x(hover) / W) * 100}% - 85px), calc(100% - 180px))` }}>
              <div><strong>{points[hover].title}</strong></div>
              <div>{shortDay(points[hover].created_at)} · {points[hover].source === 'teacher' ? 'giáo viên chấm' : 'AI chấm'}</div>
              {SERIES.map(s => {
                const v = value(points[hover], s.key);
                return v == null ? null : <div key={s.key}><i style={{ background: s.color }} /><strong>{v.toFixed(1)}</strong> {s.label}</div>;
              })}
            </div>
          )}
          <div className="rubric-legend">
            {SERIES.map(s => (
              <button key={s.key} type="button" aria-pressed={!hidden.has(s.key)}
                onClick={() => setHidden(h => { const n = new Set(h); if (n.has(s.key)) n.delete(s.key); else n.add(s.key); return n; })}>
                <i style={{ background: s.color, height: s.key === 'overall' ? 4 : 3 }} /> {s.label}
              </button>
            ))}
          </div>
          {points.length === 1 && <p style={{ margin: '6px 0 0', fontSize: '0.8rem', color: 'var(--text-muted)' }}>Cần ít nhất 2 bài IELTS để thấy xu hướng.</p>}
        </div>
      )}
    </section>
  );
}

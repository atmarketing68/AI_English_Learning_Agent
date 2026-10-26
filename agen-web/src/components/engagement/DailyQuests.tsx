'use client';

import { useState } from 'react';
import Link from 'next/link';
import confetti from 'canvas-confetti';
import {
  BookOpen, Brain, CircleCheck, ListChecks, Mic, Star, Target, Trophy, type LucideIcon,
} from 'lucide-react';
import { claimQuest, type Engagement, type Quest } from '@/lib/engagementService';
import { playSound } from '@/lib/soundEffects';
import { track } from '@/lib/analytics';

const QUEST_ICONS: Record<Quest['icon'], LucideIcon> = {
  book: BookOpen, brain: Brain, target: Target, star: Star, trophy: Trophy, mic: Mic,
};

const QUEST_LINKS: Record<string, string> = {
  lesson: '/learn', perfect: '/learn', correct: '/learn', xp: '/learn',
  review: '/review', speaking: '/practice/speaking',
};

/**
 * The three daily quests with claim buttons.
 * `compact` drops the card chrome so it can sit inside a result screen.
 */
export default function DailyQuests({
  state, onChange, compact = false,
}: {
  state: Engagement;
  onChange: (next: Engagement) => void;
  compact?: boolean;
}) {
  const [claiming, setClaiming] = useState<string | null>(null);
  const [error, setError] = useState('');
  const done = state.quests.filter(q => q.claimed).length;
  const allDone = done === state.quests.length;

  const claim = async (quest: Quest) => {
    setClaiming(quest.id);
    setError('');
    try {
      const res = await claimQuest(quest.id);
      playSound('success');
      confetti({ particleCount: 50, spread: 60, origin: { y: 0.7 }, colors: ['#D97A00', '#FF9F0A', '#1F9D55'] });
      track('quest_claimed', { code: quest.code, xp: res.xp_awarded });
      onChange(res.state);
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(detail || 'Không nhận được thưởng, thử lại nhé.');
    } finally {
      setClaiming(null);
    }
  };

  const body = (
    <>
      <div className="quests-head">
        <div className="eyebrow" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <ListChecks size={14} /> Nhiệm vụ hôm nay
        </div>
        <span className="quests-count">{done}/{state.quests.length}</span>
      </div>

      <ul className="quest-list">
        {state.quests.map((q) => {
          const Icon = QUEST_ICONS[q.icon] || Target;
          const pct = Math.round((q.progress / q.target) * 100);
          return (
            <li key={q.id} className="quest" data-state={q.claimed ? 'claimed' : q.completed ? 'ready' : 'open'}>
              <span className="quest-icon"><Icon size={18} strokeWidth={1.9} /></span>
              <div className="quest-main">
                {q.completed || q.claimed ? (
                  <span className="quest-title">{q.title}</span>
                ) : (
                  <Link href={QUEST_LINKS[q.code] || '/learn'} className="quest-title">{q.title}</Link>
                )}
                <div className="quest-progress">
                  <div className="progress-bar"><div className="progress-fill" style={{ width: `${pct}%` }} /></div>
                  <span>{q.progress}/{q.target}</span>
                </div>
              </div>
              {q.claimed ? (
                <span className="quest-claimed"><CircleCheck size={16} /> Đã nhận</span>
              ) : q.completed ? (
                <button type="button" className="btn btn-primary btn-sm quest-claim" onClick={() => claim(q)} disabled={claiming === q.id}>
                  Nhận +{q.xp_reward} XP
                </button>
              ) : (
                <span className="quest-reward"><Star size={12} fill="currentColor" /> {q.xp_reward}</span>
              )}
            </li>
          );
        })}
      </ul>

      {allDone && <div className="quests-done">Hoàn thành cả 3 nhiệm vụ hôm nay. Tuyệt vời!</div>}
      {error && <div className="alert-error" style={{ marginTop: 10 }}>{error}</div>}
    </>
  );

  if (compact) return <div className="quests-compact">{body}</div>;
  return (
    <div className="card" style={{ padding: 'var(--spacing-xl)', borderRadius: 'var(--radius-xl)', display: 'flex', flexDirection: 'column' }}>
      {body}
    </div>
  );
}

'use client';

import { useEffect, useState } from 'react';
import { BellRing, ChevronDown, ChevronUp } from 'lucide-react';
import ReminderSettingsForm, { hourLabel } from '@/components/engagement/ReminderSettingsForm';
import { getReminderSettings, type ReminderSettings } from '@/lib/reminderService';

/** Dashboard card: one-line summary of the daily reminder, expands to edit it. */
export default function ReminderCard() {
  const [settings, setSettings] = useState<ReminderSettings | null>(null);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    getReminderSettings().then(setSettings).catch(() => undefined);
  }, []);

  if (!settings) return null;
  const summary = settings.hour === null
    ? 'Chưa bật — chọn giờ để không quên học mỗi ngày'
    : `Mỗi ngày lúc ${hourLabel(settings.hour)}${settings.email ? ' · có email' : ''}`;

  return (
    <div className="card reminder-card">
      <button type="button" className="reminder-card-head" onClick={() => setOpen(!open)} aria-expanded={open}>
        <span className="icon-tile" style={{ width: 40, height: 40, background: 'var(--bg-tint)', color: 'var(--agen-primary)' }}>
          <BellRing size={20} strokeWidth={1.8} />
        </span>
        <span style={{ flex: 1, minWidth: 0, textAlign: 'left' }}>
          <span className="reminder-card-title">Nhắc học</span>
          <span className="reminder-card-sub">{summary}</span>
        </span>
        <span className="reminder-card-action">{open ? <ChevronUp size={18} /> : settings.hour === null ? 'Bật' : <ChevronDown size={18} />}</span>
      </button>
      {open && <div style={{ marginTop: 16 }}><ReminderSettingsForm onSaved={setSettings} /></div>}
    </div>
  );
}

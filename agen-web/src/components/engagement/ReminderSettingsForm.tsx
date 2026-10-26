'use client';

import { useEffect, useState } from 'react';
import { BellRing, CircleCheck, Mail, Send, Smartphone } from 'lucide-react';
import {
  PushDeniedError, currentPushState, disablePush, enablePush, getReminderSettings,
  saveReminderSettings, sendTestReminder, type PushState, type ReminderSettings,
} from '@/lib/reminderService';
import { track } from '@/lib/analytics';

const PRESETS = [
  { hour: 7, label: '7:00', hint: 'Buổi sáng' },
  { hour: 12, label: '12:00', hint: 'Giờ trưa' },
  { hour: 19, label: '19:00', hint: 'Buổi tối' },
  { hour: 21, label: '21:00', hint: 'Trước khi ngủ' },
];

export const hourLabel = (h: number) => `${h}:00`;

/** Pick the daily reminder hour and channels. Every change is saved at once. */
export default function ReminderSettingsForm({ onSaved }: { onSaved?: (s: ReminderSettings) => void }) {
  const [settings, setSettings] = useState<ReminderSettings | null>(null);
  const [push, setPush] = useState<PushState>('off');
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    getReminderSettings().then(setSettings).catch(() => setError('Không tải được cài đặt nhắc học.'));
    currentPushState().then(setPush).catch(() => undefined);
  }, []);

  const apply = (s: ReminderSettings) => { setSettings(s); onSaved?.(s); };

  const save = async (hour: number | null, email: boolean) => {
    setBusy(true);
    setError('');
    setNotice('');
    try {
      apply(await saveReminderSettings(hour, email));
      track('reminder_set', { hour, email });
    } catch {
      setError('Không lưu được, thử lại nhé.');
    } finally {
      setBusy(false);
    }
  };

  const togglePush = async () => {
    if (!settings?.push_public_key) return;
    setBusy(true);
    setError('');
    setNotice('');
    try {
      if (push === 'on') {
        const next = await disablePush();
        if (next) apply(next);
        setPush('off');
      } else {
        apply(await enablePush(settings.push_public_key));
        setPush('on');
        track('reminder_push_enabled');
      }
    } catch (err) {
      if (err instanceof PushDeniedError) {
        setPush('denied');
        setError('Trình duyệt đang chặn thông báo. Mở cài đặt trang web để cho phép rồi thử lại.');
      } else {
        setError('Không bật được thông báo trên thiết bị này.');
      }
    } finally {
      setBusy(false);
    }
  };

  const test = async () => {
    setBusy(true);
    setError('');
    setNotice('');
    try {
      const res = await sendTestReminder();
      const parts = [res.push ? 'thông báo' : '', res.email ? 'email' : ''].filter(Boolean);
      setNotice(parts.length ? `Đã gửi thử ${parts.join(' và ')}.` : 'Chưa có kênh nào để gửi thử.');
    } catch {
      setError('Gửi thử quá nhiều lần, đợi một phút nhé.');
    } finally {
      setBusy(false);
    }
  };

  if (!settings) return error ? <div className="alert-error">{error}</div> : <div className="reminder-loading">Đang tải…</div>;

  const hour = settings.hour;
  const isPreset = hour !== null && PRESETS.some(p => p.hour === hour);
  const channelsOn = (push === 'on' && settings.push_available) || (settings.email && settings.email_available);

  return (
    <div className="reminder-form">
      <div className="reminder-hours" role="group" aria-label="Giờ nhắc học">
        {PRESETS.map(p => (
          <button key={p.hour} type="button" className="reminder-hour" aria-pressed={hour === p.hour}
            onClick={() => save(p.hour, settings.email)} disabled={busy}>
            <strong>{p.label}</strong><span>{p.hint}</span>
          </button>
        ))}
        <label className="reminder-hour reminder-other" data-active={hour !== null && !isPreset}>
          <span>Giờ khác</span>
          <select
            value={hour !== null && !isPreset ? hour : ''}
            onChange={(e) => save(e.target.value === '' ? null : Number(e.target.value), settings.email)}
            disabled={busy}
            aria-label="Chọn giờ khác"
          >
            <option value="">--</option>
            {Array.from({ length: 18 }, (_, i) => i + 5).map(h => <option key={h} value={h}>{hourLabel(h)}</option>)}
          </select>
        </label>
      </div>

      {hour !== null && (
        <>
          <div className="reminder-channels">
            {settings.push_available && (
              <div className="reminder-channel">
                <Smartphone size={18} />
                <div>
                  <div className="reminder-channel-title">Thông báo trên thiết bị này</div>
                  <div className="reminder-channel-sub">
                    {push === 'unsupported'
                      ? 'Trình duyệt này chưa hỗ trợ. Trên iPhone: thêm ứng dụng vào màn hình chính trước.'
                      : push === 'denied'
                      ? 'Đang bị chặn trong cài đặt trình duyệt.'
                      : 'Nhắc ngay trên điện thoại hoặc máy tính.'}
                  </div>
                </div>
                <button type="button" className="switch" role="switch" aria-checked={push === 'on'}
                  onClick={togglePush} disabled={busy || push === 'unsupported'} aria-label="Thông báo trên thiết bị này" />
              </div>
            )}
            {settings.email_available && (
              <div className="reminder-channel">
                <Mail size={18} />
                <div>
                  <div className="reminder-channel-title">Email nhắc học</div>
                  <div className="reminder-channel-sub">Gửi đến {settings.email_address}</div>
                </div>
                <button type="button" className="switch" role="switch" aria-checked={settings.email}
                  onClick={() => save(hour, !settings.email)} disabled={busy} aria-label="Email nhắc học" />
              </div>
            )}
            {!settings.push_available && !settings.email_available && (
              <div className="reminder-channel-sub">
                <BellRing size={14} /> Đã lưu giờ nhắc. Bạn sẽ thấy lời nhắc trong chuông thông báo khi mở ứng dụng.
              </div>
            )}
          </div>

          <div className="reminder-foot">
            <span><CircleCheck size={15} color="var(--agen-success)" /> Nhắc lúc {hourLabel(hour)} nếu hôm đó bạn chưa học</span>
            <div style={{ display: 'flex', gap: 8 }}>
              {channelsOn && (
                <button type="button" className="btn btn-ghost btn-sm" onClick={test} disabled={busy}><Send size={14} /> Gửi thử</button>
              )}
              <button type="button" className="btn btn-ghost btn-sm" onClick={() => save(null, false)} disabled={busy}>Tắt nhắc</button>
            </div>
          </div>
        </>
      )}

      {notice && <div className="reminder-notice">{notice}</div>}
      {error && <div className="alert-error" style={{ marginTop: 10 }}>{error}</div>}
    </div>
  );
}

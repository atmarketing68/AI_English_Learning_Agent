'use client';

import { useState } from 'react';
import Image from 'next/image';
import { Share, SquarePlus, X } from 'lucide-react';
import { promptInstall, useInstallState } from '@/lib/pwa';

const DISMISS_KEY = 'agen-install-card-dismissed';

function wasDismissed(): boolean {
  try { return localStorage.getItem(DISMISS_KEY) === '1'; } catch { return false; }
}

/** Invites the learner to install the app; on iPhone, explains Add to Home Screen. */
export default function InstallAppCard() {
  const state = useInstallState();
  const [dismissed, setDismissed] = useState(wasDismissed);
  const [showSteps, setShowSteps] = useState(false);

  if (dismissed || state === 'installed' || state === 'none') return null;

  const dismiss = () => {
    setDismissed(true);
    try { localStorage.setItem(DISMISS_KEY, '1'); } catch { /* private mode */ }
  };

  return (
    <div className="card install-card">
      <Image src="/icons/icon-192.png" alt="" width={48} height={48} className="install-icon" />
      <div style={{ flex: 1, minWidth: 0 }}>
        <div className="install-title">Cài AI AGENT ENGLISH lên điện thoại</div>
        <div className="install-sub">Mở nhanh từ màn hình chính, toàn màn hình và nhận nhắc học mỗi ngày.</div>
        {state === 'ios' && showSteps && (
          <ol className="install-steps">
            <li>Nhấn nút <Share size={14} /> <strong>Chia sẻ</strong> ở thanh dưới của Safari</li>
            <li>Chọn <SquarePlus size={14} /> <strong>Thêm vào MH chính</strong></li>
            <li>Nhấn <strong>Thêm</strong>, rồi mở ứng dụng từ màn hình chính</li>
          </ol>
        )}
      </div>
      <div className="install-actions">
        {state === 'prompt' ? (
          <button type="button" className="btn btn-primary btn-sm" onClick={() => promptInstall()}>Cài đặt</button>
        ) : (
          <button type="button" className="btn btn-primary btn-sm" onClick={() => setShowSteps(!showSteps)}>
            {showSteps ? 'Đã hiểu' : 'Xem cách cài'}
          </button>
        )}
        <button type="button" className="icon-btn" aria-label="Ẩn" onClick={dismiss}><X size={16} /></button>
      </div>
    </div>
  );
}

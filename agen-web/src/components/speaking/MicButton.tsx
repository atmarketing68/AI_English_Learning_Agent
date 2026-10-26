'use client';

import { Mic, Square } from 'lucide-react';

interface Props {
  listening: boolean;
  disabled?: boolean;
  onClick: () => void;
  size?: number;
  label?: string;
}

/** Tap-to-start / tap-to-stop microphone (works with mouse and touch alike). */
export default function MicButton({ listening, disabled, onClick, size = 88, label }: Props) {
  return (
    <button
      type="button"
      className="mic-button"
      data-on={listening}
      style={{ width: size, height: size }}
      onClick={onClick}
      disabled={disabled}
      aria-label={label ?? (listening ? 'Dừng ghi âm' : 'Bắt đầu nói')}
    >
      {listening ? <Square size={size * 0.3} fill="currentColor" /> : <Mic size={size * 0.36} />}
    </button>
  );
}

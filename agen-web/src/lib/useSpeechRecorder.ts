'use client';

/**
 * G2 · One microphone hook for every "say it" surface (speaking steps, shadowing,
 * placement). Wraps SpeechRecognizer with transcript, timing and a friendly error.
 */
import { useCallback, useEffect, useRef, useState } from 'react';
import { SpeechRecognizer } from '@/lib/speechService';

export interface SpeechRecorder {
  supported: boolean;
  listening: boolean;
  transcript: string;
  /** Seconds between start and stop of the last take (0 while recording). */
  duration: number;
  error: string;
  start: () => void;
  stop: () => void;
  reset: () => void;
}

function describeError(err: string): string {
  if (err === 'not-allowed' || err === 'service-not-allowed') return 'Hãy cho phép trang web dùng micro để luyện nói.';
  if (err === 'no-speech') return 'Không nghe thấy gì. Hãy nói to và rõ hơn một chút.';
  if (err === 'audio-capture') return 'Không tìm thấy micro trên thiết bị này.';
  if (err === 'network') return 'Nhận giọng nói cần kết nối mạng. Hãy kiểm tra lại.';
  if (err === 'aborted') return '';
  return `Lỗi micro: ${err}`;
}

export interface SpeechRecorderOptions {
  /** Called once per take when recognition ends with a non-empty transcript. */
  onFinish?: (transcript: string, durationSeconds: number) => void;
}

export function useSpeechRecorder(options: SpeechRecorderOptions = {}): SpeechRecorder {
  const recognizer = useRef<SpeechRecognizer | null>(null);
  const startedAt = useRef<number>(0);
  const transcriptRef = useRef('');
  const onFinishRef = useRef(options.onFinish);
  const finished = useRef(false);
  useEffect(() => { onFinishRef.current = options.onFinish; });
  const [supported, setSupported] = useState(true);
  const [listening, setListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [duration, setDuration] = useState(0);
  const [error, setError] = useState('');

  useEffect(() => {
    const rec = new SpeechRecognizer(
      (r) => { transcriptRef.current = r.transcript; setTranscript(r.transcript); },
      (err) => { setError(describeError(err)); setListening(false); },
      () => {
        setListening(false);
        const secs = startedAt.current ? (Date.now() - startedAt.current) / 1000 : 0;
        if (startedAt.current) setDuration(secs);
        const text = transcriptRef.current.trim();
        if (text && !finished.current) {
          finished.current = true;
          onFinishRef.current?.(text, secs);
        }
      },
    );
    recognizer.current = rec;
    const ok = rec.isSupported();
    queueMicrotask(() => setSupported(ok));
    return () => rec.stop();
  }, []);

  const start = useCallback(() => {
    const rec = recognizer.current;
    if (!rec) return;
    setError('');
    setTranscript('');
    transcriptRef.current = '';
    setDuration(0);
    finished.current = false;
    startedAt.current = Date.now();
    rec.start();
    setListening(true);
  }, []);

  const stop = useCallback(() => {
    recognizer.current?.stop();
    setListening(false);
    if (startedAt.current) setDuration((Date.now() - startedAt.current) / 1000);
  }, []);

  const reset = useCallback(() => {
    recognizer.current?.stop();
    setListening(false);
    setTranscript('');
    transcriptRef.current = '';
    setDuration(0);
    setError('');
  }, []);

  return { supported, listening, transcript, duration, error, start, stop, reset };
}

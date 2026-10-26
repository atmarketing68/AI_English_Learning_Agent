'use client';

/**
 * G2 · One microphone hook for every "say it" surface (speaking steps, shadowing,
 * placement). Wraps SpeechRecognizer with transcript, timing and a friendly error.
 * With `captureAudio`, the take is also recorded and handed over as 16 kHz WAV so
 * the server can score it to the phoneme (G2 · 9) when that is configured.
 */
import { useCallback, useEffect, useRef, useState } from 'react';
import { SpeechRecognizer } from '@/lib/speechService';
import { AudioCapture, toWav16k } from '@/lib/audioCapture';

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

export interface SpeechRecorderOptions {
  /** Called once per take when recognition ends with a non-empty transcript. */
  onFinish?: (transcript: string, durationSeconds: number, wav?: Blob | null) => void;
  /** Also record the audio (for phoneme scoring). */
  captureAudio?: boolean;
}

function describeError(err: string): string {
  if (err === 'not-allowed' || err === 'service-not-allowed') return 'Hãy cho phép trang web dùng micro để luyện nói.';
  if (err === 'no-speech') return 'Không nghe thấy gì. Hãy nói to và rõ hơn một chút.';
  if (err === 'audio-capture') return 'Không tìm thấy micro trên thiết bị này.';
  if (err === 'network') return 'Nhận giọng nói cần kết nối mạng. Hãy kiểm tra lại.';
  if (err === 'aborted') return '';
  return `Lỗi micro: ${err}`;
}

export function useSpeechRecorder(options: SpeechRecorderOptions = {}): SpeechRecorder {
  const recognizer = useRef<SpeechRecognizer | null>(null);
  const capture = useRef<AudioCapture | null>(null);
  const startedAt = useRef<number>(0);
  const transcriptRef = useRef('');
  const optionsRef = useRef(options);
  const finished = useRef(false);
  useEffect(() => { optionsRef.current = options; });
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
        const cap = capture.current;
        capture.current = null;
        const takeAudio = cap ? cap.stop().then(b => (b ? toWav16k(b) : null)) : Promise.resolve(null);
        if (text && !finished.current) {
          finished.current = true;
          takeAudio.then(wav => optionsRef.current.onFinish?.(text, secs, wav));
        }
      },
    );
    recognizer.current = rec;
    const ok = rec.isSupported();
    queueMicrotask(() => setSupported(ok));
    return () => { rec.stop(); void capture.current?.stop(); };
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
    if (optionsRef.current.captureAudio && AudioCapture.supported()) {
      const cap = new AudioCapture();
      capture.current = cap;
      void cap.start().then(ok => { if (!ok && capture.current === cap) capture.current = null; });
    }
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
    void capture.current?.stop();
    capture.current = null;
    setListening(false);
    setTranscript('');
    transcriptRef.current = '';
    setDuration(0);
    setError('');
  }, []);

  return { supported, listening, transcript, duration, error, start, stop, reset };
}

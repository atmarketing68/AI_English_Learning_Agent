/**
 * AGEN speech helpers.
 *
 * Speech-to-text: a thin wrapper over the browser Web Speech API.
 * Text-to-speech (G2): neural audio from the server (`/audio/tts`, cached) with
 * the browser's own voice as the fallback — so every "listen" button in the app
 * sounds the same and works even when the server voice is off.
 */
import api from '@/lib/api';

// ─── Speech to Text (Recognition) ───────────────────────────────────────────

interface BrowserSpeechRecognitionEvent extends Event {
  resultIndex: number;
  results: BrowserSpeechRecognitionResultList;
}

interface BrowserSpeechRecognitionResultList {
  length: number;
  [index: number]: BrowserSpeechRecognitionSingleResult;
}

interface BrowserSpeechRecognitionSingleResult {
  isFinal: boolean;
  [index: number]: BrowserSpeechRecognitionAlternative;
}

interface BrowserSpeechRecognitionAlternative {
  transcript: string;
  confidence: number;
}

interface BrowserSpeechRecognitionErrorEvent extends Event {
  error: string;
}

interface BrowserSpeechRecognition extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  start(): void;
  stop(): void;
  onresult: ((event: BrowserSpeechRecognitionEvent) => void) | null;
  onerror: ((event: BrowserSpeechRecognitionErrorEvent) => void) | null;
  onend: (() => void) | null;
}

export interface SpeechResult {
  transcript: string;
  isFinal: boolean;
}

export class SpeechRecognizer {
  private recognition: BrowserSpeechRecognition | null = null;
  private isListening: boolean = false;

  constructor(
    private onResult: (result: SpeechResult) => void,
    private onError: (err: string) => void,
    private onEnd: () => void
  ) {
    if (typeof window !== 'undefined') {
      const SpeechRecognitionCtor =
        (window as unknown as Record<string, unknown>).SpeechRecognition as
        | (new () => BrowserSpeechRecognition)
        | undefined
        || (window as unknown as Record<string, unknown>).webkitSpeechRecognition as
        | (new () => BrowserSpeechRecognition)
        | undefined;

      if (SpeechRecognitionCtor) {
        this.recognition = new SpeechRecognitionCtor();
        this.recognition.continuous = true;
        this.recognition.interimResults = true;
        this.recognition.lang = 'en-US';

        this.recognition.onresult = (event: BrowserSpeechRecognitionEvent) => {
          let interimTranscript = '';
          let finalTranscript = '';

          for (let i = event.resultIndex; i < event.results.length; ++i) {
            if (event.results[i].isFinal) {
              finalTranscript += event.results[i][0].transcript;
            } else {
              interimTranscript += event.results[i][0].transcript;
            }
          }

          if (finalTranscript) {
            this.onResult({ transcript: finalTranscript, isFinal: true });
          } else if (interimTranscript) {
            this.onResult({ transcript: interimTranscript, isFinal: false });
          }
        };

        this.recognition.onerror = (event: BrowserSpeechRecognitionErrorEvent) => {
          console.error('Speech recognition error', event.error);
          this.onError(event.error);
        };

        this.recognition.onend = () => {
          this.isListening = false;
          this.onEnd();
        };
      } else {
        console.warn('SpeechRecognition API not supported in this browser.');
      }
    }
  }

  public start() {
    if (!this.recognition) {
      this.onError('Trình duyệt không hỗ trợ nhận diện giọng nói. Vui lòng dùng Chrome hoặc Edge.');
      return;
    }
    if (this.isListening) return;

    try {
      this.recognition.start();
      this.isListening = true;
    } catch (e) {
      console.error(e);
    }
  }

  public stop() {
    if (this.recognition && this.isListening) {
      this.recognition.stop();
      this.isListening = false;
    }
  }

  public isSupported(): boolean {
    return !!this.recognition;
  }
}

// ─── Text to Speech ─────────────────────────────────────────────────────────

export type Voice = 'female' | 'male';

export interface SpeakOptions {
  /** 1 = normal, 0.75 = slow. Browser fallback maps this to utterance.rate. */
  rate?: number;
  voice?: Voice;
  onStart?: () => void;
  onEnd?: () => void;
}

type ServerTtsState = 'unknown' | 'on' | 'off';
let serverTts: ServerTtsState = 'unknown';
const audioCache = new Map<string, string>();        // "voice|text" → object URL
const inflight = new Map<string, Promise<string | null>>();
const CACHE_MAX = 200;
let current: HTMLAudioElement | null = null;
let playToken = 0;

function hasAuthToken(): boolean {
  if (typeof window === 'undefined') return false;
  try {
    const raw = localStorage.getItem('agen-auth');
    return !!(raw && JSON.parse(raw)?.state?.token);
  } catch {
    return false;
  }
}

function normalize(text: string): string {
  return text.replace(/\s+/g, ' ').trim().slice(0, 600);
}

/** Server audio for `text` as an object URL, or null when unavailable (caller falls back). */
let probe: Promise<unknown> | null = null;

async function fetchServerAudio(text: string, voice: Voice): Promise<string | null> {
  if (serverTts === 'off' || !hasAuthToken()) return null;
  // While the first request is deciding whether the server voice exists, queue behind it
  // so a page that plays several lines at once does not fire a burst of 404s.
  if (serverTts === 'unknown' && probe) {
    await probe;
    if ((serverTts as ServerTtsState) === 'off') return null;
  }
  const key = `${voice}|${text.toLowerCase()}`;
  const cached = audioCache.get(key);
  if (cached) return cached;
  const pending = inflight.get(key);
  if (pending) return pending;

  const task = (async () => {
    try {
      const res = await api.get('/audio/tts', { params: { text, voice }, responseType: 'blob' });
      serverTts = 'on';
      const url = URL.createObjectURL(res.data as Blob);
      if (audioCache.size >= CACHE_MAX) {
        const oldest = audioCache.keys().next().value;
        if (oldest) { URL.revokeObjectURL(audioCache.get(oldest)!); audioCache.delete(oldest); }
      }
      audioCache.set(key, url);
      return url;
    } catch (err: unknown) {
      const status = (err as { response?: { status?: number } })?.response?.status;
      if (status === 404) serverTts = 'off';          // no provider configured → browser voice from now on
      return null;
    } finally {
      inflight.delete(key);
    }
  })();
  inflight.set(key, task);
  if (serverTts === 'unknown' && !probe) probe = task.finally(() => { probe = null; });
  return task;
}

/** Whether the neural server voice is known to be available (after the first call). */
export function serverVoiceAvailable(): boolean | null {
  return serverTts === 'unknown' ? null : serverTts === 'on';
}

/** Warm the cache so the first tap plays instantly. */
export function preloadText(text: string, voice: Voice = 'female'): void {
  const clean = normalize(text);
  if (clean) void fetchServerAudio(clean, voice);
}

/** Stop whatever is playing (server audio or browser voice). */
export function stopSpeech(): void {
  playToken++;
  if (current) {
    current.onended = null;
    current.pause();
    current = null;
  }
  if (typeof window !== 'undefined' && window.speechSynthesis) {
    window.speechSynthesis.cancel();
  }
}

function speakWithBrowser(text: string, opts: SpeakOptions, token: number): Promise<void> {
  return new Promise(resolve => {
    if (typeof window === 'undefined' || !window.speechSynthesis) {
      console.warn('SpeechSynthesis API not supported.');
      opts.onEnd?.();
      resolve();
      return;
    }
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'en-US';
    const voices = window.speechSynthesis.getVoices().filter(v => v.lang.startsWith('en'));
    const wantFemale = (opts.voice ?? 'female') === 'female';
    const preferred =
      voices.find(v => (v.name.includes('Google') || v.name.includes('Microsoft')) && (wantFemale ? !/male|david|mark|guy/i.test(v.name) : /male|david|mark|guy/i.test(v.name)))
      || voices.find(v => v.name.includes('Google') || v.name.includes('Microsoft'))
      || voices[0];
    if (preferred) utterance.voice = preferred;
    utterance.rate = Math.max(0.5, Math.min(1.5, (opts.rate ?? 1) * 0.92));
    utterance.pitch = 1.0;
    const done = () => { if (token === playToken) opts.onEnd?.(); resolve(); };
    utterance.onend = done;
    utterance.onerror = done;
    opts.onStart?.();
    window.speechSynthesis.speak(utterance);
  });
}

/**
 * Speak `text`. Resolves when playback ends (or immediately if nothing could play).
 * Neural server voice first, browser voice otherwise.
 */
export async function playText(text: string, opts: SpeakOptions = {}): Promise<void> {
  const clean = normalize(text);
  if (!clean) { opts.onEnd?.(); return; }
  stopSpeech();
  const token = playToken;
  const voice: Voice = opts.voice ?? 'female';

  const url = await fetchServerAudio(clean, voice);
  if (token !== playToken) return;                   // superseded while loading
  if (!url) {
    await speakWithBrowser(clean, opts, token);
    return;
  }

  await new Promise<void>(resolve => {
    const audio = new Audio(url);
    current = audio;
    audio.playbackRate = Math.max(0.5, Math.min(1.5, opts.rate ?? 1));
    try { (audio as HTMLAudioElement & { preservesPitch?: boolean }).preservesPitch = true; } catch { /* unsupported */ }
    const done = () => {
      if (current === audio) current = null;
      if (token === playToken) opts.onEnd?.();
      resolve();
    };
    audio.onended = done;
    audio.onerror = () => {
      // Broken blob/decoder → one browser-voice attempt so the learner still hears something.
      if (current === audio) current = null;
      if (token === playToken) void speakWithBrowser(clean, opts, token).then(resolve);
      else resolve();
    };
    opts.onStart?.();
    audio.play().catch(() => done());
  });
}

/** Legacy signature kept for existing call sites: speakText(text, onEnd?, rate?). */
export const speakText = (text: string, onEnd?: () => void, rate = 0.9) => {
  void playText(text, { onEnd, rate: rate < 0.85 ? 0.75 : 1 });
};

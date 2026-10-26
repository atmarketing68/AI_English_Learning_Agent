/**
 * G2 · 9 — microphone capture for phoneme-level scoring.
 *
 * Records with MediaRecorder next to the Web Speech API (both can share the
 * mic), then converts the take to the 16 kHz mono 16-bit WAV the scoring
 * provider expects — all in the browser, so the server never transcodes.
 */

export class AudioCapture {
  private recorder: MediaRecorder | null = null;
  private stream: MediaStream | null = null;
  private chunks: Blob[] = [];

  static supported(): boolean {
    return typeof window !== 'undefined' && !!navigator.mediaDevices?.getUserMedia && typeof MediaRecorder !== 'undefined';
  }

  async start(): Promise<boolean> {
    if (!AudioCapture.supported()) return false;
    try {
      this.stream = await navigator.mediaDevices.getUserMedia({ audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true } });
      this.chunks = [];
      this.recorder = new MediaRecorder(this.stream);
      this.recorder.ondataavailable = (e) => { if (e.data.size) this.chunks.push(e.data); };
      this.recorder.start(250);
      return true;
    } catch {
      this.release();
      return false;
    }
  }

  /** Stops recording and resolves with the raw take (null if nothing was recorded). */
  stop(): Promise<Blob | null> {
    return new Promise(resolve => {
      const rec = this.recorder;
      if (!rec || rec.state === 'inactive') { this.release(); resolve(null); return; }
      rec.onstop = () => {
        const type = rec.mimeType || 'audio/webm';
        const blob = this.chunks.length ? new Blob(this.chunks, { type }) : null;
        this.release();
        resolve(blob);
      };
      try { rec.stop(); } catch { this.release(); resolve(null); }
    });
  }

  private release() {
    this.stream?.getTracks().forEach(t => t.stop());
    this.stream = null;
    this.recorder = null;
  }
}

const TARGET_RATE = 16000;

/** Decode any browser recording and re-encode it as 16 kHz mono PCM WAV. */
export async function toWav16k(blob: Blob, maxSeconds = 60): Promise<Blob | null> {
  try {
    const Ctx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
    const ctx = new Ctx();
    const decoded = await ctx.decodeAudioData(await blob.arrayBuffer());
    await ctx.close();
    const seconds = Math.min(decoded.duration, maxSeconds);
    const frames = Math.ceil(seconds * TARGET_RATE);
    if (!frames) return null;
    const offline = new OfflineAudioContext(1, frames, TARGET_RATE);
    const source = offline.createBufferSource();
    source.buffer = decoded;
    source.connect(offline.destination);
    source.start(0);
    const rendered = await offline.startRendering();
    return encodeWav(rendered.getChannelData(0), TARGET_RATE);
  } catch {
    return null;
  }
}

function encodeWav(samples: Float32Array, rate: number): Blob {
  const buffer = new ArrayBuffer(44 + samples.length * 2);
  const view = new DataView(buffer);
  const str = (offset: number, s: string) => { for (let i = 0; i < s.length; i++) view.setUint8(offset + i, s.charCodeAt(i)); };
  str(0, 'RIFF');
  view.setUint32(4, 36 + samples.length * 2, true);
  str(8, 'WAVE');
  str(12, 'fmt ');
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);          // PCM
  view.setUint16(22, 1, true);          // mono
  view.setUint32(24, rate, true);
  view.setUint32(28, rate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  str(36, 'data');
  view.setUint32(40, samples.length * 2, true);
  let offset = 44;
  for (let i = 0; i < samples.length; i++, offset += 2) {
    const s = Math.max(-1, Math.min(1, samples[i]));
    view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7fff, true);
  }
  return new Blob([buffer], { type: 'audio/wav' });
}

/**
 * AGEN Web Speech API wrapper.
 * Provides easy access to browser's native Speech-to-Text and Text-to-Speech capabilities.
 */

// Browser speech recognition result types — prefixed to avoid conflict with DOM lib
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

// --- Speech to Text (Recognition) ---

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

// --- Text to Speech (Synthesis) ---

export const speakText = (text: string, onEnd?: () => void) => {
  if (typeof window === 'undefined' || !window.speechSynthesis) {
    console.warn('SpeechSynthesis API not supported.');
    if (onEnd) onEnd();
    return;
  }

  window.speechSynthesis.cancel();

  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = 'en-US';

  const voices = window.speechSynthesis.getVoices();
  const preferredVoice = voices.find(
    v => v.lang.startsWith('en') && (v.name.includes('Google') || v.name.includes('Microsoft'))
  );
  if (preferredVoice) {
    utterance.voice = preferredVoice;
  }

  utterance.rate = 0.9;
  utterance.pitch = 1.0;

  if (onEnd) {
    utterance.onend = onEnd;
  }

  window.speechSynthesis.speak(utterance);
};

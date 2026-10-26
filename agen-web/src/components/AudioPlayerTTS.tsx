'use client';

import { useState, useEffect } from 'react';

interface ScriptLine {
  speaker: string;
  text: string;
}

interface Props {
  text?: string;
  scriptLines?: ScriptLine[];
}

export default function AudioPlayerTTS({ text, scriptLines }: Props) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [showTranscript, setShowTranscript] = useState(false);
  const [error, setError] = useState('');

  // Fallback if no scriptLines but text exists
  const lines = scriptLines || (text ? [{ speaker: 'Narrator', text }] : []);

  useEffect(() => {
    return () => {
      if (typeof window !== 'undefined' && window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  const playTTS = () => {
    if (typeof window === 'undefined' || !window.speechSynthesis) {
      setError('Trình duyệt của bạn không hỗ trợ Text-to-Speech.');
      return;
    }

    if (isPlaying) {
      window.speechSynthesis.cancel();
      setIsPlaying(false);
      return;
    }

    setIsPlaying(true);
    let i = 0;

    const speakNext = () => {
      if (i >= lines.length) {
        setIsPlaying(false);
        return;
      }
      
      const utterance = new SpeechSynthesisUtterance(lines[i].text);
      utterance.lang = 'en-US';
      
      // Try to assign different voices to different speakers
      const voices = window.speechSynthesis.getVoices().filter(v => v.lang.startsWith('en'));
      if (voices.length > 0) {
        const isFemale = lines[i].speaker.toLowerCase().match(/female|mary|sarah|she|woman|girl/);
        const voiceOffset = isFemale ? 1 : 0;
        utterance.voice = voices[voiceOffset % voices.length];
      }

      utterance.rate = 0.9;
      
      utterance.onend = () => {
        i++;
        speakNext();
      };
      
      utterance.onerror = () => {
        setIsPlaying(false);
      };

      window.speechSynthesis.speak(utterance);
    };

    speakNext();
  };

  return (
    <div className="card" style={{ background: 'var(--bg-elevated)', marginBottom: 'var(--spacing-md)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <button 
          onClick={playTTS}
          className="btn btn-primary"
          style={{ display: 'flex', alignItems: 'center', gap: 8, borderRadius: 99, padding: '10px 24px' }}
        >
          <span style={{ fontSize: '1.2rem' }}>{isPlaying ? '⏸️' : '▶️'}</span>
          {isPlaying ? 'Dừng phát' : 'Nghe Audio'}
        </button>
        <button 
          onClick={() => setShowTranscript(!showTranscript)}
          className="btn btn-ghost btn-sm"
        >
          {showTranscript ? 'Ẩn' : 'Hiện'} Transcript
        </button>
      </div>

      {error && <div style={{ color: 'var(--agen-secondary)', marginTop: 12, fontSize: '0.9rem' }}>{error}</div>}

      {showTranscript && (
        <div className="animate-fade-in-up" style={{ marginTop: 24, padding: 16, background: 'var(--bg-base)', borderRadius: 8, border: '1px solid var(--border-subtle)', maxHeight: 300, overflowY: 'auto' }}>
          {lines.map((l, idx) => (
            <div key={idx} style={{ marginBottom: 12 }}>
              <strong style={{ color: 'var(--agen-primary-light)' }}>{l.speaker}:</strong>{' '}
              <span style={{ lineHeight: 1.6 }}>{l.text}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

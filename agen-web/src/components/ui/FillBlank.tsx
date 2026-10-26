'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { playSound } from '@/lib/soundEffects';
import { Lightbulb } from 'lucide-react';

export default function FillBlank({
  sentence, blankWord, options, hint, onAnswer, disabled
}: {
  sentence: string;
  blankWord: string;
  options: string[];
  hint?: string;
  onAnswer: (ans: string) => void;
  disabled: boolean;
}) {
  const [selected, setSelected] = useState<string | null>(null);

  // Parse sentence into parts (split by the blank word, case insensitive)
  const parts = sentence.split(new RegExp(`(${blankWord})`, 'i'));

  return (
    <motion.div 
      className="card" 
      style={{ width: '100%' }}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      {hint && <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: 14, display: 'flex', alignItems: 'center', gap: 6 }}><Lightbulb size={14} color="var(--agen-accent)" /> Gợi ý: {hint}</div>}
      
      <div style={{ fontSize: '1.2rem', lineHeight: 1.8, marginBottom: 24 }}>
        {parts.map((part, i) => {
          if (part.toLowerCase() === blankWord.toLowerCase()) {
            return (
              <span 
                key={i} 
                style={{
                  display: 'inline-block',
                  minWidth: 80,
                  padding: '4px 12px',
                  margin: '0 4px',
                  borderBottom: '2px solid var(--agen-primary)',
                  background: selected ? 'var(--bg-tint)' : 'var(--bg-elevated)',
                  color: selected ? 'var(--agen-primary-light)' : 'transparent',
                  fontWeight: 600,
                  textAlign: 'center',
                  borderRadius: '4px 4px 0 0'
                }}
              >
                {selected || '___'}
              </span>
            );
          }
          return <span key={i}>{part}</span>;
        })}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 20 }}>
        {options.map(opt => (
          <motion.button
            key={opt}
            disabled={disabled}
            onClick={() => { playSound('pop'); setSelected(opt); }}
            whileTap={!disabled ? { scale: 0.98 } : {}}
            style={{
              padding: '12px',
              borderRadius: 'var(--radius-md)',
              border: selected === opt ? '1.5px solid var(--agen-primary)' : '1.5px solid var(--border-subtle)',
              background: selected === opt ? 'var(--bg-tint)' : 'var(--bg-surface)',
              color: selected === opt ? 'var(--agen-primary-light)' : 'var(--text-primary)',
              cursor: disabled ? 'default' : 'pointer',
              fontWeight: 500, fontFamily: 'inherit', fontSize: '0.95rem',
              transition: 'background 0.2s, border 0.2s'
            }}
          >
            {opt}
          </motion.button>
        ))}
      </div>

      <motion.button 
        className="btn btn-primary btn-full" 
        disabled={!selected || disabled}
        onClick={() => { if (selected) onAnswer(selected); }}
        whileTap={selected && !disabled ? { scale: 0.98 } : {}}
      >
        Kiểm tra
      </motion.button>
    </motion.div>
  );
}

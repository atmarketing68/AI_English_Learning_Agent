'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { RotateCw } from 'lucide-react';

export default function FlipCard({
  word, phonetic, definition, translation, example, imageHint
}: {
  word: string;
  phonetic?: string;
  definition: string;
  translation: string;
  example: string;
  imageHint?: string;
}) {
  const [flipped, setFlipped] = useState(false);

  return (
    <motion.div 
      style={{
        perspective: '1000px',
        width: '100%',
        maxWidth: '400px',
        height: '280px',
        margin: '0 auto',
        cursor: 'pointer'
      }}
      onClick={() => setFlipped(!flipped)}
      whileHover={{ scale: 1.01 }}
      whileTap={{ scale: 0.99 }}
    >
      <motion.div 
        style={{
          width: '100%',
          height: '100%',
          position: 'relative',
          transformStyle: 'preserve-3d',
        }}
        initial={false}
        animate={{ rotateY: flipped ? 180 : 0 }}
        transition={{ duration: 0.6, ease: [0.25, 0.1, 0.25, 1] }}
      >
        {/* Front */}
        <div className="card" style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          backfaceVisibility: 'hidden',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          background: 'var(--bg-surface)',
          boxShadow: 'var(--shadow-md)',
          border: 'none'
        }}>
          {imageHint && <div style={{ fontSize: '3rem', marginBottom: 12 }}>{imageHint}</div>}
          <h2 style={{ fontSize: '2.75rem', fontWeight: 700, letterSpacing: '-0.03em', margin: 0 }}>{word}</h2>
          {phonetic && <p style={{ color: 'var(--text-muted)', marginTop: 8 }}>{phonetic}</p>}
          <div style={{ position: 'absolute', bottom: 18, fontSize: '0.8rem', color: 'var(--text-muted)', display: 'inline-flex', alignItems: 'center', gap: 6 }}><RotateCw size={13} /> Chạm để lật thẻ</div>
        </div>

        {/* Back */}
        <div className="card" style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          backfaceVisibility: 'hidden',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          transform: 'rotateY(180deg)',
          background: 'var(--bg-surface)',
          boxShadow: 'var(--shadow-md)',
          border: 'none',
          padding: 'var(--spacing-lg)',
          textAlign: 'center'
        }}>
          <h3 style={{ marginBottom: 12 }}>{definition}</h3>
          <p style={{ color: 'var(--agen-primary-light)', fontWeight: 500, marginBottom: 16 }}>{translation}</p>
          <div style={{ fontStyle: 'italic', color: 'var(--text-secondary)', fontSize: '0.9rem', borderTop: '1px solid var(--border-subtle)', paddingTop: 12, width: '100%' }}>
            &quot;{example}&quot;
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
}

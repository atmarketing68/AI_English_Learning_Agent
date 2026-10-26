'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';

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
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
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
        transition={{ type: 'spring', stiffness: 260, damping: 20 }}
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
          background: 'var(--bg-elevated)',
          border: '2px solid var(--agen-primary)'
        }}>
          {imageHint && <div style={{ fontSize: '3rem', marginBottom: 12 }}>{imageHint}</div>}
          <h2 style={{ fontSize: '2.5rem', margin: 0, color: 'var(--agen-primary-light)' }}>{word}</h2>
          {phonetic && <p style={{ color: 'var(--text-muted)', marginTop: 8 }}>{phonetic}</p>}
          <div style={{ marginTop: 'auto', fontSize: '0.8rem', color: 'var(--text-muted)' }}>Tap to flip ↺</div>
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
          background: 'var(--gradient-card)',
          padding: 'var(--spacing-lg)',
          textAlign: 'center'
        }}>
          <h3 style={{ marginBottom: 12 }}>{definition}</h3>
          <p style={{ color: 'var(--agen-accent)', fontWeight: 600, marginBottom: 16 }}>{translation}</p>
          <div style={{ fontStyle: 'italic', color: 'var(--text-secondary)', fontSize: '0.9rem', borderTop: '1px solid var(--border-subtle)', paddingTop: 12, width: '100%' }}>
            &quot;{example}&quot;
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
}

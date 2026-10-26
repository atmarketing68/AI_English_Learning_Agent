import Image from 'next/image';

/** AGEN app icon, optionally followed by the wordmark. */
export default function Logo({ size = 28, wordmark = true }: { size?: number; wordmark?: boolean }) {
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: Math.round(size * 0.32) }}>
      <Image
        src="/logo.png"
        alt={wordmark ? '' : 'AI AGENT ENGLISH'}
        width={size}
        height={size}
        priority
        style={{ display: 'block', borderRadius: size * 0.22 }}
      />
      {wordmark && (
        <span style={{ fontWeight: 600, fontSize: size * 0.6, letterSpacing: '-0.02em', color: 'var(--text-primary)', whiteSpace: 'nowrap' }}>
          AI AGENT ENGLISH
        </span>
      )}
    </span>
  );
}

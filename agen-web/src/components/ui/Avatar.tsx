'use client';

/** G4 · Learner avatar: emoji on a coloured disc with an optional frame. Falls back to the name initial. */
import type { AvatarData } from '@/types';
import { useSkin } from '@/store/skinStore';

/** The stock avatar: on the professional skin it is shown as the name initial. */
const DEFAULT_EMOJI = '🙂';

interface Props {
  avatar?: Partial<AvatarData> | null;
  name?: string;
  size?: number;
  className?: string;
  /** Always draw the emoji, even for the stock avatar on the classic skin (shop previews). */
  raw?: boolean;
}

export default function Avatar({ avatar, name, size = 36, className, raw }: Props) {
  const skin = useSkin();
  const stock = !avatar?.emoji || (avatar.emoji === DEFAULT_EMOJI && (avatar.frame || 'none') === 'none' && (avatar.color || 'sky') === 'sky');
  const emoji = skin === 'classic' && stock && !raw ? undefined : avatar?.emoji;
  const color = avatar?.color || 'sky';
  const frame = avatar?.frame || 'none';
  const initial = (name || '?').trim().slice(0, 1).toUpperCase();
  return (
    <span
      className={`avatar${className ? ` ${className}` : ''}`}
      data-color={emoji ? color : undefined}
      data-frame={emoji ? frame : undefined}
      style={{ width: size, height: size, fontSize: emoji ? size * 0.56 : size * 0.42 }}
      aria-hidden="true"
    >
      {emoji || initial}
    </span>
  );
}

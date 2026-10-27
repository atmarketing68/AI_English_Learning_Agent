'use client';

import { useEffect } from 'react';
import { refreshNativePush } from '@/lib/nativePush';

/** G13 · Inside the Android/iOS app: after sign-in, keep this phone's push token registered (no-op in browsers). */
export default function NativePushBridge() {
  useEffect(() => { void refreshNativePush().catch(() => undefined); }, []);
  return null;
}

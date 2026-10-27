/** Helpers shared by app/error.tsx and app/global-error.tsx. */
const RELOAD_KEY = 'agen-error-reload';

/** A stale or failed JS chunk (new deploy, flaky mobile network): one automatic reload usually fixes it. */
export function isChunkError(error: { name?: string; message?: string }): boolean {
  return /ChunkLoadError|Loading chunk|Failed to fetch dynamically imported module|Importing a module script failed/i
    .test(`${error?.name ?? ''} ${error?.message ?? ''}`);
}

/** Reload once per session for chunk errors; returns true when a reload was started. */
export function reloadOnceForChunkError(error: { name?: string; message?: string }): boolean {
  if (typeof window === 'undefined' || !isChunkError(error)) return false;
  try {
    if (sessionStorage.getItem(RELOAD_KEY)) return false;
    sessionStorage.setItem(RELOAD_KEY, '1');
  } catch { /* storage blocked: still try once */ }
  window.location.reload();
  return true;
}

/** Short technical detail the user can send us (message is hidden by Next for server errors). */
export function errorDetail(error: { name?: string; message?: string; digest?: string }): string {
  const parts = [error?.name, error?.message, error?.digest ? `digest ${error.digest}` : '']
    .filter(Boolean).join(' · ');
  return `${parts} · ${typeof navigator !== 'undefined' ? navigator.userAgent : ''} · ${typeof location !== 'undefined' ? location.pathname : ''}`.slice(0, 600);
}

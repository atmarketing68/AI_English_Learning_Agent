import api from '@/lib/api';

// ── G10 · Chứng nhận hoàn thành ──────────────────────────────────────────────
export interface Certificate {
  code: string;
  kind: 'track' | 'group';
  title: string;
  recipient_name: string;
  issuer_name: string;
  note: string | null;
  details: { level?: string; total_xp?: number; lessons?: number; longest_streak?: number; skills?: Record<string, number> };
  issued_at: string;
  revoked: boolean;
}

export interface MyCertificates {
  certificates: Certificate[];
  tracks: { track_id: string; title: string; completed: boolean; claimed_code: string | null }[];
}

export const getMyCertificates = async (): Promise<MyCertificates> => (await api.get('/certificates')).data;
export const claimTrackCertificate = async (trackId: string): Promise<Certificate> => (await api.post(`/certificates/tracks/${trackId}`)).data;
export const verifyCertificate = async (code: string): Promise<Certificate> => (await api.get(`/certificates/verify/${encodeURIComponent(code)}`)).data;

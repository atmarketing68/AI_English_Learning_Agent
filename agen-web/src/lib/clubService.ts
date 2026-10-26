import api from '@/lib/api';
import type { AvatarData } from '@/types';

// ── G10 · Câu lạc bộ nói: phòng 2–4 người, AI dẫn dắt ────────────────────────
export interface ClubTopic { id: string; title: string; title_vi: string; level: string; emoji: string }

export interface RoomCard {
  id: string;
  code: string;
  topic: ClubTopic;
  status: 'waiting' | 'active' | 'finished';
  members: number;
  host_name: string;
  created_at: string;
  /** G11 · booked session time (UTC, no zone suffix) */
  scheduled_at?: string | null;
}

export interface ClubLobby {
  topics: ClubTopic[];
  open_rooms: RoomCard[];
  my_rooms: RoomCard[];
  max_members: number;
  upcoming_rooms?: RoomCard[];
}

export interface ClubMember {
  learner_id: string;
  name: string;
  avatar: Partial<AvatarData>;
  turns: number;
  words: number;
  is_host: boolean;
  is_me: boolean;
}

export interface ClubMessage {
  seq: number;
  role: 'ai' | 'learner' | 'system';
  learner_id: string | null;
  name: string | null;
  text: string;
  feedback_vi: string | null;
  corrected: string | null;
  to_learner_id: string | null;
  created_at: string;
}

export interface RoomState {
  id: string;
  code: string;
  topic: ClubTopic;
  status: 'waiting' | 'active' | 'finished';
  members: ClubMember[];
  messages: ClubMessage[];
  current_speaker_id: string | null;
  is_my_turn: boolean;
  is_host: boolean;
  turns_taken: number;
  total_turns: number;
  last_seq: number;
  scheduled_at?: string | null;
  opens_at?: string | null;
}

export const getClubLobby = async (): Promise<ClubLobby> => (await api.get('/club')).data;
export const createRoom = async (topic_id: string, is_public = true, scheduled_at: string | null = null): Promise<RoomState> =>
  (await api.post('/club/rooms', { topic_id, is_public, scheduled_at })).data;

/** API times are UTC without a zone suffix. */
export const utcDate = (s: string) => new Date(/(?:[zZ]|[+-]\d\d:\d\d)$/.test(s) ? s : `${s}Z`);
export const formatSlot = (s: string) => utcDate(s).toLocaleString('vi-VN', { weekday: 'short', day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });
export const joinRoom = async (code: string): Promise<RoomState> => (await api.post('/club/rooms/join', { code })).data;
export const getRoom = async (roomId: string, after = 0): Promise<RoomState> => (await api.get(`/club/rooms/${roomId}`, { params: { after } })).data;
export const startRoom = async (roomId: string): Promise<RoomState> => (await api.post(`/club/rooms/${roomId}/start`)).data;
export const speakInRoom = async (roomId: string, transcript: string, duration_seconds?: number): Promise<RoomState> =>
  (await api.post(`/club/rooms/${roomId}/speak`, { transcript, duration_seconds })).data;
export const skipTurn = async (roomId: string): Promise<RoomState> => (await api.post(`/club/rooms/${roomId}/skip`)).data;
export const leaveRoom = async (roomId: string): Promise<ClubLobby> => (await api.post(`/club/rooms/${roomId}/leave`)).data;

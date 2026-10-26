import api from '@/lib/api';

// ── Types (mirror backend api/admin.py) ───────────────────────────────────────
export interface AdminMe {
  email: string;
  is_admin: boolean;
}

export interface EvalTraceItem {
  trace_id: string;
  agent: string;
  status: string;
  eval_score: number | null;
  eval_flags: string[] | null;
  eval_flagged: boolean | null;
  duration_ms: number;
  created_at: string;
}

export interface AgentEvalStat {
  agent: string;
  total: number;
  flagged: number;
  avg_score: number | null;
}

export interface EvalSummary {
  total_traces: number;
  evaluated: number;
  flagged: number;
  flagged_pct: number;
  avg_score: number | null;
  per_agent: AgentEvalStat[];
}

export interface PilotMetric {
  value: number;
  rate: number | null;
}

export interface PilotSummary {
  registered_learners: number;
  placement_completed: PilotMetric;
  first_lesson_completed: PilotMetric;
  d7_retention: PilotMetric;
  weekly_habit: PilotMetric;
  ai_quality: PilotMetric;
  lesson_generation: PilotMetric;
}

export interface ListEvaluationsParams {
  flaggedOnly?: boolean;
  agent?: string;
  limit?: number;
}

// ── API Calls ────────────────────────────────────────────────────────────────
export async function getAdminMe(): Promise<AdminMe> {
  const res = await api.get('/admin/me');
  return res.data;
}

export async function getEvaluationSummary(): Promise<EvalSummary> {
  const res = await api.get('/admin/evaluations/summary');
  return res.data;
}

export async function getPilotSummary(): Promise<PilotSummary> {
  const res = await api.get('/admin/pilot/summary');
  return res.data;
}

export async function listEvaluations(params: ListEvaluationsParams = {}): Promise<EvalTraceItem[]> {
  const query = new URLSearchParams();
  if (params.flaggedOnly) query.set('flagged_only', 'true');
  if (params.agent) query.set('agent', params.agent);
  query.set('limit', String(params.limit ?? 50));
  const res = await api.get(`/admin/evaluations?${query.toString()}`);
  return res.data;
}

// ── Content Factory (cached curriculum content) ───────────────────────────────
export interface ContentItem {
  curriculum_code: string;
  level: string;
  skill: string;
  topic: string;
  status: string;
  eval_score: number | null;
  eval_flagged: boolean | null;
  total_exercises: number;
}

export async function listContent(level?: string, status?: string): Promise<ContentItem[]> {
  const query = new URLSearchParams();
  if (level) query.set('level', level);
  if (status) query.set('status', status);
  const qs = query.toString();
  const res = await api.get(`/admin/content${qs ? `?${qs}` : ''}`);
  return res.data;
}

export async function setContentStatus(code: string, status: string): Promise<ContentItem> {
  const res = await api.post(`/admin/content/${code}/status`, { status });
  return res.data;
}

export interface BatchGenerateResult {
  level: string;
  attempted: number;
  generated: number;
  skipped: number;
  failed: number;
  errors: { code: string; error: string }[];
}

export async function batchGenerateContent(
  level: string,
  autoApprove = false,
  limit?: number,
): Promise<BatchGenerateResult> {
  const res = await api.post('/admin/content/generate', {
    level,
    auto_approve: autoApprove,
    limit: limit ?? null,
  });
  return res.data;
}

// ── G5 · Doanh thu & chuyển đổi ───────────────────────────────────────────────
export interface RevenueBucket { key: string; label: string; revenue_vnd: number; orders: number }

export interface RevenueSummary {
  total_vnd: number;
  paid_orders: number;
  pending_orders: number;
  failed_orders: number;
  by_month: RevenueBucket[];
  by_provider: RevenueBucket[];
  by_plan: RevenueBucket[];
  active_premium: number;
  active_family: number;
  trials_started: number;
  trials_converted: number;
  trial_conversion_pct: number;
  guests_now: number;
  guests_claimed: number;
  registered_learners: number;
}

export async function getRevenueSummary(): Promise<RevenueSummary> {
  const res = await api.get('/admin/revenue/summary');
  return res.data;
}

// ── G8 · Đơn hàng & hoá đơn VAT ───────────────────────────────────────────────
export interface AdminOrder {
  order_id: string;
  email: string | null;
  role: string | null;
  provider: string;
  plan: string;
  seats: number;
  months: number;
  amount_vnd: number;
  status: 'pending' | 'paid' | 'failed' | 'refunded';
  invoice: { company_name: string; tax_code: string; address: string; email: string } | null;
  invoice_issued_at: string | null;
  created_at: string;
  paid_at: string | null;
  currency?: 'VND' | 'USD';
  amount_foreign?: number | null;
  refunded_at?: string | null;
  refund_note?: string | null;
}

/** G11 · Refund a paid order (Stripe through the API unless `manual`; other gateways: record after refunding on the gateway). */
export async function refundOrder(orderId: string, note: string, manual = false): Promise<AdminOrder> {
  const res = await api.post(`/admin/revenue/orders/${orderId}/refund`, { note, manual });
  return res.data;
}

export async function listOrders(invoiceOnly = false, limit = 100): Promise<AdminOrder[]> {
  const res = await api.get(`/admin/revenue/orders?invoice_only=${invoiceOnly}&limit=${limit}`);
  return res.data;
}

export async function markInvoiceIssued(orderId: string, issued: boolean): Promise<AdminOrder> {
  const res = await api.post(`/admin/revenue/orders/${orderId}/invoice-issued`, { issued });
  return res.data;
}

// ── G9 · Đề thi thử do AI sinh ────────────────────────────────────────────────
export interface GeneratedExam {
  id: string;
  public_id: string;
  exam: 'ielts' | 'toeic';
  skill: 'listening' | 'reading';
  title: string;
  topic: string | null;
  status: 'draft' | 'approved' | 'rejected';
  questions: number;
  eval_score: number | null;
  eval_flagged: boolean | null;
  created_at: string;
  approved_at: string | null;
}

export async function listGeneratedExams(status?: string): Promise<GeneratedExam[]> {
  const res = await api.get(`/admin/exams${status ? `?status=${status}` : ''}`);
  return res.data;
}

export async function generateExam(payload: { exam: 'ielts' | 'toeic'; skill: 'listening' | 'reading'; topic?: string; level?: string; auto_approve?: boolean }): Promise<GeneratedExam> {
  const res = await api.post('/admin/exams/generate', payload);
  return res.data;
}

export async function getGeneratedExam(id: string): Promise<{ meta: GeneratedExam; paper: Record<string, unknown> & { sections: { title: string; instructions: string; passage?: string; audio?: { speaker: string; text: string }[]; questions: { id: string; type: string; prompt: string; options?: string[]; answer: number | string[]; explanation_vi: string }[] }[] } }> {
  const res = await api.get(`/admin/exams/${id}`);
  return res.data;
}

export async function setGeneratedExamStatus(id: string, status: 'draft' | 'approved' | 'rejected'): Promise<GeneratedExam> {
  const res = await api.post(`/admin/exams/${id}/status`, { status });
  return res.data;
}

export async function deleteGeneratedExam(id: string): Promise<void> {
  await api.delete(`/admin/exams/${id}`);
}

// ── G10 · Chi phí AI theo người dùng ──────────────────────────────────────────
export interface AiUsageBucket { key: string; calls: number; cost_usd: number }

export interface AiUsageSummary {
  days: number;
  usd_to_vnd: number;
  today_usd: number;
  week_usd: number;
  period_usd: number;
  period_vnd: number;
  calls: number;
  users_with_usage: number;
  avg_per_user_usd: number;
  limits: { free_usd: number; premium_usd: number };
  by_day: AiUsageBucket[];
  by_feature: AiUsageBucket[];
  by_provider: AiUsageBucket[];
  top_users: { user_id: string; email: string | null; role: string | null; premium: boolean; calls: number; cost_usd: number; cost_vnd: number }[];
  /** G11 · today's spend against the alert thresholds */
  alerts?: { today_usd: number; total_threshold_usd: number; user_threshold_usd: number; total_over: boolean; users_over: { user_id: string; email: string | null; cost_usd: number }[] };
}

export async function getAiUsageSummary(days = 30): Promise<AiUsageSummary> {
  const res = await api.get(`/admin/ai-usage/summary?days=${days}`);
  return res.data;
}

// ── G11 · Podcast do AI sinh ──────────────────────────────────────────────────
export interface GeneratedEpisode {
  id: string;
  public_id: string;
  level: string;
  topic: string | null;
  title: string;
  title_vi: string;
  status: 'draft' | 'approved' | 'rejected';
  lines: number;
  questions: number;
  youtube_id: string | null;
  video_start: number | null;
  video_end: number | null;
  eval_score: number | null;
  eval_flagged: boolean | null;
  created_at: string;
  approved_at: string | null;
}

export interface GeneratedEpisodeFull {
  meta: GeneratedEpisode;
  episode: {
    title: string; title_vi: string; description_vi: string; topic: string; minutes: number;
    lines: { speaker: string; text: string; vi: string }[];
    vocab: { word: string; definition: string }[];
    questions: { id: string; prompt: string; options: string[]; answer: number; explanation_vi: string }[];
  };
}

export async function listGeneratedPodcasts(status?: string): Promise<GeneratedEpisode[]> {
  const res = await api.get('/admin/podcasts', { params: status ? { status } : {} });
  return res.data;
}

export async function generatePodcast(payload: { level: string; topic?: string; style?: 'conversation' | 'talk'; auto_approve?: boolean }): Promise<GeneratedEpisode> {
  const res = await api.post('/admin/podcasts/generate', payload);
  return res.data;
}

export async function getGeneratedPodcast(id: string): Promise<GeneratedEpisodeFull> {
  const res = await api.get(`/admin/podcasts/${id}`);
  return res.data;
}

export async function setGeneratedPodcastStatus(id: string, status: 'draft' | 'approved' | 'rejected'): Promise<GeneratedEpisode> {
  const res = await api.post(`/admin/podcasts/${id}/status`, { status });
  return res.data;
}

export async function setGeneratedPodcastVideo(id: string, youtube: string | null, start?: number | null, end?: number | null): Promise<GeneratedEpisode> {
  const res = await api.post(`/admin/podcasts/${id}/video`, { youtube, start: start ?? null, end: end ?? null });
  return res.data;
}

export async function deleteGeneratedPodcast(id: string): Promise<void> {
  await api.delete(`/admin/podcasts/${id}`);
}

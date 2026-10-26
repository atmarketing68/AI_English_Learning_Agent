/**
 * Product analytics (PostHog). A no-op unless NEXT_PUBLIC_POSTHOG_KEY is set,
 * so local dev and forks run without an account.
 *
 * Learners can be minors: we identify by internal user id only (never email or
 * name) and keep session recording off.
 */
import posthog from 'posthog-js';

const KEY = process.env.NEXT_PUBLIC_POSTHOG_KEY;
const HOST = process.env.NEXT_PUBLIC_POSTHOG_HOST || 'https://us.i.posthog.com';

export const analyticsEnabled = Boolean(KEY);

/** Funnel events, so names stay consistent across pages. */
export type AnalyticsEvent =
  | 'signup_completed'
  | 'login_completed'
  | 'onboarding_completed'
  | 'placement_started'
  | 'placement_completed'
  | 'lesson_started'
  | 'lesson_completed'
  | 'lesson_generation_waited'
  | 'daily_limit_reached'
  | 'speaking_session_completed'
  | 'writing_submitted'
  | 'upgrade_clicked'
  | 'upgrade_completed'
  | 'review_started'
  | 'review_completed'
  | 'notebook_opened'
  | 'mistake_explained'
  | 'lesson_retry_completed'
  | 'quest_claimed'
  | 'weekly_goal_claimed'
  | 'weekly_goal_set'
  | 'reminder_set'
  | 'reminder_push_enabled'
  | 'app_installed'
  | 'install_prompt_answered';

export function initAnalytics(): void {
  if (!KEY || typeof window === 'undefined') return;
  try {
    posthog.init(KEY, {
      api_host: HOST,
      capture_pageview: 'history_change',
      capture_pageleave: true,
      person_profiles: 'identified_only',
      disable_session_recording: true,
    });
  } catch {
    // Analytics must never break the app.
  }
}

export function track(event: AnalyticsEvent, props?: Record<string, unknown>): void {
  if (!analyticsEnabled) return;
  try { posthog.capture(event, props); } catch { /* ignore */ }
}

export function identifyUser(userId: string, props?: { role?: string; level?: string }): void {
  if (!analyticsEnabled) return;
  try { posthog.identify(userId, props); } catch { /* ignore */ }
}

export function resetAnalytics(): void {
  if (!analyticsEnabled) return;
  try { posthog.reset(); } catch { /* ignore */ }
}

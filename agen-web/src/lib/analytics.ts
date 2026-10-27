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
  | 'install_prompt_answered'
  // G2 · speaking & listening
  | 'speaking_scenario_started'
  | 'speaking_phrase_scored'
  | 'listening_word_lookup'
  | 'listening_word_saved'
  | 'listening_shadowing_started'
  // G3 · growth
  | 'guest_trial_started'
  | 'guest_claimed'
  | 'checkout_started'
  | 'trial_started'
  | 'league_opened'
  | 'league_reward_claimed'
  | 'track_started'
  | 'track_lesson_started'
  // G4 · fun layer
  | 'shop_opened'
  | 'shop_item_bought'
  | 'shop_item_equipped'
  | 'blitz_started'
  | 'blitz_completed'
  | 'ui_skin_changed'
  // G6
  | 'friend_added'
  | 'duo_quest_claimed'
  | 'parent_report_printed'
  // G7
  | 'group_created'
  | 'group_joined'
  | 'assignment_created'
  | 'assignment_started'
  | 'parent_push_enabled'
  // G8
  | 'exam_started'
  | 'exam_completed'
  | 'tutor_asked'
  | 'group_report_exported'
  | 'invoice_requested'
  // G9
  | 'speaking_exam_started'
  | 'speaking_exam_completed'
  | 'study_plan_set'
  | 'zalo_unlinked'
  | 'exam_generated'
  // G10
  | 'media_opened'
  | 'media_submitted'
  | 'club_room_created'
  | 'club_room_joined'
  | 'club_turn_spoken'
  | 'teacher_feedback_sent'
  | 'certificate_issued'
  | 'certificate_claimed'
  // G11
  | 'podcast_generated'
  | 'club_room_scheduled'
  | 'writing_regraded'
  | 'order_refunded'
  | 'receipt_opened'
  // G12
  | 'club_schedule_created'
  | 'writing_rubric_graded'
  | 'einvoice_issued'
  // G13
  | 'class_test_created'
  | 'class_test_started'
  | 'speaking_exam_generated'
  // G14
  | 'streak_repaired'
  | 'class_test_repeat_set'
  | 'class_test_sheet_printed';

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

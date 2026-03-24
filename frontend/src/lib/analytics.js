/**
 * InFinea — PostHog analytics wrapper.
 * Uses the global `window.posthog` loaded via index.html snippet.
 * All calls are no-ops if PostHog isn't loaded (dev, ad-blockers, etc.).
 */

const ph = () => window.posthog;

/** Identify a logged-in user — call once after login/OAuth/token verify. */
export function identifyUser(user) {
  if (!ph() || !user?.user_id) return;
  ph().identify(user.user_id, {
    email: user.email,
    name: user.display_name || user.name,
    username: user.username,
    subscription_tier: user.subscription_tier || "free",
    created_at: user.created_at,
  });
}

/** Reset identity on logout — unlinks future events from the user. */
export function resetAnalytics() {
  if (!ph()) return;
  ph().reset();
}

/** Track a custom event with optional properties. */
export function track(event, properties) {
  if (!ph()) return;
  ph().capture(event, properties);
}

// ── Convenience helpers for key business events ──

export function trackSessionStarted(actionTitle, category) {
  track("session_started", { action_title: actionTitle, category });
}

export function trackSessionCompleted(data) {
  track("session_completed", {
    action_title: data.action_title,
    category: data.category,
    duration_seconds: data.actual_duration,
    rating: data.rating,
  });
}

export function trackActionCreated(action) {
  track("custom_action_created", {
    category: action?.category,
    title: action?.title,
  });
}

export function trackBadgeEarned(badge) {
  track("badge_earned", { badge_name: badge?.name, badge_id: badge?.badge_id });
}

export function trackObjectiveCreated(objective) {
  track("objective_created", { title: objective?.title });
}

export function trackSubscriptionStarted(tier) {
  track("subscription_started", { tier });
}

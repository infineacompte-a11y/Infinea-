/**
 * InFinea — Centralized API client.
 * Single source of truth for all backend calls.
 * Handles auth headers, error parsing, token management.
 */

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const BASE = `${BACKEND_URL}/api`;

function getHeaders(json = true) {
  const headers = {};
  const token = localStorage.getItem("infinea_token");
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (json) headers["Content-Type"] = "application/json";
  return headers;
}

async function request(method, path, body = null) {
  const options = {
    method,
    credentials: "include",
    headers: getHeaders(body !== null),
  };
  if (body !== null) options.body = JSON.stringify(body);

  const response = await fetch(`${BASE}${path}`, options);

  if (!response.ok) {
    let detail = "Une erreur est survenue";
    try {
      const err = await response.json();
      detail = err.detail || detail;
    } catch {}
    const error = new Error(detail);
    error.status = response.status;
    throw error;
  }

  return response.json();
}

const api = {
  get: (path) => request("GET", path),
  post: (path, body) => request("POST", path, body),
  put: (path, body) => request("PUT", path, body),
  del: (path) => request("DELETE", path),

  // ============== AUTH ==============
  login: (email, password) => api.post("/auth/login", { email, password }),
  register: (data) => api.post("/auth/register", data),
  me: () => api.get("/auth/me"),
  logout: () => api.post("/auth/logout"),
  session: (sessionId) => api.post("/auth/session", { session_id: sessionId }),

  // ============== PROFILES ==============
  getMyProfile: () => api.get("/profile/me"),
  updateProfile: (data) => api.put("/profile", data),
  getPrivacy: () => api.get("/profile/privacy"),
  updatePrivacy: (data) => api.put("/profile/privacy", data),
  getPublicProfile: (userId) => api.get(`/users/${userId}/profile`),
  searchUsers: (q) => api.get(`/users/search?q=${encodeURIComponent(q)}`),

  // ============== SOCIAL ==============
  follow: (userId) => api.post(`/users/${userId}/follow`),
  unfollow: (userId) => api.del(`/users/${userId}/follow`),
  getFollowers: (userId) => api.get(`/users/${userId}/followers`),
  getFollowing: (userId) => api.get(`/users/${userId}/following`),
  block: (userId) => api.post(`/users/${userId}/block`),
  unblock: (userId) => api.del(`/users/${userId}/block`),

  // ============== SUGGESTIONS / SESSIONS ==============
  getSuggestions: (data) => api.post("/suggestions", data),
  startSession: (actionId) => api.post("/sessions/start", { action_id: actionId }),
  completeSession: (data) => api.post("/sessions/complete", data),

  // ============== ACTIONS ==============
  getActions: (params = "") => api.get(`/actions${params}`),

  // ============== STATS ==============
  getStats: () => api.get("/stats"),

  // ============== BADGES ==============
  getBadges: () => api.get("/badges"),
  getUserBadges: () => api.get("/badges/user"),

  // ============== NOTIFICATIONS ==============
  getNotifications: () => api.get("/notifications"),
  getNotifPrefs: () => api.get("/notifications/preferences"),
  updateNotifPrefs: (data) => api.put("/notifications/preferences", data),

  // ============== SLOTS ==============
  getNextSlot: () => api.get("/slots/next"),
  dismissSlot: (slotId) => api.post(`/slots/${slotId}/dismiss`),

  // ============== REFLECTIONS ==============
  getReflections: (limit = 30) => api.get(`/reflections?limit=${limit}`),
  createReflection: (data) => api.post("/reflections", data),
  deleteReflection: (id) => api.del(`/reflections/${id}`),
  getReflectionSummaries: () => api.get("/reflections/summaries?limit=1"),

  // ============== PAYMENTS ==============
  createCheckout: (originUrl) => api.post("/payments/checkout", { origin_url: originUrl }),
  getPaymentStatus: (sessionId) => api.get(`/payments/status/${sessionId}`),
};

export default api;

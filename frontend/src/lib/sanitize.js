import DOMPurify from "dompurify";

/**
 * Sanitize user-generated content for safe rendering.
 * Strips all HTML tags — InFinea UGC is plain text only.
 */
export function sanitize(text) {
  if (!text) return "";
  return DOMPurify.sanitize(text, { ALLOWED_TAGS: [] });
}

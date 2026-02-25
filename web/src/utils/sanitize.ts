/**
 * Secure sanitization for chat/AI-generated content.
 * Prevents data exfiltration via img src (e.g. prompt injection that embeds
 * conversation history in external image URLs).
 */
import DOMPurify, { Config } from 'dompurify';

const ALLOWED_IMAGE_URL_PATTERN = /^(?:\/|data:image\/|\.\/|\.\.\/)/i;

function isAllowedImageUrl(url: string): boolean {
  if (!url || typeof url !== 'string') return false;
  const trimmed = url.trim();
  if (!trimmed) return false;
  // Allow relative URLs: /path, ./path, ../path
  if (ALLOWED_IMAGE_URL_PATTERN.test(trimmed)) return true;
  // Allow data:image/* for inline images (no network request)
  if (trimmed.toLowerCase().startsWith('data:image/')) return true;
  // Allow same-origin only
  if (typeof window !== 'undefined') {
    try {
      const parsed = new URL(trimmed, window.location.origin);
      return parsed.origin === window.location.origin;
    } catch {
      return false;
    }
  }
  return false;
}

let secureImageHookAdded = false;

function ensureSecureImageHook(): void {
  if (secureImageHookAdded) return;
  DOMPurify.addHook('afterSanitizeAttributes', (node) => {
    if (node.tagName === 'IMG') {
      const src = node.getAttribute('src');
      if (src && !isAllowedImageUrl(src)) {
        node.removeAttribute('src');
      }
    }
  });
  secureImageHookAdded = true;
}

/**
 * Sanitize content for safe rendering. Restricts img src to same-origin,
 * relative, or data: URLs only. Use for all chat/AI output and user content.
 */
export function sanitizeChatContent(dirty: string, config?: Config): string {
  ensureSecureImageHook();
  const result = DOMPurify.sanitize(dirty, {
    ADD_TAGS: ['think', 'section'],
    ADD_ATTR: ['class'],
    ...config,
  });
  return typeof result === 'string' ? result : '';
}

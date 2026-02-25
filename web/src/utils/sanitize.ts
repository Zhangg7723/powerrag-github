/**
 * Secure sanitization for chat/AI-generated content.
 * Prevents data exfiltration via img src (e.g. prompt injection that embeds
 * conversation history in external image URLs).
 */
import DOMPurify, { Config } from 'dompurify';

// Single / only (not //), ./ , ../ , or data:image/
const ALLOWED_IMAGE_URL_PATTERN = /^(?:\/(?!\/)|data:image\/|\.\/|\.\.\/)/i;

function isAllowedImageUrl(url: string): boolean {
  if (!url || typeof url !== 'string') return false;
  const trimmed = url.trim();
  if (!trimmed) return false;
  // Block protocol-relative URLs (//evil.com) and backslash variants (\\...)
  if (trimmed.startsWith('//') || trimmed.startsWith('\\\\')) return false;
  // Allow relative URLs: /path (single slash), ./path, ../path
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

/** Parse srcset attribute into list of URLs (descriptors like 1x, 100w are stripped). */
function getUrlsFromSrcset(srcset: string): string[] {
  return srcset
    .split(',')
    .map((s) => s.trim().split(/\s+/)[0])
    .filter(Boolean);
}

function isSrcsetAllowed(srcset: string): boolean {
  const urls = getUrlsFromSrcset(srcset);
  return urls.length > 0 && urls.every((url) => isAllowedImageUrl(url));
}

function sanitizeImageUrlAttributes(node: Element): void {
  const tag = node.tagName;
  if (tag !== 'IMG' && tag !== 'SOURCE') return;

  const src = node.getAttribute('src');
  if (src && !isAllowedImageUrl(src)) {
    node.removeAttribute('src');
  }

  const srcset = node.getAttribute('srcset');
  if (srcset && !isSrcsetAllowed(srcset)) {
    node.removeAttribute('srcset');
  }
}

let secureImageHookAdded = false;

function ensureSecureImageHook(): void {
  if (secureImageHookAdded) return;
  DOMPurify.addHook('afterSanitizeAttributes', (node) => {
    if (node.nodeType === 1) {
      sanitizeImageUrlAttributes(node as Element);
    }
  });
  secureImageHookAdded = true;
}

/**
 * Sanitize content for safe rendering. Restricts img/srcset (and source src/srcset)
 * to same-origin, relative, or data: URLs only. Use for all chat/AI output and user content.
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

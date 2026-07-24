import DOMPurify from 'dompurify';

DOMPurify.addHook('uponSanitizeElement', (node, data) => {
  if (data.tagName === 'img' && node instanceof Element) {
    node.removeAttribute('onerror');
    node.removeAttribute('onload');
  }
});

export function sanitizeHtml(dirty: string): string {
  return DOMPurify.sanitize(dirty, {
    ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a', 'code', 'pre', 'p', 'br', 'ul', 'ol', 'li'],
    ALLOWED_ATTR: ['href', 'target', 'rel'],
  });
}

export function sanitizeInput(dirty: string): string {
  return DOMPurify.sanitize(dirty, {
    ALLOWED_TAGS: [],
    ALLOWED_ATTR: [],
  });
}

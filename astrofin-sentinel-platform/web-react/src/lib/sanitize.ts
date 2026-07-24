import DOMPurify from 'dompurify';

let dompurifyReady = false;

try {
  if (!DOMPurify || typeof DOMPurify.addHook !== 'function') {
    throw new Error('DOMPurify not properly initialized — addHook is missing');
  }

  DOMPurify.addHook('afterSanitizeAttributes', (node) => {
    if (!(node instanceof Element)) return;
    const attrs = ['href', 'src', 'xlink:href'];
    for (const attr of attrs) {
      const val = node.getAttribute(attr);
      if (val) {
        const lower = val.trim().toLowerCase();
        if (
          lower.startsWith('javascript:') ||
          lower.startsWith('data:') ||
          lower.startsWith('vbscript:')
        ) {
          node.removeAttribute(attr);
        }
      }
    }
  });

  DOMPurify.addHook('uponSanitizeElement', (node, data) => {
    if (data.tagName === 'img' && node instanceof Element) {
      node.removeAttribute('onerror');
      node.removeAttribute('onload');
    }
  });

  dompurifyReady = true;
} catch (err) {
  console.error('[sanitize] DOMPurify init failed:', err);
}

function getPurify() {
  if (!dompurifyReady) {
    console.warn('[sanitize] DOMPurify not available — falling back to text-only');
  }
  return DOMPurify;
}

export function sanitizeHtml(dirty: string): string {
  const purify = getPurify();
  if (!dompurifyReady) {
    // Fallback: strip all HTML tags
    return dirty.replace(/<[^>]*>/g, '');
  }
  return purify.sanitize(dirty, {
    ALLOWED_TAGS: [
      'b', 'i', 'em', 'strong', 'a', 'code', 'pre',
      'p', 'br', 'ul', 'ol', 'li', 'h1', 'h2', 'h3',
      'h4', 'h5', 'h6', 'blockquote', 'hr', 'img',
      'table', 'thead', 'tbody', 'tr', 'th', 'td',
    ],
    ALLOWED_ATTR: ['href', 'target', 'rel', 'alt', 'src', 'width', 'height'],
    ALLOW_DATA_ATTR: false,
    ADD_ATTR: ['target'],
    FORCE_BODY: false,
  });
}

export function sanitizeInput(dirty: string): string {
  const purify = getPurify();
  if (!dompurifyReady) {
    return dirty.replace(/<[^>]*>/g, '');
  }
  return purify.sanitize(dirty, {
    ALLOWED_TAGS: [],
    ALLOWED_ATTR: [],
  });
}

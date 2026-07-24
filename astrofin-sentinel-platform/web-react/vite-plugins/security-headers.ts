import type { Plugin } from 'vite';
import { createHash } from 'node:crypto';

function generateNonce(): string {
  return createHash('sha256')
    .update(`${Date.now()}-${Math.random()}`)
    .digest('base64');
}

const CSP_BASE = [
  "default-src 'self'",
  "connect-src 'self' ws: wss: http://localhost:*",
  "img-src 'self' data: blob:",
  "font-src 'self'",
  "object-src 'none'",
  "base-uri 'self'",
  "form-action 'self'",
  "frame-ancestors 'none'",
];

const SECURITY_HEADERS: Record<string, string> = {
  'X-Frame-Options': 'DENY',
  'X-Content-Type-Options': 'nosniff',
  'Referrer-Policy': 'strict-origin-when-cross-origin',
  'Permissions-Policy': 'camera=(), microphone=(), geolocation=(), payment=()',
};

export function securityHeadersPlugin(): Plugin {
  return {
    name: 'vite-plugin-security-headers',
    configureServer(server) {
      server.middlewares.use((_req, res, next) => {
        const nonce = generateNonce();

        for (const [name, value] of Object.entries(SECURITY_HEADERS)) {
          res.setHeader(name, value);
        }

        res.setHeader(
          'Content-Security-Policy',
          [
            ...CSP_BASE,
            `script-src 'self' 'nonce-${nonce}'`,
            `style-src 'self' 'nonce-${nonce}'`,
          ].join('; '),
        );

        next();
      });
    },
  };
}

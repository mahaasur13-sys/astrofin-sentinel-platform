# Auth

Two accepted primitives, by design (see ADR-0009):

| Pattern | When to use | Artifact |
|---------|-------------|----------|
| **API key (timing-safe compare)** | Service-to-service, internal scripts, simple gateways | `api_key_auth.py` |
| **RS256 JWT (with key rotation)** | User-facing API, browser/mobile clients, OAuth/OIDC flows | `jwt_rs256.py` |

## Why two patterns

* API key is simpler, has no token-expiry surface, ideal for machine
  consumers.
* JWT carries identity claims (sub, aud, iss, exp) — required when the
  client must prove *who* they are, not just *that they are allowed*.

For new endpoints, pick the one whose threat model matches; do not
add a third pattern (HMAC, opaque sessions, mTLS) without an ADR.

## Anti-patterns to reject in code review

* Plain `==` comparison of secrets — use `secrets.compare_digest`.
* HS256 with a shared secret in the repo — RS256 only for new code.
* Storing JWTs in `localStorage` from server-rendered templates —
  not a Python concern, but flag it in cross-repo review.
* Re-implementing the `@require_api_key` decorator locally instead of
  importing it.

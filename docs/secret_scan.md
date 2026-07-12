# Secret Scanning

## What is it
This project uses [**gitleaks**](https://github.com/gitleaks/gitleaks) as a
post-merge pre-commit-style scanner for accidentally-committed secrets
(API keys, tokens, private keys, JWT signing secrets, etc.).

## Where the rules live
- `.gitleaks.toml` — project-level allowlist.
  - `tests/` directory: deliberate secret fixtures (kept as test data).
  - `docs/ARCHITECTURE.md`: a documented JWT-format example, not a real secret.
  - `tests/test_logging_utils.py:42` uses `AKIAIOSFODNN7EXAMPLE`, the
    well-known AWS docs placeholder.

## How to run locally
```bash
# from repo root
gitleaks detect --config .gitleaks.toml --no-banner
# exit code 0 == clean, 1 == leak found
```

## CI integration
The Quality Gate workflow does **not** run gitleaks directly.
Secret scanning is performed out-of-band by `Secret Scan (detect-secrets)` in
the CI checks list. See `docs/CI_CHECKS.md` for the full inventory.

## When you add a new secret fixture
1. Place it in `tests/` or mark it in `.gitleaks.toml` as a known fixture.
2. If the secret is **real**, do not commit it — rotate the credential first
   and follow the incident playbook in `docs/SECURITY.md`.

## Last verification
- 62 commits scanned, 0 leaks, scan took ~1.7s.
- Verified locally on 2026-07-12.

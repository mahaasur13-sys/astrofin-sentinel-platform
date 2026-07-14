# Privacy Notice

> What data `astrofin-sentinel-platform` collects, how it stores it,
> how it protects it, and the rights you have. This is the public,
> non-binding summary; for legal weight consult counsel.

## Scope

This notice covers:

- The `astrofin-sentinel-platform` source repository and the
  container images built from it.
- The "Dash" web UI (`web/`), the multi-agent runtime (`agents/`),
  and the local observability stack (`deploy/monitoring/`).
- Any data persisted to a local SQLite/Postgres store or written
  to logs by these components.

This notice **does not** cover third-party services the platform
*calls* (e.g. LLM provider APIs) — those are governed by each
provider's own policy.

## Data we collect

| Category | Examples | Why | Where it lives |
|---|---|---|---|
| Authentication credentials | JWTs, API keys (in `.env`, never in code) | Authenticate Dash UI, agents, CI | `core/auth.py`, secrets only via env |
| User-provided inputs | trade signals, config JSON, agent prompts | Run the platform | `data/`, `migrations/`, the configured DB |
| Operational telemetry | request logs, error traces, structured fields | Debug, monitor, audit | Loki / `logs/` + stdout |
| **PII** | email addresses, names, API keys/tokens in messages | End-user content that may transit logs | **Scrubbed** before persistence (see below) |

We do **not** intentionally collect:

- Government identifiers (passport, SSN, etc.).
- Financial account numbers.
- Biometric data.
- Health data.

If you push such data into the system, that is on you.

## PII scrubbing

From **Phase 3b** (PR #133) onward, every log record produced by
the platform runs through a `scrub_pii` structlog processor
(`core/logging_utils.py`) before being written. The scrubber
replaces, with `[REDACTED:<kind>]` markers:

- Email addresses.
- JWTs (3-segment base64url).
- `Authorization: Bearer …` / `Token …` headers.
- AWS access key IDs (`AKIA…`).
- GitHub `ghp_…` / `gho_…` / `ghs_…` tokens.
- OpenAI `sk-…` keys.
- Google API keys (`AIza…`).
- Long hex secrets (≥ 32 hex chars).
- Arbitrary keys whose name contains `secret`, `token`, `password`,
  `api_key`, `authorization`.

Scrubbing is recursive over nested `dict` / `list` structures and
is opt-out only for the test harness (`scrub_pii(..., enabled=False)`).

## How we protect data

- **In transit** — TLS at the edge (reverse proxy / cloud LB in
  prod). Locally, the platform binds to `127.0.0.1` by default.
- **At rest** — SQLite is the default dev store; production is
  expected to use Postgres + WAL-G / S3 backups (see
  `RUNBOOK.md`). Disk encryption is the operator's responsibility.
- **In code** — secrets are **never** committed. The repo runs
  `gitleaks` + `detect-secrets` on every PR; the baseline
  (`.secrets.baseline`) is reviewed on every change.
- **In CI** — Bandit, pip-audit, and safety run on every PR and
  push to `master`.
- **In logs** — see *PII scrubbing* above.

## Data sharing

- We do **not** sell, rent, or share user data with third parties.
- LLM provider calls happen over HTTPS to whichever provider the
  operator configures; only the prompt content is sent, and the
  provider's own policy applies to that.
- We do not embed third-party analytics, ad SDKs, or trackers.

## Your rights (GDPR / equivalent)

If you are an EU/EEA data subject, you have the right to:

- **Access** the personal data we hold about you.
- **Rectification** of inaccurate data.
- **Erasure** ("right to be forgotten"), subject to legal
  retention obligations.
- **Restriction** or **objection** to processing.
- **Data portability** — receive your data in a structured,
  machine-readable format.
- **Lodge a complaint** with your supervisory authority.

To exercise any of these, open a private issue via
[`SECURITY.md`](SECURITY.md) (re-routed to the on-call). We respond
within 30 days.

## Retention

| Data | Default retention |
|---|---|
| Application logs | 30 days (Loki default; configurable) |
| Audit/security logs | 365 days |
| User DB rows | Until the user requests deletion |
| Backups | 30 days rolling (WAL-G default) |

## Children

The platform is not directed at children under 16. Do not use it
to process children's data without a lawful basis.

## Changes to this notice

Material changes are tracked in git. Non-material edits (typos,
clarifications) ship without a version bump. A change is "material"
if it expands the categories of data we collect or weakens the
protections described above.

## Contact

- Security issues → [`SECURITY.md`](SECURITY.md)
- Privacy requests → see `MAINTAINERS.md` for the current on-call.

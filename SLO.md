# SLO — astrofin-sentinel-platform

> Top-level SLO index. Detailed SLI formulas and recording rules live in
> [`docs/slo.md`](./docs/slo.md). This file is the **short version** that
> an on-call engineer can read in 60 seconds.

## Service tier

**Tier 2** — internal multi-agent platform. Downtime hurts engineers
and the on-call rotation, but does not directly hit paying customers
yet (pre-revenue).

## SLOs (rolling 30 days)

| # | SLI | SLO target | Error budget |
|---|---|---|---|
| 1 | **API availability** — share of HTTP responses with status < 500 across all `/api/*` and `/healthz` endpoints | **≥ 99.5%** | 3 h 36 min downtime / 30 d |
| 2 | **Submission latency** — p95 of `POST /api/v1/submit` end-to-end | **< 500 ms** | 1% of submissions may exceed 500 ms in any 5-min window |
| 3 | **Request success** — share of `2xx` responses across all authenticated endpoints | **> 99.9%** | 0.1% may be `4xx` due to user error (counted) and `5xx` (counted) |

## SLI instrumentation

| SLO | Source | PromQL (sketch) |
|---|---|---|
| 1 — availability | `http_requests_total{job="astrofin-*"}` | `sum(rate(http_requests_total{code!~"5.."}[30d])) / sum(rate(http_requests_total[30d]))` |
| 2 — submit p95 | `http_request_duration_seconds_bucket{path="/api/v1/submit"}` | `histogram_quantile(0.95, rate(...[5m]))` |
| 3 — success rate | `http_requests_total{job="astrofin-*",code=~"2xx"}` | `sum(rate(http_requests_total{code=~"2xx"}[30d])) / sum(rate(http_requests_total[30d]))` |

Recording rules are not yet in `deploy/prometheus/rules/` — issue #129
tracks adding them.

## Burn-rate alerts

| Window | Burn rate | Action |
|---|---|---|
| 1 h, fast burn | 14.4× | Page on-call (SEV-2) |
| 6 h, slow burn | 6× | Slack `#oncall-astrofin` |
| 24 h, slow burn | 3× | Open an investigation issue |

These thresholds consume the 30-day error budget in 2 / 5 / 10 days
respectively if the burn does not stop.

## Error budget policy

- Budget exhausted → non-critical releases are frozen.
- Budget < 25% remaining → engineering leads are notified; prioritize
  reliability work over features.
- Budget is reset on the 1st of each month; the carry-over is 0
  (deliberately conservative until we have a multi-month track record).

## Exclusions (do not count against budget)

- Planned maintenance windows, **announced 24 h in advance** and
  tagged in Grafana.
- Outages whose root cause is an upstream provider (exchange APIs,
  auth provider) and where we have evidence the service would
  otherwise have met the SLO.

## Linked

- [`docs/slo.md`](./docs/slo.md) — full SLI definitions, recording
  rules, and the PromQL catalog.
- [`docs/chaos-engineering.md`](./docs/chaos-engineering.md) — chaos
  drills that verify these SLOs are still meaningful.
- [`RUNBOOK.md`](./RUNBOOK.md) — what to do when an alert fires.

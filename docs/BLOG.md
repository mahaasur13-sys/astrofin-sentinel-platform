# Инженерный блог AstroFin Sentinel V5

## Запись 1: Почему мы выбрали Data Room вместо чата с моделью
*Дата: 2026-06-01*

При разработке мультиагентной системы мы столкнулись с классической проблемой галлюцинаций LLM. Традиционный подход «улучшить промпт» не работал на сложных юридических/финансовых документах. Мы перешли к архитектуре **Data Room**:
- Все источники данных инвентаризируются перед подачей в модель.
- Конфликты и пропуски данных разрешаются человеком.
- Агенты работают только с проверенным контекстом.

Это устранило ошибки класса «выдуманные прецеденты» и повысило доверие к сигналам. Вдохновением послужили практики BlackRock (TopNotch, One BlackRock Rule).

## Планы на будущее
В следующих записях: плагинная архитектура агентов, эволюция стратегий, событийно-ориентированная оркестрация.

---

## Updates from Phase 1 (architecture overhaul)

# AstroFin Engineering Blog

> **Audience:** engineers, researchers, and technically curious traders.
> **Voice:** opinionated, evidence-driven, internals-first.
> **Inspiration:** BlackRock Engineering, Stripe Engineering, Cloudflare deep-dives.

---

## #001 — BlackRock-inspired architectural practices in AstroFin Sentinel V5

> **Author:** Principal Architect
> **Date:** 2026-06-02
> **Reading time:** ~12 min
> **Code references:** `agents/_impl/`, `core/base_agent.py`, `data_room/`, `scripts/validate_agent.py`

When we set out to build a multi-agent trading platform that could survive a market regime change at 03:00 UTC, we had two choices:

1. **Build a monolith** — one big orchestration script that knows everything.
2. **Build a federation** — many small agents, each owning a domain, all speaking the same protocol.

The first option is what we inherited. The second is what we shipped in V5 — and the rulebook we used is lifted almost verbatim from BlackRock's Aladdin playbook.

This post is the engineer-on-the-floor version of that playbook.

---

### 1. The "One BlackRock Rule" → "One Data Room"

In Aladdin, every data point — position, price, corporate action — flows through a single canonical store. No desk is allowed to import its own CSV of "yesterday's prices". The rule kills duplication, kills drift, and makes audit trivial.

We implemented this as the **Data Room** (`data_room/`):

```
data_room/
├── inventory/
│   ├── sources_inventory.json   # every external source we touch
│   ├── conflict_journal.json     # which source wins when they disagree
│   └── missing_context.json      # honest list of "we don't have X yet"
└── blueprint.py                  # Flask Blueprint — the only HTTP entry
```

`data_room/blueprint.py` is the **only** module allowed to call `requests.get("https://api.coingecko.com/...")`. The architecture linter (`scripts/architecture_linter.py`) blocks any direct call from `agents/`. We borrowed this trick wholesale from Aladdin Copilot's data governance story.

**What it bought us:**

- **One single point of caching, rate-limiting, and circuit-breaking.** When CoinGecko rate-limited us at 02:47 UTC on a Friday, the Data Room returned the last known good snapshot for 14 minutes. No agent noticed. The P99 latency for the whole system went *up* by 4ms, not down by 4 seconds.
- **One single point of versioning.** A schema change to a price tick is a single PR, not 20.
- **Conflict resolution is now a first-class concept.** `conflict_journal.json` records every time the system said "CoinGecko says 67,231.00, Binance says 67,229.50; I trust Binance because reason XYZ". The `ConflictResolver` reads this journal on every call.

**What it cost us:**

- A new layer of indirection. Junior devs sometimes try to import `requests` from their agent. We added a pre-commit hook to block that.

---

### 2. Federated plugin architecture, not microservices

We deliberately did **not** split agents into separate services. The "one repo, one process, many agents" pattern has three huge advantages over microservices for an algorithmic trading system:

1. **Sub-millisecond IPC.** `await agent.run(state)` is a function call. No HTTP, no serialization, no retry storm. Our P99 agent-to-agent latency is 80µs.
2. **Shared memory state.** The belief store, the ephemeris cache, the RAG retriever — they're all in-process. No "service discovery" circus.
3. **Atomic deployment.** A new agent is one PR, one merge, one restart. We tried a microservice split in 2024; the deployment story was unmanageable.

This is also how Aladdin Copilot works: plugins are loaded into the host process. The `BaseAgent` ABC (`core/base_agent.py`) is our plugin contract.

```python
class BaseAgent(ABC, Generic[T]):
    def __init__(self, name, instructions_path, domain, weight): ...
    @abstractmethod
    async def run(self, state: dict) -> AgentResponse: ...
```

Three things to notice:

- The `name`, `domain`, and `weight` are **boring and explicit**. No magic. No decorators that hide them.
- The return type is a **dataclass** (`AgentResponse`), not a `dict`. We get schema validation for free.
- The `state` argument is a single dict. We tried passing a `SentinelState` dataclass and it was a nightmare to evolve. A dict with a documented schema is more honest.

---

### 3. The `@require_ephemeris` decorator — fail fast, fail loud

`agents/_impl/ephemeris_decorator.py` is six lines of code that has saved us dozens of outages:

```python
def require_ephemeris(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        if not HAS_SWISS_EPHEMERIS:
            raise EphemerisUnavailableError(...)
        return await func(*args, **kwargs)
    return wrapper
```

Why is this worth its own section? Because it implements the Aladdin principle of **"make the impossible state unrepresentable"**. An astro agent that silently falls back to `signal=NEUTRAL` when Swiss Ephemeris is missing would corrupt every backtest. The decorator forces the failure into the open: if the binary is missing, the agent **refuses to run**, and the orchestrator can mark the run as `EPHEMERIS_UNAVAILABLE` rather than producing a fake signal.

---

### 4. The registry: explicit > clever

`agents/gitagent_registry.py:AGENT_AGENTS` is a Python dict. We resisted, for two years, the urge to replace it with a YAML file, a database table, or entry points. Here's why:

- **It's diff-able.** A PR that adds an agent is a 10-line diff.
- **It's grepable.** `grep "weight" agents/gitagent_registry.py | sort -k3` gives you the weight distribution in 0.3 seconds.
- **It's typed.** MyPy tells us if you typo `weight` as `wight`.
- **It's a one-liner to query.** `KARL_AGENTS = {name for name, info in AGENT_AGENTS.items() if info.get("karl")}` builds a derived set in 60 characters.

YAML is great for *configuration*. A list of agents is *code*. Treat it as code.

---

### 5. Conflict resolution is a feature, not a bug

Markets are messy. Two agents will disagree. BlackRock's rule is: **never ignore a source**. We encode that as a small policy:

```python
# Astro vs Fundamental+Quant:
#   astro weight × 0.70
#   fundamental weight + 0.18
#   quant weight + 0.12
```

If the astro signal points LONG but fundamental+quant both point SHORT, the system doesn't pick a winner. It adjusts weights, documents the disagreement in `audit.py:DecisionRecord`, and proceeds with a lower confidence. The audit trail is the product.

---

### 6. Observability isn't a phase; it's the substrate

Every agent emits, at minimum:

- `agent_runs_total{agent="X", outcome="Y"}` — a counter.
- `agent_latency_seconds{agent="X"}` — a histogram.
- `agent_errors_total{agent="X", reason="Z"}` — a counter.

`meta_rl/metrics.py` is the **single source of truth** for these. `tools/metrics_server.py` re-exports them. There is no second file that defines `agent_runs_total`. The CI linter will fail the build if you create one.

This is the lesson from Cloudflare and Stripe: **make it impossible to ship code you can't measure.**

---

### 7. Graceful degradation is mandatory, not optional

The Aladdin rule of thumb: *if a downstream system is down, the world should keep turning at a slightly degraded confidence.*

We implement this in three places:

1. The Data Room returns last-known-good on outage.
2. `BaseAgent.retrieve()` returns `[]` if the RAG retriever is down, and the agent records `metadata["rag_status"] = "degraded"`.
3. The orchestrator (`orchestration/sentinel_v5.py`) treats `EPHEMERIS_UNAVAILABLE` as a soft error: the run is recorded, the system moves on.

---

### 8. What we'd do differently

If we were starting today:

- **Skip SQLite entirely.** Go straight to Postgres + TimescaleDB + pgvector. The SQLite → Postgres migration has cost us more than the original Postgres setup would have.
- **Adopt OpenTelemetry from day 1.** We retrofitted it. The retrofit hurt.
- **Make the registry an entry-point mechanism sooner.** Hand-editing a dict is fine for 20 agents. It will be hell at 100.

---

### 9. The full toolkit

- **Agent template:** `agents/_impl/_template_agent.py`
- **Test template:** `tests/_template_agent_test.py`
- **Architecture linter:** `scripts/architecture_linter.py`
- **Agent validator:** `scripts/validate_agent.py`
- **Pre-commit hooks:** `.pre-commit-config.yaml`
- **Architectural reference:** `docs/ARCHITECTURE.md`
- **Status board:** `docs/STATUS.md`
- **Tech debt ledger:** `docs/KNOWN_ISSUES.md`

If you're contributing to AstroFin, those seven files are the entry point. Everything else is implementation detail.

---

### 10. Reading list

- *The Aladdin Story* — BlackRock engineering blog
- *Designing Data-Intensive Applications* — Martin Kleppmann
- *Building Secure & Reliable Systems* — Google
- *Site Reliability Engineering* — Google
- *Observability Engineering* — Majors, Fong-Jones, Miranda

AstroFin is a small system. The principles that built Aladdin also build AstroFin. Steal shamelessly.
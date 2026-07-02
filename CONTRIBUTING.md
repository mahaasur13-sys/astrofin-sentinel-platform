# Contributing to AstroFin Sentinel Platform

Thank you for your interest in contributing to the AstroFin platform. This project
uses a monorepo structure combining the trading sentinel, infrastructure, kernel,
and bridge subsystems in a single repository.

## Development Setup

```bash
git clone <your-fork-url>
cd astrofin-sentinel-platform
python3 -m venv venv
source venv/bin/activate

# Install the project in editable mode (pulls in runtime deps from pyproject.toml)
pip install -e .

# Install all extras (tests, linters, docs tools)
pip install -r requirements.all.txt
```

> Note: editable install (`pip install -e .`) registers the project packages
> (e.g. `agents/`, `core/`, `orchestration/`) on `sys.path` so tests and tooling
> can import them without manual `PYTHONPATH` tweaks. `requirements.all.txt`
> includes test, lint, and dev dependencies that are not in the runtime set.

## Project Structure (Monorepo)

```
astrofin-sentinel-platform/
├── agents/                  # AI agents (12 specialized agents, AstroCouncil)
├── core/                    # Core utilities (ephemeris, logging, volatility)
├── orchestration/           # Sentinel v5 orchestrator, router
├── meta_rl/                 # Meta-reinforcement-learning pipeline
├── trading/                 # Trading engine (Binance, TWAP, execution)
├── web/                     # FastAPI dashboard
├── knowledge/               # RAG/FAISS knowledge base
├── tests/                   # Pytest test suite
│
├── infrastructure/asurdev/  # Home-cluster IaC, ACOS admission controllers
├── kernel/atom-federation/  # Deterministic alignment kernel, formal verification
├── bridge/roma/             # GPU execution bridge, SaaS billing, Stripe webhooks
│
├── docs/                    # Architecture, ADRs, agent registry
├── deploy/                  # Docker, docker-compose, health endpoints
└── config/                  # CRDs, deployment manifests
```

When you change a file under `infrastructure/`, `kernel/`, or `bridge/`,
make sure the corresponding package still builds and its own tests pass
(`cd infrastructure/asurdev && make test`, etc.).

## Workflow

1. Fork the repository (if you do not have write access).
2. Create a feature branch from `feat/initial-monorepo` (or `main` after merge):
   `git checkout -b feat/my-change`
3. Make your changes.
4. Run tests and linters locally (see below).
5. Commit with a clear message (see Commit Messages below).
6. Open a Pull Request.

## Tests

```bash
# Fast: collect-only to ensure discovery works
python3 -m pytest --collect-only

# Full suite (note: some integration tests hit Binance/Ollama and may require
# network or running services; they are tagged with @pytest.mark.integration)
python3 -m pytest -q --no-cov
```

## Linting

```bash
flake8 agents/ orchestration/ core/ infrastructure/ kernel/ bridge/
bandit -r agents/ orchestration/ core/ infrastructure/ kernel/ bridge/
```

## Code Style

- Python 3.12+
- Type hints preferred (`from __future__ import annotations`)
- Use the centralized logger from `core/logging.py` (do not call
  `logging.getLogger(__name__)` directly inside agents/orchestration code)
- One agent per file in `agents/_impl/`
- When adding a new external dependency, update `requirements.txt`
  (runtime) or `requirements.all.txt` (dev/test) and add a note in
  the PR description.

## Commit Messages

Format: `<type>(<scope>): <subject>`

Types: `feat`, `fix`, `ci`, `docs`, `refactor`, `test`, `chore`

Examples:
- `feat(agents): add ElliotWave agent`
- `fix(orchestration): handle empty flow result gracefully`
- `docs(readme): update badges and monorepo structure`
- `ci(dependabot): add weekly pip + github-actions updates`

## CodeRabbit Review

Pull requests trigger CodeRabbit via `.coderabbit.yaml` (Russian, assertive).
CodeRabbit checks **architectural reasoning** (R1–R9 alignment,
KNOWN_ISSUES.md P1 blockers). Pre-commit handles **syntactic** checks
(Ruff, Bandit, detect-secrets, architecture_linter.py). Do not duplicate
pre-commit logic in CodeRabbit instructions — see `docs/CODE_REVIEW.md`.

## Architecture Linter

For new agents, run before requesting a PR review:

```bash
python scripts/validate_agent.py agents/_impl/new_agent.py
```

All 9 checks must pass.

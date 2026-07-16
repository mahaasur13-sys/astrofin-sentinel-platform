# Contributing to AstroFin Sentinel V5

Thank you for your interest in contributing to the AstroFin platform.

## Setup

```bash
git clone <your-fork-url>
cd push
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-change`)
3. Make your changes
4. Run tests and linters (see below)
5. Commit with a clear message
6. Open a Pull Request

## Tests

```bash
python3 -m pytest --collect-only  # check discovery
python3 -m pytest -q             # run tests
```

## Linting

```bash
flake8 agents/ orchestration/ core/
bandit -r agents/ orchestration/ core/
```

## Code Style

- Python 3.12+
- Type hints preferred (`from __future__ import annotations`)
- Use the centralized logger from `core/logging.py`
- One agent per file in `agents/_impl/`

## Commit Messages

Format: `<type>(<scope>): <subject>`

Types: `feat`, `fix`, `ci`, `docs`, `refactor`, `test`, `chore`

Example: `feat(agents): add ElliotWave agent`
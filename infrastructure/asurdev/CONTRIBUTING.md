# Contributing to AsurDev

Thank you for contributing! Please read this guide before submitting PRs.

## 🛠️ Development Setup

```bash
git clone https://github.com/mahaasur13-sys/AsurDev.git
cd AsurDev
make install        # Install deps + pre-commit hooks
make pre-commit     # Run all checks manually
```

## ✅ PR Checklist

Before opening a PR, ensure:

- [ ] `make lint` passes (Ruff)
- [ ] `make format` shows no changes (Black)
- [ ] `make test` passes (pytest + coverage)
- [ ] New features have tests in `tests/`
- [ ] `pyproject.toml` deps pinned (use `>=X.Y.Z,<X.Y+1.0` pattern)

## 📐 Code Style

| Tool | Config | Rule |
|------|--------|------|
| Ruff | `pyproject.toml` | E/F/Uup, tryceratops, pydocstyle |
| Black | `pyproject.toml` | 88-char line length |
| MyPy | `pyproject.toml` | strict mode |

Run all:
```bash
make pre-commit
```

## 🧪 Testing

```bash
# Unit tests
make test

# With coverage report
make test-cov

# Specific module
pytest tests/test_ml_api.py -v
```

Coverage threshold: **70%** minimum for new code.

## 🐳 Docker

```bash
# Build ML API image
make ml-api-docker-build

# Run prod container
make ml-api-run-prod
```

## 🔒 Security

- Never commit secrets — use `.env.example` as template
- All new dependencies scanned with Trivy (see CI)
- No `continue-on-error: true` in production workflows
- Report vulnerabilities via GitHub Security Advisories

## 📦 Release Process

1. Update `CHANGELOG.md`
2. Tag: `git tag vX.Y.Z && git push --tags`
3. CI auto-builds Docker image → GHCR
4. SLSA provenance attestations generated automatically

## 🏗️ Project Structure

```
AsurDev/
├── tests/           # pytest test suite
├── pyproject.toml   # Python deps + tool config
├── Makefile         # Dev commands
├── .github/workflows/ci.yml  # CI pipeline
└── slsa4/           # SLSA v4 provenance workflow
```

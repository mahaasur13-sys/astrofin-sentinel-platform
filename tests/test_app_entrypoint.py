"""Unit test for the app container entrypoint (no docker required).

The entrypoint must run the idempotent schema init (`python -m db`) before
delegating to the orchestrator via `exec "$@"`, with no destructive
`--reset` / `--migrate` flags.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ENTRYPOINT = REPO_ROOT / "deploy" / "docker" / "app-entrypoint.sh"
DOCKERFILE = REPO_ROOT / "deploy" / "docker" / "Dockerfile"


def test_entrypoint_runs_db_init_then_exec():
    text = ENTRYPOINT.read_text()

    assert "python -m db" in text, "entrypoint must init the schema first"
    assert 'exec "$@"' in text, "entrypoint must exec the orchestrator (CMD)"

    # Idempotent only — no destructive operations.
    assert "--reset" not in text
    assert "--migrate" not in text


def test_dockerfile_wires_entrypoint_and_keeps_orchestrator_cmd():
    text = DOCKERFILE.read_text()

    assert 'ENTRYPOINT ["/app/deploy/docker/app-entrypoint.sh"]' in text
    assert 'CMD ["python", "-m", "orchestration.sentinel_v5"]' in text

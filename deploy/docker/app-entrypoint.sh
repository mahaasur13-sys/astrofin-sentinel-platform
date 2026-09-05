#!/bin/sh
set -eu

# Idempotent schema init — Base.metadata.create_all(checkfirst), no DROP/reset.
# On an already-initialized volume this is a harmless no-op.
python -m db

# Run the orchestrator (the container CMD) and replace this shell process.
# CMD is `python -m orchestration.sentinel_v5` (see deploy/docker/Dockerfile).
exec "$@"

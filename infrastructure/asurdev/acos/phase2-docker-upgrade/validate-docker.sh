#!/usr/bin/env bash
# validate-docker.sh — статическая валидация Dockerfile на соответствие
#                       Phase-2 стандарту (см. CHECKLIST.md).
#
# Проверяет ТОЛЬКО то, что видно в тексте файла. Не запускает `docker build`
# — для этого есть smoke-build.sh.
#
# Использование:
#   ./validate-docker.sh <path/to/Dockerfile>
#   ./validate-docker.sh <path/to/Dockerfile> --compose <path/to/docker-compose.yml>
#   ./validate-docker.sh cluster/node/Dockerfile --compose docker-compose.yml
#
# Коды выхода:
#   0  — всё хорошо (только предупреждения, если есть)
#   1  — критические ошибки
#
# Зависимости: bash ≥ 4, grep, awk. Опционально: docker (для compose-проверки),
# hadolint (для дополнительного линта).
set -euo pipefail

DOCKERFILE=""
COMPOSE=""
COMPOSE_FLAG=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --compose|-c)
      COMPOSE_FLAG=1
      COMPOSE="${2:-}"
      shift 2
      ;;
    -h|--help)
      sed -n '2,18p' "$0"
      exit 0
      ;;
    *)
      DOCKERFILE="$1"
      shift
      ;;
  esac
done

DOCKERFILE="${DOCKERFILE:-Dockerfile}"

if [[ ! -f "$DOCKERFILE" ]]; then
  printf "\033[31m❌ Dockerfile not found: %s\033[0m\n" "$DOCKERFILE"
  exit 1
fi

red()   { printf "\033[31m%s\033[0m\n" "$*"; }
green() { printf "\033[32m%s\033[0m\n" "$*"; }
amber() { printf "\033[33m%s\033[0m\n" "$*"; }

fail=0
warn=0

check_pass() { green "✅ $1"; }
check_fail() { red   "❌ $1"; fail=$((fail + 1)); }
check_warn() { amber "⚠️  $1"; warn=$((warn + 1)); }

printf "\n\033[1m=== Phase-2 Dockerfile validation: %s ===\033[0m\n\n" "$DOCKERFILE"

# ────────────────────────────────────────────────────────────────────────────
# 1. Required directives
# ────────────────────────────────────────────────────────────────────────────
printf "\033[1m--- Required directives ---\033[0m\n"
for directive in FROM WORKDIR USER ENTRYPOINT HEALTHCHECK; do
  if grep -qE "^${directive}[[:space:]]" "$DOCKERFILE"; then
    check_pass "${directive} present"
  else
    check_fail "missing ${directive}"
  fi
done

# ────────────────────────────────────────────────────────────────────────────
# 2. Pinned base image (no :latest, prefer -slim)
# ────────────────────────────────────────────────────────────────────────────
printf "\n\033[1m--- Base image ---\033[0m\n"
if grep -qE "^FROM[[:space:]]+[^[:space:]]+:latest" "$DOCKERFILE"; then
  check_fail "FROM uses :latest — pin a version"
else
  check_pass "no :latest tags"
fi

FROM_LINE=$(grep -m1 -E "^FROM" "$DOCKERFILE" || true)
if [[ -n "$FROM_LINE" ]]; then
  if grep -qE "python:3\.[0-9]+-slim" <<<"$FROM_LINE"; then
    check_pass "base image is python:3.x-slim (pinned)"
  elif grep -qE "python:[0-9.]+-slim" <<<"$FROM_LINE"; then
    check_pass "base image is python:X.Y.Z-slim (fully pinned)"
  elif grep -qE "nvidia/cuda" <<<"$FROM_LINE"; then
    check_warn "base image is nvidia/cuda — verify Python runtime is also pinned"
  else
    check_warn "base image is non-standard: $FROM_LINE — confirm this is intentional"
  fi
fi

# ────────────────────────────────────────────────────────────────────────────
# 3. Multi-stage build
# ────────────────────────────────────────────────────────────────────────────
printf "\n\033[1m--- Multi-stage build ---\033[0m\n"
if grep -qE "^FROM[[:space:]]+[^[:space:]]+[[:space:]]+AS[[:space:]]+deps" "$DOCKERFILE"; then
  check_pass "multi-stage build (deps stage)"
elif grep -qE "^FROM[[:space:]]+[^[:space:]]+[[:space:]]+AS[[:space:]]+builder" "$DOCKERFILE"; then
  check_pass "multi-stage build (builder stage)"
elif grep -qE "^FROM[[:space:]]+[^[:space:]]+[[:space:]]+AS" "$DOCKERFILE"; then
  check_warn "multi-stage present but stage name is not 'deps'/'builder'"
else
  check_fail "no multi-stage build (deps + runtime required)"
fi

# ────────────────────────────────────────────────────────────────────────────
# 4. tini for PID 1
# ────────────────────────────────────────────────────────────────────────────
printf "\n\033[1m--- Init system ---\033[0m\n"
if grep -qE "tini" "$DOCKERFILE"; then
  check_pass "tini present"
else
  check_fail "tini not installed (required for proper PID 1 signal handling)"
fi

if grep -qE "^ENTRYPOINT[[:space:]]+\[\"/usr/bin/tini\"" "$DOCKERFILE"; then
  check_pass "ENTRYPOINT starts with /usr/bin/tini"
else
  check_warn "ENTRYPOINT does not start with /usr/bin/tini — confirm this is intentional"
fi

# ────────────────────────────────────────────────────────────────────────────
# 5. Non-root user
# ────────────────────────────────────────────────────────────────────────────
printf "\n\033[1m--- Non-root user ---\033[0m\n"
USER_LINE=$(grep -E "^USER" "$DOCKERFILE" | tail -1 || true)
if [[ -z "$USER_LINE" ]]; then
  check_fail "no USER directive (running as root in production)"
else
  USER_NAME=$(awk '{print $2}' <<<"$USER_LINE")
  if [[ "$USER_NAME" == "0" || "$USER_NAME" == "root" ]]; then
    check_fail "USER is root (${USER_NAME})"
  elif [[ -n "$USER_NAME" ]]; then
    check_pass "USER=${USER_NAME}"

    # Check that the user is actually created with the right uid (1001)
    if grep -qE "useradd.*--uid[[:space:]]+1001" "$DOCKERFILE" || \
       grep -qE "useradd.*-u[[:space:]]+1001" "$DOCKERFILE"; then
      check_pass "useradd with --uid 1001"
    else
      check_warn "user created without explicit --uid 1001 (Phase-2 convention)"
    fi

    # Check that the shell is /usr/sbin/nologin
    if grep -qE "useradd.*--shell[[:space:]]+/usr/sbin/nologin" "$DOCKERFILE" || \
       grep -qE "useradd.*-s[[:space:]]+/usr/sbin/nologin" "$DOCKERFILE"; then
      check_pass "useradd with --shell /usr/sbin/nologin"
    else
      check_warn "user created without --shell /usr/sbin/nologin"
    fi
  fi
fi

# ────────────────────────────────────────────────────────────────────────────
# 6. Bytecode compilation
# ────────────────────────────────────────────────────────────────────────────
printf "\n\033[1m--- Bytecode compilation ---\033[0m\n"
if grep -qE "compileall" "$DOCKERFILE"; then
  check_pass "compileall present (build-time bytecode)"
else
  check_warn "no compileall — slower cold-start + broken imports surface at runtime"
fi

# ────────────────────────────────────────────────────────────────────────────
# 7. HEALTHCHECK quality
# ────────────────────────────────────────────────────────────────────────────
printf "\n\033[1m--- HEALTHCHECK quality ---\033[0m\n"
HC_LINE=$(grep -E "^HEALTHCHECK" "$DOCKERFILE" | tail -1 || true)
if [[ -n "$HC_LINE" ]]; then
  if grep -qE "HEALTHCHECK.*python -c ['\"]import sys" "$DOCKERFILE"; then
    check_fail "HEALTHCHECK is a tautological 'python -c \"import sys; sys.exit(0)\"' — always healthy"
  elif grep -qE "HEALTHCHECK.*python -c" "$DOCKERFILE"; then
    check_warn "HEALTHCHECK is an inline python -c snippet — promote to a module"
  elif grep -qE "HEALTHCHECK.*python -m" "$DOCKERFILE"; then
    check_pass "HEALTHCHECK delegates to a python -m module (real probe)"
  elif grep -qE "HEALTHCHECK.*CMD" "$DOCKERFILE"; then
    check_pass "HEALTHCHECK CMD present"
  fi

  # Check healthcheck timing parameters
  if grep -qE "HEALTHCHECK.*--start-period" "$DOCKERFILE"; then
    check_pass "--start-period set (avoids premature unhealthy)"
  else
    check_warn "no --start-period — container may be marked unhealthy during boot"
  fi
fi

# ────────────────────────────────────────────────────────────────────────────
# 8. Pinned dependencies
# ────────────────────────────────────────────────────────────────────────────
printf "\n\033[1m--- Pinned dependencies ---\033[0m\n"
# Match `pip install -r X`, `pip install --requirement X`, AND the
# `pip install --no-deps -r X` variant used in cluster/node/Dockerfile.
# The character class `[^|;&]+` stops the match at the next shell `&&` /
# `||` / `;` so we only inspect a single pip invocation at a time.
if grep -qE 'pip install[^|;&]+(-r[[:space:]]+|\-\-requirement[[:space:]]+)' "$DOCKERFILE"; then
  check_pass "pip install uses pinned requirements file (-r / --requirement)"
  # Try to find the referenced requirements file in the build context
  REQ_PATH=$(grep -oE "COPY [^[:space:]]+requirements\.txt" "$DOCKERFILE" | head -1 | awk '{print $2}' || true)
  if [[ -n "$REQ_PATH" && ! -f "$REQ_PATH" ]]; then
    check_warn "requirements.txt referenced as '$REQ_PATH' not found in CWD — make sure build context is repo root"
  fi
elif grep -qE "pip install[[:space:]]+[a-zA-Z]" "$DOCKERFILE"; then
  check_warn "pip install without -r — unpinned dependencies"
fi

# ────────────────────────────────────────────────────────────────────────────
# 9. COPY hygiene
# ────────────────────────────────────────────────────────────────────────────
printf "\n\033[1m--- COPY hygiene ---\033[0m\n"
if grep -qE "^COPY[[:space:]]+\.[[:space:]]+\.[[:space:]]*$" "$DOCKERFILE"; then
  check_fail "COPY . . — copies tests, .git/, docs into image (bloat + leak risk)"
fi

# Check that COPY sources that contain non-root user files use --chown
if grep -qE "^COPY[[:space:]]+[^[]" "$DOCKERFILE" | grep -v "COPY --from" | grep -v "chown" >/dev/null 2>&1; then
  if grep -qE "^COPY[[:space:]]+[^[]" "$DOCKERFILE" >/dev/null 2>&1; then
    # At least one COPY without --chown — make sure USER is set after COPY so
    # chown is implicit
    if grep -qE "^COPY[[:space:]]+[a-zA-Z]" "$DOCKERFILE" | grep -v -- "--chown" | grep -v "COPY --from" >/dev/null 2>&1; then
      check_warn "COPY without --chown — files will be owned by root, USER directive applies only to runtime"
    fi
  fi
fi

# ────────────────────────────────────────────────────────────────────────────
# 10. OCI labels
# ────────────────────────────────────────────────────────────────────────────
printf "\n\033[1m--- OCI metadata ---\033[0m\n"
if grep -qE "LABEL org\.opencontainers\.image\.title" "$DOCKERFILE"; then
  check_pass "org.opencontainers.image.title set"
else
  check_warn "no org.opencontainers.image.title — image is unnamed in registries"
fi
if grep -qE "LABEL org\.opencontainers\.image\.source" "$DOCKERFILE"; then
  check_pass "org.opencontainers.image.source set"
else
  check_warn "no org.opencontainers.image.source — no provenance trail"
fi

# ────────────────────────────────────────────────────────────────────────────
# 11. Compose (optional)
# ────────────────────────────────────────────────────────────────────────────
if [[ -n "$COMPOSE_FLAG" && -n "$COMPOSE" ]]; then
  printf "\n\033[1m--- docker-compose.yml: %s ---\033[0m\n" "$COMPOSE"
  if [[ ! -f "$COMPOSE" ]]; then
    check_fail "compose file not found: $COMPOSE"
  else
    if command -v docker >/dev/null 2>&1; then
      if docker compose -f "$COMPOSE" config -q 2>/dev/null; then
        check_pass "compose syntax OK"
      else
        check_fail "compose syntax error — run 'docker compose -f $COMPOSE config' for details"
      fi
    else
      check_warn "docker not installed — skipping compose syntax check"
    fi

    # Compose healthcheck must mirror Dockerfile healthcheck
    COMPOSE_HC=$(grep -A5 "healthcheck:" "$COMPOSE" 2>/dev/null | grep -E "test:" | head -1 || true)
    if [[ -n "$COMPOSE_HC" ]]; then
      check_pass "compose has healthcheck block"
    else
      check_warn "compose has no healthcheck block — docker ps will always show Up"
    fi

    # user: directive
    if grep -qE "user:.*1001" "$COMPOSE"; then
      check_pass "compose uses uid 1001 (matches Dockerfile)"
    fi
  fi
fi

# ────────────────────────────────────────────────────────────────────────────
# 12. hadolint (optional)
# ────────────────────────────────────────────────────────────────────────────
if command -v hadolint >/dev/null 2>&1; then
  printf "\n\033[1m--- hadolint ---\033[0m\n"
  if hadolint "$DOCKERFILE" 2>&1 | tee /tmp/hadolint-out.txt | grep -q "error"; then
    check_fail "hadolint reported errors (see /tmp/hadolint-out.txt)"
  else
    if [[ -s /tmp/hadolint-out.txt ]]; then
      check_warn "hadolint warnings (acceptable): $(wc -l </tmp/hadolint-out.txt) lines"
    else
      check_pass "hadolint clean"
    fi
  fi
fi

# ────────────────────────────────────────────────────────────────────────────
# Summary
# ────────────────────────────────────────────────────────────────────────────
printf "\n\033[1m=== Summary ===\033[0m\n"
if [[ $fail -eq 0 ]]; then
  if [[ $warn -eq 0 ]]; then
    green "🎉 Dockerfile passes Phase-2 standard (no warnings)"
    exit 0
  else
    amber "✅ Dockerfile passes Phase-2 standard with $warn warning(s)"
    exit 0
  fi
else
  red "💥 $fail critical error(s), $warn warning(s) — fix errors before merging"
  exit 1
fi

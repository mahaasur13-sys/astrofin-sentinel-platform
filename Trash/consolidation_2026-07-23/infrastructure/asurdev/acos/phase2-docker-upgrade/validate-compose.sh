#!/usr/bin/env bash
# validate-compose.sh — статическая валидация docker-compose.yml на соответствие
#                       Phase-2 стандарту (см. CHECKLIST.md).
#
# Запускается ЛОКАЛЬНО на felix@localhost. Использует `docker compose config`
# для синтаксической проверки (требует запущенного Docker daemon только если
# есть переменные окружения — для чистого `docker compose config -q` daemon
# НЕ нужен, это просто YAML parse + interpolation).
#
# Использование:
#   ./validate-compose.sh <path/to/docker-compose.yml>
#   ./validate-compose.sh /home/workspace/AsurDev/docker-compose.yml
#
# Коды возврата:
#   0 — compose проходит Phase-2 standard
#   1 — есть ошибки, блокирующие Phase-2
#   2 — есть некритичные предупреждения, но блокеров нет

set -euo pipefail

COMPOSE="${1:?usage: $0 <path/to/docker-compose.yml>}"

# ── цвета ─────────────────────────────────────────────────────────────────────
if [[ -t 1 ]]; then
  RED=$'\033[31m'; GRN=$'\033[32m'; YLW=$'\033[33m'; CYA=$'\033[36m'; DIM=$'\033[2m'; OFF=$'\033[0m'
else
  RED=''; GRN=''; YLW=''; CYA=''; DIM=''; OFF=''
fi

fail_count=0
warn_count=0

banner() { printf "\n${CYA}━━━ %s ━━━${OFF}\n" "$*"; }
pass()   { printf "${GRN}✅ %s${OFF}\n" "$*"; }
fail()   { printf "${RED}❌ %s${OFF}\n" "$*"; fail_count=$((fail_count + 1)); }
warn()   { printf "${YLW}⚠️  %s${OFF}\n" "$*"; warn_count=$((warn_count + 1)); }

if [[ ! -f "$COMPOSE" ]]; then
  fail "compose file not found: $COMPOSE"
  exit 1
fi

banner "Phase-2 compose validation: $COMPOSE"

# ── 1. YAML syntax (docker compose config) ─────────────────────────────────────
# `docker compose config -q` exits 0 on success, prints errors to stderr otherwise.
# Does NOT require running services, just YAML parse + env interpolation.
if command -v docker >/dev/null 2>&1; then
  if docker compose -f "$COMPOSE" config -q 2>/dev/null; then
    pass "compose YAML syntax OK"
  else
    fail "compose YAML syntax error — run \`docker compose -f $COMPOSE config\` to inspect"
    exit 1
  fi
else
  warn "docker CLI not found — skipping YAML syntax check (install Docker or run via CI)"
fi

# ── 2. Schema version is v3.x (modern, swarm + compose-spec compatible) ────────
if grep -qE '^version:[[:space:]]*["\x27]?3' "$COMPOSE"; then
  pass "compose schema version 3.x"
elif grep -qE '^version:[[:space:]]*["\x27]?[12]' "$COMPOSE"; then
  fail "compose schema version 1.x/2.x — upgrade to 3.9+ (or omit version field for Compose Spec)"
else
  pass "no version field (uses Compose Spec — modern default)"
fi

# ── 3. Healthcheck present on every long-running service ───────────────────────
# We expect at least one service with a `healthcheck:` block.
if grep -qE '^[[:space:]]+healthcheck:' "$COMPOSE"; then
  pass "healthcheck block present"
  # Probe command should NOT be a trivial `["CMD", "true"]` or one-liner import
  if grep -qE 'healthcheck:.*\n[[:space:]]+test:[[:space:]]*\["CMD",[[:space:]]*"true"\]' "$COMPOSE"; then
    fail "healthcheck test is \`CMD true\` — это не проверка здоровья"
  fi
else
  fail "no \`healthcheck:\` block — every long-running service must define one"
fi

# ── 4. healthcheck.interval — reasonable value ─────────────────────────────────
interval=$(grep -A5 '^[[:space:]]+healthcheck:' "$COMPOSE" | grep -oE 'interval:[[:space:]]+[0-9]+[smh]' | head -1 || true)
if [[ -n "$interval" ]]; then
  pass "healthcheck interval set: $interval"
else
  warn "no explicit healthcheck.interval — Docker default is 30s"
fi

# ── 5. restart policy ──────────────────────────────────────────────────────────
# Long-running services in Phase-2 use `unless-stopped` or `always` (not `no`).
if grep -qE 'restart:[[:space:]]*(no|false)' "$COMPOSE"; then
  warn "some service uses \`restart: no\` — Phase-2 standard is \`unless-stopped\` for self-healing"
else
  pass "no service uses \`restart: no\` (good — self-healing enabled by default)"
fi

# ── 6. no `privileged: true` unless explicitly justified ───────────────────────
if grep -qE 'privileged:[[:space:]]*true' "$COMPOSE"; then
  fail "service uses \`privileged: true\` — Phase-2 standard requires dropping privileges; document justification in PR if absolutely needed"
fi

# ── 7. read_only: true where the service doesn't need filesystem write ──────────
if grep -qE 'read_only:[[:space:]]*true' "$COMPOSE"; then
  pass "read_only filesystem enabled on at least one service"
else
  warn "no \`read_only: true\` — consider it for stateless services (acos, cluster/node)"
fi

# ── 8. resource limits (memory / cpus) ─────────────────────────────────────────
if grep -qE 'limits:[[:space:]]*$' "$COMPOSE" -A3 | grep -qE '(memory|cpus):'; then
  pass "deploy.resources.limits defined"
else
  warn "no resource limits — production deployments should cap memory/cpus"
fi

# ── 9. log driver + rotation ───────────────────────────────────────────────────
if grep -qE 'logging:[[:space:]]*$' "$COMPOSE" -A4 | grep -qE 'max-size'; then
  pass "log rotation configured (max-size)"
else
  warn "no log rotation — production hosts fill /var/lib/docker/containers with logs"
fi

# ── 10. .env / config consistency ──────────────────────────────────────────────
# Phase-2 services use environment variables for config (no mounted config files
# beyond secrets). The compose file should reference env vars consistently.
env_vars=$(grep -oE '\$\{[A-Z_][A-Z0-9_]*(:-[^}]*)?\}' "$COMPOSE" | sort -u || true)
if [[ -n "$env_vars" ]]; then
  pass "compose uses \${VAR} interpolation: $(echo "$env_vars" | wc -l) unique var(s)"
else
  warn "no \${VAR} interpolation — compose is fully hardcoded (consider .env file for secrets)"
fi

# ── 11. network definition ─────────────────────────────────────────────────────
if grep -qE '^networks:[[:space:]]*$' "$COMPOSE"; then
  pass "explicit networks block (not relying on default)"
else
  warn "no explicit networks block — using \`default\` (fine for single-service stacks, limiting for multi-service)"
fi

# ── summary ────────────────────────────────────────────────────────────────────
banner "Summary"
if [[ $fail_count -gt 0 ]]; then
  printf "${RED}💥 %d error(s)${OFF}, ${YLW}%d warning(s)${OFF}\n" "$fail_count" "$warn_count"
  exit 1
elif [[ $warn_count -gt 0 ]]; then
  printf "${GRN}✅ compose passes Phase-2 standard with %d warning(s)${OFF}\n" "$warn_count"
  exit 2
else
  printf "${GRN}🎉 compose fully passes Phase-2 standard${OFF}\n"
  exit 0
fi
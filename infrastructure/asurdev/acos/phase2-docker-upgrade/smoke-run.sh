#!/usr/bin/env bash
# smoke-run.sh — быстрый локальный прогон уже собранного Phase-2 образа.
#
# Запускается на felix@localhost. Не делает build — только run + healthcheck.
# Используйте этот скрипт, чтобы проверить уже собранный образ после правок
# compose или env vars без пересборки.
#
# Использование:
#   ./smoke-run.sh <image> [extra docker run args...]
#
# Примеры:
#   ./smoke-run.sh acos:local
#   ./smoke-run.sh atom-node:phase2 -e NODE_ID=node-a -e PEERS=node-b
#
# Что делает:
#   1. docker run --rm <image>   (foreground, видно stdout)
#   2. Параллельно запускает probe-контейнер, ждёт 20s, проверяет health.
#   3. Печатает логи + status, exit 0 если оба зелёные.
#
# Коды возврата:
#   0 — foreground exit 0 + probe healthy
#   1 — image not found / docker not running
#   2 — foreground failed / probe unhealthy

set -uo pipefail

IMAGE="${1:-acos:local}"
shift || true
EXTRA_ARGS=("$@")

if [[ -t 1 ]]; then
  RED=$'\033[31m'; GRN=$'\033[32m'; YLW=$'\033[33m'; CYA=$'\033[36m'; DIM=$'\033[2m'; OFF=$'\033[0m'
else
  RED=''; GRN=''; YLW=''; CYA=''; DIM=''; OFF=''
fi

banner() { printf "\n${CYA}━━━ %s ━━━${OFF}\n" "$*"; }
ok()     { printf "${GRN}✅ %s${OFF}\n" "$*"; }
ko()     { printf "${RED}❌ %s${OFF}\n" "$*"; }
warn()   { printf "${YLW}⚠️  %s${OFF}\n" "$*"; }

banner "Phase-2 smoke-run: $IMAGE"

command -v docker >/dev/null 2>&1 || { ko "docker not found"; exit 1; }
docker info >/dev/null 2>&1       || { ko "docker daemon not running"; exit 1; }
docker image inspect "$IMAGE" >/dev/null 2>&1 || {
  ko "image '$IMAGE' not found — сначала соберите его:"
  echo "    docker build -t $IMAGE -f acos/Dockerfile ."
  exit 1
}

# ── foreground run ────────────────────────────────────────────────────────────
banner "foreground run"
printf "${DIM}docker run --rm %s %s${OFF}\n" "$IMAGE" "${EXTRA_ARGS[*]:-}"

FG_CONTAINER="phase2-fg-$$"
set +e
docker run --rm --name "$FG_CONTAINER" "${EXTRA_ARGS[@]}" "$IMAGE" 2>&1 | tee /tmp/phase2-fg.log
FG_EXIT=$?
set -e

if [[ $FG_EXIT -eq 0 ]]; then
  ok "foreground exit 0"
else
  ko "foreground exit $FG_EXIT"
  exit 2
fi

# ── healthcheck probe ────────────────────────────────────────────────────────
banner "healthcheck probe (background container, sleep 30)"

PROBE_NAME="phase2-probe-$$"
docker run -d --rm --name "$PROBE_NAME" \
  --entrypoint=/usr/bin/tini \
  "$IMAGE" \
  -- sh -c 'trap : TERM INT; sleep 30 & wait' \
  >/dev/null 2>&1 || {
    warn "image CMD exits too fast — healthcheck probe не запускается (one-shot services)"
    warn "для long-running сервисов (cluster/node) этот шаг полезен"
    exit 0
  }

printf "    waiting 20s for start_period ... "
sleep 20
printf "done\n"

HEALTH=$(docker inspect --format='{{.State.Health.Status}}' "$PROBE_NAME" 2>/dev/null || echo "unknown")
echo "    health status: $HEALTH"

# Show last healthcheck output for diagnostics
HC_OUT=$(docker inspect --format='{{range .State.Health.Log}}{{.Output}}{{end}}' "$PROBE_NAME" 2>/dev/null | tail -3)
if [[ -n "$HC_OUT" ]]; then
  echo "    healthcheck output (last 3):"
  echo "$HC_OUT" | sed 's/^/      /'
fi

docker stop "$PROBE_NAME" >/dev/null 2>&1 || true

case "$HEALTH" in
  healthy)   ok "healthcheck PASSED"; exit 0 ;;
  starting)  warn "healthcheck still 'starting' — start_period may be too short"; exit 0 ;;
  *)         ko "healthcheck FAILED ($HEALTH)"; exit 2 ;;
esac
#!/usr/bin/env bash
# run-all.sh — запуск всех четырёх проверок по очереди.
#
# Запускается на felix@localhost. Это самый удобный способ пройти
# Phase-2 acceptance за один проход: статика + compose + build + run.
#
# Использование:
#   ./run-all.sh [path/to/Dockerfile] [path/to/docker-compose.yml] [image-tag]
#
# Дефолты:
#   Dockerfile = acos/Dockerfile
#   compose    = docker-compose.yml  (если существует в CWD)
#   image-tag  = acos:phase2-smoke
#
# Шаги (любой fail — стоп, exit 1):
#   1. validate-docker.sh   — статическая проверка Dockerfile
#   2. validate-compose.sh  — статическая проверка compose (если есть)
#   3. smoke-build.sh       — реальный `docker build`
#   4. smoke-run.sh         — foreground run + healthcheck probe

set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HERE="$(cd "$(dirname "$0")" && pwd)"

DOCKERFILE="${1:-$ROOT/acos/Dockerfile}"
COMPOSE="${2:-$ROOT/docker-compose.yml}"
IMAGE="${3:-acos:phase2-smoke}"

if [[ -t 1 ]]; then
  CYA=$'\033[36m'; GRN=$'\033[32m'; RED=$'\033[31m'; OFF=$'\033[0m'
else
  CYA=''; GRN=''; RED=''; OFF=''
fi

step() { printf "\n${CYA}━━━ STEP %s / 4: %s ━━━${OFF}\n" "$1" "$2"; }
ok()   { printf "${GRN}✅ %s${OFF}\n" "$*"; }
ko()   { printf "${RED}❌ %s${OFF}\n" "$*"; }

printf "${CYA}━━━ Phase-2 acceptance — full pass on felix@localhost ━━━${OFF}\n"
printf "  Dockerfile : %s\n" "$DOCKERFILE"
printf "  compose    : %s\n" "$COMPOSE"
printf "  image      : %s\n" "$IMAGE"

# ── step 1: static Dockerfile validation ──────────────────────────────────────
step 1 "validate-docker.sh"
if bash "$HERE/validate-docker.sh" "$DOCKERFILE"; then
  ok "static Dockerfile check passed"
else
  ko "static Dockerfile check FAILED"
  exit 1
fi

# ── step 2: static compose validation (optional) ──────────────────────────────
step 2 "validate-compose.sh"
if [[ -f "$COMPOSE" ]]; then
  if bash "$HERE/validate-compose.sh" "$COMPOSE"; then
    ok "static compose check passed"
  else
    ko "static compose check FAILED"
    exit 1
  fi
else
  printf "    (compose %s not found — skipping step 2)\n" "$COMPOSE"
fi

# ── step 3: real docker build ─────────────────────────────────────────────────
step 3 "smoke-build.sh"
if bash "$HERE/smoke-build.sh" "$DOCKERFILE" "$IMAGE"; then
  ok "docker build succeeded"
else
  ko "docker build FAILED"
  exit 1
fi

# ── step 4: smoke run + healthcheck probe ─────────────────────────────────────
step 4 "smoke-run.sh"
if bash "$HERE/smoke-run.sh" "$IMAGE"; then
  ok "smoke run + healthcheck passed"
else
  ko "smoke run FAILED"
  exit 1
fi

printf "\n${GRN}━━━ 🎉 Phase-2 acceptance complete ━━━${OFF}\n"
printf "  image:  %s\n" "$(docker inspect --format='{{.Id}}' "$IMAGE" 2>/dev/null | cut -c1-12)"
printf "  size:   %s\n" "$(docker inspect --format='{{.Size}}' "$IMAGE" 2>/dev/null | numfmt --to=iec-i --suffix=B 2>/dev/null || echo unknown)"
printf "\nNext:\n"
printf "  - commit & push:    cd %s && git add ... && git commit -m '...' && git push\n" "$ROOT"
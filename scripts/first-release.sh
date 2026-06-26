#!/usr/bin/env bash
# first-release.sh — финальный релиз v1.0.0-rc1.
#
# Использование:
#   ./scripts/first-release.sh                       # просто тег + push + статус CI
#   WAIT=1 ./scripts/first-release.sh                # ждать завершения deploy-staging + smoke-test
#   STAGING_HEALTHCHECK_URL=https://… ./scripts/first-release.sh
#
# Зависимости: git, gh (аутентифицирован), опционально: kubectl, curl, jq.

set -euo pipefail

REPO="mahaasur13-sys/astrofin-sentinel-platform"
TAG="${TAG:-v1.0.0-rc1}"
REMOTE="origin"

WAIT="${WAIT:-0}"

need() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "❌ Не найдена утилита: $1" >&2
    echo "   Установите её и повторите." >&2
    exit 1
  }
}

for bin in git gh; do need "$bin"; done

if ! gh auth status >/dev/null 2>&1; then
  echo "❌ gh не аутентифицирован. Выполните: gh auth login" >&2
  exit 1
fi

# ── 1. Проверка рабочей копии ──────────────────────────────────────────────
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "❌ Не внутри git-репозитория. Перейдите в корень проекта." >&2
  exit 1
fi

current_branch="$(git rev-parse --abbrev-ref HEAD)"
echo "Текущая ветка: ${current_branch}"

if [[ "$current_branch" != "master" && -z "${ALLOW_NON_MASTER:-}" ]]; then
  echo "⚠️  Вы не на master. Тег '${TAG}' всё равно будет создан."
  echo "   Чтобы подавить эту проверку, установите ALLOW_NON_MASTER=1."
fi

# Чистота рабочей копии
if ! git diff --quiet HEAD 2>/dev/null; then
  echo "❌ Есть незакоммиченные изменения. Закоммитьте или отложите их перед релизом." >&2
  git status --short >&2
  exit 1
fi

# ── 2. Тег ─────────────────────────────────────────────────────────────────
if git ls-remote --tags "$REMOTE" "refs/tags/${TAG}" | grep -q "${TAG}"; then
  echo "✓ Тег ${TAG} уже есть в ${REMOTE}"
else
  git tag -a "${TAG}" -m "${TAG}: первый production-кандидат AstroFin Sentinel Platform"
  echo "✓ Создан локальный тег ${TAG}"
  git push "${REMOTE}" "${TAG}"
  echo "✓ Тег ${TAG} запушен"
fi

# Синхронизируем теги с remote, чтобы ${TAG}^{commit} отрезолвился локально
git fetch --tags "${REMOTE}" 2>/dev/null || true

# ── 3. Workflow run ────────────────────────────────────────────────────────
echo
echo "Жду появления workflow run для тега ${TAG}…"

run_id=""
TAG_SHA="$(git rev-parse "${TAG}^{commit}" 2>/dev/null || true)"
for attempt in {1..30}; do
  run_id="$(gh api "repos/${REPO}/actions/runs?event=push&per_page=50" \
            --jq ".workflow_runs[] | select((.head_sha == \"${TAG_SHA}\") and (.name == \"CD \\u2014 Build, Sign, Deploy\") and (.path == \".github/workflows/deploy.yml\")) | .id" \
            2>/dev/null | head -n1 || true)"
  if [[ -n "$run_id" ]]; then break; fi
  sleep 2
done

if [[ -z "$run_id" ]]; then
  echo "⚠️  workflow run пока не создан. Проверьте:"
  echo "   https://github.com/${REPO}/actions"
  exit 0
fi

run_url="https://github.com/${REPO}/actions/runs/${run_id}"
echo "Workflow run: ${run_url}"

# ── 4. Опциональное ожидание ───────────────────────────────────────────────
if [[ "$WAIT" == "1" ]]; then
  echo
  echo "Ожидаю завершения deploy-staging…"

  for attempt in {1..120}; do
    status="$(gh api "repos/${REPO}/actions/runs/${run_id}" --jq '.status' 2>/dev/null || echo "")"
    conclusion="$(gh api "repos/${REPO}/actions/runs/${run_id}" --jq '.conclusion' 2>/dev/null || echo "")"

    case "$status" in
      completed)
        echo "Статус run: ${conclusion}"
        break
        ;;
      in_progress|queued|waiting|pending)
        printf "  %s — %s …\n" "$attempt" "$status"
        sleep 5
        ;;
      *)
        printf "  %s — неизвестный статус '%s'\n" "$attempt" "$status"
        sleep 5
        ;;
    esac
  done

  if [[ "${conclusion:-}" != "success" ]]; then
    echo "❌ Workflow завершился со статусом '${conclusion:-unknown}'." >&2
    echo "   Подробности: ${run_url}" >&2
    exit 1
  fi

  # Smoke-test
  health_url="${STAGING_HEALTHCHECK_URL:-}"
  if [[ -n "$health_url" ]]; then
    echo
    echo "Smoke-test: $health_url"
    if curl -fsS --max-time 30 "$health_url" >/dev/null; then
      echo "✅ staging отвечает 200 OK"
    else
      echo "❌ staging не отвечает, проверьте ${run_url}" >&2
      exit 1
    fi
  fi
fi

echo
echo "🎉 Готово. Тег ${TAG} запушен."
echo "   Run: ${run_url}"
echo "   Следующий шаг — дождаться review/deploy-prod в GitHub UI или запустить новый тег."

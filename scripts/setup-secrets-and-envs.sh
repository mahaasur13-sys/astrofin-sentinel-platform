#!/usr/bin/env bash
# setup-secrets-and-envs.sh — финальная настройка GitHub Environments и Secrets
# для проекта astrofin-sentinel-platform.
#
# Использование:
#   ./scripts/setup-secrets-and-envs.sh                 # интерактивно
#   ./scripts/setup-secrets-and-envs.sh --non-interactive   # печатает команды и .env.secrets
#
# Скрипт безопасен для повторного запуска (идемпотентен).

set -euo pipefail

REPO="mahaasur13-sys/astrofin-sentinel-platform"
ENV_STAGING="staging"
ENV_PROD="production"

# Секреты по окружениям: имя секрета|окружение|описание
SECRETS=(
  "GHCR_TOKEN|repo|Пат для GHCR (push/pull образов). Нужен scope: read:packages, write:packages (owner — repo admin)."
  "KUBE_CONFIG_STAGING|staging|Kubeconfig staging-кластера в base64."
  "KUBE_CONFIG_PROD|production|Kubeconfig production-кластера в base64."
  "STAGING_HEALTHCHECK_URL|staging|URL для smoke-test (например https://staging.astrofin.example/healthz)."
  "SLACK_WEBHOOK_URL|production|Incoming webhook в Slack для алертов SRE (опционально)."
)

NON_INTERACTIVE=0
if [[ "${1:-}" == "--non-interactive" ]]; then
  NON_INTERACTIVE=1
fi

# ── Предусловия ──────────────────────────────────────────────────────────────
need() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "❌ Не найдена утилита: $1" >&2
    echo "   Установите её перед запуском (см. docs/FINAL_STEPS.md)." >&2
    exit 1
  }
}

need gh
need curl

if ! gh auth status >/dev/null 2>&1; then
  echo "❌ gh не аутентифицирован. Выполните: gh auth login" >&2
  exit 1
fi

echo "✅ gh готов. Репозиторий: $REPO"
echo

# ── Создание окружений ───────────────────────────────────────────────────────
create_env() {
  local env_name="$1"

  if gh api -H "Accept: application/vnd.github+json" \
       "repos/${REPO}/environments/${env_name}" \
       --silent --fail >/dev/null 2>&1; then
    echo "   • окружение '${env_name}' уже существует"
    return 0
  fi

  echo "   • создаю окружение '${env_name}'…"
  if gh api -X PUT \
       -H "Accept: application/vnd.github+json" \
       "repos/${REPO}/environments/${env_name}" \
       --input - <<< '{"wait_timer":0,"prevent_self_review":false}' \
       --silent --fail >/dev/null 2>&1; then
    echo "   ✅ окружение '${env_name}' создано"
  else
    # fallback для токенов без прав admin:environment — печатаем curl-команду
    echo "   ⚠️ не удалось через gh, вывожу curl-команду для ручного выполнения:"
    cat <<EOF
       curl -X PUT \\
         -H "Authorization: token \$(gh auth token)" \\
         -H "Accept: application/vnd.github+json" \\
         https://api.github.com/repos/${REPO}/environments/${env_name} \\
         -d '{"wait_timer":0,"prevent_self_review":false}'
EOF
  fi
}

echo "=== 1/3 Окружения GitHub ==="
create_env "$ENV_STAGING"
create_env "$ENV_PROD"
echo

# Добавим protection rules для production (reviewers = владелец репо)
owner="$(gh repo view "$REPO" --json owner --jq '.owner.login')"
echo "   • включаю protection rules для '${ENV_PROD}' (1 required reviewer: ${owner})…"
if gh api -X POST \
     -H "Accept: application/vnd.github+json" \
     "repos/${REPO}/environments/${ENV_PROD}/protection-rules" \
     --silent --fail \
     >/dev/null 2>&1; then
  echo "   ✅ protection rules отправлены (проверьте в GitHub UI)"
fi
echo

# ── Секреты ─────────────────────────────────────────────────────────────────
echo "=== 2/3 Секреты ==="

print_noninteractive() {
  echo "Режим --non-interactive: печатаю команды и сохраняю .env.secrets."
  local out=".env.secrets"
  {
    echo "# Заполните значения и выполните: set -a; source .env.secrets; set +a"
    echo "# затем запустите этот скрипт БЕЗ --non-interactive"
  } > "$out"
  for entry in "${SECRETS[@]}"; do
    IFS='|' read -r name env desc <<< "$entry"
    echo "${name}=" >> "$out"
    printf "   gh secret set %-26s --env %-10s  # %s\n" "$name" "$env" "$desc"
  done
  chmod 600 "$out"
  echo "🔒 права на '$out' установлены в 0600"
  echo
  echo "📄 Шаблон: $out"
}

if [[ "$NON_INTERACTIVE" -eq 1 ]]; then
  print_noninteractive
  exit 0
fi

read_secret_interactive() {
  local name="$1" env="$2" desc="$3"
  echo
  echo "   ┌─ Секрет: ${name}"
  echo "   │  окружение: ${env}"
  echo "   │  ${desc}"
  echo "   └─ Введите значение (Enter — оставить как есть):"
  if [[ -t 0 ]]; then
    read -r -s -p "   > " value
    echo
  else
    value=""
  fi
  if [[ -z "$value" ]]; then
    echo "      ⏭️  пропущено (можно задать позже вручную: gh secret set ${name} --env ${env})"
    return
  fi
  if gh secret set "$name" --env "$env" --body "$value" --repo "$REPO" >/dev/null; then
    echo "      ✅ установлен"
  else
    echo "      ❌ ошибка (проверьте права)"
  fi
}

for entry in "${SECRETS[@]}"; do
  IFS='|' read -r name env desc <<< "$entry"
  read_secret_interactive "$name" "$env" "$desc"
done

echo
echo "=== 3/3 Проверка ==="
gh secret list --repo "$REPO" --env "$ENV_STAGING" --json name,updatedAt 2>/dev/null | jq -r '.[] | "   [staging]    " + .name' || true
gh secret list --repo "$REPO" --env "$ENV_PROD"   --json name,updatedAt 2>/dev/null | jq -r '.[] | "   [production] " + .name' || true

echo
echo "🎉 Готово. Дальше: docs/FINAL_STEPS.md → шаг 2 (Grafana), шаг 3 (релиз)."

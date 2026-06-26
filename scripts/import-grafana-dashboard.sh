#!/usr/bin/env bash
# import-grafana-dashboard.sh — импорт дашборда Grafana из deploy/monitoring/grafana-dashboard.json
# через Grafana HTTP API.
#
# Использование:
#   GRAFANA_URL=https://grafana.example.com \
#   GRAFANA_API_TOKEN=glsa_xxx... \
#   ./scripts/import-grafana-dashboard.sh
#
# Альтернатива (ручной импорт):
#   Grafana UI → Dashboards → New → Import → Upload JSON → выбрать файл
#   deploy/monitoring/grafana-dashboard.json → Load → Import.

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
DASHBOARD_FILE="${REPO_ROOT}/deploy/monitoring/grafana-dashboard.json"
FOLDER_UID="astrofin"
FOLDER_TITLE="AstroFin Sentinel"

need() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "❌ Не найдена утилита: $1" >&2
    exit 1
  }
}

need curl
need jq

if [[ ! -f "$DASHBOARD_FILE" ]]; then
  echo "❌ Файл дашборда не найден: $DASHBOARD_FILE" >&2
  exit 1
fi

if [[ -z "${GRAFANA_URL:-}" || -z "${GRAFANA_API_TOKEN:-}" ]]; then
  cat <<'EOF'
⚠️  Не заданы GRAFANA_URL и/или GRAFANA_API_TOKEN.

Задайте переменные окружения и повторите:
  export GRAFANA_URL=https://grafana.example.com
  export GRAFANA_API_TOKEN=glsa_xxxxxxxxxxxxxxxxxxxx

Либо импортируйте дашборд вручную:
  1. Откройте Grafana → Dashboards → New → Import.
  2. Загрузите файл deploy/monitoring/grafana-dashboard.json.
  3. Выберите источник данных Prometheus (UID = prometheus).
  4. Нажмите Import.

EOF
  exit 0
fi

# нормализуем URL без trailing slash
GRAFANA_URL="${GRAFANA_URL%/}"

echo "→ Целевая Grafana: ${GRAFANA_URL}"
echo "→ Файл дашборда:  ${DASHBOARD_FILE}"

# 1. Убедимся, что folder существует (если нет — создадим).
folder_exists() {
  local code
  code="$(curl -s -o /dev/null -w '%{http_code}' \
              -H "Authorization: Bearer ${GRAFANA_API_TOKEN}" \
              "${GRAFANA_URL}/api/folders/${FOLDER_UID}")"
  [[ "$code" == "200" ]]
}

if folder_exists; then
  echo "  • папка '${FOLDER_TITLE}' уже существует"
else
  echo "  • создаю папку '${FOLDER_TITLE}'…"
  curl -fsS -X POST \
    -H "Authorization: Bearer ${GRAFANA_API_TOKEN}" \
    -H "Content-Type: application/json" \
    -d "$(jq -n --arg uid "$FOLDER_UID" --arg title "$FOLDER_TITLE" \
           '{uid:$uid, title:$title}')" \
    "${GRAFANA_URL}/api/folders" >/dev/null
  echo "  ✅ папка создана"
fi

# 2. Импорт дашборда.
echo "  • импортирую дашборд…"
payload="$(jq -n \
  --argjson dashboard "$(cat "$DASHBOARD_FILE")" \
  --arg folderUid "$FOLDER_UID" \
  '{dashboard:$dashboard, folderUid:$folderUid, overwrite:true, message:"Imported by setup script"}')"

resp="$(curl -fsS -X POST \
  -H "Authorization: Bearer ${GRAFANA_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "$payload" \
  "${GRAFANA_URL}/api/dashboards/import" || true)"

if [[ -z "$resp" ]]; then
  echo "  ❌ пустой ответ от Grafana" >&2
  exit 1
fi

uid="$(echo "$resp" | jq -r '.uid // .dashboardUid // empty')"
url="$(echo "$resp" | jq -r '.url // empty')"

if [[ -n "$uid" ]]; then
  echo "  ✅ дашборд импортирован"
  echo "     uid: $uid"
  [[ -n "$url" ]] && echo "     url: ${GRAFANA_URL}${url}"
else
  echo "  ⚠️ неожиданный ответ:"
  echo "$resp" | jq . || echo "$resp"
  exit 1
fi

# 3. Проверка.
status="$(curl -s -o /dev/null -w '%{http_code}' \
            -H "Authorization: Bearer ${GRAFANA_API_TOKEN}" \
            "${GRAFANA_URL}/api/dashboards/uid/${uid}")"
echo "  • GET /api/dashboards/uid/${uid} → ${status}"

if [[ "$status" != "200" ]]; then
  echo "  ❌ дашборд не найден после импорта" >&2
  exit 1
fi

echo
echo "🎉 Дашборд '${FOLDER_TITLE}' готов к использованию."

#!/usr/bin/env bash
# ============================================================================
#  AstroFin Sentinel — Project Board Auto-Setup
#  Версия: 1.0.0  |  Дата: 2026-07-03
#
#  Этот скрипт автоматизирует настройку GitHub Project V2 для
#  AstroFin Sentinel Platform после создания проекта в UI.
#
#  ------------------------------------------------------------------------
#  КАК ПОЛУЧИТЬ PROJECT_ID:
#  ------------------------------------------------------------------------
#  1. Создайте проект через UI:
#     https://github.com/mahaasur13-sys/astrofin-sentinel-platform/projects
#     → "New project" → Board (Kanban) → название "AstroFin Sentinel — v1.0.0
#     Production" → Create
#
#  2. Откройте созданный проект. URL будет вида:
#     https://github.com/users/mahaasur13-sys/projects/12
#     Число в конце — это PROJECT_ID (в примере: 12)
#
#  3. Также можно узнать PROJECT_ID через CLI (требуется scope: project):
#     gh project list --owner mahaasur13-sys --format json
#
#  ------------------------------------------------------------------------
#  ЗАПУСК:
#  ------------------------------------------------------------------------
#    ./auto_project_setup.sh 12              # использует project ID 12
#    ./auto_project_setup.sh 12 --dry-run    # только показать что будет
#    ./auto_project_setup.sh --help          # справка
#
#  Требования:
#    - gh CLI 2.40+ (gh --version)
#    - gh auth login с repo, project, read:org
#    - jq (sudo apt install jq)
#  ============================================================================

set -euo pipefail

# ----------------------------- CONFIG --------------------------------------
REPO="mahaasur13-sys/astrofin-sentinel-platform"
OWNER="mahaasur13-sys"
SCRIPT_NAME="$(basename "$0")"
DRY_RUN=false

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
GRAY='\033[0;90m'
BOLD='\033[1m'
RESET='\033[0m'

# ----------------------------- HELP ----------------------------------------
show_help() {
  cat <<EOF
${BOLD}AstroFin Sentinel — Project Board Auto-Setup${RESET}

${BOLD}ИСПОЛЬЗОВАНИЕ:${RESET}
  $SCRIPT_NAME <PROJECT_ID> [OPTIONS]

${BOLD}АРГУМЕНТЫ:${RESET}
  PROJECT_ID              ID проекта (число из URL проекта)

${BOLD}ОПЦИИ:${RESET}
  --dry-run               Показать план действий, ничего не менять
  --help                  Эта справка

${BOLD}ПРИМЕРЫ:${RESET}
  $SCRIPT_NAME 12
  $SCRIPT_NAME 12 --dry-run

${BOLD}ПОДРОБНЕЕ:${RESET}
  См. шапку скрипта (head -50 $SCRIPT_NAME) или docs/auto_project_setup.md

EOF
  exit 0
}

# ----------------------------- ARGUMENTS -----------------------------------
if [[ $# -eq 0 || "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  show_help
fi

PROJECT_ID="$1"
shift

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=true; shift ;;
    *) echo -e "${RED}✗ Неизвестная опция: $1${RESET}"; exit 1 ;;
  esac
done

# ----------------------------- UTILS ---------------------------------------
print_banner() {
  echo -e "${CYAN}${BOLD}"
  cat <<'BANNER'
  ╔══════════════════════════════════════════════════════════════════╗
  ║   🚀 AstroFin Sentinel — Project Board Auto-Setup               ║
  ║   v1.0.0  ·  2026-07-03  ·  github.com/mahaasur13-sys         ║
  ╚══════════════════════════════════════════════════════════════════╝
BANNER
  echo -e "${RESET}"
}

section() {
  echo ""
  echo -e "${MAGENTA}${BOLD}═══ $1 ═══${RESET}"
}

ok()    { echo -e "${GREEN}✓${RESET} $1"; }
info()  { echo -e "${BLUE}ℹ${RESET} $1"; }
warn()  { echo -e "${YELLOW}⚠${RESET} $1"; }
err()   { echo -e "${RED}✗${RESET} $1"; }
fatal() { err "$1"; exit 1; }

run() {
  if [[ "$DRY_RUN" == "true" ]]; then
    echo -e "${GRAY}[DRY-RUN]${RESET} $*"
  else
    eval "$@"
  fi
}

# ----------------------------- PRECHECKS -----------------------------------
print_banner

section "Prechecks"

# 1. gh CLI
if ! command -v gh >/dev/null 2>&1; then
  fatal "gh CLI не найден. Установите: https://cli.github.com/"
fi
GH_VERSION=$(gh --version | head -1 | awk '{print $3}')
ok "gh CLI: $GH_VERSION"

# 2. gh auth
if ! gh auth status >/dev/null 2>&1; then
  fatal "gh не залогинен. Выполните: gh auth login"
fi
GH_USER=$(gh api user --jq '.login')
ok "GitHub: $GH_USER"

# 3. project scope
if ! gh project list --owner "$OWNER" >/dev/null 2>&1; then
  warn "Нет project scope. Запустите:"
  echo -e "    ${YELLOW}gh auth refresh -s project,read:project${RESET}"
  fatal "Без этого скрипт не сможет работать с Project V2."
fi
ok "project scope: ok"

# 4. jq
if ! command -v jq >/dev/null 2>&1; then
  warn "jq не найден. Установите: apt install jq (или brew install jq)"
  warn "Часть функций будет недоступна."
fi

# 5. Project exists?
if ! gh project view "$PROJECT_ID" --owner "$OWNER" >/dev/null 2>&1; then
  fatal "Project #$PROJECT_ID не найден у $OWNER. Проверьте ID и owner."
fi
PROJECT_TITLE=$(gh project view "$PROJECT_ID" --owner "$OWNER" --format json | jq -r '.title')
ok "Project #$PROJECT_ID: $PROJECT_TITLE"

# 6. Repository access
if ! gh repo view "$REPO" >/dev/null 2>&1; then
  fatal "Нет доступа к $REPO"
fi
ok "Repo: $REPO"

# Dry-run notice
if [[ "$DRY_RUN" == "true" ]]; then
  echo ""
  warn "DRY-RUN: действия не выполняются, только показываются"
fi

# ----------------------------- 1. CUSTOM FIELDS ----------------------------
section "1. Custom Fields (8 шт.)"

create_field() {
  local name="$1"
  local data_type="$2"
  local options_json="$3"
  local field_id

  # Check if field already exists
  field_id=$(gh project field-list "$PROJECT_ID" --owner "$OWNER" --format json 2>/dev/null | \
    jq -r ".fields[] | select(.name==\"$name\") | .id" 2>/dev/null || echo "")

  if [[ -n "$field_id" ]]; then
    info "Field '$name' уже существует (id: $field_id)"
    return 0
  fi

  if [[ -n "$options_json" ]]; then
    run gh project field-create "$PROJECT_ID" --owner "$OWNER" \
      --name "$name" --data-type "$data_type" --options "$options_json"
  else
    run gh project field-create "$PROJECT_ID" --owner "$OWNER" \
      --name "$name" --data-type "$data_type"
  fi
  ok "Field создан: $name ($data_type)"
}

# 1.1 Phase (SINGLE_SELECT: Phase 0..5)
PHASE_OPTS=$(cat <<'JSON'
[
  {"name":"Phase 0 — Подготовка","color":"B60205"},
  {"name":"Phase 1 — API & Security","color":"D93F0B"},
  {"name":"Phase 2 — Database","color":"D93F0B"},
  {"name":"Phase 3 — Observability","color":"FBCA04"},
  {"name":"Phase 4 — Security & Docs","color":"0E8A16"},
  {"name":"Phase 5 — Deploy & GA","color":"006B75"}
]
JSON
)
create_field "Phase" "SINGLE_SELECT" "$PHASE_OPTS"

# 1.2 MoSCoW (SINGLE_SELECT: MUST/SHOULD/COULD/WON'T)
MOSCOW_OPTS=$(cat <<'JSON'
[
  {"name":"MUST","color":"B60205","description":"Блокер GA v1.0.0"},
  {"name":"SHOULD","color":"FBCA04","description":"Важно, но v1.0.1+"},
  {"name":"COULD","color":"0E8A16","description":"Nice-to-have"},
  {"name":"WON'T","color":"FFFFFF","description":"Отложено в v1.2+"}
]
JSON
)
create_field "MoSCoW" "SINGLE_SELECT" "$MOSCOW_OPTS"

# 1.3 Estimate (NUMBER: часы)
create_field "Estimate (h)" "NUMBER" ""

# 1.4 Owner (SINGLE_SELECT: роли)
OWNER_OPTS=$(cat <<'JSON'
[
  {"name":"Backend","color":"1D76DB"},
  {"name":"DevOps","color":"5319E7"},
  {"name":"Security","color":"B60205"},
  {"name":"Tech Writer","color":"0075CA"},
  {"name":"Tech Lead","color":"FBCA04"}
]
JSON
)
create_field "Owner" "SINGLE_SELECT" "$OWNER_OPTS"

# 1.5 Component (SINGLE_SELECT: где в коде)
COMPONENT_OPTS=$(cat <<'JSON'
[
  {"name":"agents/","color":"C5DEF5"},
  {"name":"core/","color":"C5DEF5"},
  {"name":"orchestration/","color":"C5DEF5"},
  {"name":"web/","color":"C5DEF5"},
  {"name":"db/","color":"C5DEF5"},
  {"name":"observability/","color":"C5DEF5"},
  {"name":"deploy/","color":"C5DEF5"},
  {"name":"tests/","color":"C5DEF5"},
  {"name":"docs/","color":"C5DEF5"},
  {"name":"tools/","color":"C5DEF5"},
  {"name":"infra","color":"D4C5F9"},
  {"name":"adr","color":"D4C5F9"}
]
JSON
)
create_field "Component" "SINGLE_SELECT" "$COMPONENT_OPTS"

# 1.6 Sprint (SINGLE_SELECT: Sprint 1..4)
SPRINT_OPTS=$(cat <<'JSON'
[
  {"name":"Sprint 1","color":"B60205"},
  {"name":"Sprint 2","color":"D93F0B"},
  {"name":"Sprint 3","color":"FBCA04"},
  {"name":"Sprint 4","color":"0E8A16"},
  {"name":"Backlog","color":"BFBFBF"}
]
JSON
)
create_field "Sprint" "SINGLE_SELECT" "$SPRINT_OPTS"

# 1.7 Blocked (SINGLE_SELECT: status)
BLOCKED_OPTS=$(cat <<'JSON'
[
  {"name":"No","color":"0E8A16"},
  {"name":"Yes — waiting","color":"FBCA04"},
  {"name":"Yes — critical","color":"B60205"}
]
JSON
)
create_field "Blocked" "SINGLE_SELECT" "$BLOCKED_OPTS"

# 1.8 Milestone (поле уже есть в Project V2 автоматически — пропускаем)
info "Field 'Milestone' уже есть в Project V2 (built-in)"

# ----------------------------- 2. VIEWS ------------------------------------
section "2. Views (Saved views)"

create_view() {
  local name="$1"
  local layout="$2"  # board / table
  info "View: $name ($layout) — создайте вручную через UI:"
  echo -e "    ${GRAY}https://github.com/orgs/$OWNER/projects/$PROJECT_ID/views${RESET}"
  echo -e "    ${GRAY}Layout: $layout${RESET}"
}

# 2.1 Board by Status
create_view "By Status (default)" "board"
# 2.2 Board by Owner
create_view "By Owner" "board"
# 2.3 Board by Sprint
create_view "By Sprint" "board"
# 2.4 Table: Burndown
create_view "Burndown Table" "table"
# 2.5 Roadmap
create_view "Roadmap (by Milestone)" "roadmap"

warn "Views создаются через UI (cli не поддерживает views creation). Ссылка выше."

# ----------------------------- 3. AUTOMATIONS ------------------------------
section "3. Automation Rules"

# 3.1 Auto-add to project when issue opened with sprint-* label
info "Создайте automation в UI:"
echo -e "  ${BOLD}Rule 1:${RESET} Issue opened with label 'sprint-1' → set Sprint='Sprint 1'"
echo -e "  ${BOLD}Rule 2:${RESET} Issue closed → move to Done column"
echo -e "  ${BOLD}Rule 3:${RESET} Pull request merged → set Status=Done"
echo -e "  ${BOLD}Rule 4:${RESET} Issue labeled 'blocker' → assign to Tech Lead + priority high"
echo ""
echo -e "  ${GRAY}Path: Project → ⚙ Settings → Workflows → Add workflow${RESET}"

# ----------------------------- 4. BULK-ADD ISSUES -------------------------
section "4. Bulk-add Sprint 1 issues в Project"

info "Получаю все issues из milestone 'Sprint 1 (v1.0.0-prep)'..."

# Get all open issues from Sprint 1 milestone
SPRINT_ISSUES=$(gh issue list \
  --repo "$REPO" \
  --milestone "Sprint 1 (v1.0.0-prep)" \
  --state all \
  --limit 100 \
  --json number,title 2>/dev/null)

TOTAL_ISSUES=$(echo "$SPRINT_ISSUES" | jq 'length')
ok "Найдено issues в milestone: $TOTAL_ISSUES"

if [[ "$TOTAL_ISSUES" -eq 0 ]]; then
  warn "Issues в milestone не найдены. Сначала создайте их."
else
  COUNT_ADDED=0
  COUNT_FAILED=0
  COUNT_SKIPPED=0

  while IFS= read -r issue_num; do
    [[ -z "$issue_num" ]] && continue

    ISSUE_TITLE=$(echo "$SPRINT_ISSUES" | jq -r ".[] | select(.number==$issue_num) | .title")

    # Check if already in project
    in_project=$(gh project item-list "$PROJECT_ID" --owner "$OWNER" --format json 2>/dev/null | \
      jq -r ".items[] | select(.content.number==$issue_num) | .id" 2>/dev/null || echo "")

    if [[ -n "$in_project" ]]; then
      echo -e "  ${GRAY}→${RESET} #$issue_num: уже в проекте, skip"
      COUNT_SKIPPED=$((COUNT_SKIPPED+1))
      continue
    fi

    # Add to project
    if [[ "$DRY_RUN" == "true" ]]; then
      echo -e "  ${GRAY}[DRY-RUN]${RESET} → Добавлю #$issue_num: $ISSUE_TITLE"
      COUNT_ADDED=$((COUNT_ADDED+1))
    else
      if gh project item-add "$PROJECT_ID" --owner "$OWNER" --url "https://github.com/$REPO/issues/$issue_num" >/dev/null 2>&1; then
        ok "#$issue_num: добавлен"
        COUNT_ADDED=$((COUNT_ADDED+1))
      else
        err "#$issue_num: FAILED"
        COUNT_FAILED=$((COUNT_FAILED+1))
      fi
    fi
  done < <(echo "$SPRINT_ISSUES" | jq -r '.[].number')

  echo ""
  info "Итого: добавлено=$COUNT_ADDED, skipped=$COUNT_SKIPPED, failed=$COUNT_FAILED"
fi

# ----------------------------- FINAL SUMMARY -------------------------------
section "✨ Готово — Сводка"

cat <<EOF
${BOLD}Project:#${RESET}    $PROJECT_ID ($PROJECT_TITLE)
${BOLD}URL:${RESET}       https://github.com/orgs/$OWNER/projects/$PROJECT_ID
${BOLD}Repo:${RESET}      $REPO
${BOLD}Custom Fields:${RESET} 8 (Phase, MoSCoW, Estimate, Owner, Component, Sprint, Blocked, +built-in Milestone)
${BOLD}Views:${RESET}        5 (Status, Owner, Sprint, Burndown, Roadmap) — создайте вручную в UI
${BOLD}Issues added:${RESET} $COUNT_ADDED / $TOTAL_ISSUES
${BOLD}Mode:${RESET}         $([[ "$DRY_RUN" == "true" ]] && echo "DRY-RUN" || echo "APPLIED")

${CYAN}${BOLD}Следующие шаги:${RESET}
  1. Откройте Project → Settings → Workflows → добавьте 4 automation
  2. Создайте 5 Saved Views (см. URLs в выводе выше)
  3. Распределите issues по колонкам (Backlog → To Do → In Progress → Review → Done)
  4. Запустите Sprint 1 в понедельник
  5. Закрепите Project в README репо

${GREEN}${BOLD}Happy shipping! 🚀${RESET}
EOF

#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

TODAY=$(date +%Y-%m-%d)
PROGRESS_FILE="$ROOT/progress.md"

# Если файл не существует, создаём с заголовком
if [ ! -f "$PROGRESS_FILE" ]; then
    echo "# Progress Log" > "$PROGRESS_FILE"
    echo "" >> "$PROGRESS_FILE"
fi

# Получаем коммиты за сегодня
COMMITS=$(git log --since="midnight" --pretty="  - %s" 2>/dev/null || echo "  (no commits today)")

# Краткая сводка healthcheck
HEALTH_LINE=""
if [ -f "$ROOT/tools/healthcheck.py" ]; then
    HEALTH_OUTPUT=$(python "$ROOT/tools/healthcheck.py" 2>/dev/null || echo '{"status":"error"}')
    HEALTH_LINE=$(echo "$HEALTH_OUTPUT" | python -c "import sys,json; d=json.load(sys.stdin); print(f'  - venv: {d[\"checks\"][\"venv\"][\"active\"]}, postgres: {d[\"checks\"][\"postgresql\"][\"available\"]}, ollama: {d[\"checks\"][\"ollama\"][\"available\"]}')" 2>/dev/null || echo "  - healthcheck: unavailable")
else
    HEALTH_LINE="  - healthcheck: script not found"
fi

# Добавляем запись
{
    echo ""
    echo "## $TODAY"
    echo ""
    echo "### Commits"
    echo "$COMMITS"
    echo ""
    echo "### Environment Health"
    echo "$HEALTH_LINE"
    echo ""
} >> "$PROGRESS_FILE"

echo "Progress updated for $TODAY"

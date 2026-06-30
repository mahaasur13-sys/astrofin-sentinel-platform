#!/bin/bash
set -euo pipefail
MAX_ITERATIONS=${1:-3}
BRANCH="ralph-loop-$(date +%Y%m%d-%H%M%S)"

echo "🚀 Запускаем Ralph Loop (Python Agent). Итераций: $MAX_ITERATIONS"
git checkout -b "$BRANCH"

for ((i=1; i<=MAX_ITERATIONS; i++)); do
  echo "🔄 === Итерация $i из $MAX_ITERATIONS ==="
  python3 scripts/ralph_agent.py

  if ! grep -q '\[ \]' docs/tickets.md; then
    echo "✅ Все задачи выполнены!"
    break
  fi
done

echo "🏁 Цикл завершён в ветке $BRANCH"

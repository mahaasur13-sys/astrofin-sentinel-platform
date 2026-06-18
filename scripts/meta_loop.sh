#!/bin/bash
set -euo pipefail

export VSELM_API_KEY="${VSELM_API_KEY:-REVOKED_KEY_REMOVED}"

MAX_ATTEMPTS=5
ITERATIONS_PER_LOOP=3
BENCHMARK_DIR="tests/ralph_benchmark"
ARCHIVE_DIR="archive/meta_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$ARCHIVE_DIR"

echo "🚀 Meta Loop стартует. Попыток: $MAX_ATTEMPTS"

git stash --include-untracked
INITIAL_COMMIT=$(git rev-parse HEAD)

for ((attempt=1; attempt<=MAX_ATTEMPTS; attempt++)); do
    echo "🔄 Попытка $attempt из $MAX_ATTEMPTS"

    ./scripts/ralph_loop.sh $ITERATIONS_PER_LOOP

    set +e
    pytest "$BENCHMARK_DIR" -v --tb=short > "$ARCHIVE_DIR/bench_${attempt}.log" 2>&1
    BENCH_EXIT_CODE=$?
    set -e

    if [ $BENCH_EXIT_CODE -eq 0 ]; then
        echo "✅ Бенчмарк пройден! Сохраняем изменения."
        git add -A
        git commit -m "Meta Loop: успешная попытка $attempt, бенчмарк пройден"
        git stash pop || true
        exit 0
    else
        echo "❌ Бенчмарк упал. Откатываем изменения и пробуем с другой температурой."
        git reset --hard "$INITIAL_COMMIT"
        if [ -f "scripts/ralph_agent.py" ]; then
            sed -i "s/temperature=[0-9.]\+/temperature=0.$((attempt % 5))/" scripts/ralph_agent.py
        fi
    fi
done

echo "🏁 Meta Loop завершён после $MAX_ATTEMPTS попыток. Бенчмарк не пройден."
git stash pop || true
exit 1

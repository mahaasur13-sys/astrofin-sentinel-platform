#!/bin/bash
# submit_wrapper.sh — отправляет задание на оптимальный узел через AI scheduler
# Использование: ./submit_wrapper.sh <job_type> <job_script>
#   job_type: gpu | cpu
#   job_script: путь к скрипту задания

set -euo pipefail

# Параметры
JOB_TYPE="${1:-cpu}"               # по умолчанию cpu
JOB_SCRIPT="${2:-}"                # скрипт задания (обязателен)
SCHEDULER_URL="${SCHEDULER_URL:-http://localhost:8080}"

# Проверка наличия скрипта
if [[ -z "$JOB_SCRIPT" ]]; then
    echo "[ERROR] Usage: $0 <gpu|cpu> <job_script>"
    exit 1
fi

if [[ ! -f "$JOB_SCRIPT" ]]; then
    echo "[ERROR] Job script not found: $JOB_SCRIPT"
    exit 1
fi

# Запрос к AI scheduler (получение рекомендации по partition)
RESPONSE=$(curl -s -X POST "${SCHEDULER_URL}/api/v1/tasks" \
    -H "Content-Type: application/json" \
    -d "{\"job_type\": \"$JOB_TYPE\", \"job_name\": \"$(basename "$JOB_SCRIPT")\"}")

# Извлечение partition из ответа (пример: {"partition": "gpu", "reason": "queue"})
PARTITION=$(echo "$RESPONSE" | jq -r '.partition // "cpu"')
REASON=$(echo "$RESPONSE" | jq -r '.reason // "no_reason"')

echo "[scheduler] Target: $JOB_TYPE, Partition: $PARTITION, Reason: $REASON"

# Если scheduler говорит поставить в очередь (не запускать сейчас)
if [[ "$REASON" == "queue" ]]; then
    echo "[scheduler] Job queued – $REASON"
    exit 0
fi

# Отправка задания в Slurm
case "$PARTITION" in
    gpu*)
        sbatch --partition=gpu "$JOB_SCRIPT"
        ;;
    cpu*)
        sbatch --partition=cpu "$JOB_SCRIPT"
        ;;
    *)
        sbatch "$JOB_SCRIPT"
        ;;
esac

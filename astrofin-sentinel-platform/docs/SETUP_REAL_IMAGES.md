## Quick Start

Run these commands on your Pop!_OS:

1. cd ~/astrofin-sentinel-platform
2. git pull origin master
3. git submodule update --init --recursive
4. docker compose down --remove-orphans
5. docker compose build --no-cache
6. docker compose up -d
7. sleep 30 && docker compose ps

## Что уже сделано на сервере

В этой копии репозитория (клон с GitHub):

- ✅ Клонирован astrofin-sentinel-platform
- ✅ Все 8 submodules инициализированы:
  - AsurDev (master @ 1e45085)
  - home-cluster-iac (master @ 61ac95c)
  - roma-execution-bridge (v1.0.0 @ ad49c84)
  - AstroFinSentinelV5 (main @ 13cfec7)
  - astrofin-sentinel-v5 (phase4-observability @ 8b4fb29)
  - atom-federation-os (v9.10-stable @ 41a74e2)
  - integrations/gitagent (ATOM-GITAGENT-002 @ 93cf8f2)
  - push (main @ 71d6e1d)
- ✅ Все 4 Dockerfile'а реальные (не заглушки):
  - web/Dockerfile (2020 байт, slim multi-stage)
  - AsurDev/ml_engine/Dockerfile (913 байт)
  - home-cluster-iac/feature_pipeline/Dockerfile (1801 байт)
  - roma-execution-bridge/gpu_worker/Dockerfile (2238 байт)
- ✅ Все 3 requirements файла на месте:
  - AsurDev/requirements-ml.txt
  - home-cluster-iac/requirements-features.txt
  - roma-execution-bridge/requirements-worker.txt
- ✅ docker-compose.yml ссылается на правильные context/dockerfile
- ✅ .env.example присутствует, реальный .env НЕ нужен (compose использует env_file: .env.example)


## Проверка здоровья (после запуска)

```bash
# Web Dashboard
curl -s -o /dev/null -w "Web: HTTP %{http_code}\n" http://localhost:8050

# ML Engine
curl -s -o /dev/null -w "ML:  HTTP %{http_code}\n" http://localhost:8081/health

# Feature Pipeline
curl -s -o /dev/null -w "FP:  HTTP %{http_code}\n" http://localhost:8090/healthy

# Postgres
docker exec astrofin-postgres pg_isready -U astrofin

# Redis
docker exec astrofin-redis redis-cli ping

# Prometheus
curl -s -o /dev/null -w "Prom: HTTP %{http_code}\n" http://localhost:9090/-/healthy
```

Ожидаемый результат:
- Web: HTTP 200
- ML:  HTTP 200
- FP:  HTTP 200
- Postgres: accepting connections
- Redis: PONG
- Prom: HTTP 200


## Troubleshooting

### Проблема: submodule не клонируется (auth fail)

```bash
# Проверьте SSH-ключ
ssh-add -l    # должен показать id_ed25519

# Если пусто:
eval $(ssh-agent -s)
ssh-add ~/.ssh/id_ed25519

# Проверьте доступ к GitHub
ssh -T git@github.com
# Ожидаемый ответ: "Hi mahaasur13-sys! You've successfully authenticated..."

# Если всё равно 403 — URL submodule'ей в .gitmodules мог быть HTTPS
# Переключите на SSH:
cd ~/astrofin-sentinel-platform
sed -i 's|https://github.com/mahaasur13-sys|git@github.com:mahaasur13-sys|g' .gitmodules
git submodule sync
git submodule update --init --recursive
```

### Проблема: docker compose build падает на AsurDev

```bash
# Проверьте, что requirements-ml.txt существует
ls AsurDev/requirements-ml.txt

# Если нет — submodule не инициализирован
git submodule update --init AsurDev
```

### Проблема: порт 8050 занят

```bash
# Найдите процесс
sudo ss -tlnp | grep 8050
# Или:
sudo lsof -i :8050

# Остановите его или измените порт в .env:
echo "WEB_PORT=8051" >> .env
```


## Замечание про gpu-worker

`gpu-worker` (roma-execution-bridge) требует NVIDIA Container Toolkit. На машинах без GPU он не запустится. Это нормально.

Чтобы пропустить его:
```bash
docker compose up -d postgres redis ml-engine feature-pipeline app prometheus
```


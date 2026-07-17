# Live Docker Run — AstroFin Sentinel Platform

Краткая инструкция по локальному/живому запуску 7-сервисной
контейнеризованной платформы. Предполагается уже выполненный `git clone`
репозитория `mahaasur13-sys/astrofin-sentinel-platform`.

---

## 1. Предварительные требования

| Компонент            | Минимальная версия | Примечание |
|----------------------|--------------------|------------|
| Docker Engine        | 24.0+              | с поддержкой Compose v2 |
| Docker Compose plugin| v2.20+             | `docker compose` (не `docker-compose` v1) |
| Git                  | 2.30+              | для `submodule update` |
| NVIDIA Container Toolkit | последний      | **только** для `gpu-worker` (CUDA); остальные сервисы работают без GPU |
| Свободное место      | ~5 ГБ              | образы `python:3.12-slim` + базовые слои |
| RAM                  | 4 ГБ+              | TimescaleDB + Redis + 3 Python-сервиса |

**Проверка окружения:**

```bash
docker --version         # Docker version 24.x or higher
docker compose version   # Docker Compose version v2.x
nvidia-smi               # опционально — только для gpu-worker
```

---

## 2. Подготовка: подтянуть сабмодули

Dockerfile'ы `ml-engine`, `feature-pipeline` и `gpu-worker` живут
**внутри сабмодулей** (`AsurDev`, `home-cluster-iac`, `roma-execution-bridge`).
Без `submodule update` сборка упадёт на шаге 4.

```bash
cd /path/to/astrofin-sentinel-platform
git submodule update --init --recursive
```

Для верификации, что все 4 ожидаемых Dockerfile на месте:

```bash
ls web/Dockerfile \
   AsurDev/ml_engine/Dockerfile \
   home-cluster-iac/feature_pipeline/Dockerfile \
   roma-execution-bridge/gpu_worker/Dockerfile
# → все 4 пути должны существовать
```

> CI workflow `.github/workflows/compose-check.yml` запускает ровно эту
> проверку и блокирует merge при отсутствии любого из этих путей.

---

## 3. Переменные окружения

Скопируйте шаблон и заполните секреты:

```bash
cp .env.example .env
# отредактируйте .env: ключи API, пароли БД и т.д.
```

Минимум, что нужно проверить в `.env`:

- `POSTGRES_PASSWORD` — пароль пользователя `astrofin` БД TimescaleDB
- `REDIS_PASSWORD`   — если Redis сконфигурирован с auth
- любые `*_API_KEY`    — внешние интеграции (CoinGecko, Polygon и т.д.)

`docker-compose.yml` ссылается на `.env` через `env_file: .env.example`
для сервиса `app` (web dashboard). Для остальных сервисов переменные
пробрасываются напрямую из compose-секции `environment`.

---

## 4. Сборка и запуск

```bash
# Сборка всех образов
docker compose build

# Запуск в фоне
docker compose up -d

# Подождите инициализацию (БД, healthchecks, прогрев)
sleep 30

# Список и статус контейнеров
docker compose ps
```

Ожидаемая картина после `up -d`:

```
NAME                       STATUS              PORTS
astrofin-web               Up (healthy)        0.0.0.0:8050->8050/tcp
acos-ml-engine             Up (healthy)        0.0.0.0:8081->8081/tcp
acos-feature-pipeline      Up                  0.0.0.0:8090->8090/tcp
roma-gpu-worker            Up (healthy)        0.0.0.0:8000->8000/tcp
astrofin-postgres          Up (healthy)        0.0.0.0:5432->5432/tcp
astrofin-redis             Up (healthy)        0.0.0.0:6379->6379/tcp
astrofin-prometheus        Up                  0.0.0.0:9090->9090/tcp
```

> Статусы `Up (healthy)` появятся через 20–60 секунд после старта —
> это нормально (start_period у каждого healthcheck 15–20s + 3 попытки).

---

## 5. Healthcheck-эндпоинты

После того как `docker compose ps` показал `(healthy)` для нужного
сервиса, проверьте HTTP-эндпоинты:

```bash
# Web Dashboard (Dash)
curl -s -o /dev/null -w "%{http_code}" http://localhost:8050/health
# ожидание: 200

# ML Inference API (FastAPI)
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/health
# ожидание: 200

# GPU Worker (FastAPI)
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health
# ожидание: 200

# Feature Pipeline (если health-эндпоинт не реализован — только TCP-чек)
nc -z localhost 8090 && echo "feature-pipeline: port open" || echo "CLOSED"
# (в текущей версии healthcheck в compose отсутствует, см. docker-compose.yml)

# Prometheus
curl -s -o /dev/null -w "%{http_code}" http://localhost:9090/-/healthy
# ожидание: 200

# Postgres
docker compose exec postgres pg_isready -U astrofin -d astrofin
# ожидание: "accepting connections"

# Redis
docker compose exec redis redis-cli ping
# ожидание: PONG
```

**Если сервис не отвечает 200** — смотрите логи:

```bash
docker compose logs <service-name> --tail 200
# примеры:
docker compose logs app --tail 200
docker compose logs ml-engine --tail 200
```

---

## 6. Сквозной smoke-тест (web → ml-engine)

Минимальный e2e-чек, что web-dashboard может дотянуться до ml-engine
через `ML_ENGINE_URL`:

```bash
# 1) Прямой запрос к ml-engine
curl -s http://localhost:8081/health | python3 -m json.tool
# ожидание: {"status": "ok", ...}

# 2) С web-dashboard, через внутреннюю сеть compose
docker compose exec app python3 -c "
import urllib.request, json
r = urllib.request.urlopen('http://ml-engine:8081/health', timeout=5)
print('ml-engine says:', json.loads(r.read()))
"
# ожидание: {'status': 'ok', ...}
```

### ACOS / governance

**ACOS (Governance/Execution/Trace) пока не контейнеризован** — на этой
стадии он работает как host-only systemd-сервис, который provision-ит
`home-cluster-iac/acos/` через Ansible.

- Где смотреть: `home-cluster-iac/acos/` (Ansible-роль + systemd unit)
- Проверка статуса (на host): `systemctl status acos`
- gRPC-эндпоинт (если включён): `localhost:50051` (для `grpc_health_probe`)

**HTTP-эндпоинта для приёма ACOS-заданий на текущий момент нет.**
Все governance-операции выполняются через:
1. CLI: `python -m acos_cli <subcommand>` (см. `AsurDev/acos/`)
2. gRPC-канал, если развёрнут воркером.
Добавление `POST /submit` HTTP-эндпоинта — запланировано (см. `docs/cluster-integration.md`).

### ROMA execution bridge (gpu-worker)

Запуск задания через воркер (HTTP):

```bash
curl -s -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"job_id": "smoke-test-001", "payload": {}}' | python3 -m json.tool
```

Логи воркера:

```bash
docker compose logs gpu-worker --tail 100
```

---

## 7. GPU-воркер: требования

`gpu-worker` (ROMA execution bridge) использует CUDA. Без GPU хоста
контейнер стартует, но CUDA-вызовы вернут ошибку.

**На NVIDIA-хосте** установите [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)
и убедитесь, что в `/etc/docker/daemon.json` есть `"default-runtime": "nvidia"`.

**Проверка:**

```bash
docker run --rm --gpus all nvidia/cuda:12.3.1-base-ubuntu22.04 nvidia-smi
# ожидание: таблица с GPU
```

В `docker-compose.yml` сервис `gpu-worker` помечен `deploy.resources.reservations.devices` — Compose
автоматически запросит у Docker доступ к GPU. Если toolkit не
установлен, `docker compose up` упадёт именно на этом сервисе с
ошибкой вида:

```
Error response from daemon: could not select device driver "" with capabilities: [[gpu]]
```

В этом случае просто **уберите gpu-worker из compose** (закомментируйте
блок `gpu-worker:`) или запустите с профилем `CPU_ONLY`:

```bash
docker compose --profile default up -d
# gpu-worker стартует только если переменная COMPOSE_PROFILES не ограничивает его
```

---

## 8. Остановка и очистка

```bash
# Мягкая остановка (SIGTERM, даёт сервисам завершить запросы)
docker compose down

# Полная очистка (включая volumes с данными БД)
docker compose down -v
```

**Удаление только собранных образов** (если нужно пересобрать):

```bash
docker compose down --rmi all
```

---

## 9. Troubleshooting

| Симптом | Причина | Решение |
|---------|---------|---------|
| `ERROR: Dockerfile not found: ml_engine/Dockerfile` | сабмодули не подтянуты | `git submodule update --init --recursive` |
| `app` падает с `ConnectionError: postgres` | TimescaleDB не успела стартовать | подождите 30–60s, `docker compose restart app` |
| `gpu-worker` exit code 1 при старте | нет NVIDIA toolkit | см. раздел 7 |
| `permission denied` на bind-mount | uid внутри контейнера ≠ host-uid | смените `user:` в compose или chmod на хосте |
| Web-dashboard не открывается, `localhost:8050` | `app` unhealthy | `docker compose logs app` — частая причина: БД ещё не готова |

---

## 10. Ссылки

- `docker-compose.yml` — корневой compose, 7 сервисов
- `.github/workflows/compose-check.yml` — CI, валидирующий compose + наличие всех Dockerfile
- `AsurDev/acos/Dockerfile` — стандарт контейнеризации, применённый к `cluster/node/Dockerfile`
- `home-cluster-iac/acos/` — Ansible-роль для host-only ACOS
- `docs/cluster-integration.md` — gRPC/HTTP-интеграции

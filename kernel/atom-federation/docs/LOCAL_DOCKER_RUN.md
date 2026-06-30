# Локальная сборка и запуск (Docker на ПК)

Все команды — на твоём локальном ПК (Pop!_OS / Linux).  
В этом sandbox Docker недоступен, поэтому здесь только инструкции.

## 1. Предусловия

```bash
docker --version          # Docker 24+
docker compose version    # v2 (compose-plugin)
git --version
```

## 2. Клонирование

```bash
git clone https://github.com/mahaasur13-sys/atom-federation-os.git
cd atom-federation-os
git log --oneline -3
# 656f021 ci: cluster-image-check — hadolint DL3008 + compose schema + dockerfile syntax
# 455b13f feat(cluster): real liveness probe, compose parity, image CI
# 0f40a9b feat(cluster): upgrade node Dockerfile to Python 3.12, add healthcheck, pin deps
```

## Шаг 1 — собрать образ узла

**⚠️ Важно:** Dockerfile использует пути `cluster/node/requirements.txt`, `cluster/`, `proto/`, `sbs/` — все они относительны к **корню репозитория**. Поэтому build context должен быть `.` (корень), а не `./cluster/node/`.

```bash
cd /home/workspace/atom-federation-os/atom-federation-os

# правильная команда — собираем из корня репо
docker build -t atom-node:dev -f cluster/node/Dockerfile .

# проверяем, что образ собрался
docker images | grep atom-node
```

Ожидаемый результат:
```
atom-node   dev   <IMAGE_ID>   <DATE>   ~180MB
```

Если видишь ошибку `"/sbs": not found` или `"/proto": not found` — ты запустил сборку не из корня репо. Перейди в корень (`cd /home/workspace/atom-federation-os/atom-federation-os`) и повтори.

Проверка что multi-stage сработал (runtime-слой должен быть тонким):

```bash
docker images atom-node:dev --format '{{.Size}}'
# ожидаемо: ~150-200 MB (slim + tini + deps)

docker history atom-node:dev --no-trunc | head -25
# видна последовательность: builder → runtime (после FROM python:3.12-slim AS runtime)
```

Проверка non-root пользователя:

```bash
docker run --rm atom-node:dev id
# ожидаемо: uid=1001(node) gid=1001(node) groups=1001(node)

docker run --rm atom-node:dev which tini
# ожидаемо: /usr/bin/tini

docker run --rm atom-node:dev ls /app | head -10
# ожидаемо: cluster  README.md  shared  ... (собранный код)
```

## 4. Smoke-тест healthcheck (без поднятия кластера)

```bash
docker run -d --name atom-node-smoke \
  -e NODE_ID=smoke \
  -e NODE_PORT=50060 \
  atom-node:dev

# Подождать старт tini + healthcheck
sleep 5

docker inspect --format='{{json .State.Health}}' atom-node-smoke | python3 -m json.tool
# ожидаемо:
# {
#     "Status": "healthy",
#     "FailingStreak": 0,
#     "Log": [
#         { "Start": "...", "End": "...", "ExitCode": 0, "Output": "ok" },
#         ...
#     ]
# }

docker logs --tail 30 atom-node-smoke
# ожидаемо:
# [ENTRY] smoke booting — NODE_ID=smoke, PEERS=[]
# [BOOT] shared.runtime_bootstrap ready
# ... (или старт gRPC сервера, если порт открылся)

docker rm -f atom-node-smoke
```

## 5. Подъём 3-нодового кластера через docker compose

```bash
cd cluster  # в репозитории
docker compose config --quiet   # синтаксис compose валиден
docker compose up -d --build    # соберёт и поднимет node-a, node-b, node-c
```

Проверки:

```bash
docker compose ps
# ожидаемо: все 3 сервиса в State: Up (healthy)

# Логи каждой ноды
docker compose logs --tail 20 node-a
docker compose logs --tail 20 node-b
docker compose logs --tail 20 node-c

# Healthcheck изнутри compose
docker compose exec node-a python -c "from cluster.node.healthcheck import healthz; print(healthz())"
# ожидаемо: ok
```

## 6. Сетевая связность между нодами

```bash
docker network inspect cluster_atom-net --format '{{range .Containers}}{{.Name}} {{.IPv4Address}}{{"\n"}}{{end}}'
# ожидаемо: 3 контейнера с разными IP в подсети 172.x

# Проверка что порты слушаются
docker compose exec node-a bash -c 'ss -tlnp | grep 50060 || netstat -tlnp | grep 50060'
```

## 7. Проверка CI workflow локально (опционально)

```bash
# hadolint — синтаксис Dockerfile
docker run --rm -i hadolint/hadolint < cluster/node/Dockerfile

# yamlint для compose
docker run --rm -i cytopia/yamllint -d "{extends: default, rules: {line-length: disable}}" < cluster/docker-compose.yml
```

## 8. Остановка

```bash
docker compose down -v      # с очисткой томов
```

## 9. Возможные проблемы

| Симптом | Причина / фикс |
|---|---|
| `failed to solve: python:3.12-slim` | нет интернета на момент сборки; проверить `docker pull python:3.12-slim` |
| `permission denied` при запуске | HEALTHCHECK `cluster.node.healthcheck` ожидает uid 1001; убедись что образ non-root (см. шаг 3) |
| `bind: address already in use` | порт 50060/50061/50062 занят на хосте; сменить в `docker-compose.yml` |
| `Health: starting` дольше 30s | увеличить `start_period` в `docker-compose.yml` healthcheck |
| `ModuleNotFoundError: cluster` | `cluster/node/__init__.py` пуст — это OK; проверить что `cluster/` в корне `WORKDIR /app` |

## 10. Push в GitHub (если менял локально)

```bash
git checkout -b feat/local-docker-test
# ... правки ...
git add -A
git commit -m "test: local docker build verified"
git push origin feat/local-docker-test
# потом открыть PR на GitHub
```

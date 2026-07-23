# Phase-2 Docker Upgrade — Validation Toolkit

> **Что это:** Reference-материалы + скрипты для проверки и smoke-build
> Phase-2 стандарта Dockerfile, применённого в `AsurDev/acos` и
> `atom-federation-os/cluster/node`.
>
> **Что это НЕ:** Готовый Dockerfile для копирования. Эталонные
> Dockerfiles лежат в репозиториях (`acos/Dockerfile` здесь,
> `cluster/node/Dockerfile` в atom-federation-os). Канонический шаблон —
> в [REFERENCE_DOCKERFILE.md](./REFERENCE_DOCKERFILE.md).

---

## Зачем этот каталог

К моменту завершения Фазы 1 (jun 2026) эталонные Dockerfile для
ACOS и cluster-node были разработаны, протестированы и запушены:

| Сервис | Dockerfile | Коммит |
|---|---|---|
| `acos` (AsurDev) | `acos/Dockerfile` | `5c3cec4 feat(acos): add slim Dockerfile …` |
| `cluster-node` (atom-federation-os) | `cluster/node/Dockerfile` | `0f40a9b feat(cluster): upgrade node Dockerfile …` |

Этот каталог — **набор инструментов**, который позволяет любому
разработчику (в первую очередь вам, `felix@localhost`) проверить,
что новый Dockerfile соответствует Phase-2 стандарту, и собрать
его локально, не гадая, какие директивы обязательны.

---

## Содержимое

```
acos/phase2-docker-upgrade/
├── README.md                    ← этот файл
├── CHECKLIST.md                 ← канонический чеклист Phase-2 (что и почему)
├── REFERENCE_DOCKERFILE.md      ← эталонный Dockerfile-шаблон (документированный)
├── REFERENCE_COMPOSE.md         ← эталонный compose-блок (документированный)
├── validate-docker.sh           ← статическая валидация Dockerfile (не нужен Docker)
├── validate-compose.sh          ← статическая валидация compose (нужен Docker daemon)
├── smoke-build.sh               ← реальный `docker build` + проверки образа
├── smoke-run.sh                 ← foreground run + healthcheck probe (нужен Docker daemon)
└── run-all.sh                   ← запуск всех четырёх шагов одной командой
```

### Что каждый файл делает

| Файл | Нужен Docker? | Проверяет | Когда использовать |
|---|---|---|---|
| `CHECKLIST.md` | ❌ | Phase-2 standard | Перед началом любых правок Dockerfile |
| `REFERENCE_DOCKERFILE.md` | ❌ | Шаблон | Когда пишете новый Dockerfile |
| `REFERENCE_COMPOSE.md` | ❌ | Шаблон | Когда пишете новый compose-сервис |
| `validate-docker.sh` | ❌ | Статические требования | В CI, в pre-commit, перед commit |
| `validate-compose.sh` | ✅ (для YAML schema) | Структурные best-practice | Перед merge compose-изменений |
| `smoke-build.sh` | ✅ | Реальный build + размер + meta | Перед push в registry, локальная проверка |
| `smoke-run.sh` | ✅ | Liveness probe, exit-коды, логи | После каждого изменения entrypoint/CMD |
| `run-all.sh` | ✅ | Все 4 проверки | Acceptance gate перед merge |

---

## Быстрый старт на felix@localhost

### Acceptance за один запуск

```bash
# из AsurDev/
cd ~/AsurDev            # или /home/workspace/AsurDev
./acos/phase2-docker-upgrade/run-all.sh \
    acos/Dockerfile \
    docker-compose.yml \
    acos:phase2-smoke
```

Это прогонит 4 проверки подряд: статика Dockerfile → статика compose
→ реальный build → foreground run с healthcheck. Если любой шаг
падает — выполнение прерывается с понятным сообщением.

### Только статика (без Docker daemon)

Подходит для CI-окружений, где Docker недоступен (например, GitHub
Actions без `docker:dind` service):

```bash
cd ~/AsurDev
bash acos/phase2-docker-upgrade/validate-docker.sh acos/Dockerfile
bash acos/phase2-docker-upgrade/validate-compose.sh docker-compose.yml
```

`validate-docker.sh` не вызывает Docker вообще — только `grep`/`awk`
по тексту. `validate-compose.sh` использует `docker compose config`
для YAML-валидации (можно отключить флагом `--no-docker`).

### Только smoke-build (когда уже знаете, что статика в порядке)

```bash
cd ~/AsurDev
bash acos/phase2-docker-upgrade/smoke-build.sh acos/Dockerfile acos:phase2-smoke
bash acos/phase2-docker-upgrade/smoke-run.sh acos:phase2-smoke
```

---

## Что НЕ входит в этот каталог

- **Эталонный Dockerfile** — лежит в `acos/Dockerfile` и
  `cluster/node/Dockerfile`. Копировать файлы отсюда в
  `cluster/node` **не нужно** — эта работа уже сделана и
  закоммичена (`0f40a9b`, `455b13f`, `940f536`).
- **GitHub-token обновление** — см. `docs/github-token-upgrade.md`.
  По состоянию на 2026-06-19 push работает через SSH, дополнительных
  действий не требуется.
- **Hadolint config** — DL3008 warning одинаково присутствует в обоих
  reference Dockerfile. Линт-фикс оставлен на Фазу 3 (единый config
  на оба репозитория).

---

## Phase-2 standard: что именно проверяется

Краткая версия (полная — в [CHECKLIST.md](./CHECKLIST.md)):

| # | Правило | Зачем |
|---|---|---|
| 1 | Базовый образ `python:3.x-slim` (НЕ `:latest`) | reproducible builds |
| 2 | Multi-stage build (deps + runtime) | build context меньше, runtime-слой тонкий |
| 3 | tini как PID 1 | signal forwarding, zombie reaping |
| 4 | Non-root user (uid 1001, `/usr/sbin/nologin`) | least privilege |
| 5 | `python -m compileall` на этапе build | быстрее запуск, ошибки импорта видно в build, не в run |
| 6 | Pinned deps в `requirements.txt` | reproducible, безопасные апгрейды |
| 7 | HEALTHCHECK с `--start-period` | не помечать контейнер `unhealthy` во время boot |
| 8 | ENTRYPOINT начинается с `/usr/bin/tini` | корректная обработка сигналов от Docker/k8s |
| 9 | OCI labels (`org.opencontainers.image.*`) | provenance trail в реестре |
| 10 | Нет `COPY . .` | не утекает `.git/`, `tests/`, `.venv/` в образ |

Все эти пункты проверяются автоматически через `validate-docker.sh`
(кроме реального `docker build`, для которого есть `smoke-build.sh`).

---

## Различия между acos и cluster/node

Оба следуют стандарту, но есть намеренные различия:

| | acos | cluster/node |
|---|---|---|
| Non-root user | `acos` uid 1001 | `atom` uid 1001 |
| Runtime deps | stdlib-only | `grpcio==1.80.0`, `protobuf==6.33.6` |
| Entrypoint | `python -m acos_cli invariants` | `python cluster/node/entrypoint.py` |
| Healthcheck | `python -m acos_cli invariants` | `python -m cluster.node.healthcheck` |
| EXPOSE | `8080` (HTTP reserved) | none (gRPC port per-node via env) |

Асимметрия `EXPOSE` осознанная: acos — это stateful HTTP-сервис,
cluster/node — это mesh из 3-х gRPC-узлов с разными портами.

---

## Troubleshooting

**`smoke-build.sh` падает на `apt-get update` с "repository not signed"**

Phase-2 Dockerfile наследует `apt-get update` из `python:3.12-slim`. Этот
базовый образ регулярно обновляется; если локальный Docker-кеш
устарел, поможет:

```bash
docker pull python:3.12-slim
docker builder prune -af      # ⚠️  сбросит ВСЕ build-кеши
```

**`validate-docker.sh` ругается на "no :latest tags", но я их не использую**

Скорее всего, это upstream-базовый образ (например, `python:3.12-slim`
— это не `:latest`, но `slim` без версии Python тоже считается
"незакреплённым"). Валидатор делает консервативную проверку: явное
`python:3.x-slim` ОК, всё остальное — warning.

**`smoke-run.sh` показывает `starting` вместо `healthy`**

Это нормально в первые 20 секунд (`start_period`). Подождите
`start_period + interval × retries` (по умолчанию ~30с × 4 = 2 минуты
для acos, ~15с + 90с = 105с для cluster/node). Если через 2 минуты
всё ещё `unhealthy` — смотрите `docker logs <container>`.

**`run-all.sh` падает на шаге 1, но статически Dockerfile выглядит нормально**

Запустите `validate-docker.sh` напрямую с `--verbose` и убедитесь,
что валидатор читает именно тот Dockerfile, который вы правили.
Частый случай: `acos/Dockerfile` и `cluster/node/Dockerfile` имеют
разные требования (см. таблицу различий выше), и передача одного
вместо другого даёт ложноположительные ошибки.

---

## См. также

- [CHECKLIST.md](./CHECKLIST.md) — канонический чеклист Phase-2.
- [REFERENCE_DOCKERFILE.md](./REFERENCE_DOCKERFILE.md) — шаблон Dockerfile.
- [REFERENCE_COMPOSE.md](./REFERENCE_COMPOSE.md) — шаблон compose-блока.
- `AsurDev/acos/Dockerfile` — reference #1 (stdlib-only service).
- `atom-federation-os/cluster/node/Dockerfile` — reference #2 (gRPC service).
- `AsurDev/docs/github-token-upgrade.md` — статус push-токенов.
- `AsurDev/docs/cluster-integration.md` — межрепозиторные контракты.
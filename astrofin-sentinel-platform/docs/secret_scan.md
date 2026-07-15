# Secret Scan Runbook

Этот документ описывает, как в `astrofin-sentinel-platform` устроена
защита от утечки секретов: какие правила `gitleaks` активны, что попадает
в allowlist, как гонять сканер локально и в CI, и как действовать при
ротации ключей.

> **TL;DR.** Реальные секреты **никогда** не хранятся в репозитории.
> Все runtime-значения берутся из переменных окружения (см.
> `core/settings.py`), а примеры/плейсхолдеры лежат в `.env.example`.
> Сканер `gitleaks` ищет случайные литералы в исходниках и CI держит
> ветку «зелёной» только при нулевых новых находках сверх baseline.

## 1. Схема секретов

Источник истины — модуль [`core/settings.py`](../core/settings.py).
Все настройки читаются через `pydantic-settings` из переменных
окружения, в том числе:

| Категория | Поля `Settings` | Соответствующая env-переменная |
|-----------|-----------------|--------------------------------|
| Auth / JWT | `jwt_private_key_path`, `jwt_public_key_path`, `jwt_issuer`, `jwt_audience` | `JWT_PRIVATE_KEY_PATH`, `JWT_PUBLIC_KEY_PATH`, `JWT_ISSUER`, `JWT_AUDIENCE` |
| Flask / Dash | `secret_key` | `SECRET_KEY` |
| DB | `postgres_password` (SecretStr) | `POSTGRES_PASSWORD` |
| Grafana | `grafana_admin_password` (SecretStr) | `GRAFANA_ADMIN_PASSWORD` |
| Exchange (CCXT) | `ccxt_api_key`, `ccxt_api_secret` | `CCXT_API_KEY`, `CCXT_API_SECRET` |
| Messaging | `telegram_bot_token` | `TELEGRAM_BOT_TOKEN` |
| Observability | `sentry_dsn` | `SENTRY_DSN` |
| AI providers | `openai_api_key` и др. | `OPENAI_API_KEY` |

Полный список (~90 полей) сгенерирован в [`.env.example`](../.env.example)
скриптом-генератором на основе самой схемы. **В `.env.example` нет
реальных значений** — только плейсхолдеры вида `your_xxx_here`,
`changeme`, `REPLACE_WITH_*`, `${VAR:?VAR is required}` и т. п.

## 2. Custom-правила `gitleaks`

Конфиг — [`.gitleaks.toml`](../.gitleaks.toml). Сверх стандартного
набора gitleaks добавлены правила под конкретные имена переменных
проекта:

| RuleID | Назначение | Regex (упрощённо) |
|--------|------------|-------------------|
| `asp-postgres-password` | `POSTGRES_PASSWORD=<value>` | `POSTGRES_PASSWORD\s*[:=]\s*['"]?([^\s'"#]{4,})` |
| `asp-grafana-admin-password` | `GRAFANA_ADMIN_PASSWORD=<value>` | `GRAFANA_ADMIN_PASSWORD\s*[:=]\s*['"]?([^\s'"#]{6,})` |
| `asp-ccxt-api-key` | `CCXT_API_KEY=...`, `EXCHANGE_API_KEY=...` | см. `.gitleaks.toml` |
| `asp-ccxt-api-secret` | `CCXT_API_SECRET=...` | см. `.gitleaks.toml` |
| `asp-jwt-private-key` | `JWT_PRIVATE_KEY_PATH=...` | см. `.gitleaks.toml` |
| `asp-jwt-public-key` | `JWT_PUBLIC_KEY_PATH=...` | см. `.gitleaks.toml` |
| `asp-flask-secret-key` | `SECRET_KEY=...` | см. `.gitleaks.toml` |
| `asp-telegram-bot-token` | Telegram bot token (формат `<id>:AA…`) | см. `.gitleaks.toml` |
| `asp-sentry-dsn` | `SENTRY_DSN=https://<id>@host/n` | см. `.gitleaks.toml` |

Каждое правило помечено тегом `asp`, чтобы их было легко отличать от
стандартных (`generic-api-key`, `aws-access-token` и т. д.).

## 3. Allowlist (что мы сознательно игнорируем)

Глобальный `[allowlist]` в `.gitleaks.toml` подавляет:

- **Placeholders** из `.env.example`:
  `your_<x>_here`, `your_<x>_password_here`, `your_<x>_secret_here`,
  `your_<x>_key_here`, `your_<x>_token_here`, `your_<x>_dsn_here`.
- **Универсальные placeholder'ы**:
  `REPLACE_WITH_*`, `CHANGE_ME`, `change-me-in-production`,
  `placeholder`, `XXXXXX`, `12345678`, `ghp_xxxxxx+`,
  `sk_test_placeholder`, `whsec_placeholder`, `postgres@localhost`.
- **Bash fallback-значения** (например, `${VAR:-admin}`): regex
  `\$\{[A-Z_]+(?::?[-]?[A-Za-z0-9_]*)?\}`.
- **Шаблонные ссылки в документации**: `<password>`, `<secret>`,
  `<token>`, `<your_*>`, `example.com`, `changeme`.
- **Трекинг-файлы, которые легитимно содержат примеры**:
  `.env.example`, `.env.pgvector.example`, `deploy/iac/ansible/group_vars/all.yml.example`,
  `deploy/iac/terraform/terraform.tfvars.example`,
  `scripts/generate_secrets.sh`, `scripts/validate_docker_security.py`,
  `src/bridges/roma/billing/stripe_client.py`, `tests/**/*.py`,
  `tests/fixtures/**`, `[ARCHIVED] audit_repo/** (no longer in git index)`.

Если у вас появляется **новая** ложная находка — сначала проверьте, не
нарушает ли она allowlist. Если нарушает — лучше исправить источник
(заменить литерал на `${VAR:?...}` или плейсхолдер), а не расширять
allowlist.

## 4. Локальный запуск

```bash
# Полный скан + baseline (рекомендуемый путь)
gitleaks detect --source . --baseline-path .gitleaks-baseline.json

# Только новое в текущих uncommitted-файлах
gitleaks detect --source . --no-git --baseline-path .gitleaks-baseline.json

# С отчётом
gitleaks detect --source . --baseline-path .gitleaks-baseline.json \
  --report-path gitleaks-report.json --report-format json
```

`.gitleaks-baseline.json` хранится в репозитории и **обновляется
только осознанно** (см. § 6). Стандартный выход:

```
INF  scan completed in 40.5s
WRN  leaks found: 24       ← те, что уже в baseline (см. § 5)
exit=0                       ← baseline успешно применён
```

`exit=0` означает, что **новых** находок нет. Любой `exit≠0` —
блокер.

## 5. CI / Quality Gate

CI workflow [`.github/workflows/quality-gate.yml`](../.github/workflows/quality-gate.yml)
запускает `gitleaks detect --source . --baseline-path .gitleaks-baseline.json`
после `setup-uv`. Если код выхода ≠ 0 — PR не мерджится.

Baseline коммитится в репо: это нужно, чтобы:

- защититься от регрессий на уже известных находках;
- получать осмысленный diff при добавлении новых правил (появилось
  много новых строк → `git diff .gitleaks-baseline.json`).

## 6. Как интерпретировать результат и обновлять baseline

| Ситуация | Что делать |
|----------|------------|
| `exit=0`, 24 находки | Это **baseline** — игнорируем. |
| `exit=0`, 25+ находки | Скорее всего, **новая** находка. Открыть `gitleaks-report.json` и понять, leak или FP. |
| Новая находка — реальный секрет | **Ротировать ключ** (см. § 7), затем удалить литерал из кода. |
| Новая находка — false positive | Либо исправить источник (заменить на placeholder), либо добавить в allowlist. |
| Хотим переписать baseline «с нуля» | Сначала вычистить все исторические литералы, затем `gitleaks detect --source . --baseline-path .gitleaks-baseline.json` снова запишет JSON. **Не делать без явной причины.** |

Сейчас в baseline попадают (легитимные FP):

- **Legacy в истории Git**: hard-coded `POSTGRES_PASSWORD=astrofin` в
  старых коммитах `docker-compose.yml`/`docker-compose.pgvector.yml`
  (в актуальных файлах уже `${POSTGRES_PASSWORD:?...}`).
- **Fallback defaults** в shell-скриптах развёртывания
  (`${GRAFANA_ADMIN_PASSWORD:-admin123}`).
- **Документация**: пример `admin123` в `deploy/iac/docs/architecture.md`.

Каждый такой случай — потенциальная утечка только при доступе к
истории Git. Сейчас репо **приватное**, что нивелирует риск; при
публикации рекомендуется (а) полностью вычистить историю (`git filter-repo`)
либо (б) перевести такие литералы в `.env.example`.

## 7. Ротация ключей

| Что ротируем | Где живёт в проде | Как заменить |
|--------------|-------------------|--------------|
| `POSTGRES_PASSWORD` | Kubernetes Secret `postgres-secrets`, Vault path `secret/data/asp/postgres` | `kubectl create secret generic postgres-secrets --from-literal=password=... -n asp --dry-run=client -o yaml \| kubectl apply -f -` или Vault `kv put`. Перезапустить под. |
| `SECRET_KEY` (Flask/Dash) | Vault `secret/data/asp/secret-key` | Vault `kv put`, перезапустить web-pod. |
| `JWT_PRIVATE_KEY`/`JWT_PUBLIC_KEY` | Vault `secret/data/asp/jwt` | Vault `kv put`, рестарт `auth_jwt`. |
| `GRAFANA_ADMIN_PASSWORD` | Vault `secret/data/asp/grafana` | Vault `kv put`, рестарт Grafana. |
| `CCXT_API_KEY`/`CCXT_API_SECRET` | Vault `secret/data/asp/ccxt` | Vault `kv put`, рестарт trading-pod'ов. |
| `TELEGRAM_BOT_TOKEN` | Vault `secret/data/asp/telegram` | Vault `kv put`, рестарт бота. |
| `OPENAI_API_KEY` (и провайдеры) | Vault `secret/data/asp/openai` | Vault `kv put`, рестарт LLM-воркеров. |
| `SENTRY_DSN` | Vault `secret/data/asp/sentry` | Vault `kv put`, рестарт web + observability. |

**Процедура**:

1. Сгенерировать новый ключ у поставщика (или Vault: `vault read -format=json secret/data/asp/foo | jq -r .data.data.value` → rotate).
2. Положить в Vault/K8s Secret.
3. Перезапустить соответствующие поды.
4. Отозвать старый ключ у поставщика.
5. Закоммитить обновлённый `.env.example` (если имена переменных
   изменились) и пересоздать baseline, если меняли allowlist.

## 8. Что **никогда** нельзя коммитить

- Реальные значения `POSTGRES_PASSWORD`, `SECRET_KEY`,
  `JWT_*_KEY`, `GRAFANA_ADMIN_PASSWORD`, `CCXT_API_*`,
  `TELEGRAM_BOT_TOKEN`, `OPENAI_API_KEY`, `SENTRY_DSN`, любых
  cloud-provider credentials.
- Приватные ключи (`.pem`, `.key`, `id_rsa`, `id_ed25519`).
- Содержимое `.env` (только `.env.example`).
- Снимки БД, логи с токенами, дампы Vault.

## 9. Где искать «потерянный» секрет

Если `gitleaks` сработал на PR — в выводе всегда есть `File` и
`StartLine`. Открываем файл, удаляем литерал, при необходимости —
добавляем `os.getenv(...)` или `Settings.<field>`. Если «не наш» файл
(например, сгенерированный артефакт) — добавляем в `[[rules]].path` в
`.gitleaks.toml` или в `[allowlist].paths`.

## 10. Полезные ссылки

- [`core/settings.py`](../core/settings.py) — схема конфигурации.
- [`.env.example`](../.env.example) — полный список переменных.
- [`.gitleaks.toml`](../.gitleaks.toml) — конфиг сканера.
- [`.gitleaks-baseline.json`](../.gitleaks-baseline.json) — известные
  находки.
- [`.github/workflows/quality-gate.yml`](../.github/workflows/quality-gate.yml) — CI-проверка.
- [`docs/SECRETS_ROTATION.md`](SECRETS_ROTATION.md) — детальная runbook
  по ротации (планируется).

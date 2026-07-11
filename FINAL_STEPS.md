# Final Steps — запуск production

Финальный чек-лист после того, как `prod-readiness-10` (PR #15) и `first-release-helpers` (PR #16) смержены в `master`.

Все три скрипта лежат в `scripts/` и идемпотентны: можно запускать повторно.

| # | Шаг | Скрипт | Время |
|---|---|---|---|
| 1 | Окружения + секреты GitHub | `scripts/setup-secrets-and-envs.sh` | 3–5 мин |
| 2 | Импорт дашборда Grafana | `scripts/import-grafana-dashboard.sh` | 1 мин |
| 3 | Первый релиз `v1.0.0-rc1` | `scripts/first-release.sh` | 10–15 мин |

---

## Шаг 1. Окружения и секреты GitHub

Скрипт создаёт окружения `staging` и `production`, добавляет protection rules на production (1 reviewer) и интерактивно устанавливает 5 секретов.

**Интерактивный режим (рекомендуется):**
```bash
./scripts/setup-secrets-and-envs.sh
```

**Без интерактива** — создаётся файл `.env.secrets` и печатаются команды:
```bash
./scripts/setup-secrets-and-envs.sh --non-interactive
# заполнить .env.secrets, потом:
set -a; source .env.secrets; set +a
./scripts/setup-secrets-and-envs.sh
```

### Что нужно подготовить заранее

| Имя секрета | Окружение | Как получить |
|---|---|---|
| `GHCR_TOKEN` | repo | GitHub → Settings → Developer settings → PAT (`read:packages`, `write:packages`). Если репо ваше — используйте `GITHUB_TOKEN` из Actions: в workflow подставляется автоматически, отдельный секрет можно не делать. |
| `KUBE_CONFIG_STAGING` | staging | `cat ~/.kube/config \| base64 -w0` (staging-кластер) |
| `KUBE_CONFIG_PROD` | production | `cat ~/.kube/config \| base64 -w0` (prod-кластер) |
| `STAGING_HEALTHCHECK_URL` | staging | URL вида `https://staging.<domain>/healthz` после деплоя |
| `SLACK_WEBHOOK_URL` | production | Slack → Apps → Incoming Webhooks → New (опционально) |

### Альтернатива вручную через curl

Если `gh` не имеет права admin:environment, скрипт сам выведет готовые команды. Базовый вид:

```bash
# Создать окружения
curl -X PUT \
  -H "Authorization: token $(gh auth token)" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/mahaasur13-sys/astrofin-sentinel-platform/environments/staging \
  -d '{"wait_timer":0,"prevent_self_review":false}'

curl -X PUT \
  -H "Authorization: token $(gh auth token)" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/mahaasur13-sys/astrofin-sentinel-platform/environments/production \
  -d '{"wait_timer":0,"prevent_self_review":true}'

# Установить секрет
echo -n "VALUE" | gh secret set KUBE_CONFIG_STAGING --env staging --repo mahaasur13-sys/astrofin-sentinel-platform
```

---

## Шаг 2. Дашборд Grafana

```bash
export GRAFANA_URL=https://grafana.example.com
export GRAFANA_API_TOKEN=glsa_xxxxxxxxxxxxxxxxxxxx
./scripts/import-grafana-dashboard.sh
```

Скрипт создаёт папку `AstroFin Sentinel`, импортирует `deploy/monitoring/grafana-dashboard.json` и проверяет итоговый `GET /api/dashboards/uid/astrofin-overview`.

### Альтернатива вручную
1. Grafana → **Dashboards → New → Import**.
2. Upload JSON → выбрать `deploy/monitoring/grafana-dashboard.json`.
3. В выпадающем списке Prometheus выбрать источник с `uid = prometheus`.
4. **Import**.

---

## Шаг 3. Первый релиз `v1.0.0-rc1`

Минимальный режим (тег + push + ссылка на run):
```bash
./scripts/first-release.sh
```

С ожиданием завершения `deploy-staging` и smoke-тестом:
```bash
export STAGING_HEALTHCHECK_URL=https://staging.example.com/healthz
WAIT=1 ./scripts/first-release.sh
```

Скрипт:
1. Проверяет чистоту рабочей копии.
2. Создаёт аннотированный тег `v1.0.0-rc1` (если ещё нет).
3. Пушит тег.
4. Находит workflow run через `gh api`.
5. Если `WAIT=1` — опрашивает статус, затем делает `curl /healthz`.
6. Печатает `https://github.com/mahaasur13-sys/astrofin-sentinel-platform/actions/runs/<id>`.

После успешного `deploy-staging`:
1. Откройте run в GitHub → дождитесь approval-запроса на `deploy-prod`.
2. Approve → `deploy-prod` → smoke-test prod → релиз выпущен.

### Альтернатива вручную
```bash
git tag -a v1.0.0-rc1 -m "v1.0.0-rc1"
git push origin v1.0.0-rc1
gh release create v1.0.0-rc1 --generate-notes --draft
```

---

## Проверка Dependabot

После шага 1 убедитесь, что Dependabot активен:

1. **Settings → Code security and analysis** — включить:
   - Dependabot alerts ✅
   - Dependabot security updates ✅
   - Dependabot version updates ✅
2. **Insights → Dependency graph → Dependabot** — должно быть «0 alerts» (или разумное число).
3. При наличии алертов — открыть PR от Dependabot и вмержить.

Файл `.github/dependabot.yml` уже в репозитории и проверяет:

| Экосистема | Расписание | Группировка |
|---|---|---|
| pip | weekly Monday | patch/minor в группе, major — отдельно |
| github-actions | weekly Monday | minor patch в группе |
| docker | weekly Monday | minor patch в группе |

---

## Чек-лист «production-ready 10/10»

- [x] PR #15 (`prod-readiness-10`) смержен в master.
- [x] PR #16 (`first-release.sh` + checklist) смержен в master.
- [x] Скрипты `setup-secrets-and-envs.sh`, `import-grafana-dashboard.sh`, обновлённый `first-release.sh` добавлены.
- [ ] **Шаг 1 выполнен** — окружения и секреты установлены.
- [ ] **Шаг 2 выполнен** — дашборд Grafana импортирован.
- [ ] **Шаг 3 выполнен** — тег `v1.0.0-rc1` запушен, staging задеплоен, prod одобрен.
- [ ] Dependabot проверен.

Когда все 4 пункта отмечены — **production готов**.

# 🗓️ AstroFin Sentinel — Week 1 Sprint (Phase 0 + начало Phase 1)

> **Sprint Window:** 2026-07-06 (Mon) → 2026-07-12 (Sun) — 5 рабочих дней + 2 буферных
****Sprint Goal:** «Разблокировать push и закрыть дыры, которые мешают выкатить что-либо в прод»
****Capacity:** 1 Senior Backend (full, \~40 ч) + 0.5 DevOps (\~20 ч) + 0.25 Security (\~10 ч) + 0.25 Writer (\~10 ч) = **\~80 ч**
****Source:** `file PRODUCTION_BACKLOG.md` (Top-15 W1) + критический путь
****Status:** 📋 Ready to start

---

## 🎯 Sprint Goal (Definition of Success)

**К концу недели мы сможем:**

1. ✅ Запушить что-нибудь в `mahaasur13-sys/astrofin-sentinel-platform` без submodule-конфликтов (G22 закрыт)
2. ✅ Зашифровать секреты через SOPS и расшифровать в k8s init-container (G1 закрыт)
3. ✅ Включить JWT параллельно с API_KEY, не сломав существующих клиентов (G5 начат)
4. ✅ `/readyz` корректно отделяет liveness от readiness для k8s (блокер P5-01)
5. ✅ SLO/SLI определены и подписаны командой (основа для P3-03)

**Readiness delta:** +10 % (с \~75 % до **\~85 %**)

---

## 📅 Дневной план

### 🟦 Mon (2026-07-06) — «Stop the bleeding»

| \# | ID | Задача | Owner | Часы | Время | Зависит от | Definition of Done |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | **P0-01** | Расследовать 26 failing tests: `pytest --collect-only`, классифицировать в `file tests/FAILING_TESTS.md` | Backend | 3 | 09:00-12:00 | — | Файл создан, ≥5 зафиксировано как flaky/import, остальные перенесены в issue |
| 2 | **P0-01.b** | Починить top-3 broken imports (`grep -rn "ImportError" tests/` × fix) | Backend | 2 | 13:00-15:00 | #1 | `pytest -q tests/test_*.py` показывает ≥ 21 fail (было 26) |
| 3 | **P0-02** | Удалить `.bak` файлы, добавить `*.bak*` в `.gitignore` | Backend | 1 | 15:00-16:00 | — | `git grep '\.bak-'` → 0; `git status` чист |
| 4 | **P0-04** | Создать ветку `release/1.0.0`, выставить branch protection | DevOps | 1 | 09:00-10:00 | — | Ветка существует; protection: 1 review + CI required |
| 5 | **P0-06** | Прочитать 6 bandit high, классифицировать | Security | 2 | 10:00-12:00 | — | `file docs/security/bandit-baseline.md` создан |

**Daily target:** 9 ч × 4 треков = 36 ч. **Subtotal Mon: 9 ч**

**Standup (17:00):** показать `file FAILING_TESTS.md` + `.gitignore` PR + branch protection.

---

### 🟦 Tue (2026-07-07) — «Submodule crisis resolution»

| \# | ID | Задача | Owner | Часы | Время | Зависит от | Definition of Done |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 6 | **P0-03** | План submodule→subtree: написать `file docs/MIGRATION_submodules.md` | DevOps | 4 | 09:00-13:00 | — | Документ: dry-run команды, rollback, contact list |
| 7 | **P0-03.b** | **Dry-run** на отдельной ветке: `git checkout -b migration/dryrun`, выполнить шаги, откатить | DevOps | 3 | 14:00-17:00 | #6 | Ветка `migration/dryrun` существует, push работает в тестовый remote |
| 8 | **P0-05** | Сгенерировать `requirements.lock` через `pip-compile` | Backend | 2 | 09:00-11:00 | — | `requirements.lock` коммитится, `file python-setup.yml` его использует |
| 9 | **P0-07** | ADR-0001: «Adopt 13-agent hybrid signal architecture» | Writer | 2 | 11:00-13:00 | — | `file docs/adr/0001-hybrid-agents.md` в шаблоне MADR |
| 10 | **P0-01.c** | Починить ещё 2 broken tests (async timeout в `file tests/test_council.py`) | Backend | 3 | 14:00-17:00 | #2 | pytest count: 26 → 19 fail |

**Subtotal Tue: 14 ч**

**Standup:** показать MIGRATION_plan.md, push успешно идёт в dry-run remote, ADR-0001 готов.

---

### 🟦 Wed (2026-07-08) — «Secrets foundation»

| \# | ID | Задача | Owner | Часы | Время | Зависит от | Definition of Done |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 11 | **P1-01** | Создать `.env.prod.example` со всеми обязательными ключами | DevOps | 2 | 09:00-11:00 | — | Файл в репо, README секция «Setup prod env» |
| 12 | **P1-01.b** | `file tools/check_env.py` — fail-fast на отсутствующие ключи | DevOps | 1 | 11:00-12:00 | #11 | `python tools/check_env.py --prod` exit 1 без env, exit 0 с шаблоном |
| 13 | **P1-02** | SOPS+age интеграция: установить sops в CI, создать `file .sops.yaml` | DevOps | 4 | 13:00-17:00 | #11 | `sops --decrypt .env.prod.enc` работает локально и в CI |
| 14 | **P1-02.b** | k8s init-container скрипт: `file tools/secrets-init.sh` (decrypts SOPS на старте) | DevOps | 1 | 17:00-18:00 | #13 | Скрипт работает в `kind` локально, output в `/run/secrets/.env` |
| 15 | **P1-03** | `file core/auth/jwt.py`: RS256, `/auth/login`, `/auth/refresh`, JWKS endpoint | Backend | 4 | 09:00-13:00 | — | `pytest tests/test_jwt.py` зелёный, `/auth/login` выдаёт tokens |
| 16 | **P1-05** | Pydantic v2 schemas для top-3 endpoint'ов (`/signal`, `/backtest`, `/healthz`) | Backend | 3 | 14:00-17:00 | — | 422 на bad input, 200 на good input |
| 17 | **P3-01** | SLO/SLI черновик: latency, error rate, availability для 3 API | Writer | 2 | 14:00-16:00 | — | `file docs/SLO.md` черновик с 3 SLI определениями + error budget формулой |

**Subtotal Wed: 17 ч**

**Standup:** SOPS encrypt/decrypt roundtrip работает, JWT tokens выпускаются, 3 endpoint'а валидируют вход.

---

### 🟦 Thu (2026-07-09) — «Error handling & readiness»

| \# | ID | Задача | Owner | Часы | Время | Зависит от | Definition of Done |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 18 | **P1-08** | Глобальный error handler: JSON `{error_code, message, request_id, hint}` | Backend | 3 | 09:00-12:00 | — | `curl -X DELETE /api/v1/agent/nonexistent` → 404 JSON, нет stack trace |
| 19 | **P1-09** | Request-ID middleware: UUIDv7, прокидывается в логи/трейсы/метрики | Backend | 2 | 12:00-14:00 | — | Каждый ответ содержит `X-Request-ID`, grep по нему в logs находит 1 запись |
| 20 | **P1-13** | Разделить `/livez` и `/readyz`: liveness=process alive, readiness=DB+Redis+OTel up | Backend | 2 | 14:00-16:00 | — | `curl /livez` 200 даже при down DB; `curl /readyz` 503 при down Redis |
| 21 | **P1-12** | Graceful shutdown: SIGTERM handler в FastAPI и Flask | Backend | 2 | 16:00-18:00 | — | `kill -TERM` → 0 exit, in-flight requests завершаются |
| 22 | **P1-04** | Per-user rate limiting (через JWT subject claim) | Backend | 2 | 09:00-11:00 | #15 | 61-й запрос в минуту от user → 429 |
| 23 | **P1-14** | Убрать `subprocess.run` без `check=True/timeout` | Backend | 2 | 11:00-13:00 | — | `grep -rn "subprocess.run" core/ orchestration/` → все с `check=True, timeout=...` |
| 24 | **P1-11** | `print()` → `logger`: ruff rule T201, починить top-10 вхождений | Backend | 1 | 13:00-14:00 | — | `ruff check` 0 errors; `git grep "print(" core/ orchestration/ web/ | wc -l` &lt; 5 |
| 25 | **P1-13 (sess)** | Security hardening: SOPS+age secrets, JWT auth (P1-03), IP rate limit (P1-05), security headers middleware, RBAC+audit log | Backend | 8 | 14:00-22:00 | P1-03, P1-05 | PR #103 merged; 22/22 tests pass; `logs/audit.jsonl` пишется; `SecurityHeadersMiddleware` подключён в `health_endpoints.py` |

**Subtotal Thu: 14 ч**

**Standup:** Demo: `curl /readyz` при down Redis → 503, /livez → 200. SOPS-encrypted env real-time.

---

### 🟦 Fri (2026-07-10) — «Security hardening + Sprint review»

| \# | ID | Задача | Owner | Часы | Время | Зависит от | Definition of Done |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 25 | **P1-06** | CORS whitelist (не `*`): `ALLOWED_ORIGINS` env, применяется в `file web/app.py` + FastAPI middleware | Backend | 1 | 09:00-10:00 | — | `curl -H "Origin: evil.com"` → нет `Access-Control-Allow-Origin` |
| 26 | **P1-07** | Security headers middleware: HSTS, CSP, X-Frame-Options, Referrer-Policy, Permissions-Policy | Backend | 2 | 10:00-12:00 | — | `curl -I` показывает все 5 заголовков |
| 27 | **P1-15** | `secrets.compare_digest` для HMAC webhook-проверок | Backend | 1 | 12:00-13:00 | — | `grep -rn "==.*hmac|hmac.*==" web/ health_endpoints.py` → 0 |
| 28 | **P1-10** | OpenAPI/Redoc: `/docs`, `/redoc`, `/openapi.json` для FastAPI | Backend | 2 | 13:00-15:00 | #16 | Swagger UI рендерит все endpoints, schemas валидны |
| 29 | **P0-01.d** | Починить оставшиеся flaky async tests: timeout → 30s, добавить `pytest-timeout` | Backend | 2 | 15:00-17:00 | #10 | pytest: ≤ 15 fail (с 26 → 15 за неделю) |
| 30 | **Sprint Review** | Подготовка demo для команды: 30 мин скринкаст, summary | Backend + Writer | 1 | 17:00-18:00 | All W1 | Записано в `file docs/sprints/2026-W27_REVIEW.md` |

**Subtotal Fri: 9 ч**

**Sprint Review (17:00 Friday):**

- Demo: end-to-end flow login → signal → audit
- Burndown chart: 26 → 15 failing tests, 0 .bak files, secrets encrypted
- Retro: что пошло не так, что улучшить
- W2 preview: Phase 1 finish + Phase 2 start

---

### 🟩 Sat-Sun (2026-07-11 — 2026-07-12) — «Buffer / self-review»

> Только для критических блокеров. Если W1 идёт по плану — выходные свободны.
> Если что-то отстало — добиваем.

- 🟧 Buffer для P0-03 (если dry-run выявил неожиданные конфликты)
- 🟧 Buffer для P1-03 (если JWT-тесты упали)
- 🟧 Code review собственного кода
- 🟧 Документация: обновить README с новыми командами

---

## 📊 Сводка спринта

| День | Часы (план) | Ключевая поставка |
| --- | --- | --- |
| Mon | 9 | 26→21 failing tests, .bak удалены, branch protection |
| Tue | 14 | submodule план + dry-run push OK, requirements.lock, ADR-0001 |
| Wed | 17 | .env.prod.example, SOPS encrypt/decrypt, JWT выпуск, Pydantic schemas, SLO draft |
| Thu | 14 | error handler, request-id, /livez+/readyz, graceful shutdown, per-user rate limit |
| Fri | 9 | CORS, security headers, OpenAPI, 26→15 failing tests, Sprint Review |
| **Total** | **63 ч** | из 80 ч доступных → **78 % utilization**, 17 ч buffer |

**Все 17 буферных часов** — на code review, парное программирование (bus factor!), и непредвиденные блокеры.

---

## 🏁 Acceptance Criteria для всего спринта (W1 → GA)

### Обязательно (must-have)

- [ ] `pytest -q` показывает ≤ 15 fail (с 26 → −11 за неделю)

- [ ] `git push origin master` в корневой репо работает (после submodule dry-run fix)

- [ ] `python tools/check_env.py --prod` exit 0 при полном `.env.prod.enc`

- [ ] `sops --decrypt .env.prod.enc` работает в CI и в k8s init-container

- [ ] `curl -X POST /auth/login -d '{"user":"x","pass":"y"}'` → JWT tokens

- [ ] `curl /readyz` при down Redis → 503; `/livez` → 200

- [ ] `curl -I https://app/` показывает HSTS, CSP, X-Frame-Options

- [ ] `file docs/SLO.md` согласован командой

- [ ] `file docs/MIGRATION_submodules.md` существует, dry-run проверен

- [ ] `file docs/adr/0001-hybrid-agents.md` в формате MADR

### Желательно (nice-to-have)

- [ ] Per-user rate limit срабатывает на 61-м запросе

- [ ] `ruff check` и `bandit` 0 новых high

- [ ] OpenAPI UI доступен на `/docs`

- [ ] README обновлён с новыми командами

### Отложено в W2+

- [ ] Pen-test (P4-02)

- [ ] Tempo/Jaeger (P3-06)

- [ ] pgvector (P2-02)

- [ ] Sentry (P3-13)

- [ ] Telegram bot (P5-12)

---

## 🔗 Зависимости между задачами W1

```markdown
P0-01 ─┬─► P0-01.b ─► P0-01.c ─► P0-01.d
       │
P0-02 ─┤
       │
P0-04 ─┤ (независим)
       │
P0-06 ─┤
       │
P0-03 ─┴─► P0-03.b (dry-run)
       │
P0-05 ─┤
       │
P0-07 ─┤
       │
P1-01 ─┼─► P1-01.b
       │     │
       │     └─► P1-02 ─► P1-02.b (k8s init-container)
       │
       └─► P1-03 ─► P1-04 (per-user rate limit)
              │
              └─► P1-05 (Pydantic) ─► P1-10 (OpenAPI)
                     │
                     └─► P1-08 (error handler) ─► P1-09 (request-id)

P1-06, P1-07, P1-11, P1-12, P1-13, P1-14, P1-15 — независимые, могут идти параллельно
```

**Critical path:** P0-01 → P0-01.b → P0-01.c → P0-01.d (если не доделать тесты, ничего мержить нельзя)
**Second critical path:** P1-01 → P1-02 → P1-02.b (без секретов нельзя в прод)

---

## 📈 Burndown (как будем трекать)

Создать `file docs/sprints/2026-W27_BURNDOWN.md` с ежедневным обновлением:

| Метрика | Mon | Tue | Wed | Thu | Fri |
| --- | --- | --- | --- | --- | --- |
| Failing tests | 21 | 19 | 19 | 19 | **15** |
| Bandit high (новые) | 6 | 6 | 6 | 5 | **5** |
| Ruff errors | ? | ? | ? | ? | **0** |
| PR open / merged | 2/1 | 4/3 | 6/5 | 8/7 | **10/10** |
| AC выполнено (из 10 must) | 1 | 3 | 6 | 8 | **10** |

**Burnrate цель:** 2 AC в день, после Wed — ускорение (всё параллельно).

---

## 🚨 Риски спринта

| \# | Риск | Митигация |
| --- | --- | --- |
| W1-R1 | **Submodule dry-run выявит, что GitHub-репо удалено полностью** (не 404, а 410 Gone) | План Б: оставить как submodule, но force-push в новые GitHub-репо (создать заново с тем же именем) |
| W1-R2 | **JWT-библиотека конфликтует с существующей `file core/auth.py`** | План Б: P1-03 dual-mode (API_KEY + JWT) 2 недели, потом deprecate API_KEY |
| W1-R3 | **26 failing tests — на самом деле 30** (мы не все нашли) | Сначала полный collect-only, потом классификация |
| W1-R4 | **SOPS age-key теряется** (один ключ на всю команду) | Создать age-key в `1Password`, реплицировать в CI secret и в 2 личных keychains |
| W1-R5 | **P1-12 graceful shutdown ломает k8s probes** (закрывает socket до того, как endpoint отвечает) | План Б: 5-секундная задержка между SIGTERM и SIGKILL через `preStop` hook |

---

## 📞 Коммуникация

- **Daily standup:** 17:00 (Samara TZ), 15 мин, формат: вчера/сегодня/блокеры
- **Sprint Review:** Fri 17:00, 30 мин demo + 30 мин retro
- **Канал:** Telegram `asurdev-prod` (создать), или существующий `@1022845958`
- **PR policy:** каждый PR проходит self-review + 1 reviewer (asurdev self-approve для emergency-фиксов ≤ 5 LOC, иначе ждём mahaasur13-sys)
- **Daily update:** в конце дня обновить burndown chart, написать 3-5 строк в `file docs/sprints/2026-W27_DAILY_<date>.md`

---

## 🎬 Команда для старта (Mon 09:00)

```bash
# 1. Создать директорию для спринта
mkdir -p docs/sprints/2026-W27

# 2. Скопировать burndown-шаблон
cp docs/sprints/TEMPLATE_BURNDOWN.md docs/sprints/2026-W27_BURNDOWN.md

# 3. Убедиться, что pre-flight checks зелёные
cd /home/workspace/astrofin-sentinel-platform
python tools/healthcheck.py  # должен exit 0

# 4. Создать ветку спринта
git checkout -b sprint/W27-release-prep
git push -u origin sprint/W27-release-prep

# 5. Начать с P0-01
pytest --collect-only 2>&1 | tee /tmp/pytest_collect.log
# → классифицировать в tests/FAILING_TESTS.md
```

---

## 📎 Шаблон Daily Update (для burndown)

```markdown
## 2026-07-06 (Mon) — Day 1

### ✅ Done
- P0-01: pytest collect-only, FAILING_TESTS.md создан (26 fail → 5 broken imports)
- P0-02: 3 .bak файла удалены, .gitignore обновлён
- P0-04: release/1.0.0 ветка + protection

### 🔄 In Progress
- P0-01.b: фикс import errors (2/5 сделано)

### 🚧 Blockers
- async timeout в test_council.py — нужно увеличить pytest-timeout

### 📊 Burndown
- Failing tests: 26 → 21
- AC complete: 1/10
- Hours spent: 7/9

### 📝 Notes
SOPS-установка потребует sudo на CI-runner (Ubuntu 22.04), проверить с DevOps завтра.
```

---

> 📌 **Sprint Outcome (Sun EOD):**
> Production readiness **75 % → 85 %**.
> Push в root разблокирован.
> Секреты зашифрованы.
> API готов к JWT-миграции.
> Sprint 2 (W28) фокус: Phase 1 finish + Phase 2 start (TimescaleDB, pgvector, RLS).
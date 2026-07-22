# 🎫 AstroFin Sentinel — Sprint 1 Issue Generator (Phase 0 + начало Phase 1)

> **Sprint Window:** 2026-07-06 → 2026-07-12
> **Milestone:** `Sprint 1 (v1.0.0-prep)`
> **Всего issues:** 30
> **Формат:** готовые markdown-блоки для копирования в GitHub New Issue

## 📖 Как пользоваться

**Вариант A — ручной (5 мин на issue):**
1. Открой репо → Issues → New Issue
2. Скопируй блок **Issue Body** нужной задачи
3. Установи лейблы (указаны в метаданных) и milestone
4. Submit

**Вариант B — bulk через `gh` CLI (30 сек на issue):**
См. секцию «Bulk-команды для gh CLI» внизу файла.

**Вариант C — GitHub Projects / ProjectV2:**
Все issue можно добавить в один Project со следующими колонками: `Backlog → In Progress → Review → Done`.

---

# 🟥 PHASE 0 — Подготовка (7 issues)

## Issue #1 — P0-01: Расследовать 26 failing tests

**Labels:** `phase-0`, `critical`, `backend`, `testing`, `blocker`, `sprint-1`
**Assignee:** @asurdev
**Estimate:** 3 ч
**Milestone:** Sprint 1 (v1.0.0-prep)
**Depends on:** —

### Body

```markdown
## 🎯 Цель
Классифицировать 26 failing tests, найти корневые причины, починить top-3 broken imports, остальное перенести в tracked issue.

## 📋 Зачем
CI сейчас красный. Без зелёных тестов невозможно мерджить в `release/1.0.0`. PRR (P5-10) не сможет подписать go-live.

## 🔧 Шаги
1. `cd /home/workspace/astrofin-sentinel-platform`
2. `source venv/bin/activate  # если есть`
3. `pytest --collect-only -q 2>&1 | head -50` — собрать список
4. `pytest tests/ -x --tb=short 2>&1 | tee /tmp/test_run.log`
5. Создать `tests/FAILING_TESTS.md` с шаблоном:
   - [ ] Test ID | Error | Category (flaky/import/broken/regression) | Action
6. Категории:
   - **flaky** → создать отдельный issue, не блокер
   - **broken import** → починить (P0-01.b)
   - **regression** → смотреть git log, bisect
   - **async timeout** → известная проблема, отметить
7. Top-3 broken import — починить сразу (P0-01.b)
8. `git add tests/FAILING_TESTS.md && git commit -m "P0-01: document 26 failing tests"`

## ✅ Acceptance Criteria
- [ ] `tests/FAILING_TESTS.md` существует, заполнен на 100 %
- [ ] ≥ 5 tests помечены как flaky/import (фикс на этой неделе)
- [ ] Top-3 broken import починены
- [ ] `pytest -q tests/test_*.py 2>&1 | tail -1` показывает ≤ 23 fail (было 26)
- [ ] Коммит в ветке с тегом `P0-01`

## 🔗 Related
- P0-01.b (top-3 fixes)
- P3-12 (performance baseline — нельзя делать без green tests)
- P5-10 (PRR — блокер)
```

---

## Issue #2 — P0-01.b: Починить top-3 broken imports

**Labels:** `phase-0`, `critical`, `backend`, `testing`, `sprint-1`
**Assignee:** @asurdev
**Estimate:** 2 ч
**Depends on:** #1 (P0-01)

### Body

```markdown
## 🎯 Цель
Починить три самых частых broken imports, обнаруженных в P0-01.

## 🔧 Шаги
1. `grep -rn "ImportError" tests/ | head -10` — собрать кандидатов
2. `grep -rn "ModuleNotFoundError" tests/ | head -10` — кандидаты v2
3. Выбрать top-3 наиболее частых
4. Для каждого:
   - Понять, нужен ли модуль в `requirements.txt`
   - Добавить фикс (mock / new import / skip с reason)
5. `pytest -q tests/ 2>&1 | tail -1` — должно стать ≥ 21 fail (было 26)
6. `git add -A && git commit -m "P0-01.b: fix top-3 broken imports"`

## ✅ Acceptance Criteria
- [ ] `pytest -q` показывает ≤ 21 fail
- [ ] Коммит с тегом `P0-01.b`
- [ ] `git log --oneline | grep P0-01.b` присутствует
```

---

## Issue #3 — P0-02: Удалить .bak файлы и защитить .gitignore

**Labels:** `phase-0`, `critical`, `backend`, `git`, `security`, `sprint-1`
**Assignee:** @asurdev
**Estimate:** 1 ч
**Depends on:** —

### Body

```markdown
## 🎯 Цель
Удалить backup-файлы из репозитория (G20 — `audit.py.bak-006` потенциально содержит `VSELM_API_KEY` placeholder). Защитить репо от повторного попадания.

## 🔧 Шаги
1. `cd /home/workspace/astrofin-sentinel-platform`
2. `find . -name "*.bak*" -not -path "./.git/*" -not -path "./venv/*"` — найти все
3. `git log --all -- '*.bak*' | head -20` — проверить историю на секреты
4. **Если найдены реальные секреты** → немедленно rotate, НЕ просто удалять
5. `git rm --cached $(find . -name "*.bak*" -not -path "./.git/*")` — убрать из индекса
6. `find . -name "*.bak*" -not -path "./.git/*" -not -path "./venv/*" -delete` — удалить
7. Добавить в `.gitignore`:
   ```
   *.bak
   *.bak-*
   *.tmp
   *.swp
   *~
   ```
8. `git add -A && git commit -m "P0-02: remove .bak files, harden .gitignore"`
9. `git push origin master` — проверить, что push проходит

## ✅ Acceptance Criteria
- [ ] `git grep '\\.bak-'` возвращает 0 результатов
- [ ] `.gitignore` содержит `*.bak*`
- [ ] `git log --all -- '*.bak*' | grep -i "api_key\|password\|secret"` → 0
- [ ] Push в `master` работает (разблокировано)
- [ ] Коммит с тегом `P0-02`

## 🔗 Related
- G20 (AUDIT_V2)
- P1-02 (SOPS для будущих секретов)
```

---

## Issue #4 — P0-03: Submodule→subtree migration plan

**Labels:** `phase-0`, `critical`, `devops`, `git`, `infra`, `blocker`, `sprint-1`
**Assignee:** @mahaasur13-sys (DevOps)
**Estimate:** 4 ч
**Depends on:** —

### Body

```markdown
## 🎯 Цель
Написать пошаговый план миграции 4 из 5 submodule (404 на GitHub) в обычные подпапки (G22 — критический блокер для push).

## 🔧 Шаги
1. Прочитать `AUDIT_V2.md` раздел 7
2. Изучить `git submodule status` (должно быть 4 missing)
3. Создать `docs/MIGRATION_submodules.md` со структурой:
   - **Контекст**: что сломалось и почему
   - **Pre-flight checks**: backup, freeze code, notify team
   - **Пошаговые команды** для каждого submodule:
     - `git submodule deinit -f <name>`
     - `git rm -f <name>`
     - удалить строку из `.gitmodules`
     - `git rm --cached <name>` если нужно
     - перенести содержимое из `archive/`
   - **Dry-run** (создать ветку `migration/dryrun`)
   - **Real run** (после успешного dry-run)
   - **Rollback plan**
   - **Контакты** (кого уведомить, кому звонить)
4. Конкретные команды — лучше дать готовый shell-скрипт `tools/migrate_submodules.sh`
5. `git add docs/ tools/ && git commit -m "P0-03: submodule migration plan"`

## ✅ Acceptance Criteria
- [ ] `docs/MIGRATION_submodules.md` существует, разделы все заполнены
- [ ] `tools/migrate_submodules.sh` существует, syntax-checked (`bash -n`)
- [ ] Plan содержит конкретные команды (не абстракции)
- [ ] Rollback section присутствует
- [ ] Коммит с тегом `P0-03`

## 🔗 Related
- P0-03.b (dry-run)
- P5-13 (real migration)
- P5-11 (snapshot v5)
```

---

## Issue #5 — P0-03.b: Dry-run submodule migration

**Labels:** `phase-0`, `critical`, `devops`, `git`, `infra`, `sprint-1`
**Assignee:** @mahaasur13-sys
**Estimate:** 3 ч
**Depends on:** #4 (P0-03)

### Body

```markdown
## 🎯 Цель
Выполнить dry-run миграции submodule→subtree на отдельной ветке, доказать что push в GitHub не падает.

## 🔧 Шаги
1. `cd /home/workspace/astrofin-sentinel-platform`
2. `git checkout -b migration/dryrun`
3. Выполнить команды из `tools/migrate_submodules.sh` для ОДНОГО submodule (например, `roma-execution-bridge`)
4. `git status` — должно показать modified files
5. `git add -A && git commit -m "P0-03.b: dry-run migration of roma-execution-bridge"`
6. `git push origin migration/dryrun` — проверить
7. Создать test remote: `git remote add testlocal /tmp/test-repo.git && git push testlocal migration/dryrun` — проверить
8. Задокументировать результат в `docs/MIGRATION_submodules.md` → раздел «Dry-run результат»
9. `git checkout master && git branch -D migration/dryrun`

## ✅ Acceptance Criteria
- [ ] Push в remote проходит без ошибок
- [ ] Тестовый клон работает: `git clone /tmp/test-repo.git /tmp/test-clone && cd /tmp/test-clone && ls`
- [ ] Размер клона разумный (< 500 MB)
- [ ] Коммит с тегом `P0-03.b`
- [ ] Результат dry-run записан в docs

## ⚠️ Risk
Если dry-run упал — НЕ делать real run, эскалировать.

## 🔗 Related
- P5-13 (real run, через 4 недели)
```

---

## Issue #6 — P0-04: Создать release/1.0.0 + branch protection

**Labels:** `phase-0`, `high`, `devops`, `git`, `sprint-1`
**Assignee:** @mahaasur13-sys
**Estimate:** 1 ч
**Depends on:** —

### Body

```markdown
## 🎯 Цель
Создать `release/1.0.0` ветку, настроить branch protection (1 review + CI required).

## 🔧 Шаги
1. `cd /home/workspace/astrofin-sentinel-platform`
2. `git checkout master && git pull`
3. `git checkout -b release/1.0.0 && git push -u origin release/1.0.0`
4. GitHub → Settings → Branches → Add rule:
   - Branch name pattern: `release/1.0.0`
   - ☑ Require a pull request before merging (1 approval)
   - ☑ Require status checks to pass: `ci`, `quality-gate`, `secret-scan`
   - ☑ Require linear history
   - ☐ Allow force pushes (НЕ ставить)
   - ☐ Allow deletions (НЕ ставить)
5. Также защитить `master`:
   - Same as above, + require `release/1.0.0` branch up to date
6. Создать `BRANCH_PROTECTION.md` со скриншотами и настройками

## ✅ Acceptance Criteria
- [ ] Ветка `release/1.0.0` существует
- [ ] Branch protection active (попробовать push напрямую — должно отвергнуться)
- [ ] `BRANCH_PROTECTION.md` создан
- [ ] `master` тоже под защитой

## 🔗 Related
- Все остальные issues: PRы пойдут в `release/1.0.0`
```

---

## Issue #7 — P0-05: Зафиксировать requirements.lock

**Labels:** `phase-0`, `high`, `backend`, `deps`, `ci`, `sprint-1`
**Assignee:** @asurdev
**Estimate:** 2 ч
**Depends on:** —

### Body

```markdown
## 🎯 Цель
Сгенерировать reproducible `requirements.lock` через `pip-compile` и подключить его в CI (G13).

## 🔧 Шаги
1. `cd /home/workspace/astrofin-sentinel-platform`
2. `pip install pip-tools`
3. `pip-compile requirements.in --output-file requirements.lock --upgrade` (если `requirements.in` нет — создать: `cp requirements.txt requirements.in`)
4. `pip-sync requirements.lock` — установить точные версии
5. Обновить `.github/workflows/python-setup.yml`:
   ```yaml
   - name: Install dependencies
     run: |
       pip install pip-tools
       pip-sync requirements.lock
   ```
6. Удалить `uv.lock` если он неиспользуемый (или оставить — оба работают)
7. `git add requirements.in requirements.lock .github/workflows/python-setup.yml`
8. `git commit -m "P0-05: pin dependencies via requirements.lock"`

## ✅ Acceptance Criteria
- [ ] `requirements.lock` коммитится в репо
- [ ] CI использует `pip-sync requirements.lock` (не `pip install -r requirements.txt`)
- [ ] Fresh clone: `pip-sync requirements.lock` ставит те же версии
- [ ] Размер `requirements.lock` < 1 MB
- [ ] Коммит с тегом `P0-05`

## 🔗 Related
- P0-01 (тесты должны проходить с locked deps)
- P4-04 (pip-audit — будет читать из lock)
```

---

## Issue #8 — P0-06: Bandit sweep + classification

**Labels:** `phase-0`, `medium`, `security`, `sprint-1`
**Assignee:** Security Engineer (part-time)
**Estimate:** 2 ч
**Depends on:** —

### Body

```markdown
## 🎯 Цель
Прочитать 6 bandit high предупреждений (G14), классифицировать (true positive vs false positive), завести issue на фиксы.

## 🔧 Шаги
1. `cd /home/workspace/astrofin-sentinel-platform`
2. `bandit -r . -lll 2>&1 | tee /tmp/bandit.log`
3. Создать `docs/security/bandit-baseline.md`:
   ```markdown
   | # | File:Line | B-code | Description | Classification | Action |
   |---|-----------|--------|-------------|----------------|--------|
   | 1 | core/foo.py:42 | B303 | MD5 use | False positive (cache key, not security) | Add # nosec comment + link to issue |
   | 2 | ... | | | | |
   ```
4. Для каждого true positive — создать отдельный issue с `security` label
5. Для false positive — добавить `# nosec B<code>` с обоснованием
6. `git add docs/security/ && git commit -m "P0-06: bandit baseline + classification"`

## ✅ Acceptance Criteria
- [ ] `docs/security/bandit-baseline.md` создан, все 6 high классифицированы
- [ ] 0 remaining true positive (всё либо fixed, либо в issue)
- [ ] Коммит с тегом `P0-06`
- [ ] Follow-up issues созданы (если есть)

## 🔗 Related
- P4-03 (semgrep в CI)
- P4-04 (pip-audit)
```

---

## Issue #9 — P0-07: ADR-0001 «Adopt 13-agent hybrid signal architecture»

**Labels:** `phase-0`, `medium`, `docs`, `adr`, `sprint-1`
**Assignee:** @asurdev (Tech Writer)
**Estimate:** 2 ч
**Depends on:** —

### Body

```markdown
## 🎯 Цель
Зафиксировать архитектурное решение о 13-агентном совете с HYBRID_WEIGHTS в формате MADR (Markdown Architectural Decision Records).

## 🔧 Шаги
1. `cd /home/workspace/astrofin-sentinel-platform`
2. `mkdir -p docs/adr`
3. Создать `docs/adr/0001-hybrid-agents.md` по шаблону MADR:
   ```markdown
   # ADR-0001: Adopt 13-agent hybrid signal architecture as canonical

   * Status: accepted
   * Date: 2026-07-06
   * Deciders: @asurdev, @mahaasur13-sys
   * Consulted: -
   * Informed: -

   ## Context and Problem Statement
   [Почему 13 агентов, какие проблемы решает]

   ## Considered Options
   * Single LLM
   * 5-agent minimal
   * 13-agent hybrid ← выбрано
   * 30-agent polyagent

   ## Decision Outcome
   Chosen option: 13-agent hybrid. HYBRID_WEIGHTS = {...}.

   ### Positive Consequences
   - Hybrid signal: 4 источника (fundamental, quant, sentiment, astro)
   - Conflict resolution: astro vs fundamental+quant правило
   - ...

   ### Negative Consequences
   - Сложность orchestration
   - 13 * latency каждого = медленно
   - ...

   ## Pros and Cons of the Options
   [Таблица]

   ## Links
   - agents/_impl/ — реализация
   - orchestration/sentinel_v5.py — оркестратор
   - core/aspects.py — aspects engine
   ```
4. `git add docs/adr/ && git commit -m "P0-07: ADR-0001 hybrid-agents"`
5. Упомянуть в `AGENTS.md` раздел «AI Agent Rules» → «Architecture decisions»

## ✅ Acceptance Criteria
- [ ] `docs/adr/0001-hybrid-agents.md` создан по MADR-шаблону
- [ ] Содержит все 4 обязательные секции MADR
- [ ] Ссылается на конкретные файлы репо
- [ ] Упомянут в `AGENTS.md`
- [ ] Коммит с тегом `P0-07`

## 🔗 Related
- P4-12 (остальные ADR: pgvector, tempo, jwt, sops)
```

---

# 🟧 PHASE 1 — Quick Wins + API Hardening (21 issue)

## Issue #10 — P1-01: Production .env.prod.example + check_env.py

**Labels:** `phase-1`, `critical`, `devops`, `config`, `env`, `sprint-1`
**Assignee:** @mahaasur13-sys
**Estimate:** 3 ч
**Depends on:** #6 (P0-04 — protected ветка)

### Body

```markdown
## 🎯 Цель
Создать production-ready шаблон переменных окружения + автоматический чекер, который падает при отсутствии обязательных переменных (G1).

## 🔧 Шаги
1. `cd /home/workspace/astrofin-sentinel-platform`
2. Создать `.env.prod.example`:
   ```bash
   # Application
   APP_ENV=production
   APP_PORT=8050
   APP_WORKERS=4
   LOG_LEVEL=info

   # Database
   DATABASE_URL=postgresql://astrofin:***@postgres:5432/astrofin
   DATABASE_POOL_SIZE=20

   # Redis
   REDIS_URL=redis://redis:6379/0

   # Auth
   API_KEY=  # legacy, deprecated after P1-03
   JWT_SECRET=  # openssl rand -hex 32
   JWT_ALGORITHM=RS256
   JWT_ACCESS_TTL=900  # 15 min
   JWT_REFRESH_TTL=604800  # 7 days

   # Observability
   OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
   SENTRY_DSN=
   PROMETHEUS_PORT=9090

   # Storage
   S3_BACKUP_BUCKET=astrofin-prod-backups
   S3_ENDPOINT=https://storage.yandexcloud.net
   S3_ACCESS_KEY=
   S3_SECRET_KEY=

   # Security
   ALLOWED_ORIGINS=https://app.astrofin.io
   SENTRY_SAMPLE_RATE=0.1
   ```
3. Создать `tools/check_env.py`:
   - Читает `.env.prod` (или `os.environ`)
   - Проверяет наличие всех обязательных переменных
   - Проверяет формат (URL, port range, length)
   - Exit 1 если что-то отсутствует
4. `python tools/check_env.py --prod --strict`
5. Добавить в `.gitignore`: `.env.prod`, `.env.local`, `*.key`, `*.pem`
6. `git add .env.prod.example tools/check_env.py .gitignore`
7. `git commit -m "P1-01: prod env template + check_env.py"`

## ✅ Acceptance Criteria
- [ ] `.env.prod.example` содержит все переменные (с комментариями)
- [ ] `tools/check_env.py` валидирует наличие и формат
- [ ] `python tools/check_env.py --prod` exit 0 с заполненным `.env.prod`
- [ ] `python tools/check_env.py --prod` exit 1 с пустым `.env`
- [ ] `.gitignore` защищает секреты
- [ ] Коммит с тегом `P1-01`

## 🔗 Related
- P1-02 (SOPS использует этот env)
- P1-03 (JWT_* переменные)
```

---

## Issue #11 — P1-02: SOPS + age для секретов

**Labels:** `phase-1`, `critical`, `devops`, `security`, `secrets`, `sprint-1`
**Assignee:** @mahaasur13-sys
**Estimate:** 6 ч
**Depends on:** #10 (P1-01)

### Body

```markdown
## 🎯 Цель
Интегрировать `mozilla/sops` + `age` для шифрования `.env.prod` и k8s secrets. Dev пишет plaintext, CI шифрует, runtime расшифровывает (G1 — критический блокер).

## 🔧 Шаги
1. Установить: `apt-get install sops age` или `brew install sops age`
2. Сгенерировать age keypair: `age-keygen -o keys/age.prod.key` (коммитить **только** public part)
3. `sops --age $(cat keys/age.prod.pub) --encrypt --in-place .env.prod`
4. Создать `Makefile` targets:
   ```makefile
   .PHONY: secrets-decrypt secrets-encrypt secrets-edit
   secrets-decrypt:
   	sops --decrypt .env.prod > /tmp/.env.prod && cp /tmp/.env.prod .env.prod.dec
   secrets-encrypt:
   	sops --encrypt --in-place .env.prod
   secrets-edit:
   	sops .env.prod
   ```
5. Создать `k8s/sealed-secret.yaml` template (если используем k8s)
6. Добавить в `.github/workflows/deploy.yml` шаг:
   ```yaml
   - name: Decrypt secrets
     run: |
       echo "$SOPS_AGE_KEY" | base64 -d > /tmp/age.key
       sops --decrypt .env.prod > $RUNNER_TEMP/.env.prod
   ```
7. Создать `docs/SECRETS.md`:
   - Как добавить нового maintainer (нужен age.pub)
   - Как rotate master key
   - Как восстановить доступ при потере ключа
8. `git add .env.prod (encrypted) keys/age.prod.pub Makefile docs/SECRETS.md`
9. `git commit -m "P1-02: SOPS encryption for .env.prod"`

## ✅ Acceptance Criteria
- [ ] `.env.prod` зашифрован (cat → binary)
- [ ] `sops --decrypt .env.prod` возвращает plaintext (с правильным key)
- [ ] `make secrets-edit` открывает редактор и перешифровывает
- [ ] CI deploy step расшифровывает секреты
- [ ] `keys/age.prod.key` НЕ коммитится (только .pub)
- [ ] `docs/SECRETS.md` существует
- [ ] Коммит с тегом `P1-02`

## ⚠️ Risk
Потеря age.key = потеря всех секретов. Документировать и backup.

## 🔗 Related
- P2-05 (S3 backups credentials)
- P4-19 (secret rotation policy)
- P5-04 (multi-region DR — нужны одинаковые secrets в двух кластерах)
```

---

## Issue #12 — P1-03: JWT вместо статичного API_KEY

**Labels:** `phase-1`, `high`, `backend`, `api`, `security`, `sprint-1`
**Assignee:** @asurdev
**Estimate:** 8 ч
**Depends on:** #10 (P1-01)

### Body

```markdown
## 🎯 Цель
Реализовать JWT-аутентификацию с RS256, access (15 мин) + refresh (7 дн) токенами. Dual-mode с API_KEY на 2 недели (G5).

## 🔧 Шаги
1. `cd /home/workspace/astrofin-sentinel-platform`
2. `pip install PyJWT[crypto] python-jose[cryptography]`
3. Добавить в `requirements.in`: `PyJWT[crypto]==2.8.0`
4. Создать `core/auth/jwt.py`:
   ```python
   from jose import jwt
   from cryptography.hazmat.primitives import serialization
   from datetime import datetime, timedelta, timezone

   ALGORITHM = "RS256"
   ACCESS_TTL = timedelta(minutes=15)
   REFRESH_TTL = timedelta(days=7)

   def load_private_key():
       with open("keys/jwt.private.pem", "rb") as f:
           return serialization.load_pem_private_key(f.read(), password=None)

   def load_public_key():
       with open("keys/jwt.public.pem", "rb") as f:
           return serialization.load_pem_public_key(f.read())

   def issue_access_token(user_id: str, claims: dict) -> str:
       payload = {
           "sub": user_id,
           "type": "access",
           "iat": datetime.now(timezone.utc),
           "exp": datetime.now(timezone.utc) + ACCESS_TTL,
           **claims,
       }
       return jwt.encode(payload, load_private_key(), algorithm=ALGORITHM)

   def issue_refresh_token(user_id: str) -> str: ...
   def verify_token(token: str) -> dict: ...
   ```
5. Сгенерировать keypair: `openssl genrsa -out keys/jwt.private.pem 2048 && openssl rsa -in keys/jwt.private.pem -pubout -out keys/jwt.public.pem`
6. Создать эндпоинты `core/auth/routes.py`:
   - `POST /auth/login` (user, password → access + refresh)
   - `POST /auth/refresh` (refresh → new access)
   - `GET /.well-known/jwks.json` (public key для verify)
7. Обновить middleware: если `Authorization: Bearer ...` → JWT verify; если `X-API-Key: ...` → legacy (warn-log); иначе 401
8. Создать `core/auth/migrations/00XX_add_users.sql`:
   ```sql
   CREATE TABLE users (
     user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
     email TEXT UNIQUE NOT NULL,
     password_hash TEXT NOT NULL,
     roles TEXT[] DEFAULT ARRAY['user'],
     created_at TIMESTAMPTZ DEFAULT NOW(),
     disabled_at TIMESTAMPTZ
   );
   ```
9. Тесты `tests/test_auth_jwt.py`: issue, verify, expired, wrong-signature
10. `git add -A && git commit -m "P1-03: JWT auth with RS256, dual-mode with API_KEY"`

## ✅ Acceptance Criteria
- [ ] `POST /auth/login` возвращает access + refresh (15 мин / 7 дн)
- [ ] `Authorization: Bearer <token>` работает на protected эндпоинтах
- [ ] `X-API-Key: <key>` всё ещё работает (с warning-логом)
- [ ] Expired token → 401
- [ ] Wrong signature → 401
- [ ] JWKS endpoint возвращает public key
- [ ] `tests/test_auth_jwt.py` — 10/10 passing
- [ ] Коммит с тегом `P1-03`

## 🔗 Related
- P1-04 (per-user rate limit использует sub claim)
- P1-13 (livez/readyz — должны быть public)
- P4-19 (rotation policy)
```

---

## Issue #13 — P1-04: Per-user rate limiting

**Labels:** `phase-1`, `high`, `backend`, `api`, `rate-limit`, `sprint-1`
**Assignee:** @asurdev
**Estimate:** 3 ч
**Depends on:** #12 (P1-03)

### Body

```markdown
## 🎯 Цель
Расширить rate limiting с IP-only до per-user (по JWT sub claim) с fallback на IP.

## 🔧 Шаги
1. `cd /home/workspace/astrofin-sentinel-platform`
2. Открыть `core/rate_limit.py`
3. Изменить `key_func`:
   ```python
   def user_or_ip_key():
       from flask import request
       from core.auth.jwt import verify_token
       auth = request.headers.get("Authorization", "")
       if auth.startswith("Bearer "):
           try:
               claims = verify_token(auth[7:])
               return f"user:{claims['sub']}"
           except Exception:
               pass
       return f"ip:{request.remote_addr}"
   ```
4. Лимиты:
   - User (authenticated): 60 req/min
   - IP (anonymous): 600 req/min
   - Public endpoints (/livez, /readyz, /.well-known/*): exempt
5. Добавить 429 handler с retry-after
6. Тест `tests/test_rate_limit.py`:
   - 60 запросов с JWT → OK
   - 61-й → 429
   - 600 с IP → OK
   - 601-й → 429
7. `git add -A && git commit -m "P1-04: per-user rate limiting"`

## ✅ Acceptance Criteria
- [ ] Rate limit 60/min на user
- [ ] 429 при превышении (не 503)
- [ ] Retry-After header присутствует
- [ ] Тесты passing
- [ ] `/livez` и `/readyz` exempt
- [ ] Коммит с тегом `P1-04`
```

---

## Issue #14 — P1-05: Pydantic v2 input validation

**Labels:** `phase-1`, `high`, `backend`, `api`, `security`, `sprint-1`
**Assignee:** @asurdev
**Estimate:** 6 ч
**Depends on:** —

### Body

```markdown
## 🎯 Цель
Применить Pydantic v2 для валидации всех входных данных на FastAPI endpoints и `marshmallow` на Flask (где нельзя Pydantic).

## 🔧 Шаги
1. `cd /home/workspace/astrofin-sentinel-platform`
2. `pip install "pydantic>=2.0" pydantic-settings`
3. Создать `core/schemas/`:
   - `signal_request.py` (symbol: str, timeframe: Literal, horizon: int)
   - `backtest_request.py` (start, end, params: dict)
   - `user_create.py` (email, password: constr(min_length=12))
4. Для каждого FastAPI endpoint — добавить `request: SignalRequest` parameter
5. Для Flask — `marshmallow` schemas + `web/validators.py`
6. Глобальный handler для `ValidationError` → 422 с полями
7. Тесты: invalid input → 422, невалидный email → 422, oversize payload → 413
8. `git add -A && git commit -m "P1-05: Pydantic v2 + marshmallow validation"`

## ✅ Acceptance Criteria
- [ ] 100 % FastAPI endpoints принимают Pydantic models
- [ ] 422 на invalid input (не 500)
- [ ] Error response содержит field path
- [ ] Тесты: 5+ cases, all passing
- [ ] Коммит с тегом `P1-05`

## 🔗 Related
- P1-08 (error handler)
- P4-02 (pen-test — меньше шансов найти injection)
```

---

## Issue #15 — P1-06: CORS whitelist

**Labels:** `phase-1`, `high`, `backend`, `api`, `security`, `sprint-1`
**Assignee:** @asurdev
**Estimate:** 1 ч
**Depends on:** —

### Body

```markdown
## 🎯 Цель
Заменить `*` CORS на whitelist из env `ALLOWED_ORIGINS`.

## 🔧 Шаги
1. `cd /home/workspace/astrofin-sentinel-platform`
2. В `web/app.py` (Flask): `CORS(app, origins=os.environ["ALLOWED_ORIGINS"].split(","))`
3. В `health_endpoints.py` (FastAPI): `app.add_middleware(CORSMiddleware, allow_origins=os.environ["ALLOWED_ORIGINS"].split(","))`
4. Проверить что `ALLOWED_ORIGINS` есть в `.env.prod.example` (уже добавлен в P1-01)
5. Тест: запрос с не-whitelisted origin → CORS error в preflight
6. `git add -A && git commit -m "P1-06: CORS whitelist"`

## ✅ Acceptance Criteria
- [ ] `allow_origins=*` нигде не встречается
- [ ] `ALLOWED_ORIGINS` читается из env
- [ ] Preflight с плохим origin → отвергнут
- [ ] Коммит с тегом `P1-06`
```

---

## Issue #16 — P1-07: Security headers middleware

**Labels:** `phase-1`, `high`, `backend`, `api`, `security`, `sprint-1`
**Assignee:** @asurdev
**Estimate:** 2 ч
**Depends on:** —

### Body

```markdown
## 🎯 Цель
Добавить middleware, проставляющее HSTS, CSP, X-Frame-Options, Referrer-Policy, Permissions-Policy на все ответы.

## 🔧 Шаги
1. `cd /home/workspace/astrofin-sentinel-platform`
2. Создать `web/middleware.py`:
   ```python
   from starlette.middleware.base import BaseHTTPMiddleware

   class SecurityHeadersMiddleware(BaseHTTPMiddleware):
       async def dispatch(self, request, call_next):
           response = await call_next(request)
           response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
           response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'"
           response.headers["X-Frame-Options"] = "DENY"
           response.headers["X-Content-Type-Options"] = "nosniff"
           response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
           response.headers["Permissions-Policy"] = "geolocation=(), microphone=()"
           return response
   ```
3. Подключить в `health_endpoints.py`: `app.add_middleware(SecurityHeadersMiddleware)`
4. Аналог для Flask: `web/app.py` → `app.after_request`
5. Тест `tests/test_security_headers.py`: 5 проверок на headers
6. `git add -A && git commit -m "P1-07: security headers middleware"`

## ✅ Acceptance Criteria
- [ ] `curl -I http://app:8050/` показывает все 6 headers
- [ ] CSP не блокирует legit UI (проверить dash widgets)
- [ ] HSTS присутствует
- [ ] Тесты passing
- [ ] Коммит с тегом `P1-07`
```

---

## Issue #17 — P1-08: Глобальный error handler

**Labels:** `phase-1`, `high`, `backend`, `api`, `observability`, `sprint-1`
**Assignee:** @asurdev
**Estimate:** 3 ч
**Depends on:** #16 (P1-07 — request_id из middleware)

### Body

```markdown
## 🎯 Цель
Все ошибки → JSON `{error_code, message, request_id, hint}`. Stack traces — только в логи, не в ответы.

## 🔧 ШаSteps
1. `cd /home/workspace/astrofin-sentinel-platform`
2. Создать `web/errors.py`:
   ```python
   from fastapi import Request
   from fastapi.responses import JSONResponse
   import logging, traceback

   logger = logging.getLogger(__name__)

   async def global_error_handler(request: Request, exc: Exception):
       request_id = request.headers.get("X-Request-ID", "unknown")
       tb = traceback.format_exc()
       logger.error(f"[{request_id}] Unhandled exception", exc_info=True)
       return JSONResponse(
           status_code=500,
           content={
               "error_code": "INTERNAL_ERROR",
               "message": "An internal error occurred. Our team has been notified.",
               "request_id": request_id,
               "hint": "Please retry. If persists, contact support with this request_id.",
           },
       )
   ```
3. Подключить: `app.add_exception_handler(Exception, global_error_handler)`
4. Custom handlers для 401, 403, 404, 422, 429
5. Flask: `app.register_error_handler(500, ...)` с тем же форматом
6. Тест: `curl -X POST /signal` с broken input → 422 + JSON; `curl` с crafted error → 500 без stack trace
7. `git add -A && git commit -m "P1-08: global error handler"`

## ✅ Acceptance Criteria
- [ ] 4xx и 5xx → JSON с error_code, message, request_id
- [ ] Stack traces НЕ в response body
- [ ] Logs содержат полный traceback
- [ ] Тесты: 4 cases (400, 404, 422, 500)
- [ ] Коммит с тегом `P1-08`
```

---

## Issue #18 — P1-09: Request-ID middleware (UUIDv7)

**Labels:** `phase-1`, `high`, `backend`, `observability`, `api`, `sprint-1`
**Assignee:** @asurdev
**Estimate:** 2 ч
**Depends on:** —

### Body

```markdown
## 🎯 Цель
Middleware проставляет `X-Request-ID` (UUIDv7) на каждый запрос, прокидывает в логи, метрики, трейсы.

## 🔧 Шаги
1. `cd /home/workspace/astrofin-sentinel-platform`
2. `pip install uuid7` (или `uuid6` от rsprd)
3. Создать `web/middleware.py` (если не существует) → `RequestIDMiddleware`:
   ```python
   from uuid6 import uuid7
   from contextvars import ContextVar
   request_id_var: ContextVar[str] = ContextVar("request_id", default="")

   class RequestIDMiddleware(BaseHTTPMiddleware):
       async def dispatch(self, request, call_next):
           request_id = request.headers.get("X-Request-ID") or str(uuid7())
           request_id_var.set(request_id)
           response = await call_next(request)
           response.headers["X-Request-ID"] = request_id
           return response

   def get_request_id() -> str:
       return request_id_var.get()
   ```
4. Добавить filter в `core/logging.py`: `LogFilter` подставляет request_id в каждую запись
5. Тест: два запроса → разные X-Request-ID; в логах видно request_id; trace_id == request_id (для correlation)
6. `git add -A && git commit -m "P1-09: request ID middleware (UUIDv7)"`

## ✅ Acceptance Criteria
- [ ] Каждый response содержит `X-Request-ID`
- [ ] Каждый log line содержит `request_id=<uuid>`
- [ ] Тесты passing
- [ ] Коммит с тегом `P1-09`
```

---

## Issue #19 — P1-10: OpenAPI / Redoc для FastAPI

**Labels:** `phase-1`, `medium`, `backend`, `api`, `docs`, `sprint-1`
**Assignee:** @asurdev
**Estimate:** 3 ч
**Depends on:** #14 (P1-05)

### Body

```markdown
## 🎯 Цель
Включить встроенный OpenAPI для FastAPI; для Flask — apispec или вручную.

## 🔧 Шаги
1. FastAPI: добавить метаданные в `app = FastAPI(title="AstroFin Sentinel API", version="1.0.0", description="...")`
2. Уже доступно: `/docs` (Swagger UI), `/redoc`, `/openapi.json`
3. Добавить tags: `["auth", "signal", "backtest", "agents", "health"]`
4. Для каждого endpoint — `summary`, `description`, `responses={401: ..., 422: ...}`
5. Сохранить `openapi.json` → `docs/api/openapi.json` (для публикации)
6. Flask: установить `apispec==6.6.0`, создать `web/apispec.py` с маршрутами
7. `git add -A && git commit -m "P1-10: OpenAPI/Redoc docs"`

## ✅ Acceptance Criteria
- [ ] `/docs` показывает все endpoints
- [ ] `/redoc` показывает grouped по tags
- [ ] `/openapi.json` валидный (можно сохранить)
- [ ] Коммит с тегом `P1-10`

## 🔗 Related
- P4-13 (API docs site)
```

---

## Issue #20 — P1-11: print() → logger.info() sweep

**Labels:** `phase-1`, `medium`, `backend`, `hygiene`, `ci`, `sprint-1`
**Assignee:** @asurdev
**Estimate:** 2 ч
**Depends on:** —

### Body

```markdown
## 🎯 Цель
Заменить `print()` на `logger.info()` в `core/`, `orchestration/`, `web/`. Включить ruff T201.

## 🔧 Шаги
1. `cd /home/workspace/astrofin-sentinel-platform`
2. `ruff rule --select T201 --fix .` (если ruff установлен)
3. `grep -rn "print(" core/ orchestration/ web/ | grep -v "test_" | head -20`
4. Заменить вручную top-20 offenders:
   ```python
   # Было
   print(f"[agent] running {name}")
   # Стало
   logger.info("agent running", extra={"name": name})
   ```
5. В `pyproject.toml` → `[tool.ruff]` → `select = ["T201"]`
6. Запустить `ruff check .` — должно быть 0 errors
7. `git add -A && git commit -m "P1-11: replace print() with logger calls"`

## ✅ Acceptance Criteria
- [ ] `ruff check .` 0 errors
- [ ] `grep -rn "print(" core/ orchestration/ web/` → 0 (или только в docstring)
- [ ] Коммит с тегом `P1-11`
```

---

## Issue #21 — P1-12: Graceful shutdown (SIGTERM)

**Labels:** `phase-1`, `high`, `backend`, `api`, `reliability`, `sprint-1`
**Assignee:** @asurdev
**Estimate:** 3 ч
**Depends on:** —

### Body

```markdown
## 🎯 Цель
SIGTERM handler: in-flight requests завершаются, DB pool дренируется, exit 0.

## 🔧 Шаги
1. `cd /home/workspace/astrofin-sentinel-platform`
2. В `health_endpoints.py`:
   ```python
   import signal, asyncio
   from contextlib import asynccontextmanager

   @asynccontextmanager
   async def lifespan(app: FastAPI):
       # Startup
       yield
       # Shutdown
       await close_db_pool()
       await close_redis_pool()
       logger.info("Graceful shutdown complete")

   app = FastAPI(lifespan=lifespan, ...)
   ```
3. В `web/app.py` (Flask/Werkzeug): `signal.signal(signal.SIGTERM, graceful_shutdown)`
4. DB pool: `from db.session import engine; engine.dispose()` на shutdown
5. Redis: `from core.cache import redis_client; await redis_client.aclose()`
6. Тест: `kill -TERM <pid>` → in-flight запросы завершаются, exit 0 за < 30s
7. `git add -A && git commit -m "P1-12: graceful shutdown on SIGTERM"`

## ✅ Acceptance Criteria
- [ ] `kill -TERM <pid>` → exit 0, лог "Graceful shutdown complete"
- [ ] In-flight requests завершаются нормально (не 503)
- [ ] DB connection pool корректно закрывается
- [ ] Тесты passing
- [ ] Коммит с тегом `P1-12`
```

---

## Issue #22 — P1-13: /livez и /readyz разделение

**Labels:** `phase-1`, `high`, `backend`, `k8s`, `observability`, `sprint-1`
**Assignee:** @asurdev
**Estimate:** 2 ч
**Depends on:** —

### Body

```markdown
## 🎯 Цель
`/livez` = процесс жив (всегда 200); `/readyz` = DB+Redis+OTel готовы (503 при отказе). Это нужно для k8s (блокер P5-01 — canary deploy).

## 🔧 Шаги
1. `cd /home/workspace/astrofin-sentinel-platform`
2. В `health_endpoints.py`:
   ```python
   @app.get("/livez", status_code=200)
   async def liveness():
       return {"status": "alive"}

   @app.get("/readyz", status_code=200)
   async def readiness(response: Response):
       checks = {
           "db": await check_db(),
           "redis": await check_redis(),
           "otel": check_otel_exporter(),
       }
       if not all(checks.values()):
           response.status_code = 503
           return {"status": "not_ready", "checks": checks}
       return {"status": "ready", "checks": checks}
   ```
3. `/healthz` — оставить как комбо (для обратной совместимости)
4. K8s livenessProbe: `httpGet: /livez`; readinessProbe: `httpGet: /readyz`
5. Тест: `curl /readyz` при работающем Redis → 200; при `redis-cli shutdown` → 503
6. `git add -A && git commit -m "P1-13: split /livez and /readyz"`

## ✅ Acceptance Criteria
- [ ] `/livez` всегда 200
- [ ] `/readyz` 503 при отказе DB или Redis
- [ ] K8s probes в `home-cluster-iac/*.yaml` (если есть) обновлены
- [ ] Тесты passing
- [ ] Коммит с тегом `P1-13`

## 🔗 Related
- P5-01 (canary deploy)
- P5-02 (auto-rollback)
```

---

## Issue #23 — P1-14: subprocess safety

**Labels:** `phase-1`, `high`, `backend`, `security`, `sprint-1`
**Assignee:** @asurdev
**Estimate:** 3 ч
**Depends on:** —

### Body

```markdown
## 🎯 Цель
Найти и починить `subprocess.run(shell=True)` / `os.system()` / `shell=True` в коде.

## 🔧 Шаги
1. `cd /home/workspace/astrofin-sentinel-platform`
2. `grep -rn "shell=True\|os.system\|os.popen" core/ orchestration/ web/ | grep -v "test_"`
3. Для каждого находка:
   - `subprocess.run(f"echo {user_input}", shell=True)` → `subprocess.run(["echo", user_input], check=True, timeout=10)`
   - `os.system("rm -rf /tmp/x")` → `subprocess.run(["rm", "-rf", "/tmp/x"], check=True, timeout=30)`
4. `bandit -r . -lll 2>&1 | grep -i "subprocess\|shell"` — должно быть чисто
5. `git add -A && git commit -m "P1-14: subprocess hardening (no shell=True)"`

## ✅ Acceptance Criteria
- [ ] `grep -rn "shell=True" core/ orchestration/ web/` → 0
- [ ] `grep -rn "os.system" core/ orchestration/ web/` → 0
- [ ] `bandit -r .` без B602/B603 warnings
- [ ] Коммит с тегом `P1-14`
```

---

## Issue #24 — P1-15: secrets.compare_digest для HMAC

**Labels:** `phase-1`, `high`, `backend`, `security`, `sprint-1`
**Assignee:** @asurdev
**Estimate:** 1 ч
**Depends on:** —

### Body

```markdown
## 🎯 Цель
Все HMAC-проверки (webhook-секреты, signature) — `secrets.compare_digest()`, не `==`.

## 🔧 Шаги
1. `cd /home/workspace/astrofin-sentinel-platform`
2. `grep -rn "hmac.compare_digest\|hashlib.*==\|signature ==\|== signature" core/ web/ | grep -v "test_"`
3. Заменить `if sig == expected:` на `if secrets.compare_digest(sig, expected):`
4. `bandit -r . -lll 2>&1 | grep -i "B105\|B303"` — проверить
5. `git add -A && git commit -m "P1-15: timing-safe HMAC comparisons"`

## ✅ Acceptance Criteria
- [ ] `grep -rn "== \"sha256=\|== signature" core/ web/` → 0 (только `compare_digest`)
- [ ] `bandit` без timing-attack warnings
- [ ] Коммит с тегом `P1-15`
```

---

## Issue #25 — P1-02.b: SOPS-encrypted test (.env.prod.dec example)

**Labels:** `phase-1`, `high`, `devops`, `security`, `sprint-1`
**Assignee:** @mahaasur13-sys
**Estimate:** 2 ч
**Depends on:** #11 (P1-02)

### Body

```markdown
## 🎯 Цель
Создать зашифрованный `.env.prod` для staging окружения, чтобы разработчики могли тестировать SOPS-расшифровку.

## 🔧 Шаги
1. Скопировать `.env.prod.example` → `.env.prod.staging`
2. Заполнить тестовыми значениями
3. `sops --encrypt --in-place .env.prod.staging`
4. Коммит
5. `sops --decrypt .env.prod.staging | head -10` — проверить расшифровку
6. Добавить в `docs/SECRETS.md` раздел «Staging workflow»
7. `git add -A && git commit -m "P1-02.b: encrypted staging env example"`

## ✅ Acceptance Criteria
- [ ] `.env.prod.staging` коммитится (в зашифрованном виде)
- [ ] Расшифровка с dev key работает
- [ ] Коммит с тегом `P1-02.b`
```

---

## Issue #26 — P1-08.b: Error handler для Flask (web/app.py)

**Labels:** `phase-1`, `high`, `backend`, `api`, `observability`, `sprint-1`
**Assignee:** @asurdev
**Estimate:** 2 ч
**Depends on:** #17 (P1-08 — FastAPI handler)

### Body

```markdown
## 🎯 Цель
Параллельный Flask error handler в `web/app.py` (Dash dashboard) с тем же форматом.

## 🔧 Шаги
1. `cd /home/workspace/astrofin-sentinel-platform`
2. В `web/app.py`:
   ```python
   from werkzeug.exceptions import HTTPException
   import traceback, logging
   logger = logging.getLogger(__name__)

   @app.server.errorhandler(Exception)
   def handle_exception(e):
       request_id = flask.request.headers.get("X-Request-ID", "unknown")
       logger.error(f"[{request_id}] Unhandled", exc_info=True)
       return flask.jsonify({
           "error_code": "INTERNAL_ERROR",
           "message": str(e) if isinstance(e, HTTPException) else "Internal error",
           "request_id": request_id,
       }), getattr(e, "code", 500)
   ```
3. Тест: crafted error в Dash callback → JSON
4. `git add -A && git commit -m "P1-08.b: Flask error handler"`

## ✅ Acceptance Criteria
- [ ] Exception в Dash callback → JSON, не HTML
- [ ] Stack trace в логах, не в response
- [ ] Коммит с тегом `P1-08.b`
```

---

## Issue #27 — P1-12.b: Graceful shutdown для Dash

**Labels:** `phase-1`, `high`, `backend`, `reliability`, `sprint-1`
**Assignee:** @asurdev
**Estimate:** 2 ч
**Depends on:** #21 (P1-12)

### Body

```markdown
## 🎯 Цель
Dash-приложение (`web/app.py`) тоже корректно обрабатывает SIGTERM.

## 🔧 Шаги
1. `cd /home/workspace/astrofin-sentinel-platform`
2. В `web/app.py`:
   ```python
   import signal, sys
   def graceful_shutdown(signum, frame):
       logger.info("SIGTERM received, shutting down")
       # close DB pool, redis, etc.
       sys.exit(0)
   signal.signal(signal.SIGTERM, graceful_shutdown)
   signal.signal(signal.SIGINT, graceful_shutdown)
   ```
3. Тест: `kill -TERM <pid>` → exit 0
4. `git add -A && git commit -m "P1-12.b: Dash graceful shutdown"`

## ✅ Acceptance Criteria
- [ ] Dash реагирует на SIGTERM
- [ ] Exit code 0
- [ ] Коммит с тегом `P1-12.b`
```

---

## Issue #28 — P1-13.b: K8s probes в home-cluster-iac

**Labels:** `phase-1`, `high`, `devops`, `k8s`, `sprint-1`
**Assignee:** @mahaasur13-sys
**Estimate:** 2 ч
**Depends on:** #22 (P1-13)

### Body

```markdown
## 🎯 Цель
Обновить k8s deployment manifests в `home-cluster-iac/` чтобы использовать `/livez` и `/readyz`.

## 🔧 Шаги
1. `cd /home/workspace/astrofin-federation-stack` или `home-cluster-iac/`
2. Найти deployment yaml: `grep -rln "/healthz" deploy/`
3. Заменить:
   ```yaml
   livenessProbe:
     httpGet: { path: /healthz, port: 8050 }
     periodSeconds: 30
   readinessProbe:
     httpGet: { path: /healthz, port: 8050 }
     periodSeconds: 10
   ```
   на:
   ```yaml
   livenessProbe:
     httpGet: { path: /livez, port: 8050 }
     periodSeconds: 30
     failureThreshold: 3
   readinessProbe:
     httpGet: { path: /readyz, port: 8050 }
     periodSeconds: 5
     timeoutSeconds: 2
   ```
4. Применить локально в `kind`: `kubectl apply -f deploy/`
5. `git add -A && git commit -m "P1-13.b: k8s probes use /livez and /readyz"`

## ✅ Acceptance Criteria
- [ ] `/livez` и `/readyz` упоминаются в манифестах
- [ ] Liveness не падает при отказе Redis
- [ ] Readiness падает → pod удаляется из service endpoints
- [ ] Коммит с тегом `P1-13.b`

## 🔗 Related
- P5-01 (canary)
```

---

## Issue #29 — P1-04.b: Rate limit тесты в CI

**Labels:** `phase-1`, `medium`, `backend`, `testing`, `sprint-1`
**Assignee:** @asurdev
**Estimate:** 2 ч
**Depends on:** #13 (P1-04)

### Body

```markdown
## 🎯 Цель
Regression-тесты для rate limiting: добавить в CI чтобы перфоманс не деградировал.

## 🔧 Шаги
1. `cd /home/workspace/astrofin-sentinel-platform`
2. `tests/test_rate_limit.py` уже есть из P1-04
3. Добавить в `.github/workflows/ci.yml` job `rate-limit-test`:
   ```yaml
   rate-limit-test:
     runs-on: ubuntu-latest
     steps:
       - uses: actions/checkout@v4
       - name: Run rate limit tests
         run: |
           pip install -r requirements.lock
           pytest tests/test_rate_limit.py -v
   ```
4. `git add -A && git commit -m "P1-04.b: rate limit CI job"`

## ✅ Acceptance Criteria
- [ ] CI job `rate-limit-test` runs on every PR
- [ ] Тесты passing
- [ ] Коммит с тегом `P1-04.b`
```

---

## Issue #30 — P1-08.c: Errors documentation page

**Labels:** `phase-1`, `medium`, `backend`, `api`, `docs`, `sprint-1`
**Assignee:** @asurdev
**Estimate:** 2 ч
**Depends on:** #17 (P1-08)

### Body

```markdown
## 🎯 Цель
Страница `/docs/errors` со списком всех error_code, их семантикой и рекомендуемыми действиями клиента.

## 🔧 Шаги
1. `cd /home/workspace/astrofin-sentinel-platform`
2. Создать `web/routes/docs.py` (FastAPI)
3. Markdown-файл `docs/errors.md`:
   - Таблица error_code → message → action
4. Endpoint `GET /docs/errors` → отдаёт markdown с правильным content-type
5. Ссылка в `GET /` (если есть) или в `/docs` (OpenAPI)
6. `git add -A && git commit -m "P1-08.c: /docs/errors page"`

## ✅ Acceptance Criteria
- [ ] `GET /docs/errors` отдаёт markdown
- [ ] Содержит все error_code из API
- [ ] Коммит с тегом `P1-08.c`
```

---

# 🚀 Bulk-команды для `gh` CLI (быстрое создание всех 30 issues)

```bash
# 1. Установить gh и залогиниться: gh auth login
# 2. Запустить скрипт:
REPO="mahaasur13-sys/astrofin-sentinel-platform"

# Создать milestone
gh api repos/$REPO/milestones -f title="Sprint 1 (v1.0.0-prep)" -f due_on="2026-07-12T23:59:59Z"

# Создать labels (один раз)
for label in "phase-0:0e8a16" "phase-1:fbca04" "critical:b60205" "high:d93f0b" "medium:fbca04" "backend:1d76db" "devops:5319e7" "security:b60205" "testing:0e8a16" "sprint-1:cccccc" "blocker:b60205" "docs:0075ca" "api:bfd4f2"; do
  name="${label%%:*}"; color="${label##*:}"
  gh label create "$name" --color "$color" --repo "$REPO" 2>/dev/null || true
done

# Создать issue (пример для Issue #1)
gh issue create --repo "$REPO" \
  --title "[P0-01] Расследовать 26 failing tests" \
  --body-file issues/P0-01.md \
  --label "phase-0,critical,backend,testing,blocker,sprint-1" \
  --milestone "Sprint 1 (v1.0.0-prep)" \
  --assignee "asurdev"

# ... повторить для каждой issue
```

---

# 📂 Рекомендуемая структура каталогов

```
astrofin-sentinel-platform/
├── docs/
│   ├── adr/
│   │   └── 0001-hybrid-agents.md
│   ├── MIGRATION_submodules.md
│   ├── SECURITY.md  ← будущее
│   ├── errors.md
│   ├── SLO.md  ← будущее
│   └── ...
├── core/
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── jwt.py
│   │   └── routes.py
│   ├── rate_limit.py
│   ├── tracing.py
│   ├── logging.py
│   └── ...
├── web/
│   ├── app.py
│   ├── middleware.py
│   ├── errors.py
│   ├── routes/
│   │   └── docs.py
│   └── ...
├── tests/
│   ├── FAILING_TESTS.md
│   ├── test_auth_jwt.py
│   ├── test_rate_limit.py
│   ├── test_security_headers.py
│   └── ...
├── tools/
│   ├── check_env.py
│   ├── migrate_submodules.sh
│   └── diag/
└── .env.prod.example
```

---

# 📊 Сводка по Sprint 1

| Phase | Issues | Часы (труд.) | Owners |
|-------|-------:|-------------:|--------|
| Phase 0 | 9 (Issue #1–#9) | 20 | Backend + DevOps + Security + Writer |
| Phase 1 | 21 (Issue #10–#30) | 43 | Backend + DevOps |
| **ИТОГО** | **30** | **63 ч** | смешанная команда |

**Capacity:** 80 ч → 17 ч buffer (21 %)
**Критический путь:** #1 → #2 → #10 → #11 (тесты → .env → SOPS)
**Readiness delta:** +10 % (с ~75 % до **~85 %**)

---

> 📌 **Этот файл — рабочий артефакт для спринта.** После завершения недели перенести в `BACKLOG_STATUS.md` burndown chart.

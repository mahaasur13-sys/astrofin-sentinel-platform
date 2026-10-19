# Гайд: подключение чата Sentinel к ROMA (DeepSeek + tenant-ключ)

Пошаговая навигация для новичков. Делайте шаги по порядку, не пропуская проверки.

Цель: чат лендинга ходит в **ROMA** (`POST /api/chat/stream`) через серверную прослойку
`chat_shim.py`, которая добавляет tenant-ключ на сервере. Ключи не попадают в JS/URL/историю.

Нужно сделать две вещи:
1. Заменить невалидный ключ DeepSeek у ROMA и перезапустить ROMA.
2. Дать tenant `X-API-Key` в `.env` лендинга (для прослойки).

---

## Часть 1. Заменить ключ DeepSeek у ROMA

### Шаг 1.1 — Откройте файл

```bash
nano ~/roma-execution-bridge/.env
```

### Шаг 1.2 — Найдите строку 31

Она выглядит так (ключ здесь — пример, у вас свой):

```
DEEPSEEK_API_KEY=<your-deepseek-key>
```

Этот ключ **невалиден** (проверено: DeepSeek отвечает `401 "api key …82e7 is invalid"`).

### Шаг 1.3 — Замените на рабочий ключ

Ваш рабочий ключ — тот, благодаря которому прокси `8787` отвечает `OK` (а не ошибкой).
Если не помните его значение, найдите его:

```bash
# в том же терминале, где запускали deepseek_proxy.py:
echo $DEEPSEEK_API_KEY
```

Правила записи (важно):
- Без кавычек, без пробелов, без `export`.
- Только `DEEPSEEK_API_KEY=<your-deepseek-key>...` в одну строку.
- Следите, чтобы не осталось старого хвоста `…82e7`.

### Шаг 1.4 — Сохраните и закройте

- `Ctrl+O` → `Enter` (сохранить)
- `Ctrl+X` (выйти)

---

## Часть 2. Перезапустить ROMA

ROMA читает `.env` **только при старте**, поэтому просто сохранить файл недостаточно —
нужно перезапустить процесс.

### Шаг 2.1 — Поймите, как ROMA у вас запущен

```bash
ps aux | grep -E 'uvicorn|main:app' | grep -v grep
```

и (если используется supervisor):

```bash
sudo supervisorctl status
```

### Шаг 2.2 — Перезапуск по способу запуска

**Вариант A — запущен вручную через `make run-bridge` (uvicorn в отдельном терминале):**

1. Перейдите в тот терминал, где крутится ROMA.
2. Нажмите `Ctrl+C`.
3. Запустите снова:

```bash
cd ~/roma-execution-bridge
source .venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8080
```

> Примечание: флаг `--reload` следит только за `.py`-файлами, а не за `.env`,
> поэтому перезапуск руками обязателен.

**Вариант B — запущен через supervisor:**

```bash
sudo supervisorctl restart roma-execution-bridge
```

**Вариант C — не уверены, как запущен:**

Проверьте оба варианта по порядку: сначала `sudo supervisorctl status`. Если он выводит
`roma-execution-bridge`, используйте Вариант B. Иначе — Вариант A.

### Шаг 2.3 — Убедитесь, что ROMA поднялся

```bash
curl -s http://127.0.0.1:8080/health
```

Должно вернуть JSON со `"status":"ok"` и `"version":"2.1.0"`.

---

## Часть 3. Проверить, что чат ROMA заработал

```bash
curl -s -N -X POST http://127.0.0.1:8080/api/chat/stream \
  -H 'Content-Type: application/json' \
  -d '{"message":"Say exactly: OK"}'
```

- ✅ Успех: ответ приходит потоком и содержит текст (`OK` или что-то ещё), а **НЕ**
  `«DeepSeek временно недоступен»`.
- ❌ Если снова «недоступен» — ключ в `.env` не подхватился. Проверьте шаг 1.2–1.4
  и что ROMA действительно перезапущен (шаг 2.2).

---

## Часть 4. Дать tenant `X-API-Key`

Прослойка `chat_shim.py` добавляет заголовок `X-API-Key`, по которому ROMA резолвит
`tenant_id` и подтягивает живые данные (баланс, usage, gate). Ключ хранится **только на
сервере** в `.env` лендинга.

### Шаг 4.1 — Поймите, какой у вас ключ

Tenant-ключ — это обычная строка (например `sk-...` или длинный hex), которая
принадлежит одному тенанту в ROMA. ROMA хранит не сам ключ, а его **sha256-хэш**.

### Шаг 4.2 — Вариант A: у вас уже есть tenant-ключ

Если ключ у вас есть (из Dashboard / Telegram `/get_key` / почты) — просто впишите его
в `.env` лендинга:

```bash
nano ~/astrofin-sentinel-platform/.env
```

Найдите строку и впишите значение (без кавычек, без пробелов):

```
ROMA_API_KEY=ваш-tenant-ключ
```

### Шаг 4.3 — Вариант B: выпустить новый tenant-ключ (если нет готового)

1. Придумайте ключ, например:

```bash
MYKEY="sk-roma-$(openssl rand -hex 24)"
echo "$MYKEY"
```

2. Посчитайте его хэш (именно он хранится в БД):

```bash
python3 -c "import hashlib,sys; print(hashlib.sha256(sys.argv[1].encode()).hexdigest())" "$MYKEY"
```

3. Посмотрите своих тенантов:

```bash
sudo -u postgres psql -d astrofin -c "SELECT id, name, plan FROM tenants LIMIT 10;"
```

4. Привяжите ключ к нужному тенанту (подставьте хэш из шага 2 и id из шага 3):

```bash
sudo -u postgres psql -d astrofin -c \
  "UPDATE tenants SET api_key_hash='<хэш>' WHERE id='<tenant-id>';"
```

5. Впишите **сам ключ** (`$MYKEY` из шага 1) в `.env` лендинга:

```
ROMA_API_KEY=sk-roma-<то, что вывел echo $MYKEY>
```

### Шаг 4.4 — Проверьте, что ключ резолвится в тенанта

```bash
curl -s http://127.0.0.1:8080/usage -H "X-API-Key: $ROMA_API_KEY"
```

- ✅ Успех: вернётся JSON с `"tenant_id": ...` и данными usage.
- ❌ `401/403` — ключ не резолвится: проверьте шаг 4.3 (хэш и id).

---

## Часть 5. Финальное включение (после того, как оба ключа готовы)

1. Запустите прослойку (в отдельном терминале):

```bash
cd ~/astrofin-sentinel-platform/artifacts/landing
python3 chat_shim.py
```

2. Проверьте сквозной путь:

```bash
curl -s -X POST http://127.0.0.1:8788/chat \
  -H 'Content-Type: application/json' \
  -d '{"messages":[{"role":"user","content":"Say exactly: OK"}]}'
```

Должно вернуть `{"content": "..."}` с ответом DeepSeek через ROMA.

3. Затем (это делает агент) — переключить `ai_chat.js` с `8787` на `8788` и остановить
   старый `deepseek_proxy.py`.

---

## Чек-лист безопасности

- [ ] Ключ DeepSeek и tenant-ключ — **только** в `.env`, не в JS, не в URL, не в истории чата.
- [ ] У каждого запроса к ROMA есть `X-API-Key` (добавляет прослойка на сервере).
- [ ] Без ключа / с чужим ключом → `401/403`, чужих данных не видно.
- [ ] Read-only (`GET /usage`, `GET /billing/balance`, `GET /decisions`) и action
      (`POST /submit`, `POST /v1/decisions`) разделены; объяснения идут через dry-run
      `POST /v1/decisions/evaluate`.
- [ ] Чат остаётся explain-only и не выдумывает цифры (если живых данных нет — пишет
      «static demo — live state not connected»).

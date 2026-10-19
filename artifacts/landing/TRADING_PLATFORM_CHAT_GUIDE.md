# Гайд: научить «Sentinel — your assistant» отвечать по торговой платформе

Пошаговая навигация для новичков. Цель — чтобы чат лендинга, кроме ROMA
(биллинг/задачи/gate), отвечал и по **торговой платформе**: агенты, ансамблевый
сигнал, рыночный режим, астро-тайминг.

## Карта: три слоя, которые видит чат

| Слой | Порт | Что даёт | Сейчас |
|------|------|----------|--------|
| Прокси Sentinel (`deepseek_proxy.py`) | 8787 | персона + DeepSeek + explain-only | ✅ работает |
| ROMA (execution/billing) | 8080 | tenant, баланс, лимиты, gate | ✅ подключён |
| **Platform API (трейдинг)** | **8000** | агенты, ensemble, режим, астро | ❌ не запущен |

Нужно: запустить Platform API и добавить его данные в прокси.

---

## Часть 1. Запустить Platform API (порт 8000)

Код платформы лежит в отдельном дереве `~/Projects/astrofin-sentinel-platform`.

```bash
cd ~/Projects/astrofin-sentinel-platform
source .venv/bin/activate
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

Проверка, что поднялся:

```bash
curl -s http://127.0.0.1:8000/health
```

Должно вернуть `{"status":"ok","version":"0.4.0"}`.

> Если порт занят или нужен другой — поменяйте `--port` и не забудьте поправить
> `PLATFORM_URL` в Части 4.

---

## Часть 2. Разобраться с ключом Platform API

Platform API защищён `X-API-Key` (модуль `core/auth.py`).

По умолчанию (без `.env`-правок):
- `require_auth = true`
- `api_key = <your-api-key>`

То есть прямо сейчас рабочий ключ — **`<your-api-key>`**. Проверьте:

```bash
curl -s http://127.0.0.1:8000/api/v1/dashboard -H "X-API-Key: <your-api-key>"
```

- ✅ Вернётся JSON с `agents`, `ensemble`, `regime` → ключ работает.
- ❌ `401/403` → ключ другой. Смотрите/задайте его в `~/Projects/astrofin-sentinel-platform/.env`:

```
API_KEY=ваш-ключ
REQUIRE_AUTH=false   # только если хотите отключить проверку (локально)
```

---

## Часть 3. Что станет «живым» (какие эндпоинты)

| Эндпоинт | Метод | Что отдаёт |
|----------|-------|------------|
| `/api/v1/dashboard` | GET | 13 агентов (вес/сигнал/уверенность), `ensemble` (signal, confidence, buy/sell/hold), `regime` (bull/bear/sideways/high_vol/anomaly), `safety_gate` |
| `/api/v1/agent/run` | POST | анализ агентов по `{agentId, prompt}` |
| `/api/v1/astro/aspects` | GET | текущие планетарные аспекты |
| `/api/v1/astro/interpretation` | GET | вердикт (favourable/caution/avoid), мухурта, накшатра |

Для чата достаточно **`/api/v1/dashboard`** (основной сигнал) и
**`/api/v1/astro/interpretation`** (тайминг). Оба read-only.

---

## Часть 4. Подключить данные к прокси

### Шаг 4.1 — добавить в `.env` лендинга

```bash
nano ~/astrofin-sentinel-platform/.env
```

Добавьте две строки (после `ROMA_URL=...`):

```
PLATFORM_URL=http://127.0.0.1:8000
PLATFORM_API_KEY=<your-api-key>
```

### Шаг 4.2 — добавить в `deepseek_proxy.py` загрузку и выборку

Рядом с `ROMA_BASE = ...` добавьте:

```python
PLATFORM_BASE = _env_value("PLATFORM_URL") or "http://127.0.0.1:8000"
PLATFORM_API_KEY = _env_value("PLATFORM_API_KEY") or "<your-api-key>"
```

И функцию выборки (после `fetch_live_state`):

```python
def _platform_call(path, body=None):
    headers = {"X-API-Key": PLATFORM_API_KEY, "Content-Type": "application/json"}
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(PLATFORM_BASE + path, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_platform_state():
    state = {}
    for name, path, body in (
        ("dashboard", "/api/v1/dashboard", None),
        ("astro", "/api/v1/astro/interpretation", None),
    ):
        try:
            state[name] = _platform_call(path, body)
        except Exception:
            state[name] = None
    return state if any(state.values()) else None
```

### Шаг 4.3 — впрыснуть в системный промпт

В `do_POST`, там где собирается `system_content` (после блока `live`), добавьте:

```python
        platform = fetch_platform_state()
        if platform:
            system_content += (
                "\n\nCURRENT TRADING PLATFORM STATE (from Platform API, read-only):\n"
                + json.dumps(platform, ensure_ascii=False)
                + "\nUse these real values when the user asks about the trading platform, "
                "strategy, signal, regime or timing. Never invent them."
            )
```

---

## Часть 5. Проверка

```bash
# 1. Синтаксис
cd ~/astrofin-sentinel-platform/artifacts/landing
python3 -m py_compile deepseek_proxy.py

# 2. Перезапустить прокси (в его терминале): Ctrl+C, затем
python3 deepseek_proxy.py
# в логе должно появиться: live-state: ON

# 3. Сквозной тест
curl -s -X POST http://127.0.0.1:8787/chat \
  -H 'Content-Type: application/json' \
  -d '{"messages":[{"role":"user","content":"What is the current trading signal and regime? Be brief."}]}'
```

Ответ должен опираться на реальные `ensemble`/`regime` из `/api/v1/dashboard`,
а не на выдуманные числа.

---

## Честные ограничения (важно, чтобы не врать)

1. **«Decision 78% / Coherence 64%» как отдельного поля в API нет.** Этот процент
   считается в оркестраторе (`orchestration/sentinel_v5.py`), а не отдаётся
   эндпоинтом `/api/v1/dashboard`. Эндпоинт даёт **агентов + ensemble + regime +
   safety_gate** — вот это чат и должен цитировать как живое. Не заставляйте чат
   «показывать 78%» — это будет та же красивая ложь, от которой мы уходили.
2. **Некоторые ответы Platform API содержат русский текст** (например
   `/api/v1/agent/run` и `/api/v1/astro/interpretation`). Системный промпт Sentinel
   уже требует «English only», но если нужно — можно чистить/переводить в прокси.
3. **Первый вызов `/api/v1/dashboard` может быть медленным** — эндпоинт на лету
   гоняет агентов Gann/Bradley/Elliot и тянет цену из CoinGecko. Держите таймаут
   побольше (в коде выше — 10 с).

---

## Чек-лист

- [ ] Platform API запущен (`/health` → ok), порт 8000.
- [ ] `X-API-Key` для Platform API известен (`<your-api-key>` или свой).
- [ ] `PLATFORM_URL` и `PLATFORM_API_KEY` добавлены в `.env` лендинга.
- [ ] `deepseek_proxy.py` тянет `/api/v1/dashboard` + `/api/v1/astro/interpretation`.
- [ ] Прокси перезапущен (`live-state: ON`).
- [ ] Чат отвечает по платформе **живыми** значениями, без выдуманных 78/64.
- [ ] Ответ по-английски, explain-only, без размещения сделок.

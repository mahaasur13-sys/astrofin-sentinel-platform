# ADD-2026-09-I1: Jev-клиент через OpenRouter Decisions API

**Статус:** принято к реализации (родитель: ADD-2026-09 rev 3, Приложение A пп.1–2).
**Слово владельца:** шлюз = OpenRouter · модель = `typesafe/jev-1.13` (ПИН).

## Решение

1. **Шлюз** — OpenRouter Decisions API (β): `POST https://openrouter.ai/api/alpha/decisions`.
   Запрещено: OpenAI-совместимый `/chat/completions`, `GET /api/v1/models` (типы `typesafe/*` не листингуются), `POST /v1/systemone` (второй surface для TypeSafe SDK), прямой `api.typesafe.ai`.
2. **Пин модели** — `typesafe/jev-1.13`; `typesafe/jev-latest` **запрещён** (механически, в коде).
3. **Ключ** — переиспользуется существующий `OPENROUTER_API_KEY` (surface: `core.settings.Settings.jev_api_key`, `validation_alias="OPENROUTER_API_KEY"`). Отдельный `JEV_API_KEY` не заводится.
4. **Пороги** (per-primitive, значения-заглушки до калибровки S-1) — канон `docs/decisions/jev-agent-canon.json`:
   `choice 0.7 · noul 0.8 · score 0.7`. Парити `settings.jev_thresholds == canon` проверяется тестом.
5. **Отказ от LiteLLM/LangChain** — в дереве отсутствуют; клиент на `httpx` + `pydantic` (без новых зависимостей).
6. **Fail-closed** — любая не-2xx/редирект/таймаут/невалидная схема/переполнение 32K/чужой хост/не-пин модели → `JevError`; «разрешено по умолчанию» не существует.
7. **Сеть** — редиректы не следуются; допустимые хосты: `openrouter.ai` + loopback (тесты); тесты — только fake-server, live-вызовов в CI нет.

## Файлы (вайтлист)

- `core/jev_client.py` (новый) — `get_jev_client()` + `JevClient.decide()`.
- `core/settings.py` — только поля `jev_*`.
- `.env.example` — зеркало имён (без значений).
- `tests/unit/test_jev_client.py` (новый).
- `docs/decisions/jev-agent-canon.json` + этот документ.

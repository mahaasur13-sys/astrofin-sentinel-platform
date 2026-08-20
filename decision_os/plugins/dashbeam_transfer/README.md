"""
DecisionOS v2.0 — Plugin Architecture
=====================================

«Всё — плагин»

DecisionOS Core — минимальное ядро (PluginManager, HookSystem, Sandbox, Registry, ThoughtTracer).
Любой функционал подключается как плагин.

## Архитектура

```
DecisionOS Core (минимальное ядро)
        │
        ▼
Plugin Manager (жизненный цикл)
        │
   ┌────┼────┐
   │    │    │
Sandbox  PluginLoader  Registry
   │
   ▼
Активные плагины:
• policy-engine       — Policy Engine
• decision-gate       — Decision Gate
• crypto-payments     — Криптоплатежи (Monero, USDT, BTC)
• crypto-wallets      — Кошельки (Monero view-only + subaddresses)
• support-chat        — Поддержка (WebSocket + тикеты)
• dashbeam-transfer   — P2P-передача файлов (Iroh + QUIC)
• menu                — Боковое меню
• dashboard           — Дашборд
• settings            — Настройки
• community/*         — Плагины сообщества
```

## Структура папок

```
decision-os/
├── core/
│   ├── __init__.py          # Minimal kernel exports
│   ├── hook_system.py       # Hook System — точки расширения
│   ├── plugin_manager.py    # Plugin Manager — install/load/enable/disable
│   ├── plugin_registry.py   # Plugin Registry — manifests
│   ├── sandbox.py           # Sandbox — изоляция
│   └── thought_tracer.py    # Thought Tracer — запись мышления
├── plugins/
│   ├── dashbeam-transfer/
│   │   ├── manifest.json    # Манифест плагина
│   │   └── main.py          # Реализация
│   └── builtin/
│       ├── policy-engine/
│       │   ├── manifest.json
│       │   └── main.py
│       ├── decision-gate/
│       │   ├── manifest.json
│       │   └── main.py
│       ├── crypto-payments/
│       │   ├── manifest.json
│       │   └── main.py
│       ├── crypto-wallets/
│       │   ├── manifest.json
│       │   └── main.py
│       ├── support-chat/
│       │   ├── manifest.json
│       │   └── main.py
│       ├── plugin-system/
│       │   ├── manifest.json
│       │   └── main.py
│       ├── menu/
│       │   ├── manifest.json
│       │   └── main.py
│       ├── dashboard/
│       │   ├── manifest.json
│       │   └── main.py
│       └── settings/
│           ├── manifest.json
│           └── main.py
├── api/
│   └── main.py              # FastAPI API Gateway
├── cli/
│   └── main.py              # CLI (decisionos list|install|status)
├── sandbox/                 # WebAssembly / WASI sandbox
├── hooks/                   # Hook definitions
├── registry/                # Plugin registry storage
├── thought-tracer/          # Thought tracing
├── tests/
│   ├── __init__.py
│   └── test_core.py         # Full test suite
└── README.md                # ← этот файл
```

## Манифест плагина (обязательный формат)

```json
{
  "id": "dashbeam-transfer",
  "name": "DashBeam P2P Transfer",
  "version": "1.0.0",
  "description": "Безопасная P2P-передача файлов через Iroh + QUIC",
  "author": "DecisionOS Team",
  "permissions": [
    "support:file:send_p2p",
    "audit:export:p2p",
    "dashbeam:ticket:create",
    "dashbeam:file:send",
    "dashbeam:relay:configure",
    "dashbeam:wallet:share_view_only"
  ],
  "hooks": ["before_message_send", "after_ticket_create"],
  "tier_required": ["Pro", "Enterprise"],
  "entry_point": "main.py"
}
```

## Запуск

```bash
# Запуск API Gateway
cd decision-os
python -m api.main

# CLI
python -m cli.main list
python -m cli.main install dashbeam-transfer

# Тесты
python -m tests.test_core
```

## Уровни доступа

| Tier | Возможности |
|------|------------|
| **Start** | Только официальные builtin плагины |
| **Pro** | Официальные + проверенные сообществом |
| **Enterprise** | Свои плагины + свой Marketplace + свой relay |

## DashBeam Transfer (основные сущности)

| Сущность | Описание |
|----------|----------|
| DashBeamTicket | Одноразовый код для сопряжения |
| DashBeamSession | Активная P2P-сессия |
| PairedDevice | Доверенное устройство |
| DashBeamRelayConfig | Конфигурация relay-сервера (Enterprise) |

## Интеграция DashBeam с другими плагинами

- **Support Chat** → кнопка «Отправить через DashBeam»
- **Audit Trail** → «Экспорт через P2P»
- **Crypto Wallets** → безопасный sharing только view-only данных Monero (spend keys жёстко запрещены)

## Безопасность

- Каждый плагин в Sandbox (WebAssembly / WASI)
- Жёсткий whitelist permissions
- Цифровая подпись плагинов
- Tenant-изоляция
- Все действия через Policy Engine → Decision Gate → Audit Trail
- Spend keys Monero никогда не покидают Crypto Wallets Plugin

## API Endpoints

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/health` | Health check |
| GET | `/api/plugins` | Список всех плагинов |
| POST | `/api/plugins/{id}/enable` | Включить плагин |
| POST | `/api/plugins/{id}/disable` | Выключить плагин |
"""

# План: настоящее E2E-подключение MCP с аутентификацией

**Проект:** AstroFin Sentinel V5 / GitAgent
**Задача:** ATOM-GITAGENT-002
**Дата:** 2026-08-17
**Целевой слой оркестрации:** LangGraph
**Роль n8n:** только ingress/webhook

## 1. Что уже подтверждено

Реальный E2E-тест выполнен для официального GitHub MCP Server:

- GitHub CLI авторизован как `mahaasur13-sys`.
- Токен получен через `gh auth token` и передан только дочернему MCP-процессу через `GITHUB_PERSONAL_ACCESS_TOKEN`.
- Токен не выводился, не сохранялся в проекте и не попадал в Git.
- MCP handshake прошёл.
- Сервер: `github-mcp-server v0.6.2`.
- Protocol: `2024-11-05`.
- `tools/list` вернул 26 инструментов.
- Read-only вызов `search_repositories` успешно нашёл `mahaasur13-sys/astrofin-sentinel-platform`.

## 2. Что это означает

Базовая сетевая связность, аутентификация, MCP handshake, discovery и реальный tool call доказаны.

Однако этот тест запускал официальный GitHub MCP Server напрямую через stdio. Он ещё не доказывает, что текущий `integrations/gitagent/adapters/mcp_adapter.py` способен выполнить тот же сценарий в production-пути.

В проекте `MCPAdapter` ожидает Smithery CLI/API (`smithery` или `npx @smithery/cli`), а установленная команда `mcp` — другой локальный CLI и не является Smithery CLI. Нельзя считать эти команды взаимозаменяемыми.

Текущий статус: **direct MCP E2E passed; GitAgent adapter mock path passed; live adapter E2E pending**.

## Обновлённый статус реализации (2026-08-17)

- **DONE:** `MCPAdapter` поддерживает direct stdio и Smithery lifecycle через единые `initialize()`, `list_tools()`, `call_tool()`, `close()` и `reconnect()`.
- **DONE:** Добавлены timeout/retry/error-классы, redaction и read-only policy с явным `MCP_ALLOW_WRITE=true` для write-инструментов.
- **DONE:** Mock stdio tests покрывают handshake, discovery, read-only call, write denial, reconnect, malformed response, timeout, redaction и отсутствие секретов в argv; обычный набор проходит.
- **PENDING:** live GitHub adapter E2E. В текущем окружении отсутствует бинарник `github-mcp-server`; ручной direct E2E уже доказал работу официального сервера отдельно.

## 3. План дальнейших действий

### Этап A — закрепить секреты и границы доступа

1. Для постоянного запуска в Zo добавить секрет в Settings → Advanced:
   - `GITHUB_PERSONAL_ACCESS_TOKEN` — только если runtime действительно запускает GitHub MCP Server через env.
2. Не хранить токен в `.env`, JSON-манифестах, `installed_servers.json`, логах или Git.
3. Для первого staging-сценария использовать read-only операции:
   - `search_repositories`;
   - `get_file_contents`;
   - `list_commits`.
4. Запретить write-инструменты до отдельного согласования:
   - `create_or_update_file`;
   - `push_files`;
   - `create_issue`;
   - `create_pull_request`;
   - `merge_pull_request`.
5. Добавить redaction для `Authorization`, PAT, OAuth-кодов и значений секретных конфигурационных полей.

**Критерий:** секрет отсутствует в исходниках, артефактах и логах; read-only allowlist действует.

### Этап B — выбрать и реализовать production-транспорт

1. Зафиксировать первым реальным сервером официальный GitHub MCP Server.
2. Добавить в GitAgent транспорт stdio для запуска MCP-процесса с контролируемым env.
3. Разделить транспортный слой и `MCPAdapter`:
   - `StdioMCPTransport` — subprocess, JSON-RPC, lifecycle;
   - `SmitheryRemoteTransport` — hosted MCP через Smithery;
   - общий интерфейс: `connect`, `initialize`, `list_tools`, `call_tool`, `close`.
4. Не подменять Smithery CLI локальным `mcp` CLI.
5. Все сетевые обращения оставлять в разрешённом integration/tool слое и проверить архитектурным линтером.
6. Сохранять в `installed_servers.json` только безопасные metadata:
   - server name;
   - connection id;
   - transport;
   - tool allowlist;
   - redacted configuration.

**Критерий:** `MCPAdapter` сам выполняет handshake, discovery и read-only tool call, без ручного вспомогательного скрипта.

### Этап C — добавить реальные integration-тесты

Добавить pytest-тесты с маркером `slow` и явным opt-in через окружение:

1. `test_real_mcp_connection` — процесс запускается и отвечает на initialize.
2. `test_real_mcp_tool_discovery` — обнаружены инструменты GitHub.
3. `test_real_mcp_readonly_tool_call` — поиск репозитория возвращает ожидаемую структуру.
4. `test_mcp_timeout` — зависший сервер завершается по timeout.
5. `test_mcp_auth_failure` — отсутствующий или неверный токен даёт контролируемую ошибку.
6. `test_mcp_malformed_response` — некорректный JSON-RPC не ломает процесс тестов.
7. `test_mcp_reconnect` — после остановки процесса соединение создаётся заново.
8. `test_secret_redaction` — секрет не появляется в exception, stdout/stderr и persisted metadata.
9. `test_tool_allowlist` — write-инструмент отклоняется до разрешения.

Запуск:

```bash
pytest integrations/gitagent/tests -q --no-cov
pytest -m slow integrations/gitagent/tests -q --no-cov
```

Slow-тесты не должны запускаться в обычном CI без явно доступного секрета.

**Критерий:** обычный набор стабилен без credentials; slow-набор проходит в staging при наличии credentials.

### Этап D — надёжность и производительность

1. Добавить общий timeout на initialize/list/call.
2. Добавить ограниченный retry только для transport/network ошибок.
3. Не повторять небезопасные write-вызовы автоматически.
4. Добавить circuit breaker и понятные классы ошибок:
   - auth;
   - timeout;
   - protocol;
   - tool execution;
   - server unavailable.
5. Добавить тест 10–20 параллельных read-only вызовов.
6. Измерять p50, p95, p99, error rate и reconnect rate.
7. Не логировать содержимое секретных заголовков и полные tool arguments, если они могут содержать credentials.

**Критерий:** 10–20 параллельных вызовов завершаются без гонок состояния, с измеренными latency percentiles.

### Этап E — документация и merge-gate

Обновить `integrations/gitagent/README.md`:

- direct stdio GitHub E2E;
- Smithery remote flow отдельно;
- требования к секретам;
- запуск slow-тестов;
- allowlist инструментов;
- troubleshooting auth/timeout/reconnect.

Перед merge выполнить:

```bash
source .venv/bin/activate
python tools/healthcheck.py
ruff check integrations/gitagent
python scripts/architecture_linter.py
pytest integrations/gitagent/tests -q --no-cov
```

Если изменяется production-код, обновить документацию в том же PR и приложить E2E-артефакт без секретов.

## 4. Приоритеты

| Приоритет | Действие | Статус |
|---|---|:---:|
| P0 | Зафиксировать секреты и read-only allowlist | DONE |
| P0 | Встроить stdio transport в `MCPAdapter` | DONE |
| P0 | Перенести текущий ручной E2E в `pytest -m slow` | PENDING — нужен `github-mcp-server` |
| P1 | Timeout/retry/reconnect/error taxonomy | DONE — mock path |
| P1 | Performance: 10–20 параллельных calls | PLANNED |
| P1 | Smithery remote authenticated transport | PENDING — нужны namespace/credentials |
| P2 | Документация, CI job для staging slow-тестов | PLANNED |

## 5. Финальный критерий готовности

Задача считается полностью закрытой только когда один и тот же сценарий проходит через сам GitAgent adapter:

```text
GitAgent MCPAdapter
  → authenticated transport
  → initialize
  → tools/list
  → read-only tools/call
  → structured result
  → redacted audit record
  → clean close/reconnect
```

До этого формулировка должна оставаться: **direct MCP E2E validated, adapter production integration pending**.

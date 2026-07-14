# =============================================================================
# AstroFin Sentinel Platform — Makefile для разработки
# =============================================================================
# Использование:
#   make help           — список команд
#   make up             — поднять основной стек
#   make monitoring     — поднять мониторинг
#   make all            — поднять всё
#   make down           — остановить всё
#   make logs           — логи всех сервисов
#   make token          — создать Service Account token в Grafana
#   make dashboard      — импортировать дашборд в Grafana
#   make reset          — ⚠️  удалить volumes (потеря данных)
# =============================================================================

SHELL := /bin/bash
.DEFAULT_GOAL := help

ENV_FILE       := .env
COMPOSE_MAIN   := deploy/docker-compose.yml
COMPOSE_MON    := deploy/docker-compose.monitoring.yml
GRAFANA_URL    ?= http://localhost:9051
GRAFANA_USER   ?= admin
DASHBOARD_FILE := deploy/monitoring/grafana-dashboard.json
SA_NAME        := astrofin-importer
SA_TOKEN_FILE  := ~/.grafana_importer_token

# Загрузить .env если есть
ifneq (,$(wildcard $(ENV_FILE)))
include $(ENV_FILE)
export
endif

# -----------------------------------------------------------------------------
# Help
# -----------------------------------------------------------------------------
.PHONY: help
help: ## Показать список команд
	@awk 'BEGIN {FS = ":.*##"; printf "\nAstroFin Sentinel Platform — команды:\n\n"} \
		/^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2 }' \
		$(MAKEFILE_LIST)
	@echo ""

# -----------------------------------------------------------------------------
# Setup
# -----------------------------------------------------------------------------
.PHONY: env
env: ## Создать .env из .env.example (если нет)
	@if [ ! -f $(ENV_FILE) ]; then \
		cp .env.example $(ENV_FILE); \
		echo "✓ Создан $(ENV_FILE). Отредактируйте его."; \
	else \
		echo "$(ENV_FILE) уже существует"; \
	fi

.PHONY: check-docker
check-docker: ## Проверить docker и права пользователя
	@docker --version || (echo "✗ Docker не установлен" && exit 1)
	@docker compose version || (echo "✗ Docker Compose plugin не установлен" && exit 1)
	@docker ps >/dev/null 2>&1 || (echo "✗ Нет доступа к docker.sock. Запустите: sudo usermod -aG docker $$USER && newgrp docker" && exit 1)
	@echo "✓ Docker OK"

# -----------------------------------------------------------------------------
# Основной стек
# -----------------------------------------------------------------------------
.PHONY: up
up: check-docker env ## Поднять основной стек
	docker compose -f $(COMPOSE_MAIN) up -d
	@echo "✓ Основной стек поднят"

.PHONY: down
down: ## Остановить основной стек
	docker compose -f $(COMPOSE_MAIN) down

.PHONY: ps
ps: ## Статус основного стека
	docker compose -f $(COMPOSE_MAIN) ps

.PHONY: logs
logs: ## Логи основного стека (follow)
	docker compose -f $(COMPOSE_MAIN) logs -f --tail=100

.PHONY: restart
restart: down up ## Перезапустить основной стек

# -----------------------------------------------------------------------------
# Мониторинг
# -----------------------------------------------------------------------------
.PHONY: monitoring
monitoring: check-docker ## Поднять стек мониторинга (Prometheus+Grafana+Alertmanager)
	docker compose -f $(COMPOSE_MON) up -d
	@echo "✓ Мониторинг поднят: Prometheus :9050, Grafana :9051, Alertmanager :9053"
	@sleep 5
	@$(MAKE) monitoring-health

.PHONY: monitoring-down
monitoring-down: ## Остановить стек мониторинга
	docker compose -f $(COMPOSE_MON) down

.PHONY: monitoring-health
monitoring-health: ## Healthcheck всех сервисов мониторинга
	@for pair in "Prometheus:9050:/-/ready" \
	             "Grafana:9051:/api/health" \
	             "Alertmanager:9053:/-/ready" \
	             "Blackbox:9115:/-/healthy" \
	             "NodeExporter:9100:/-/healthy"; do \
	  name=$${pair%%:*}; \
	  rest=$${pair#*:}; \
	  port=$${rest%%:*}; \
	  path=$${rest#*:}; \
	  code=$$(curl -sS -o /dev/null -w "%{http_code}" http://localhost:$$port$$path || echo "000"); \
	  printf "  %-15s (:%s)  HTTP %s\n" "$$name" "$$port" "$$code"; \
	done

.PHONY: monitoring-logs
monitoring-logs: ## Логи мониторинга (follow)
	docker compose -f $(COMPOSE_MON) logs -f --tail=50

# -----------------------------------------------------------------------------
# Grafana — provisioning
# -----------------------------------------------------------------------------
.PHONY: grafana-info
grafana-info: ## Показать URL и логин Grafana
	@echo "URL:    $(GRAFANA_URL)"
	@echo "Login:  $(GRAFANA_USER)"
	@echo "Pass:   $${GRAFANA_ADMIN_PASSWORD:-admin (default — change!)}"

.PHONY: token
token: ## Создать Service Account token в Grafana (сохраняется в $(SA_TOKEN_FILE))
	@if [ -z "$$GRAFANA_ADMIN_PASSWORD" ]; then \
		echo "✗ GRAFANA_ADMIN_PASSWORD не задан в $(ENV_FILE)"; exit 1; \
	fi
	@echo "→ Создаю Service Account '$(SA_NAME)'..."
	@SA=$$(curl -sS -u "$(GRAFANA_USER):$$GRAFANA_ADMIN_PASSWORD" \
		-X POST $(GRAFANA_URL)/api/serviceaccounts \
		-H "Content-Type: application/json" \
		-d "{\"name\":\"$(SA_NAME)\",\"role\":\"Admin\",\"isDisabled\":false}"); \
	SA_ID=$$(echo "$$SA" | jq -r '.id'); \
	if [ "$$SA_ID" = "null" ] || [ -z "$$SA_ID" ]; then \
		echo "✗ SA уже существует или ошибка: $$SA"; \
		SA_ID=$$(curl -sS -u "$(GRAFANA_USER):$$GRAFANA_ADMIN_PASSWORD" \
			$(GRAFANA_URL)/api/serviceaccounts \
			| jq -r '.[] | select(.name=="$(SA_NAME)") | .id'); \
	fi; \
	echo "→ SA id=$$SA_ID, создаю token..."; \
	TOK=$$(curl -sS -u "$(GRAFANA_USER):$$GRAFANA_ADMIN_PASSWORD" \
		-X POST $(GRAFANA_URL)/api/serviceaccounts/$$SA_ID/tokens \
		-H "Content-Type: application/json" \
		-d '{"name":"importer-'$$(date +%Y%m%d)'"}'); \
	KEY=$$(echo "$$TOK" | jq -r '.key'); \
	if [ "$$KEY" = "null" ] || [ -z "$$KEY" ]; then \
		echo "✗ Ошибка: $$TOK"; exit 1; \
	fi; \
	echo "$$KEY" > $(SA_TOKEN_FILE); \
	chmod 600 $(SA_TOKEN_FILE); \
	echo "✓ Token сохранён в $(SA_TOKEN_FILE)"; \
	echo "$$KEY"

.PHONY: dashboard
dashboard: ## Импортировать дашборд Grafana
	@if [ ! -f $(SA_TOKEN_FILE) ]; then \
		echo "→ Token не найден, создаю..."; \
		$(MAKE) token >/dev/null; \
	fi
	@GRAFANA_URL=$(GRAFANA_URL) \
	GRAFANA_API_TOKEN=$$(cat $(SA_TOKEN_FILE)) \
	./scripts/import-grafana-dashboard.sh

.PHONY: dashboard-list
dashboard-list: ## Список дашбордов в Grafana
	@if [ ! -f $(SA_TOKEN_FILE) ]; then echo "✗ Token не найден: $(SA_TOKEN_FILE)"; exit 1; fi
	@curl -sS -u "$$(cat $(SA_TOKEN_FILE)):" \
		$(GRAFANA_URL)/api/search?type=dash-db \
		| jq -r '.[] | "\(.uid)\t\(.title)\t\(.url)"' \
		| column -t -s $$'\t'

# -----------------------------------------------------------------------------
# Полный жизненный цикл
# -----------------------------------------------------------------------------
.PHONY: all
all: monitoring up ## Поднять всё: мониторинг + основной стек
	@echo "✓ Полный стек поднят"
	@echo ""
	@echo "Доступ:"
	@echo "  Grafana:       $(GRAFANA_URL)  (admin / $${GRAFANA_ADMIN_PASSWORD:-admin})"
	@echo "  Prometheus:    http://localhost:9050"
	@echo "  Alertmanager:  http://localhost:9053"
	@echo ""
	@make dashboard-list

.PHONY: down-all
down-all: ## Остановить ВСЁ (основной стек + мониторинг)
	-@docker compose -f $(COMPOSE_MAIN) down
	-@docker compose -f $(COMPOSE_MON) down
	@echo "✓ Всё остановлено"

.PHONY: reset
reset: ## ⚠️  ОСТАНОВИТЬ всё и УДАЛИТЬ volumes (потеря данных!)
	@read -p "Удалить все volumes? (yes/no): " ans && [ "$$ans" = "yes" ]
	-@docker compose -f $(COMPOSE_MAIN) down -v
	-@docker compose -f $(COMPOSE_MON) down -v
	@echo "✓ Volumes удалены"

# -----------------------------------------------------------------------------
# Безопасность / аудит
# -----------------------------------------------------------------------------
.PHONY: audit
audit: ## Запустить validate_docker_security.py
	@python3 scripts/validate_docker_security.py \
		--compose deploy/docker-compose.yml \
		--compose deploy/docker-compose.monitoring.yml

.PHONY: validate-agent
validate-agent: ## Валидация нового агента (пример: AGENTS_PATH=...)
	@if [ -z "$(AGENTS_PATH)" ]; then \
		echo "Usage: make validate-agent AGENTS_PATH=agents/_impl/new_agent.py"; exit 1; \
	fi
	@python3 scripts/validate_agent.py "$(AGENTS_PATH)"

# -----------------------------------------------------------------------------
# Разработка
# -----------------------------------------------------------------------------
.PHONY: shell
shell: ## Войти в shell указанного сервиса (SERVICE=app)
	@if [ -z "$(SERVICE)" ]; then \
		echo "Usage: make shell SERVICE=app"; exit 1; \
	fi
	docker compose -f $(COMPOSE_MAIN) exec $(SERVICE) /bin/bash

.PHONY: lint
lint: ## Запустить pre-commit на всех файлах
	@command -v pre-commit >/dev/null || pip install pre-commit
	pre-commit run --all-files
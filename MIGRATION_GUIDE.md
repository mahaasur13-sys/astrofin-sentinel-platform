# Полная отвязка от Zo Computer — чек-лист миграции

**Версия:** 1.0 | **Дата:** 2026-04-01 | **Статус:** FINAL

---

> **⛔ ВАЖНОЕ ПРЕДУПРЕЖДЕНИЕ**
> Перед началом любых действий по удалению файлов **обязательно** сделайте полный бэкап.
> Потеря данных в этом проекте = потеря всех ваших стратегий и результатов эволюции.

---

## 1. Финальный Backup (обязательно выполнить первым)

```bash
cd /home/workspace
# Основной архив всего проекта
tar -czf astrofin-complete-backup-$(date +%Y%m%d-%H%M).tar.gz \
    AstroFinSentinelV5 \
    astrofin-meta-rl \
    start-dashboard.sh \
    .env.example 2>/dev/null
# Отдельный архив только с сессиями стратегий (самое ценное)
tar -czf sessions-only-backup-$(date +%Y%m%d-%H%M).tar.gz \
    AstroFinSentinelV5/data/meta_rl/sessions 2>/dev/null
echo '✅ Backup создан:'
ls -lh astrofin-complete-backup-*.tar.gz sessions-only-backup-*.tar.gz
```

## 2. Локальный запуск (Linux/macOS/Windows+WSL)

```bash
# Клонировать репозитории
git clone https://github.com/SERJLEEM/asurdev-workspace-backup.git
cd asurdev-workspace-backup/AstroFinSentinelV5

# Backend: Python 3.10+
pip install -r requirements.txt
python -m meta_rl.cli --gens 20 --pop 20

# Frontend: Node.js + Bun
cd ../astrofin-meta-rl
bun install
bun run dev
```

**Порты:**
- Backend API: `http://localhost:8050`
- Frontend: `http://localhost:5173`
- Meta-RL дашборд (опционально): `http://localhost:8050` (gunicorn)

## 3. Production deployment

### systemd service (Linux)
```bash
sudo tee /etc/systemd/system/astrofin-dashboard.service << 'EOF'
[Unit]
Description=AstroFin Sentinel V5 Dashboard
After=network.target

[Service]
Type=simple
User=YOUR_USER
WorkingDirectory=/home/YOUR_USER/astrofin
ExecStart=/home/YOUR_USER/astrofin/start-dashboard.sh start
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable astrofin-dashboard
sudo systemctl start astrofin-dashboard
```

### Docker
```Dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY . /app
RUN pip install -r requirements.txt
EXPOSE 8050
CMD ["gunicorn", "--bind", "0.0.0.0:8050", "web.wsgi:app"]
```

## 4. Активация live-режима (реальные деньги)

> **⛔ ВНИМАНИЕ: реальные деньги**

```bash
# 1. Создать .env из примера
cp .env.example .env

# 2. Заполнить ключи API биржи
# Binance:
CCXT_API_KEY=your_binance_api_key
CCXT_API_SECRET=your_binance_secret
CCXT_SANDBOX_MODE=false

# 3. Telegram alerts (опционально)
TELEGRAM_BOT_TOKEN=your_telegram_token
TELEGRAM_CHAT_ID=your_chat_id
TELEGRAM_ALERTS_ENABLED=true

# 4. Тест в sandbox режиме
python -m meta_rl.cli --paper --symbol BTC/USDT --gens 10
```

**API-ключи НИКОГДА не коммитятся в git.** `.env` добавлен в `.gitignore`.

## 5. Следующие шаги

- [ ] Сделать backup (секция 1)
- [ ] Клонировать репозитории на локальную машину
- [ ] Протестировать `python -m meta_rl.cli --gens 5 --pop 10`
- [ ] Настроить .env с API-ключами
- [ ] Запустить в paper-режиме на 1 неделю
- [ ] Проверить результаты A/B тестирования
- [ ] Перейти в live-режим

---
*Документ создан AstroCouncil Agent • AstroFinSentinelV5*

"""Locust load profile for AstroFin Sentinel Platform.

Сценарий нагрузки:
  - основной healthcheck  GET  /healthz       (liveness)
  - readiness             GET  /readyz        (readiness)
  - метрики Prometheus    GET  /metrics       (scraper polling)
  - базовый дашборд       GET  /              (HTML, ~50 KB)
  - защищённый endpoint   GET  /secure        (требует JWT, ожидаем 401)

Все задачи — анонимный пользователь. JWT-эндпоинт ожидаемо возвращает 401;
если начнёт возвращать 200 без токена — это инцидент безопасности.

Запуск:
    locust -f tests/load/locustfile.py --host https://staging.example

Параметры окружения:
    LOCUST_HEALTH_PATH  (по умолчанию /healthz)
    LOCUST_SECURE_PATH  (по умолчанию /secure)
"""

from __future__ import annotations

import os
from locust import HttpUser, task, between, events

HEALTH_PATH = os.getenv("LOCUST_HEALTH_PATH", "/healthz")
READY_PATH = os.getenv("LOCUST_READY_PATH", "/readyz")
METRICS_PATH = os.getenv("LOCUST_METRICS_PATH", "/metrics")
DASHBOARD_PATH = os.getenv("LOCUST_DASHBOARD_PATH", "/")
SECURE_PATH = os.getenv("LOCUST_SECURE_PATH", "/secure")

# Weights — распределение нагрузки между endpoint'ами.
# Healthcheck должен доминировать, чтобы проверить поведение под нагрузкой.
WEIGHT_HEALTH = 50
WEIGHT_READY = 20
WEIGHT_METRICS = 15
WEIGHT_DASHBOARD = 10
WEIGHT_SECURE = 5


class AstroFinUser(HttpUser):
    """Анонимный пользователь AstroFin."""

    # Имитация реального пользователя: между запросами 50–500 мс.
    wait_time = between(0.05, 0.5)

    # Базовые заголовки для всех запросов.
    def on_start(self):
        self.client.headers.update(
            {
                "User-Agent": "locust-astrofin/1.0",
                "Accept": "application/json,text/html;q=0.9,*/*;q=0.5",
            }
        )

    @task(WEIGHT_HEALTH)
    def get_health(self):
        """Liveness probe."""
        with self.client.get(
            HEALTH_PATH,
            name=f"GET {HEALTH_PATH}",
            catch_response=True,
        ) as r:
            if r.status_code != 200:
                r.failure(f"health returned {r.status_code}")
            elif r.elapsed.total_seconds() > 0.5:
                r.failure(f"health too slow: {r.elapsed.total_seconds()*1000:.0f} ms")

    @task(WEIGHT_READY)
    def get_ready(self):
        """Readiness probe."""
        with self.client.get(
            READY_PATH,
            name=f"GET {READY_PATH}",
            catch_response=True,
        ) as r:
            if r.status_code not in (200, 503):
                r.failure(f"ready returned {r.status_code}")

    @task(WEIGHT_METRICS)
    def get_metrics(self):
        """Prometheus scrape."""
        self.client.get(
            METRICS_PATH,
            name=f"GET {METRICS_PATH}",
        )

    @task(WEIGHT_DASHBOARD)
    def get_dashboard(self):
        """Главная страница дашборда (HTML)."""
        self.client.get(
            DASHBOARD_PATH,
            name=f"GET {DASHBOARD_PATH}",
        )

    @task(WEIGHT_SECURE)
    def get_secure_unauthorized(self):
        """Защищённый endpoint без токена — должен вернуть 401.

        Если возвращает 200 — это потенциальная утечка, считаем failure.
        """
        with self.client.get(
            SECURE_PATH,
            name=f"GET {SECURE_PATH} (no token)",
            catch_response=True,
        ) as r:
            if r.status_code == 200:
                r.failure("secure endpoint returned 200 WITHOUT auth!")
            elif r.status_code not in (401, 403):
                r.failure(f"unexpected status {r.status_code} (expected 401/403)")


# ---------------------------------------------------------------------------
# Lifecycle hooks — emit summary to GitHub Actions logs.
# ---------------------------------------------------------------------------


@events.test_start.add_listener
def _on_test_start(environment, **kwargs):
    print(f"[locust] starting against {environment.host}")


@events.test_stop.add_listener
def _on_test_stop(environment, **kwargs):
    stats = environment.stats
    print(
        f"[locust] done — total={stats.total.num_requests} "
        f"failures={stats.total.num_failures} "
        f"p95={stats.total.get_response_time_percentile(0.95):.0f} ms "
        f"rps={stats.total.total_rps:.1f}"
    )

"""Locust load test — Sprint G (Week 2) performance baseline.

Scenarios:
  1. DashboardUser:  GET  /api/v1/dashboard      50 users, ramp 1/min
  2. AgentRunUser:   POST /api/v1/agent/run      10 users, with Meta-RL inference
  3. ProbeUser:      GET  /health + /readyz      100 users (probe simulation)

Usage:
    locust -f tests/load/locustfile_sprint_e.py --host http://localhost:8000 \
        -u 50 -r 1 --run-time 10m --html docs/performance/assets/locust_report_staging.html

Environment:
    TEST_API_KEY — API key for agent/run (default: test-api-secret-key-123)
"""

from __future__ import annotations

import os
from locust import HttpUser, task, between

TEST_API_KEY = os.getenv("TEST_API_KEY", "test-api-secret-key-123")


class DashboardUser(HttpUser):
    """50 users hitting /api/v1/dashboard with 1-3s think time."""
    wait_time = between(1, 3)

    @task(3)
    def get_dashboard(self):
        self.client.get(
            "/api/v1/dashboard?symbol=BTCUSDT",
            name="GET /api/v1/dashboard",
            headers={"Accept": "application/json"},
        )

    @task(1)
    def get_dashboard_eth(self):
        self.client.get(
            "/api/v1/dashboard?symbol=ETHUSDT",
            name="GET /api/v1/dashboard (ETH)",
            headers={"Accept": "application/json"},
        )


class AgentRunUser(HttpUser):
    """10 users running agent inference with Meta-RL."""
    wait_time = between(5, 10)

    @task
    def run_fundamental_agent(self):
        self.client.post(
            "/api/v1/agent/run",
            json={
                "agentId": "fundamental",
                "prompt": "Analyze BTC current valuation and market position",
            },
            headers={
                "X-API-Key": TEST_API_KEY,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            name="POST /api/v1/agent/run (fundamental)",
        )

    @task(2)
    def run_synthesis_agent(self):
        self.client.post(
            "/api/v1/agent/run",
            json={
                "agentId": "karl",
                "prompt": "Synthesize market signals for BTCUSDT SWING position",
            },
            headers={
                "X-API-Key": TEST_API_KEY,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            name="POST /api/v1/agent/run (synthesis)",
        )


class ProbeUser(HttpUser):
    """100 users simulating health/readiness probes."""
    wait_time = between(0.05, 0.3)

    @task(5)
    def get_health(self):
        self.client.get(
            "/health",
            name="GET /health",
            headers={"Accept": "application/json"},
        )

    @task(2)
    def get_readyz(self):
        self.client.get(
            "/readyz",
            name="GET /readyz",
            headers={"Accept": "application/json"},
        )

"""Locust load test — Sprint E performance baseline."""

from locust import HttpUser, between, task


class DashboardUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def get_dashboard(self):
        self.client.get("/api/v1/dashboard?symbol=BTCUSDT")

    @task(1)
    def get_health(self):
        self.client.get("/health")

    @task(1)
    def get_aspects(self):
        self.client.get("/api/v1/astro/aspects")


class AgentRunUser(HttpUser):
    wait_time = between(5, 10)

    @task
    def run_agent(self):
        self.client.post(
            "/api/v1/agent/run",
            json={
                "agentId": "fundamental",
                "prompt": "Analyze BTC current valuation",
            },
            headers={"X-API-Key": "test-api-secret-key-123"},
        )

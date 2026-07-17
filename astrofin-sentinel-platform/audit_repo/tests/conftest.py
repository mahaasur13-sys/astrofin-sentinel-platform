import os


def pytest_configure(config):
    """Set default environment variables before any test module is imported."""
    os.environ.setdefault("API_KEY", "test-secret-key")
    os.environ.setdefault("REQUIRE_AUTH", "true")

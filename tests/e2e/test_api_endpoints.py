from __future__ import annotations

import pytest

from web.app import server


@pytest.fixture
def client():
    server.config["TESTING"] = True
    with server.test_client() as c:
        yield c


def test_health(client):
    rv = client.get("/health")
    assert rv.status_code == 200

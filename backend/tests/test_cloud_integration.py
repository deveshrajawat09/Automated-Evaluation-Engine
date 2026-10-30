import os

import httpx
import pytest


pytestmark = pytest.mark.skipif(
    os.getenv("RUN_CLOUD_INTEGRATION_TESTS") != "1",
    reason="Set RUN_CLOUD_INTEGRATION_TESTS=1 to run deployed service checks",
)


def test_deployed_health_endpoint():
    base_url = os.environ["CLOUD_API_URL"].rstrip("/")
    response = httpx.get(f"{base_url}/health", timeout=10)
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_deployed_frontend_is_reachable():
    frontend_url = os.environ["CLOUD_FRONTEND_URL"].rstrip("/")
    response = httpx.get(frontend_url, timeout=10)
    assert response.status_code == 200
    assert "HackEval" in response.text

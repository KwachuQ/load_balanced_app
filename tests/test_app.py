"""
Unit tests for the load-balanced FastAPI web application.
Mocks calls to the AWS EC2 IMDSv2 metadata service endpoints.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
import requests

from app.app import app

client = TestClient(app)


def test_health_endpoint() -> None:
    """Verifies that the /health endpoint returns a 200 OK status."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_info_endpoint_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Verifies that the /info endpoint returns region and AZ details when
    EC2 metadata services respond successfully.
    """
    # Mock token request (requests.put)
    class MockTokenResponse:
        text = "mock-token-abc-123"
        def raise_for_status(self) -> None:
            pass

    # Mock instance document request (requests.get)
    class MockIdentityResponse:
        def raise_for_status(self) -> None:
            pass

        def json(self) -> dict[str, str]:
            return {
                "region": "eu-central-1",
                "availabilityZone": "eu-central-1a"
            }

    # Apply monkeypatching to prevent actual network calls to 169.254.169.254
    monkeypatch.setattr(
        requests,
        "put",
        lambda *args, **kwargs: MockTokenResponse()
    )
    monkeypatch.setattr(
        requests,
        "get",
        lambda *args, **kwargs: MockIdentityResponse()
    )

    response = client.get("/info")
    assert response.status_code == 200
    assert response.json() == {
        "region": "eu-central-1",
        "availability_zone": "eu-central-1a"
    }


def test_info_endpoint_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Verifies that /info returns a 503 Service Unavailable status when
    the metadata service is not reachable (e.g. timeout or exception).
    """
    def mock_put_failure(*args, **kwargs) -> None:
        raise requests.exceptions.ConnectTimeout("Connection timed out")

    monkeypatch.setattr(requests, "put", mock_put_failure)

    response = client.get("/info")
    assert response.status_code == 503
    assert "Metadata unavailable" in response.json()["detail"]

# Integration tests verifying that the GET /health endpoint responds with HTTP 200
# and matches the expected HealthResponse JSON schema.
from fastapi.testclient import TestClient


def test_health_check_returns_200(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200


def test_health_check_payload_schema(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ok"
    assert data["app_name"] == "Chatrio Test API"
    assert data["version"] == "0.1.0-test"
    assert data["environment"] == "testing"

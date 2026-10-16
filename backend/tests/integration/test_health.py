#test_health is used to test the health of the app and it will be called when the app is started for configuration fast api with settings and middleware and routes
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

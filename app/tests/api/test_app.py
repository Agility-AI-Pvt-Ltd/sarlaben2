from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_check() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_openapi_contains_core_paths() -> None:
    response = client.get("/openapi.json")
    paths = response.json()["paths"]

    assert "/api/v1/auth/otp/send" in paths
    assert "/api/v1/auth/otp/verify" in paths
    assert "/api/v1/auth/users/{user_id}" in paths
    assert "/api/v1/cattle" in paths
    assert "/api/v1/calls/farmer/{farmer_id}" in paths
    assert "/api/v1/notifications/push-tokens" in paths
    assert "/api/v1/message/cattle/{cattle_id}/human/{human_id}" in paths
    assert "/api/v1/calls" in paths


def test_cors_preflight_for_otp_send() -> None:
    response = client.options(
        "/api/v1/auth/otp/send",
        headers={
            "Origin": "http://localhost:8081",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:8081"
    assert "POST" in response.headers["access-control-allow-methods"]

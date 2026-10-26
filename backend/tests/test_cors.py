"""CORS: the React app (FRONTEND_URL) may call the API from the browser; other origins may not."""

from config import get_settings

FRONTEND = get_settings().cors_origins[0]
OTHER = "https://evil.example"


def test_frontend_origin_passes_preflight(client):
    response = client.options(
        "/api/auth/me",
        headers={
            "Origin": FRONTEND,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == FRONTEND
    assert "authorization" in response.headers["access-control-allow-headers"].lower()


def test_other_origins_are_refused(client):
    preflight = client.options(
        "/api/auth/me", headers={"Origin": OTHER, "Access-Control-Request-Method": "GET"}
    )
    assert preflight.status_code == 400
    assert "access-control-allow-origin" not in preflight.headers

    simple = client.get("/", headers={"Origin": OTHER})
    assert "access-control-allow-origin" not in simple.headers


def test_retry_after_is_readable_by_the_frontend(client):
    response = client.get("/", headers={"Origin": FRONTEND})
    assert response.headers["access-control-allow-origin"] == FRONTEND
    exposed = [h.strip().lower() for h in response.headers["access-control-expose-headers"].split(",")]
    assert "retry-after" in exposed


def test_error_responses_carry_cors_headers(client):
    # Without them the browser hides the {"detail": ...} message from the app.
    response = client.get("/api/auth/me", headers={"Origin": FRONTEND})
    assert response.status_code == 401
    assert response.headers["access-control-allow-origin"] == FRONTEND

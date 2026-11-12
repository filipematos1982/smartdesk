"""Session 2 security regressions use isolated SQLite and synthetic credentials."""
import re

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from src.database import connect
from src.main import create_app
from src.security import LoginLimiter
from .conftest import csrf, login, person, post_form, create_ticket


def test_login_requires_session_bound_token(env):
    client, _ = env
    credentials = {"email": "ana@test", "password": "Password123!"}
    assert client.post("/login", data=credentials).status_code == 403
    token = csrf(client)
    assert client.post("/login", data={**credentials, "csrf_token": "wrong"}).status_code == 403
    assert client.post("/login", data={**credentials, "csrf_token": token},
                       follow_redirects=False).status_code == 303
    assert csrf(client) != token
    assert client.post("/logout", headers={"X-CSRF-Token": token}).status_code == 403


def test_token_from_another_session_is_rejected(env):
    client, _ = env
    token = csrf(client)
    client.cookies.clear()
    csrf(client)
    assert client.post("/login", data={"email": "ana@test", "password": "Password123!"},
                       headers={"X-CSRF-Token": token}).status_code == 403


def test_cookie_defaults_and_logout(env, monkeypatch):
    client, path = env
    login_response = login(client, "ana@test")
    response = client.get("/tickets")
    cookie = login_response.headers["set-cookie"].lower()
    assert "secure" in cookie and "httponly" in cookie and "samesite=lax" in cookie
    assert "max-age=3600" in cookie
    assert response.headers["cache-control"] == "no-store"
    response = post_form(client, "/logout", follow_redirects=False)
    assert "expires=thu, 01 jan 1970" in response.headers["set-cookie"].lower()
    assert client.cookies.get("session") is None
    assert client.get("/tickets", follow_redirects=False).status_code == 303
    monkeypatch.setenv("SMARTDESK_COOKIE_SECURE", "false")
    with TestClient(create_app(path=path, secret="test-secret-of-at-least-32-characters")) as local:
        cookie = local.get("/login").headers["set-cookie"].lower()
        assert "secure" not in cookie and "httponly" in cookie


@pytest.mark.parametrize("setting,value", [
    ("SMARTDESK_COOKIE_SECURE", "invalid"),
    ("SMARTDESK_SESSION_MAX_AGE", "0"),
    ("SMARTDESK_SESSION_MAX_AGE", "invalid"),
])
def test_invalid_security_configuration_fails_closed(monkeypatch, setting, value):
    monkeypatch.setenv(setting, value)
    with pytest.raises(RuntimeError):
        create_app(secret="test-secret-of-at-least-32-characters")


def test_placeholder_signing_secret_is_rejected():
    with pytest.raises(RuntimeError):
        create_app(secret="REPLACE_WITH_RANDOM_SESSION_SECRET_AT_LEAST_32_CHARACTERS")


def test_unknown_and_wrong_password_do_not_authenticate_and_are_throttled(env):
    client, _ = env
    for email in ("ana@test", "missing@test", "ana@test", "missing@test", "ana@test"):
        response = post_form(client, "/login", data={"email": email, "password": "incorrect"})
        assert response.status_code == 200
        assert "Incorrect email or password." in response.text
    response = post_form(client, "/login", data={"email": "ana@test", "password": "Password123!"},
                         headers={"X-Forwarded-For": "192.0.2.1"})
    assert response.status_code == 429
    assert 1 <= int(response.headers["retry-after"]) <= 60
    assert client.get("/tickets", follow_redirects=False).status_code == 303


def test_limiter_expires_windows_and_bounds_memory():
    now = [0.0]
    limiter = LoginLimiter(limit=2, window=60, capacity=2, clock=lambda: now[0])
    limiter.check("first")
    limiter.check("first")
    with pytest.raises(HTTPException) as blocked:
        limiter.check("first")
    assert blocked.value.status_code == 429
    limiter.check("second")
    limiter.check("third")
    assert len(limiter.entries) == 2
    now[0] = 60
    limiter.check("first")
    assert len(limiter.entries) == 1


def test_logout_and_ticket_mutations_require_csrf_and_leave_data_unchanged(env):
    client, path = env
    login(client, "ana@test")
    assert client.post("/tickets/new", data={"title": "Unsafe", "description": "Issue",
                                             "category": "Hardware"}).status_code == 403
    assert client.post("/logout").status_code == 403
    assert client.get("/tickets").status_code == 200
    with connect(path) as db:
        assert db.execute("SELECT count(*) FROM tickets").fetchone()[0] == 0
        ticket = create_ticket(db)
        tech = person(db, "miguel@test")["id"]
    post_form(client, "/logout")
    login(client, "sofia@test")
    for action, data in [("assign", {"technician_id": tech}), ("start", {}),
                         ("resolve", {"resolution": "Fixed"}), ("return", {}),
                         ("close", {"confirmed": "true"})]:
        response = client.post(f"/api/tickets/{ticket['id']}/{action}", data=data)
        assert response.status_code == 403
        assert "CSRF" in response.json()["detail"]
    with connect(path) as db:
        actual = dict(db.execute("SELECT * FROM tickets WHERE id=?", (ticket["id"],)).fetchone())
        assert actual == ticket


def test_all_rendered_forms_include_csrf(env):
    client, path = env
    login_page = client.get("/login")
    assert 'name="csrf_token"' in login_page.text
    login(client, "ana@test")
    pages = [client.get("/tickets"), client.get("/tickets/new")]
    with connect(path) as db:
        ticket = create_ticket(db)
    pages.append(client.get(f"/tickets/{ticket['id']}"))
    for page in pages:
        forms = re.findall(r"<form\b.*?</form>", page.text, flags=re.S)
        assert forms
        assert all('name="csrf_token"' in form for form in forms)


@pytest.mark.parametrize("email", ["ana@test", "outro@test", "miguel@test", "technician2@test"])
def test_only_manager_can_assign_without_mutating_ticket(env, email):
    client, path = env
    with connect(path) as db:
        ticket = create_ticket(db)
        tech = person(db, "miguel@test")["id"]
    login(client, email)
    response = post_form(client, f"/api/tickets/{ticket['id']}/assign", data={"technician_id": tech})
    assert response.status_code == 403
    with connect(path) as db:
        assert dict(db.execute("SELECT * FROM tickets WHERE id=?", (ticket["id"],)).fetchone()) == ticket


def test_anonymous_api_contract_and_non_employee_creation(env):
    client, path = env
    assert client.post("/api/tickets/1/start").status_code == 401
    login(client, "miguel@test")
    response = post_form(client, "/tickets/new", data={"title": "Denied", "description": "Issue",
                                                     "category": "Hardware"})
    assert response.status_code == 403
    with connect(path) as db:
        assert db.execute("SELECT count(*) FROM tickets").fetchone()[0] == 0


@pytest.mark.parametrize("operation,email", [
    ("start", "ana@test"), ("start", "sofia@test"), ("start", "technician2@test"),
    ("resolve", "ana@test"), ("resolve", "sofia@test"), ("resolve", "technician2@test"),
    ("return", "outro@test"), ("return", "miguel@test"), ("return", "sofia@test"),
    ("close", "ana@test"), ("close", "miguel@test"), ("close", "technician2@test"),
])
def test_lifecycle_route_permissions_deny_without_mutation(env, operation, email):
    from src import services
    client, path = env
    with connect(path) as db:
        ticket = create_ticket(db)
        manager = person(db, "sofia@test")
        technician = person(db, "miguel@test")
        ticket = services.assign(db, manager, ticket["id"], technician["id"])
        if operation != "start":
            ticket = services.start(db, technician, ticket["id"])
        if operation in {"return", "close"}:
            ticket = services.resolve(db, technician, ticket["id"], "Applied solution")
    login(client, email)
    response = post_form(client, f"/api/tickets/{ticket['id']}/{operation}",
                         data={"resolution": "Changed", "confirmed": "true"})
    assert response.status_code == 403
    with connect(path) as db:
        assert dict(db.execute("SELECT * FROM tickets WHERE id=?", (ticket["id"],)).fetchone()) == ticket


def test_tampered_session_cookie_cannot_authenticate(env):
    client, _ = env
    login(client, "ana@test")
    cookie = client.cookies.get("session")
    client.cookies.clear()
    client.cookies.set("session", cookie + "tampered")
    assert client.get("/tickets", follow_redirects=False).status_code == 303

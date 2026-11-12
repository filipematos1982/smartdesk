"""PostgreSQL acceptance requires an explicitly approved ephemeral test target."""
import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Event

import pytest
from fastapi import HTTPException

from src.database import initialize
from src import services
from src.auth import hash_password
from .postgres_target import MissingTestTarget, approved_target


@pytest.fixture
def pg_db():
    try:
        target = approved_target()
    except MissingTestTarget as exc:
        pytest.skip(str(exc))
    from psycopg import sql
    schema = "smartdesk_test_" + uuid.uuid4().hex
    with target.connect() as db:
        db.connection.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
    db = target.connect(schema)
    db.target = target
    try:
        initialize(db)
        yield db
    finally:
        # Retain test schemas only inside the verified ephemeral container.
        db.connection.rollback()
        db.connection.close()


def seed(db):
    people = []
    for role in ("employee", "technician", "responsavel"):
        result = db.execute("INSERT INTO users(name,email,secret,role) VALUES(?,?,?,?)",
                            (role, role + "@pg.test", hash_password("Synthetic-test-password"), role))
        people.append({"id": result.lastrowid, "role": role})
    db.commit()
    return people


def test_pg01_pg06_initialization_is_idempotent(pg_db):
    employee, _, _ = seed(pg_db)
    ticket = services.create(pg_db, employee, "Printer", "Not printing", "Hardware")
    initialize(pg_db)
    assert services.get(pg_db, ticket["id"])["title"] == "Printer"


def test_pg02_pg03_pg04_pg05_pg08_lifecycle_and_new_connection(pg_db):
    employee, technician, manager = seed(pg_db)
    ticket = services.create(pg_db, employee, "Network", "No access", "Access")
    ticket_id = ticket["id"]
    assert ticket["state"] == "Open"
    services.assign(pg_db, manager, ticket_id, technician["id"])
    assert services.start(pg_db, technician, ticket_id)["state"] == "In Progress"
    assert services.resolve(pg_db, technician, ticket_id, "Reconfigured")["resolution"] == "Reconfigured"
    assert services.reopen(pg_db, employee, ticket_id)["state"] == "In Progress"
    services.resolve(pg_db, technician, ticket_id, "Verified repair")
    assert services.close(pg_db, manager, ticket_id, True)["state"] == "Closed"
    with pytest.raises(HTTPException):
        services.reopen(pg_db, employee, ticket_id)
    pg_db.commit()
    with pg_db.target.connect(pg_db.schema) as another:
        assert another.execute("SELECT state FROM tickets WHERE id=?", (ticket_id,)).fetchone()["state"] == "Closed"


class PausedWrite:
    """Hold a service immediately before its UPDATE, after its validation reads."""
    def __init__(self, db, ready, release):
        self.db, self.ready, self.release = db, ready, release

    def execute(self, statement, params=()):
        if statement.startswith("UPDATE tickets"):
            self.ready.set()
            if not self.release.wait(5):
                raise TimeoutError("Concurrent test did not release the stale write")
        return self.db.execute(statement, params)

    def commit(self):
        self.db.commit()

    def rollback(self):
        self.db.rollback()


def test_concurrent_start_has_exactly_one_winner(pg_db):
    employee, technician, manager = seed(pg_db)
    ticket = services.create(pg_db, employee, "Printer", "Issue", "Hardware")
    services.assign(pg_db, manager, ticket["id"], technician["id"])
    barrier = Barrier(2, timeout=5)

    def start_once():
        with pg_db.target.connect(pg_db.schema) as db:
            class SynchronizedWrite:
                def execute(self, statement, params=()):
                    if statement.startswith("UPDATE tickets"):
                        barrier.wait()
                    return db.execute(statement, params)
                def commit(self):
                    db.commit()
                def rollback(self):
                    db.rollback()
            try:
                return services.start(SynchronizedWrite(), technician, ticket["id"])["state"]
            except HTTPException as exc:
                return exc.status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(start_once) for _ in range(2)]
        results = [future.result(timeout=12) for future in futures]
    assert results.count("In Progress") == 1
    assert results.count(409) == 1


@pytest.mark.parametrize("stale_action", ["start", "resolve", "assign", "close", "reopen"])
def test_stale_state_or_assignment_cannot_overwrite_concurrent_change(pg_db, stale_action):
    employee, technician, manager = seed(pg_db)
    other = pg_db.execute("INSERT INTO users(name,email,secret,role) VALUES(?,?,?,?)",
                          ("Other technician", "other@pg.test", hash_password("Synthetic-test-password"), "technician"))
    other_technician_id = other.lastrowid
    pg_db.commit()
    ticket = services.create(pg_db, employee, "Printer", "Issue", "Hardware")
    services.assign(pg_db, manager, ticket["id"], technician["id"])
    if stale_action in {"resolve", "close", "reopen"}:
        services.start(pg_db, technician, ticket["id"])
    if stale_action in {"close", "reopen"}:
        services.resolve(pg_db, technician, ticket["id"], "Original repair")
    ready, release = Event(), Event()

    def stale_write():
        with pg_db.target.connect(pg_db.schema) as db:
            delayed = PausedWrite(db, ready, release)
            try:
                if stale_action == "assign":
                    services.assign(delayed, manager, ticket["id"], other_technician_id)
                elif stale_action == "close":
                    services.close(delayed, manager, ticket["id"], True)
                elif stale_action == "resolve":
                    services.resolve(delayed, technician, ticket["id"], "Stale repair")
                elif stale_action == "reopen":
                    services.reopen(delayed, employee, ticket["id"])
                else:
                    services.start(delayed, technician, ticket["id"])
            except HTTPException as exc:
                return exc.status_code
            return "unexpected success"

    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(stale_write)
        try:
            assert ready.wait(5), "Stale writer did not reach its UPDATE"
            with pg_db.target.connect(pg_db.schema) as competitor:
                if stale_action == "assign":
                    expected = services.start(competitor, technician, ticket["id"])
                elif stale_action == "close":
                    expected = services.reopen(competitor, employee, ticket["id"])
                elif stale_action == "reopen":
                    expected = services.close(competitor, manager, ticket["id"], True)
                else:
                    expected = services.assign(competitor, manager, ticket["id"], other_technician_id)
        finally:
            release.set()
        assert future.result(timeout=12) == 409
    with pg_db.target.connect(pg_db.schema) as check:
        assert services.get(check, ticket["id"]) == expected


def test_transaction_exception_rolls_back_without_removing_data(pg_db):
    with pytest.raises(RuntimeError, match="synthetic rollback"):
        with pg_db.target.connect(pg_db.schema) as db:
            db.execute("INSERT INTO users(name,email,secret,role) VALUES(?,?,?,?)",
                       ("Uncommitted", "rollback@pg.test", "synthetic", "employee"))
            raise RuntimeError("synthetic rollback")
    with pg_db.target.connect(pg_db.schema) as check:
        assert check.execute("SELECT id FROM users WHERE email=?", ("rollback@pg.test",)).fetchone() is None


def test_constraint_failure_is_rolled_back_and_connection_is_usable(pg_db):
    import psycopg
    with pytest.raises(psycopg.errors.CheckViolation):
        pg_db.execute("INSERT INTO users(name,email,secret,role) VALUES(?,?,?,?)",
                      ("Invalid", "invalid@pg.test", "synthetic", "unknown"))
    pg_db.rollback()
    assert pg_db.execute("SELECT id FROM users WHERE email=?", ("invalid@pg.test",)).fetchone() is None
    assert len(seed(pg_db)) == 3


def test_real_target_rejects_incorrect_marker_without_changing_schema(pg_db):
    from dataclasses import replace

    wrong_target = replace(pg_db.target, target_id=pg_db.target.target_id + "_unapproved")
    with pytest.raises(RuntimeError, match="marker"):
        wrong_target.connect(pg_db.schema)
    with pg_db.target.connect(pg_db.schema) as check:
        assert check.execute("SELECT count(*) AS total FROM users").fetchone()["total"] == 0


@pytest.fixture
def pg_client(pg_db, monkeypatch):
    """Exercise real HTTP/database integration only in this fixture's unique schema."""
    import src.main as main_module
    from fastapi.testclient import TestClient

    monkeypatch.delenv("SMARTDESK_SEED_DEMO_USERS", raising=False)
    monkeypatch.setenv("SMARTDESK_COOKIE_SECURE", "true")
    monkeypatch.setattr(main_module, "connect", lambda path=None: pg_db.target.connect(pg_db.schema))
    for name, role in (("employee", "employee"), ("other", "employee"),
                       ("technician", "technician"), ("second", "technician"),
                       ("manager", "responsavel")):
        pg_db.execute("INSERT INTO users(name,email,secret,role) VALUES(?,?,?,?)",
                      (name, name + "@http.test", hash_password("Synthetic-test-password"), role))
    pg_db.commit()
    app = main_module.create_app(secret="synthetic-postgres-http-session-secret-32-characters")
    with TestClient(app, base_url="https://testserver") as client:
        yield client


def test_postgres_http_lifecycle_visibility_csrf_and_reconnection(pg_db, pg_client):
    from .conftest import login, post_form

    client = pg_client
    assert client.post("/api/tickets/1/start").status_code == 401
    response = login(client, "employee@http.test", "Synthetic-test-password")
    assert "secure" in response.headers["set-cookie"].lower()
    data = {"title": "HTTP PostgreSQL ticket", "description": "Synthetic issue", "category": "Hardware"}
    assert client.post("/tickets/new", data=data).status_code == 403
    with pg_db.target.connect(pg_db.schema) as check:
        assert check.execute("SELECT count(*) AS total FROM tickets").fetchone()["total"] == 0
    created = post_form(client, "/tickets/new", data=data, follow_redirects=False)
    assert created.status_code == 303
    with pg_db.target.connect(pg_db.schema) as check:
        original = dict(check.execute("SELECT * FROM tickets").fetchone())
        technician = check.execute("SELECT id FROM users WHERE email=?", ("technician@http.test",)).fetchone()["id"]
    ticket_id = original["id"]
    assert original["state"] == "Open"

    def switch(name):
        assert post_form(client, "/logout", follow_redirects=False).status_code == 303
        login(client, name + "@http.test", "Synthetic-test-password")

    switch("other")
    assert data["title"] not in client.get("/tickets").text
    assert client.get(f"/tickets/{ticket_id}").status_code == 403
    switch("manager")
    assert post_form(client, f"/api/tickets/{ticket_id}/assign", data={"technician_id": technician},
                     follow_redirects=False).status_code == 303
    switch("technician")
    assert data["title"] in client.get("/tickets").text
    assert post_form(client, f"/api/tickets/{ticket_id}/start", follow_redirects=False).status_code == 303
    assert post_form(client, f"/api/tickets/{ticket_id}/resolve", data={"resolution": "First repair"},
                     follow_redirects=False).status_code == 303
    switch("employee")
    assert post_form(client, f"/api/tickets/{ticket_id}/return", follow_redirects=False).status_code == 303
    switch("technician")
    assert post_form(client, f"/api/tickets/{ticket_id}/resolve", data={"resolution": "Verified repair"},
                     follow_redirects=False).status_code == 303
    switch("manager")
    assert "Verified repair" in client.get(f"/tickets/{ticket_id}").text
    assert post_form(client, f"/api/tickets/{ticket_id}/close", data={"confirmed": "true"},
                     follow_redirects=False).status_code == 303
    switch("employee")
    assert post_form(client, f"/api/tickets/{ticket_id}/return").status_code == 400
    with pg_db.target.connect(pg_db.schema) as check:
        final = dict(check.execute("SELECT * FROM tickets WHERE id=?", (ticket_id,)).fetchone())
        assert final["state"] == "Closed"
        assert final["resolution"] == "Verified repair"
        assert final["technician_id"] == technician


@pytest.mark.parametrize("actor,action,state", [
    ("employee", "assign", "Open"),
    ("manager", "start", "Open"),
    ("second", "start", "Open"),
    ("second", "resolve", "In Progress"),
    ("other", "return", "Resolved"),
    ("technician", "close", "Resolved"),
])
def test_postgres_http_denied_actions_do_not_mutate(pg_db, pg_client, actor, action, state):
    from .conftest import login, post_form

    people = {name: dict(pg_db.execute("SELECT * FROM users WHERE email=?", (name + "@http.test",)).fetchone())
              for name in ("employee", "technician", "manager")}
    ticket = services.create(pg_db, people["employee"], "Protected ticket", "Synthetic", "Access")
    ticket = services.assign(pg_db, people["manager"], ticket["id"], people["technician"]["id"])
    if state in {"In Progress", "Resolved"}:
        ticket = services.start(pg_db, people["technician"], ticket["id"])
    if state == "Resolved":
        ticket = services.resolve(pg_db, people["technician"], ticket["id"], "Synthetic repair")
    login(pg_client, actor + "@http.test", "Synthetic-test-password")
    response = post_form(pg_client, f"/api/tickets/{ticket['id']}/{action}",
                         data={"technician_id": people["technician"]["id"], "resolution": "Denied", "confirmed": "true"})
    assert response.status_code == 403
    with pg_db.target.connect(pg_db.schema) as check:
        assert services.get(check, ticket["id"]) == ticket

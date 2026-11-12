"""Connection controls and test-target guards never contact a real database."""
from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from src.database import PostgresConnection, connect
from src import services
from .conftest import create_ticket, person
from .postgres_target import MissingTestTarget, approved_target


def target_environment(**overrides):
    settings = {
        "SMARTDESK_TEST_DATABASE_URL": "postgresql://smartdesk_test:synthetic@127.0.0.1:15432/smartdesk_test",
        "SMARTDESK_TEST_DATABASE_APPROVED": "isolated-ephemeral",
        "SMARTDESK_TEST_TARGET_ID": "session3_synthetic_target",
    }
    settings.update(overrides)
    return settings


def test_target_never_falls_back_to_ambient_application_database():
    with pytest.raises(MissingTestTarget):
        approved_target({"DATABASE_URL": "postgresql://do-not-contact.invalid/application"})


@pytest.mark.parametrize("url", [
    "postgresql://smartdesk_test:synthetic@remote.invalid:15432/smartdesk_test",
    "postgresql://application:synthetic@127.0.0.1:15432/smartdesk_test",
    "postgresql://smartdesk_test:synthetic@127.0.0.1:15432/application",
    "postgresql://smartdesk_test:synthetic@127.0.0.1:15432/smartdesk_test?host=remote.invalid",
    "postgresql://smartdesk_test:synthetic@127.0.0.1/smartdesk_test",
    "postgresql://smartdesk_test:synthetic@127.0.0.1:invalid/smartdesk_test",
    "host=127.0.0.1 dbname=smartdesk_test",
])
def test_test_target_rejects_unscoped_urls_before_connection(url):
    with pytest.raises(RuntimeError):
        approved_target(target_environment(SMARTDESK_TEST_DATABASE_URL=url))


@pytest.mark.parametrize("setting,value", [
    ("SMARTDESK_TEST_DATABASE_APPROVED", ""),
    ("SMARTDESK_TEST_DATABASE_APPROVED", "true"),
    ("SMARTDESK_TEST_TARGET_ID", ""),
    ("SMARTDESK_TEST_TARGET_ID", "application"),
])
def test_test_target_requires_approval_and_marker(setting, value):
    with pytest.raises(RuntimeError):
        approved_target(target_environment(**{setting: value}))


def test_guard_verifies_identity_and_marker_before_application_writes(monkeypatch):
    import tests.postgres_target as target_module
    db = Mock()
    db.execute.return_value.fetchone.return_value = {"db": "application", "role": "application"}
    factory = Mock(return_value=db)
    monkeypatch.setattr(target_module, "PostgresConnection", factory)
    with pytest.raises(RuntimeError, match="identity"):
        approved_target(target_environment()).connect()
    assert db.connection.execute.call_count == 0
    db.connection.close.assert_called_once()


def test_missing_marker_closes_connection_before_schema_changes(monkeypatch):
    import tests.postgres_target as target_module
    db = Mock()
    db.execute.return_value.fetchone.return_value = {"db": "smartdesk_test", "role": "smartdesk_test"}
    db.connection.execute.return_value.fetchone.return_value = None
    monkeypatch.setattr(target_module, "PostgresConnection", Mock(return_value=db))
    with pytest.raises(RuntimeError, match="marker"):
        approved_target(target_environment()).connect()
    assert db.connection.execute.call_count == 1
    assert db.connection.execute.call_args.args[0].startswith("SELECT target_id")
    db.connection.close.assert_called_once()


@pytest.mark.parametrize("schema", ["public", "smartdesk_test_bad", "smartdesk_test_" + "a" * 32 + "; SELECT 1"])
def test_unscoped_schema_is_rejected_before_search_path_changes(monkeypatch, schema):
    import tests.postgres_target as target_module
    db = Mock()
    db.execute.return_value.fetchone.return_value = {"db": "smartdesk_test", "role": "smartdesk_test"}
    db.connection.execute.return_value.fetchone.return_value = {"target_id": "session3_synthetic_target"}
    monkeypatch.setattr(target_module, "PostgresConnection", Mock(return_value=db))
    with pytest.raises(RuntimeError, match="schema"):
        approved_target(target_environment()).connect(schema)
    assert db.connection.execute.call_count == 1
    db.connection.rollback.assert_called_once()
    db.connection.close.assert_called_once()
    db.commit.assert_not_called()


def test_failed_marker_query_rolls_back_and_closes_without_writes(monkeypatch):
    import tests.postgres_target as target_module
    db = Mock()
    db.execute.return_value.fetchone.return_value = {"db": "smartdesk_test", "role": "smartdesk_test"}
    db.connection.execute.side_effect = RuntimeError("synthetic marker lookup failure")
    monkeypatch.setattr(target_module, "PostgresConnection", Mock(return_value=db))
    with pytest.raises(RuntimeError, match="marker lookup"):
        approved_target(target_environment()).connect("smartdesk_test_" + "a" * 32)
    assert db.connection.execute.call_count == 1
    db.connection.rollback.assert_called_once()
    db.connection.close.assert_called_once()
    db.commit.assert_not_called()


def test_postgres_components_preserve_uri_special_password_characters(monkeypatch):
    import psycopg
    monkeypatch.delenv("DATABASE_URL", raising=False)
    values = {"POSTGRES_HOST": "db", "POSTGRES_DB": "smartdesk", "POSTGRES_USER": "smartdesk",
              "POSTGRES_PASSWORD": "synthetic:@/?#% password", "POSTGRES_PORT": "5432",
              "SMARTDESK_DB_CONNECT_TIMEOUT": "7"}
    for key, value in values.items():
        monkeypatch.setenv(key, value)
    driver = Mock()
    monkeypatch.setattr(psycopg, "connect", driver)
    connect()
    assert driver.call_args.kwargs["password"] == values["POSTGRES_PASSWORD"]
    assert driver.call_args.kwargs["connect_timeout"] == 7
    assert driver.call_args.kwargs["port"] == 5432
    assert driver.call_args.kwargs["dbname"] == "smartdesk"


def test_database_url_precedence_and_default_timeout(monkeypatch):
    import psycopg
    monkeypatch.setenv("DATABASE_URL", "postgresql://synthetic.invalid/synthetic")
    monkeypatch.delenv("SMARTDESK_DB_CONNECT_TIMEOUT", raising=False)
    monkeypatch.setenv("POSTGRES_HOST", "ignored")
    driver = Mock()
    monkeypatch.setattr(psycopg, "connect", driver)
    connect()
    assert driver.call_args.args == ("postgresql://synthetic.invalid/synthetic",)
    assert driver.call_args.kwargs["connect_timeout"] == 5
    assert "host" not in driver.call_args.kwargs


@pytest.mark.parametrize("timeout", ["0", "-1", "invalid"])
def test_invalid_connection_timeout_never_contacts_database(monkeypatch, timeout):
    import psycopg
    monkeypatch.setenv("SMARTDESK_DB_CONNECT_TIMEOUT", timeout)
    driver = Mock()
    monkeypatch.setattr(psycopg, "connect", driver)
    with pytest.raises(RuntimeError):
        PostgresConnection("postgresql://synthetic.invalid/synthetic")
    driver.assert_not_called()


@pytest.mark.parametrize("port", ["0", "65536", "invalid"])
def test_invalid_component_port_never_contacts_database(monkeypatch, port):
    import psycopg
    monkeypatch.delenv("DATABASE_URL", raising=False)
    for key in ("POSTGRES_HOST", "POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD"):
        monkeypatch.setenv(key, "synthetic")
    monkeypatch.setenv("POSTGRES_PORT", port)
    driver = Mock()
    monkeypatch.setattr(psycopg, "connect", driver)
    with pytest.raises(RuntimeError):
        connect()
    driver.assert_not_called()


def test_connection_context_rolls_back_and_closes_on_exception(monkeypatch):
    import psycopg
    driver_connection = Mock()
    monkeypatch.setattr(psycopg, "connect", Mock(return_value=driver_connection))
    with pytest.raises(RuntimeError, match="synthetic"):
        with PostgresConnection("postgresql://synthetic.invalid/synthetic"):
            raise RuntimeError("synthetic")
    driver_connection.rollback.assert_called_once()
    driver_connection.close.assert_called_once()
    driver_connection.commit.assert_not_called()


def test_stale_technician_cannot_resolve_after_reassignment_in_sqlite(env):
    _, path = env
    with connect(path) as db:
        employee = person(db, "ana@test")
        technician = person(db, "miguel@test")
        manager = person(db, "sofia@test")
        other_technician = person(db, "technician2@test")
        ticket = create_ticket(db)
        services.assign(db, manager, ticket["id"], technician["id"])
        services.start(db, technician, ticket["id"])

        class ReassignBeforeWrite:
            def execute(self, statement, params=()):
                if statement.startswith("UPDATE tickets"):
                    with connect(path) as competitor:
                        services.assign(competitor, manager, ticket["id"], other_technician["id"])
                return db.execute(statement, params)
            def commit(self):
                db.commit()
            def rollback(self):
                db.rollback()

        with pytest.raises(HTTPException) as conflict:
            services.resolve(ReassignBeforeWrite(), technician, ticket["id"], "Stale solution")
        assert conflict.value.status_code == 409
        final = services.get(db, ticket["id"])
        assert final["technician_id"] == other_technician["id"]
        assert final["state"] == "In Progress"
        assert final["resolution"] is None

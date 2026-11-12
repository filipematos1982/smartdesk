"""Explicit opt-in and identity checks for the disposable Session 3 test target.

This helper never reads DATABASE_URL, creates databases, or removes test schemas.
The coordinator must verify the container identity and create its marker first.
"""
import os
import re
from dataclasses import dataclass, field
from urllib.parse import unquote, urlsplit

from src.database import PostgresConnection


class MissingTestTarget(RuntimeError):
    pass


@dataclass(frozen=True)
class ApprovedTarget:
    url: str = field(repr=False)
    target_id: str

    def connect(self, schema=None):
        """Verify identity and marker before any schema or application writes."""
        from psycopg import sql
        db = PostgresConnection(self.url, connect_timeout=5,
                                options="-c statement_timeout=10000 -c lock_timeout=5000",
                                application_name="smartdesk-session3-tests")
        try:
            identity = db.execute("SELECT current_database() AS db, current_user AS role").fetchone()
            if identity != {"db": "smartdesk_test", "role": "smartdesk_test"}:
                raise RuntimeError("The isolated PostgreSQL test identity does not match")
            marker = db.connection.execute(
                "SELECT target_id FROM public.smartdesk_test_target WHERE target_id=%s",
                (self.target_id,)).fetchone()
            if marker is None:
                raise RuntimeError("The isolated PostgreSQL test marker does not match")
            if schema:
                if not re.fullmatch(r"smartdesk_test_[0-9a-f]{32}", schema):
                    raise RuntimeError("Invalid isolated test schema name")
                db.connection.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(schema)))
                db.schema = schema
            db.commit()
            return db
        except BaseException:
            db.connection.rollback()
            db.connection.close()
            raise


def approved_target(environ=None):
    """Validate the explicit target before opening even a read-only connection."""
    environ = os.environ if environ is None else environ
    url = environ.get("SMARTDESK_TEST_DATABASE_URL")
    if not url:
        raise MissingTestTarget("SMARTDESK_TEST_DATABASE_URL absent: PostgreSQL not executed")
    if environ.get("SMARTDESK_TEST_DATABASE_APPROVED") != "isolated-ephemeral":
        raise RuntimeError("Explicit isolated PostgreSQL test approval is required")
    target_id = environ.get("SMARTDESK_TEST_TARGET_ID", "")
    if not re.fullmatch(r"session3_[A-Za-z0-9_-]{8,100}", target_id):
        raise RuntimeError("An explicit Session 3 target marker is required")
    try:
        parsed = urlsplit(url)
        valid = (
            parsed.scheme in {"postgresql", "postgres"}
            and parsed.hostname in {"127.0.0.1", "localhost", "smartdesk-test-db"}
            and parsed.port is not None and 0 < parsed.port <= 65535
            and unquote(parsed.username or "") == "smartdesk_test"
            and bool(parsed.password)
            and unquote(parsed.path) == "/smartdesk_test"
            and not parsed.query and not parsed.fragment
        )
    except ValueError:
        valid = False
    if not valid:
        raise RuntimeError("Only the explicitly scoped local PostgreSQL test URL is allowed")
    return ApprovedTarget(url=url, target_id=target_id)

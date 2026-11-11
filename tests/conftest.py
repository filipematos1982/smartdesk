"""Fixtures de integração: base de dados isolada e cinco utilizadores fictícios.

Cada teste começa com uma base nova. Nenhum teste modifica dados reais.
"""
import os
import pytest
from fastapi.testclient import TestClient
from src.database import connect, initialize
from src.auth import hash_password
os.environ.setdefault('SMARTDESK_SESSION_SECRET', 'test-only-session-secret-at-least-32-characters')
from src.main import create_app

@pytest.fixture
def env(tmp_path):
    path = str(tmp_path / "smartdesk_test.sqlite3")
    with connect(path) as db:
        initialize(db)
        for name, email, role in (
            ("Ana", "ana@test", "employee"),
            ("Outro", "outro@test", "employee"),
            ("Miguel", "miguel@test", "technician"),
            ("Técnico 2", "technician2@test", "technician"),
            ("Sofia", "sofia@test", "responsavel"),
        ):
            db.execute("INSERT INTO users(name,email,secret,role) VALUES(?,?,?,?)",
                       (name, email, hash_password("Password123!"), role))
        db.commit()
    with TestClient(create_app(path=path, secret="test-secret-of-at-least-32-characters")) as client:
        yield client, path

def login(client, email, password="Password123!"):
    response = client.post("/login", data={"email": email, "password": password},
                           follow_redirects=False)
    assert response.status_code == 303
    return response

def person(db, email):
    return dict(db.execute("SELECT id,name,email,role FROM users WHERE email=?", (email,)).fetchone())

def create_ticket(db, title="Printer"):
    from src.services import create
    return create(db, person(db, "ana@test"), title, "Does not print", "Hardware")

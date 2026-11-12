"""RF-001/RNF-003, US-001, T-01/T-13: autenticação e sessão.

Esperado: credenciais corretas permitem consultar tickets; incorretas
não autenticam; sair invalida a sessão.
"""
from .conftest import post_form, login

def test_t01_valid_login_and_logout(env):
    client, _ = env
    login(client, "ana@test")
    assert client.get("/tickets").status_code == 200
    assert post_form(client, "/logout", follow_redirects=False).status_code == 303
    assert client.get("/tickets", follow_redirects=False).status_code == 303

def test_t13_wrong_password(env):
    client, _ = env
    response = post_form(client, "/login", data={"email": "ana@test", "password": "errada"})
    assert "Incorrect email or password." in response.text
    assert client.get("/tickets", follow_redirects=False).status_code == 303

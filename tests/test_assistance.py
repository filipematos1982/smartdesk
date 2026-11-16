"""Provisional local recommendations preserve manual decisions and MVP data."""
import socket

import pytest

from src.assistance import recommend
from src.database import connect
from tests.conftest import login, post_form


@pytest.mark.parametrize('title,description,category', [
    ('Printer toner cartridge', 'Paper jam printing device', 'Hardware'),
    ('Application crashes', 'Software update install program error', 'Software'),
    ('Password reset', 'Account locked authentication login denied', 'Access'),
])
def test_local_examples_are_deterministic_and_make_no_network_calls(monkeypatch, title, description, category):
    monkeypatch.setattr(socket, 'socket', lambda *a, **k: pytest.fail('Local recommendation attempted network access'))
    result = recommend(title, description)
    assert result == recommend(title, description)
    assert result['category'] == category
    assert result['provisional'] is True
    assert result['matched_terms']
    assert 0 <= result['similarity'] <= 1
    assert 'not probability' in result['limitations']


@pytest.mark.parametrize('text,priority', [
    ('All users report an outage', 'High'),
    ('Suspected ransomware data loss', 'High'),
    ('Cosmetic request when convenient', 'Low'),
    ('This is non-urgent', 'Low'),
    ('No outage and no breach', 'Normal'),
    ('Without data loss', 'Normal'),
    ('Normal support request', 'Normal'),
])
def test_priority_is_an_explained_provisional_suggestion(text, priority):
    result = recommend(text, '')
    assert result['priority'] == priority
    assert result['priority_definition']
    assert 'human review' in result['limitations']


@pytest.mark.parametrize('title,description', [('', ''), ('zxqv blrk', 'unrecognizableword')])
def test_unknown_input_does_not_force_a_category(title, description):
    result = recommend(title, description)
    assert result['category'] is None
    assert 'manually' in result['explanation']


@pytest.mark.parametrize('title,description', [('x'*201, ''), ('', 'x'*10001), (None, '')])
def test_input_is_bounded(title, description):
    with pytest.raises(ValueError):
        recommend(title, description)


@pytest.mark.parametrize('route', ['/api/assist/recommend', '/tickets/recommend'])
def test_recommendation_requires_authentication_csrf_and_permitted_role(env, route):
    client, path = env
    unauthenticated = post_form(client, route, data={'title':'Printer'})
    assert unauthenticated.status_code == (401 if route.startswith('/api/') else 200)
    if route == '/tickets/recommend':
        assert unauthenticated.url.path == '/login'
    login(client, 'miguel@test')
    assert post_form(client, route, data={'title':'Printer'}).status_code == 403
    post_form(client, '/logout')
    login(client, 'ana@test')
    assert client.post(route, data={'title':'Printer'}).status_code == 403
    assert post_form(client, route, data={'title':'x'*201}).status_code == 422
    assert post_form(client, route, data={'description':'x'*10001}).status_code == 422
    assert post_form(client, route, data={'title':'Printer'}).status_code == 200
    post_form(client, '/logout')
    login(client, 'sofia@test')
    assert post_form(client, route, data={'title':'Printer'}).status_code == 200
    with connect(path) as db:
        assert db.execute('SELECT count(*) AS n FROM tickets').fetchone()['n'] == 0


def test_form_advice_preserves_manual_category_escapes_input_and_creates_no_ticket(env):
    client, path = env
    login(client, 'ana@test')
    payload = '<script>alert("synthetic")</script> printer'
    response = post_form(client, '/tickets/recommend', data={
        'title':payload, 'description':'Printer toner cartridge', 'category':'Access'})
    assert response.status_code == 200
    assert '<script>' not in response.text
    assert '&lt;script&gt;' in response.text
    assert 'value="Access" selected' in response.text
    assert 'Suggested category:' in response.text and 'Hardware' in response.text
    assert 'Nothing is saved automatically' in response.text
    with connect(path) as db:
        assert db.execute('SELECT count(*) AS n FROM tickets').fetchone()['n'] == 0
        assert 'priority' not in {row['name'] for row in db.execute('PRAGMA table_info(tickets)')}
    result = post_form(client, '/tickets/new', data={'title':'Manual choice', 'description':'Printer toner', 'category':'Access'})
    assert result.status_code == 200
    with connect(path) as db:
        assert db.execute('SELECT category FROM tickets').fetchone()['category'] == 'Access'

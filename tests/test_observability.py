"""Check safe local health, monitoring, security headers and structured event output."""
import io
import json
import re
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import pytest

from src.observability import Telemetry
from tests.conftest import login, post_form


def capture(client):
    stream = io.StringIO()
    client.app.state.telemetry.logger.handlers[0].setStream(stream)
    return stream


def test_health_separates_liveness_from_database_readiness_without_error_leaks(env, monkeypatch):
    client, _ = env
    stream = capture(client)
    assert client.get('/health/live').json() == {'status':'live'}
    assert client.get('/health/ready').json() == {'status':'ready'}
    def unavailable(*args, **kwargs):
        raise RuntimeError('private-database-password-do-not-log')
    monkeypatch.setattr('src.main.connect', unavailable)
    assert client.get('/health/live').status_code == 200
    failed = client.get('/health/ready')
    assert failed.status_code == 503 and failed.json() == {'status':'not_ready'}
    assert 'private-database-password' not in failed.text + stream.getvalue()


@pytest.mark.parametrize('email,expected', [(None,401), ('ana@test',403), ('miguel@test',403), ('sofia@test',200)])
def test_monitoring_is_manager_only(env, email, expected):
    client, _ = env
    if email:
        login(client, email)
    response = client.get('/api/monitoring')
    assert response.status_code == expected
    if expected == 200:
        metrics = response.json()
        assert metrics['scope'] == 'single-process-local'
        assert metrics['counts']['requests'] > 0
        assert 'Resets on restart' in metrics['limitations']


def test_logs_are_allowlisted_and_request_ids_are_generated_server_side(env):
    client, _ = env
    stream = capture(client)
    secret = 'synthetic-secret-not-for-logs'
    response = client.get('/unknown/' + secret + '?password=' + secret,
                          headers={'X-Request-ID':secret, 'Cookie':'private='+secret})
    identifier = response.headers['x-request-id']
    assert re.fullmatch('[0-9a-f]{32}', identifier)
    assert identifier != secret
    post_form(client, '/login', data={'email':'private-email@test', 'password':secret})
    client.post('/login', data={'password':secret})
    login(client, 'sofia@test')
    events = [json.loads(line) for line in stream.getvalue().splitlines()]
    assert events
    assert all(set(event) == {'timestamp','event','request_id','method','route','status','duration_ms','actor_role'} for event in events)
    assert secret not in stream.getvalue() and 'private-email@test' not in stream.getvalue()
    assert any(event['route']=='unmatched' for event in events)
    assert any(event['event']=='authentication_failed' for event in events)
    assert any(event['event']=='authentication_succeeded' for event in events)
    metrics = client.get('/api/monitoring').json()
    assert metrics['counts']['authentication_failures'] == 1
    assert metrics['counts']['client_errors'] >= 2


@pytest.mark.parametrize('path', ['/login','/health/live','/missing'])
def test_security_headers_cover_success_and_error_responses(env, path):
    client, _ = env
    response = client.get(path)
    assert response.headers['cache-control'] == 'no-store'
    assert response.headers['x-content-type-options'] == 'nosniff'
    assert response.headers['x-frame-options'] == 'DENY'
    assert response.headers['referrer-policy'] == 'no-referrer'
    assert "frame-ancestors 'none'" in response.headers['content-security-policy']
    assert response.headers['strict-transport-security'].startswith('max-age=')


def test_unhandled_error_is_redacted_and_counted(env):
    client, _ = env
    stream = capture(client)
    @client.app.get('/qa-failing-route')
    def failing():
        raise RuntimeError('private-exception-value')
    response = client.get('/qa-failing-route')
    assert response.status_code == 500
    assert response.json() == {'detail':'Internal server error'}
    assert 'private-exception-value' not in response.text + stream.getvalue()
    assert client.app.state.telemetry.snapshot()['counts']['server_errors'] == 1


def test_metrics_are_process_local_bounded_and_thread_safe():
    telemetry = Telemetry()
    telemetry.logger.handlers[0].setStream(io.StringIO())
    def request(number):
        telemetry.record({'route':SimpleNamespace(path='/route/'+str(number)), 'method':'GET'}, 200, .001)
    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(request, range(200)))
    result = telemetry.snapshot()
    assert result['counts']['requests'] == 200
    assert len(result['routes']) <= 65
    assert sum(route['requests'] for route in result['routes'].values()) == 200
    assert Telemetry().snapshot()['counts']['requests'] == 0

"""Measure a synthetic loopback workload and exercise installed branded browsers.

This opt-in local check uses only a new SQLite database and new browser profiles.
It is separate from PostgreSQL, container, and instructor-specific acceptance.
"""
import argparse
import json
import os
from pathlib import Path
import re
import socket
import threading
import time

import httpx
import uvicorn

BROWSERS = {
    'chrome': Path('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'),
    'edge': Path('/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge'),
}
PASSWORD = 'Synthetic-session4-browser-password'


def conditions():
    return {
        'database': 'new isolated SQLite file; 3 synthetic users and 30 synthetic tickets',
        'transport': 'loopback HTTP with local-lab secure-cookie exception',
        'workload': 'one client; one warmup then 10 sequential GETs per page; no concurrency',
        'pages': ['/login', '/tickets (technician)', '/tickets/1 (technician)'],
        'measurement': 'wall-clock request plus complete response body; each measured response <= 3 seconds',
        'threshold_seconds': 3.0,
        'limits': 'small warm synthetic workload; no production load or PostgreSQL timing; not instructor certification',
    }


def seed(database):
    from src.auth import hash_password
    from src.database import connect, initialize
    from src import services
    with connect(str(database)) as db:
        initialize(db)
        people = []
        for role in ('employee', 'technician', 'responsavel'):
            result = db.execute('INSERT INTO users(name,email,secret,role) VALUES(?,?,?,?)',
                                (role, role + '@session4.test', hash_password(PASSWORD), role))
            people.append({'id': result.lastrowid, 'role': role})
        db.commit()
        for number in range(30):
            ticket = services.create(db, people[0], 'Synthetic ticket ' + str(number),
                                     'Synthetic local validation data', 'Hardware')
            services.assign(db, people[2], ticket['id'], people[1]['id'])


def measure(base):
    measurements = {}
    with httpx.Client(base_url=base, follow_redirects=True, trust_env=False, timeout=10) as client:
        for page in ('/login',):
            measurements[page] = page_timings(client, page)
        login = client.get('/login')
        token = re.search(r'name="csrf-token" content="([^"]+)"', login.text).group(1)
        response = client.post('/login', data={'email':'technician@session4.test',
                                             'password':PASSWORD, 'csrf_token':token})
        assert response.status_code == 200 and response.url.path == '/tickets'
        for page in ('/tickets', '/tickets/1'):
            measurements[page] = page_timings(client, page)
    return measurements


def page_timings(client, page):
    warmup = client.get(page)
    assert warmup.status_code == 200
    values = []
    for _ in range(10):
        start = time.perf_counter()
        response = client.get(page)
        content = response.content
        elapsed = time.perf_counter() - start
        assert response.status_code == 200 and content
        values.append(elapsed)
    assert max(values) <= 3.0, f'{page} exceeded the approved provisional three-second target'
    return {'status':'passed', 'samples_seconds':values, 'maximum_seconds':max(values)}


def browser_check(name, executable, base, output):
    if not executable.is_file():
        return {'status':'skipped', 'reason':'Installed branded browser executable is absent', 'path':str(executable)}
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return {'status':'skipped', 'reason':'Optional Playwright tooling is not installed'}
    profile = output / (name + '-new-profile')
    profile.mkdir(mode=0o700)
    with sync_playwright() as playwright:
        context = playwright.chromium.launch_persistent_context(
            str(profile), executable_path=str(executable), headless=True,
            args=['--disable-sync', '--disable-background-networking', '--disable-component-update',
                  '--disable-default-apps', '--disable-extensions', '--no-first-run',
                  '--password-store=basic', '--use-mock-keychain'])
        try:
            page = context.new_page()
            page.set_default_timeout(15000)
            response = page.goto(base + '/login')
            assert response.status == 200
            page.locator('input[name=email]').fill('employee@session4.test')
            page.locator('input[name=password]').fill(PASSWORD)
            page.locator('form[action="/login"] button').click()
            page.wait_for_url(base + '/tickets')
            response = page.goto(base + '/tickets/new')
            assert response.status == 200
            title = 'Real ' + name + ' synthetic ticket'
            page.locator('input[name=title]').fill(title)
            page.locator('textarea[name=description]').fill('Created by a fresh browser profile')
            page.locator('select[name=category]').select_option('Hardware')
            page.locator('form[action="/tickets/new"] button').click()
            page.wait_for_url(re.compile(re.escape(base) + r'/tickets/\d+$'))
            assert title in page.locator('h2').inner_text(), 'Created ticket title was not displayed'
            assert page.get_by_text('Open', exact=True).count() > 0
            user_agent = page.evaluate('navigator.userAgent')
            return {'status':'passed', 'user_agent':user_agent,
                    'checks':['real browser login', 'CSRF form submission', 'ticket creation and detail'],
                    'profile':profile.name}
        finally:
            context.close()


def run(output):
    output = Path(output).resolve()
    os.umask(0o077)
    output.mkdir(parents=True, mode=0o700, exist_ok=False)
    (output / 'conditions.json').write_text(json.dumps(conditions(), indent=2) + '\n')
    # All service configuration is synthetic and process-local; the DB path is explicit.
    os.environ['SMARTDESK_SESSION_SECRET'] = 'synthetic-session4-local-signing-key-at-least-32-characters'
    os.environ['SMARTDESK_COOKIE_SECURE'] = 'false'
    os.environ['SMARTDESK_SESSION_MAX_AGE'] = '3600'
    from src.main import create_app
    database = output / 'synthetic.sqlite3'
    seed(database)
    app = create_app(path=str(database))
    server = uvicorn.Server(uvicorn.Config(app, host='127.0.0.1', port=0, log_level='error', access_log=False))
    listener = socket.socket()
    listener.bind(('127.0.0.1', 0))
    listener.listen(128)
    base = 'http://127.0.0.1:' + str(listener.getsockname()[1])
    thread = threading.Thread(target=server.run, kwargs={'sockets':[listener]}, daemon=True)
    thread.start()
    results = {}
    try:
        for _ in range(100):
            if server.started:
                break
            if not thread.is_alive():
                raise RuntimeError('Owned loopback server stopped during startup')
            time.sleep(0.1)
        else:
            raise RuntimeError('Owned loopback server did not become ready')
        try:
            results['performance'] = {'status':'passed', 'pages':measure(base)}
        except Exception as exc:
            results['performance'] = {'status':'failed', 'reason':type(exc).__name__ + ': ' + str(exc)}
        for name, executable in BROWSERS.items():
            try:
                results[name] = browser_check(name, executable, base, output)
            except Exception as exc:
                # No browser trace, cookie, password or token is written to public reports.
                results[name] = {'status':'failed', 'reason':type(exc).__name__}
    finally:
        server.should_exit = True
        thread.join(timeout=15)
        listener.close()
    counts = {status:sum(result['status']==status for result in results.values())
              for status in ('passed','failed','skipped')}
    summary = {'results':results, 'counts':counts, 'warnings':0,
               'server_stopped':not thread.is_alive(), 'conditions_file':'conditions.json'}
    (output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))
    return 1 if counts['failed'] or thread.is_alive() else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--approve-local-acceptance', action='store_true')
    parser.add_argument('--output-dir', required=True, type=Path)
    args = parser.parse_args()
    if not args.approve_local_acceptance:
        parser.error('Explicit approval for new synthetic data and new browser profiles is required')
    return run(args.output_dir)


if __name__ == '__main__':
    raise SystemExit(main())

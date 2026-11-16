"""Start a new loopback-only synthetic SQLite demo without Docker or cloud access."""
import argparse
from contextlib import contextmanager
import json
import os
from pathlib import Path
import re
import secrets
import signal
import socket
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[1]


def prepare(output):
    """Create only new private files; never accept an existing database target."""
    output = Path(output).resolve()
    if output.parent != ROOT / 'reports' or not re.fullmatch(r'submission-demo-[A-Za-z0-9_-]+', output.name):
        raise ValueError('Choose a new reports/submission-demo-<unique-id> directory')
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    from src.auth import hash_password
    from src.database import connect, initialize
    database = output / 'synthetic.sqlite3'
    accounts = []
    with connect(str(database)) as db:
        initialize(db)
        for name, email, role in (
            ('Demo Employee', 'employee@smartdesk.test', 'employee'),
            ('Other Employee', 'other@smartdesk.test', 'employee'),
            ('Demo Technician', 'technician@smartdesk.test', 'technician'),
            ('Demo Manager', 'manager@smartdesk.test', 'responsavel'),
        ):
            password = secrets.token_urlsafe(18)
            db.execute('INSERT INTO users(name,email,secret,role) VALUES(?,?,?,?)',
                       (name, email, hash_password(password), role))
            accounts.append({'name': name, 'email': email, 'role': role, 'password': password})
    credentials = output / 'accounts.private.json'
    with credentials.open('x') as file:
        os.chmod(credentials, 0o600)
        json.dump(accounts, file, indent=2)
        file.write('\n')
    os.chmod(database, 0o600)
    return database


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8765, help='Loopback port; 0 selects a free port')
    parser.add_argument('--output-dir', type=Path,
                        default=ROOT / 'reports' / ('submission-demo-' + secrets.token_hex(6)))
    args = parser.parse_args()
    if not 0 <= args.port <= 65535:
        parser.error('Port must be between 0 and 65535')
    # No inherited cloud, database, proxy, registry or service credentials.
    path = os.environ.get('PATH', '/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin')
    os.environ.clear()
    os.environ.update(PATH=path, PYTHONDONTWRITEBYTECODE='1', PIP_CONFIG_FILE='/dev/null',
                      SMARTDESK_SESSION_SECRET=secrets.token_urlsafe(48),
                      SMARTDESK_COOKIE_SECURE='false', SMARTDESK_SESSION_MAX_AGE='3600',
                      SMARTDESK_SEED_DEMO_USERS='0')
    sys.dont_write_bytecode = True
    os.umask(0o077)
    listener = socket.socket()
    try:
        listener.bind(('127.0.0.1', args.port))
        listener.listen(128)
        output = args.output_dir.resolve()
        database = prepare(output)
        from src.main import create_app
        import uvicorn
        app = create_app(path=str(database))
        class DemoServer(uvicorn.Server):
            @contextmanager
            def capture_signals(self):
                # This owned CLI handles graceful signals without Uvicorn replay.
                # Replayed SIGTERM would terminate before the manifest finally block.
                yield
        server = DemoServer(uvicorn.Config(app, log_level='warning', access_log=False,
                                           proxy_headers=False))
        manifest = {'database_backend': 'sqlite', 'synthetic_data_only': True,
                    'pid': os.getpid(), 'host': '127.0.0.1',
                    'port': listener.getsockname()[1], 'status': 'starting',
                    'azure_spending_authorized_eur': 0, 'ai_api_spending_authorized_eur': 0}
        def save():
            target = output / 'manifest.json'
            target.write_text(json.dumps(manifest, indent=2) + '\n')
            os.chmod(target, 0o600)
        save()
        stopped = threading.Event()
        def watch():
            for _ in range(600):
                if stopped.is_set():
                    return
                if server.started:
                    manifest['status'] = 'ready'
                    save()
                    print(f"Demo ready: http://127.0.0.1:{manifest['port']}/login", flush=True)
                    print(f'Private synthetic accounts: {output / "accounts.private.json"}', flush=True)
                    return
                time.sleep(0.05)
        watcher = threading.Thread(target=watch, daemon=True)
        watcher.start()
        def graceful_exit(signum, frame):
            server.should_exit = True
        previous = {number: signal.signal(number, graceful_exit)
                    for number in (signal.SIGINT, signal.SIGTERM)}
        try:
            server.run(sockets=[listener])
        finally:
            for number, handler in previous.items():
                signal.signal(number, handler)
            stopped.set()
            watcher.join(timeout=2)
            manifest['status'] = 'stopped'
            save()
    except (OSError, ValueError) as exc:
        parser.exit(1, f'Local demo refused: {type(exc).__name__}; existing data was not reused.\n')
    finally:
        listener.close()


if __name__ == '__main__':
    main()

# SmartDesk — Support Ticket Management

SmartDesk is a personal training project with a FastAPI/Jinja web interface and PostgreSQL persistence. The approved [MVP](docs/produto/03_mvp_backlog_e_aceitacao.md), [requirements](docs/produto/02_requisitos_e_user_stories.md), and [Gherkin scenarios](features/tickets.feature) remain authoritative. Existing database values and API route names are preserved.

## MVP responsibilities

- Employees create and view their own tickets and report unresolved problems.
- Technicians view assigned tickets, start work, and record a resolution.
- Managers view all tickets, assign or reassign technicians, and close resolved tickets after checking the solution.
- States: `Open → In Progress → Resolved → Closed`; a resolved ticket can return to `In Progress`. Closed tickets cannot reopen.
- Categories: `Hardware`, `Software`, and `Access`. Title, description, and category are required.

## Local Docker setup

Prerequisite: Docker with Docker Compose and Linux container support. Run commands from the personal SmartDesk checkout. These instructions describe approved procedures; they do not prove that a build or database validation has run.

### 1. Obtain the personal repository

```bash
git clone https://github.com/filipematos1982/smartdesk.git
cd smartdesk
```

For an existing checkout, use its current directory and preserve local work; do not clone over it or reset it.

### 2. Prepare local configuration

If `.env` does not exist, copy the supplied example without overwriting an existing file:

```bash
cp -n .env.example .env
```

Edit `.env` locally before starting containers:

- Replace `POSTGRES_PASSWORD` with a unique random password using URL-safe letters, digits, `-`, and `_`. The current Compose file interpolates credentials into a URI without percent encoding. Broader URI-safe connection construction belongs to Session 3.
- Replace `SMARTDESK_SESSION_SECRET` with a different random signing key of at least 32 characters. It is not a login password. Generate it with a password manager or a local cryptographic generator; never paste it into Git, logs, or chat. The supplied placeholder is not a usable secret.
- `SMARTDESK_COOKIE_SECURE=false` is an explicit exception for this loopback-only HTTP lab. The application defaults to secure cookies; use `true` with HTTPS. A secure cookie will not be sent over ordinary HTTP.
- `SMARTDESK_SESSION_MAX_AGE=3600` limits session cookie lifetime to one hour.
- Leave `SMARTDESK_SEED_DEMO_USERS=0`. Create synthetic users interactively instead of embedding login passwords in configuration.

Do not reuse production credentials. Environment files, local credential directories, private keys, test databases, and generated reports are excluded from Git. `.env.example` contains placeholders only.

Changing PostgreSQL initialization variables does not change credentials already stored in an existing database volume. Preserve that volume and arrange a separate approved credential change if necessary; never remove data to make setup succeed.

### 3. Build and create local demonstration accounts

```bash
docker compose build
docker compose up -d db
docker compose run --rm web python -m scripts.create_demo_users
```

The account script prompts privately for a password of at least eight characters and skips accounts that already exist. Use synthetic lab passwords only. It stores password hashes, not plaintext passwords.

| Role | Demonstration login |
| --- | --- |
| Employee | `ana@nexaserv.test` |
| Technician | `miguel@nexaserv.test` |
| Manager | `sofia@nexaserv.test` |

### 4. Start the local web application

```bash
docker compose up -d web
```

Open `http://localhost:8080/login`. Compose binds the web port to loopback and does not publish PostgreSQL. Existing data resides in the `postgres_data` named volume. This Session 2 work does not authorize deleting volumes, migrating data, or deploying to Kubernetes or Azure.

## Authentication and request security

Session cookies are signed, HTTP-only, use `SameSite=Lax`, and are secure by default. Keep the signing key private and consistent for a single deployment. Signed cookie contents are not encrypted: never store secrets in them. Login replaces the anonymous session and CSRF token; logout clears the browser session. A previously copied signed cookie cannot be centrally revoked by this single-process design before its expiry or signing-key rotation.

Every unsafe browser or cookie-authenticated API request requires a CSRF token. Forms include a hidden `csrf_token`; HTML pages also expose it through the `csrf-token` meta element. API clients first obtain a page in the same cookie session, then send its token as `X-CSRF-Token` on writes. After login, obtain the new token before further writes. Missing or invalid tokens return HTTP 403; route paths and existing business payload fields are unchanged.

Login throttling allows up to five failed attempts per 60-second window per socket client IP and returns HTTP 429 when exceeded. A successful login resets that address counter. Its bounded in-memory state is process-local and resets on restart. It is a local-lab defense, not a distributed limiter. Shared client IPs share a limit. Do not trust arbitrary forwarded headers; proxy identity and shared throttling require a separate deployment design.

## Session 2 automated validation

Local Python is optional for Docker operation. An existing development environment can run the following isolated SQLite/HTTP suite without contacting PostgreSQL or generating reports:

```bash
env -u DATABASE_URL PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest tests/ --ignore=tests/test_postgres.py -p no:cacheprovider -ra
```

The PostgreSQL file is intentionally excluded: its current fixture creates and drops schemas using `DATABASE_URL`. Do not run it against the application database. Session 3 requires a separately approved local test database and target guards before any PostgreSQL validation. Do not run the all-suite report script against the normal Compose environment.

The suite includes automated business-rule, HTTP, security, and BDD checks. Skipped performance and real Chrome/Edge criteria remain unvalidated; TestClient is not a real browser. See [Session 2 validation](docs/qualidade/04_session_2_validation.md) for actual commands, results, and limits from this implementation.

## Training boundaries and remaining work

- **Session 1:** approved requirements and Gherkin remain unchanged.
- **Session 2:** bootstrap, web authentication/CSRF/throttling, HTTP/SQLite regression checks, and container hardening. Automated success alone does not certify a running Docker deployment.
- **Session 3:** ticket concurrency, PostgreSQL transactions/persistence/recovery, isolated database validation, and local Kubernetes/k3s. Existing data and volumes must be preserved.
- **Session 4:** expanded PostgreSQL/security coverage, real browser/performance acceptance, reliable reports, Jenkins gates, and reproducible image delivery.
- **Session 5:** instructor-confirmed Azure preparation, actual regional pricing, networking/TLS/identity/monitoring/rollback, and separately authorized deployment.

Public exposure remains unapproved. PostgreSQL acceptance, concurrency remediation, distributed throttling, recovery, proxy configuration, and cloud readiness are not established by Session 2. No `/health` endpoint or new MVP feature is introduced here.

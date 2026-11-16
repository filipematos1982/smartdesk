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

- Replace `POSTGRES_PASSWORD` with a unique random password. Session 3 passes database credentials as separate psycopg parameters rather than interpolating them into a URI. Single-quote values containing `$` in the private `.env` to avoid Compose interpolation.
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

Open `http://localhost:8080/login`. Compose binds the web port to loopback and does not publish PostgreSQL. Existing data resides in the `postgres_data` named volume. Never delete an existing volume to repair a lab setup. Use only the dedicated Session 3 lab for validation; Azure deployment remains separately authorized.

## Authentication and request security

Session cookies are signed, HTTP-only, use `SameSite=Lax`, and are secure by default. Keep the signing key private and consistent for a single deployment. Signed cookie contents are not encrypted: never store secrets in them. Login replaces the anonymous session and CSRF token; logout clears the browser session. A previously copied signed cookie cannot be centrally revoked by this single-process design before its expiry or signing-key rotation.

Every unsafe browser or cookie-authenticated API request requires a CSRF token. Forms include a hidden `csrf_token`; HTML pages also expose it through the `csrf-token` meta element. API clients first obtain a page in the same cookie session, then send its token as `X-CSRF-Token` on writes. After login, obtain the new token before further writes. Missing or invalid tokens return HTTP 403; route paths and existing business payload fields are unchanged.

Login throttling allows up to five failed attempts per 60-second window per socket client IP and returns HTTP 429 when exceeded. A successful login resets that address counter. Its bounded in-memory state is process-local and resets on restart. It is a local-lab defense, not a distributed limiter. Shared client IPs share a limit. Do not trust arbitrary forwarded headers; proxy identity and shared throttling require a separate deployment design.

## Session 2 automated validation

Local Python is optional for Docker operation. An existing development environment can run the following isolated SQLite/HTTP suite without contacting PostgreSQL or generating reports:

```bash
env -u DATABASE_URL PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest tests/ --ignore=tests/test_postgres.py -p no:cacheprovider -ra
```

The command above intentionally excludes PostgreSQL. Session 3 PostgreSQL tests require `SMARTDESK_TEST_DATABASE_URL`, explicit approval, and a verified target marker; they never fall back to application `DATABASE_URL`. Each test creates a unique schema in the approved disposable target and leaves it intact. Do not point tests at the application database or an unknown target. See the Session 3 validation record for the verified local procedure.

The suite includes automated business-rule, HTTP, security, and BDD checks. Skipped performance and real Chrome/Edge criteria remain unvalidated; TestClient is not a real browser. See [Session 2 validation](docs/qualidade/04_session_2_validation.md) for actual commands, results, and limits from this implementation.

## Training boundaries and remaining work

Session 3 follows the confirmed training outline and the public instructor implementation reference. See [reference and Docker Hub boundaries](docs/arquitetura/05_session_3_reference.md), [PostgreSQL architecture](docs/arquitetura/04_persistencia_postgresql.md), and [executed Session 3 validation](docs/qualidade/05_session_3_validation.md). The full Notebook 09A/09B instructions are unavailable; their exact acceptance cannot be certified. Local builds and k3s image imports do not publish to Docker Hub.

- **Session 1:** approved requirements and Gherkin remain unchanged.
- **Session 2:** bootstrap, web authentication/CSRF/throttling, HTTP/SQLite regression checks, and container hardening. Automated success alone does not certify a running Docker deployment.
- **Session 3:** ticket concurrency, PostgreSQL transactions/persistence/recovery, isolated database validation, and local Kubernetes/k3s. Existing data and volumes must be preserved.
- **Session 4:** full automated-test inventory, fresh reports, required PostgreSQL CI gate, pinned Python dependencies, and local browser/performance validation where supported. See the Session 4 records below for actual results and runtime blockers.
- **Session 5:** local Azure preparation, current official EUR pricing, networking/TLS/identity/monitoring/rollback proposals, and explicit approval boundaries. Instructor-specific Azure requirements remain unconfirmed.

Public exposure remains unapproved. Session 2 alone does not establish PostgreSQL acceptance, concurrency remediation, recovery, proxy configuration, distributed throttling, or cloud readiness. Session 3 evidence is recorded separately. No `/health` endpoint or new MVP feature is introduced here.


## Session 4 local CI and delivery preparation

The [Session 4 reference](docs/arquitetura/06_session_4_reference.md) separates the authorized scope from unavailable instructor requirements. The [validation record](docs/qualidade/06_session_4_validation.md) records actual commands, counts, failures and unexecuted checks. Session 3 evidence does not substitute for validation of the changed Session 4 image.

`requirements.txt` records dependency ranges; `requirements.lock` records the complete Python 3.12 resolution used for this session. Docker installs the lock. The lock does not pin the base image or supply package hashes; Linux installation, image architecture and image runtime require their own successful checks.

Docker runtime validation is currently blocked because the available Docker environment is shared with unrelated/company projects. Do not run the runtime command below in that environment. A separately approved dedicated personal Docker environment is required.

After explicit local authorization, a dedicated personal Jenkins agent can run the reviewed `Jenkinsfile`. Configure its `smartdesk-personal-local` label, public personal SCM URL without credentials, Python 3, Git, Docker CLI/daemon and an explicit local Unix socket. The `LOCAL_DOCKER_HOST` build parameter defaults to `unix:///var/run/docker.sock`; a dedicated macOS agent needs its approved personal Docker Desktop socket instead. Never attach this job to a company agent or use an ambient remote Docker context.

The equivalent local infrastructure command is:

```bash
sh scripts/session4_ci.sh --approve-local-ci \
  --docker-host unix:///Users/filipematos/.docker/run/docker.sock \
  --output-dir reports/session4-ci-UNIQUE-RUN-ID
```

Choose a new output directory each time. The helper uses an empty Docker configuration, builds a unique local image, creates a labelled internal network and new tmpfs PostgreSQL target, verifies its identity, and runs tests as UID/GID 10001 with PostgreSQL required. It stops only containers whose recorded IDs and labels still match, and retains resources and private diagnostics. It never publishes images or applies deployments. A failed or skipped required PostgreSQL gate must prevent a successful CI result. Only fresh copied test artifacts are archived; generated database credentials and Docker state stay private and ignored.

A host regression run can use an isolated Python environment and the report runner:

```bash
env -i PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin \
  PYTHONDONTWRITEBYTECODE=1 /path/to/isolated/python \
  -m scripts.run_validation --output-dir reports/session4-tests-UNIQUE-RUN-ID
```

This host command has no approved PostgreSQL target and must report PostgreSQL skips. `--require-postgres` makes absent or skipped PostgreSQL integration a failure. Do not point it at an existing application database. Real browser/performance commands and their declared measurement conditions are recorded separately in the validation record.

Before any separately approved registry delivery, confirm the personal Docker Hub namespace, build platform, source commit, successful mandatory gates and image contents, then publish only with explicit authorization and verify the remote digest. Prepare the deployment with that immutable registry reference and confirmed target-cluster identity. The existing `k8s/` manifests and local k3s harness remain preparation inputs; no external deployment or registry publication is part of Session 4. Azure resource creation and deployment require separate authorization.


## Session 5 Azure preparation

The proposed training architecture uses Azure Container Apps Consumption, ACR Basic and PostgreSQL Flexible Server 16 with private database networking. Managed identity supplies narrowly scoped registry/secret access; Key Vault references keep runtime secrets out of committed configuration. HTTPS terminates at internal application ingress. The initial design exposes no public application endpoint and creates no AKS cluster. An instructor requirement for AKS has not been established.

See the [architecture and prerequisites](docs/arquitetura/07_session_5_azure.md), [deployment/verification/rollback runbook](docs/arquitetura/08_session_5_runbook.md), [current EUR cost assumptions](docs/arquitetura/09_session_5_costs.md), and [preparation validation record](docs/qualidade/07_session_5_preparation.md). Draft templates are under `infra/azure/`; local preparation tools are under `scripts/azure/`. Local validation does not establish Azure deployment success, subscription permissions, quota, TLS handshake, image compatibility, managed-identity access or private network connectivity.

West Europe is a proposed region, pending approval. The 730-hour model estimates EUR 46.29/month for a small scale-to-zero workload or EUR 70.51/month with continuous active app compute, before VAT and documented exclusions. Managed load-balancer and egress-IP charges are included. These estimates assume no free credits/grants and are not a spending cap or binding offer.

Azure CLI is not currently installed. Do not authenticate, inspect an account/subscription, run a cloud plan/what-if, create resources, publish an image, expose the application, or deploy from this preparation. The current shared Docker environment remains off limits. A future deployment needs explicit personal-account/region/budget approval, a dedicated image/PostgreSQL/Jenkins validation environment, protected Terraform state, private administrative access, reviewed secrets and database bootstrap, an immutable tested image digest, and separate approval of the exact infrastructure plan. Public publication requires another security/ingress review and authorization. Cleanup remains a reviewed procedure; no database, backup or resource deletion is authorized.

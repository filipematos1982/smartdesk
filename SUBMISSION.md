# SmartDesk submission — 17 November 2026

**Submission date: 17 November 2026. Oral presentation: 26 November 2026.** These are different deadlines. This document is the current implementation/submission entry point. Earlier planning documents are preserved as dated history and may describe the pre-implementation state.

SmartDesk retains the approved ticket MVP and adds provisional local teaching extensions for Sessions 6–7. Confirmed course topics are preserved; detailed Session 6–8 instructor acceptance criteria remain **UNCONFIRMED**. Local implementation/test success does not establish instructor sign-off.

## Run the application locally

Use an existing isolated Python 3.12 environment with `requirements.lock` installed. The validated environment and exact verification results are recorded in [submission validation](docs/qualidade/08_submission_validation.md). If a new environment is needed, create it inside a new ignored reports directory and install the lock using only public package sources; never overwrite `.venv` or reuse company credentials.

For a source-package recipient without that environment, choose a genuinely new directory and install the locked application/test dependencies first (use an installed Python 3.12 executable):

```bash
test ! -e reports/submission-env-UNIQUE && \
python3.12 -m venv reports/submission-env-UNIQUE/venv && \
env -i PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin PIP_CONFIG_FILE=/dev/null \
  PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1 \
  reports/submission-env-UNIQUE/venv/bin/python -m pip install \
  --index-url https://pypi.org/simple -r requirements.lock
```

Stop if the new-directory check fails; do not overwrite an environment. Replace the Python path in subsequent commands with this new environment's `venv/bin/python`. Public package downloading is not Azure or AI API usage. Optional real-browser/coverage tools are declared separately in `requirements-qa.txt` and are not necessary to start the app.

From the personal project root, using the existing validated environment:

```bash
env -i PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 \
  reports/session4-qa-tools-bcfab7d03e/venv/bin/python -m scripts.run_local_demo --port 8765
```

The launcher binds only `127.0.0.1`, creates a new private `reports/submission-demo-<unique-id>/` directory, a synthetic SQLite database and four random-password accounts. It prints the ready URL and private account-file location after startup. Read that **new synthetic** `accounts.private.json` locally for the employee, other employee, technician and manager logins. Do not share or commit it. No existing database is opened, no `.env` is read, and no Docker or cloud account is used. If port 8765 is occupied, choose another unused port or `--port 0`; do not stop an unrelated process.

Open the printed `/login` URL. Use the employee to create tickets; manager to assign and close; assigned technician to start and resolve; employee to return a resolved ticket to handling. The other employee demonstrates visibility isolation. Closed tickets cannot reopen. Category choices and stored role/state values are unchanged.

Ctrl+C stops only this foreground demo. Its data/evidence remain intact. A new invocation creates a new database; it does not reopen or delete an earlier run. The explicit HTTP secure-cookie exception is restricted to this loopback demonstration; it is not public-deployment guidance. This launcher demonstrates SQLite, not PostgreSQL.

## Session 6 — provisional offline assistance

On the employee ticket form, enter an English title/description and choose **Suggest category and priority locally**. The suggestion is displayed without creating a ticket or changing the selected category. Select the final category yourself before normal ticket creation. Managers may also use the authenticated API; technicians cannot request assistance.

`POST /api/assist/recommend` accepts form fields `title` (up to 200 characters) and `description` (up to 10,000 characters) in an authenticated, CSRF-protected employee/manager session. `POST /tickets/recommend` returns the form with escaped input and the recommendation. No schema change or persisted priority is introduced.

The implementation uses a small deterministic TF-IDF nearest-example retrieval model over nine synthetic English examples, using the standard library only. It is not generative AI or a calibrated production classifier. The existing categories are Hardware, Software and Access. Weak/ambiguous matches return no suggested category. Similarity is not a probability. Source thresholds are provisional design constants, not instructor criteria.

| Provisional recommendation | Local illustrative meaning |
| --- | --- |
| High | Text suggests a widespread outage, security incident or data loss; review promptly. |
| Normal | Impact is not established; review through the ordinary support queue. |
| Low | Text explicitly describes a cosmetic or non-urgent request; review when scheduled. |

These advisory impact rules are not SLAs, official priority definitions or the MVP's development backlog P0/P1 labels. English phrase matching has limitations; human review is required. Nothing is applied automatically. There are no network calls, paid APIs, external models, API keys or inference charges.

## Session 7 — local security and observability

Existing password hashing, signed HTTP-only sessions, CSRF protection, role/ownership authorization and login throttling remain. Responses add no-store, content-type protection, frame denial, referrer policy, CSP and server-generated request IDs; HTTPS responses additionally receive HSTS. Existing proxy/session-revocation limitations remain documented and public exposure is not approved.

- `/health/live`: minimal liveness response, independent of database availability.
- `/health/ready`: executes a database query and returns 200 or a minimal 503 without connection/exception details. Startup still requires successful initialization.
- `/api/monitoring`: authenticated manager-only JSON with per-process request/error/authentication-failure counters, bounded route-template labels, aggregate request duration and uptime. Refresh after activity to observe updated counters.

Structured JSON stdout events record request/authentication outcomes, generated request ID, method, route template, status, duration and allowlisted actor role. They do not record passwords, tokens, cookies, query strings, raw unknown paths, emails or ticket bodies. Metrics reset on restart; there is no external monitoring platform, persistent audit store, alert delivery or cloud service. Those capabilities and instructor-specific logging/monitoring acceptance remain unconfirmed.

Docker/Compose readiness points to `/health/ready`; Kubernetes startup/liveness uses `/health/live` and readiness uses `/health/ready`. These integrations are statically reviewed only until a dedicated runtime environment is approved. Do not operate the current shared Docker environment.

## Tests, integration and evidence

Read [the actual submission validation record](docs/qualidade/08_submission_validation.md) for commands, environment versions, pass/fail/skip/warning counts, corrected failures and real loopback verification. Historical Session 1–5 records remain unchanged; older counts are not added to the new suite.

A new native PostgreSQL 17.9 target was created solely for this submission's integration tests using installed binaries, a private data directory, unique loopback port, synthetic credentials and an identity marker. No existing database or Docker resource is used. This does not prove PostgreSQL 16 Docker compatibility or Kubernetes rollout. Test schemas and target files are preserved; only the exact owned test process may be stopped.

## Session 8 — submission package

The source package is generated locally with `scripts.package_submission`, using a reviewed successful normal report summary. It includes allowlisted source/tests/docs/templates plus a per-file SHA-256 manifest and numeric-only test evidence. It excludes `.git`, environments, raw reports/logs, account files, databases, Terraform state/plans, actual secrets and company configuration. The archive records the source commit and whether reviewed working files are uncommitted; file hashes identify exactly what is included. Private historical evidence paths may be referenced by documentation but their contents are intentionally not distributed.

```bash
env -i PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 \
  reports/session4-qa-tools-bcfab7d03e/venv/bin/python -m scripts.package_submission \
  --evidence-summary reports/REVIEWED-SUBMISSION-RUN/summary.json \
  --output-dir reports/submission-package-NEW-UNIQUE-ID
```

Use the actual reviewed evidence path from the validation record and a new output directory. Verify `SHA256SUMS` before handing over the archive. No upload, Git push or automatic submission occurs. Final grading rubric, presentation format/duration and submission channel/time remain **UNCONFIRMED**; the known submission date is 17 November.

## Delivery limits

Azure is **Prepared, not deployed**, with **EUR 0** spending authorized. AI API spending authorization is **EUR 0**. No promotional credits, Azure authentication, resources or deployment are used. The preserved paid Azure architecture is reference material only and cannot be provisioned under the current policy.

Session 6 feature design and Session 7 observability are provisional local extensions, not invented official requirements. Docker image runtime, current Kubernetes rollout, actual Jenkins execution, registry publication, Edge browser acceptance and cloud deployment remain separate unverified items. Do not claim them from unit tests, static files, historical execution or an HTTP 200 alone. Existing company/unrelated resources must remain untouched.

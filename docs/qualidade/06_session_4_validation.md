# Session 4 implementation and validation

## Baseline and authorization

Started on clean branch `main`, commit `7dbe1ce743c4c8f791a2486f6c4a43644e788c32`. The configured local tracking reference reported three commits ahead; no remote fetch or push was performed. The user explicitly handed over Session 4 files, confirmed no other specialist was active, and authorized implementation, local tests and a local commit. DevOps completed and returned ownership before QA started. No specialists worked concurrently.

The confirmed scope and missing instructor material are recorded in [Session 4 reference](../arquitetura/06_session_4_reference.md). Session 3 results remain historical evidence and are not presented as validation of the changed Session 4 image.

## Dependencies and environment

The coordinator created a new CPython 3.12.13 environment under `reports/session4-dependencies-876fd0327407/venv` on macOS 26.6.2 arm64. It used a sanitized process environment, public PyPI, disabled pip configuration/cache, and the existing dependency ranges. Exact resolved transitive versions were saved to `requirements.lock`; `pip check` reported no broken requirements. The existing `.venv` was preserved.

Dependency preparation commands (process environments were sanitized; private logs are ignored):

```bash
/opt/homebrew/bin/python3.12 -m venv reports/session4-dependencies-876fd0327407/venv
reports/session4-dependencies-876fd0327407/venv/bin/python -m pip install --index-url https://pypi.org/simple -r requirements.txt
reports/session4-dependencies-876fd0327407/venv/bin/python -m pip freeze
reports/session4-dependencies-876fd0327407/venv/bin/python -m pip check
reports/session4-dependencies-876fd0327407/venv/bin/python -m pip download --index-url https://pypi.org/simple --only-binary=:all: --no-deps --platform manylinux_2_28_aarch64 --platform manylinux2014_aarch64 --python-version 3.12 --implementation cp --abi cp312 --dest reports/session4-dependencies-876fd0327407/linux-arm64-wheels -r requirements.lock
```

All commands completed successfully. The wheel availability check downloaded 36 wheels. It did not execute Linux code or prove image installation. The lock has no package hashes, was resolved on macOS, and does not pin the Python base image or PostgreSQL image digest; byte-for-byte image reproducibility is not established.

Optional host QA tools are declared separately in `requirements-qa.txt` and were installed in `reports/session4-qa-tools-bcfab7d03e/venv`: Playwright 1.65.2 and coverage 7.17.3. They do not change the runtime image dependency set.

## Jenkins and local image workflow

The revised pipeline selects a dedicated personal agent, restricts SCM to the public personal repository without configured credentials, disables ambient Git credential helpers/prompts, disables concurrent builds, sets a timeout, and selects a new report directory per build. Its `LOCAL_DOCKER_HOST` parameter must select an approved dedicated personal Unix socket; it does not authorize using the current shared daemon. Its shell helper builds a uniquely tagged local image, prepares a newly labelled internal network and tmpfs PostgreSQL target, verifies identity/marker, and runs the full suite with PostgreSQL required as UID/GID 10001. It checks subprocess and container exit status and requires fresh nonempty JUnit reports. Generated secrets and build diagnostics are excluded from archived test artifacts. GitHub Checks publication is disabled. No registry publication or deployment stage exists.

The helper stops only recorded containers whose names, IDs and ownership labels still match. It retains containers, networks, images and diagnostics, and never deletes databases, volumes or schemas. Resource retention is intentional; disk cleanup requires separate authorization.

DevOps validation passed shell syntax and embedded Python AST checks, refusal without explicit authorization, refusal of a remote TCP endpoint, and refusal to reuse an existing report directory without changing its manifest. The actual helper invocation failed safely with exit 1 because the explicit local Docker socket was unavailable. Evidence: `reports/session4-ci-devops-daemon-refusal-8e71a1/manifest.json`; zero resources were created.

```bash
sh -n scripts/session4_ci.sh
sh scripts/session4_ci.sh --approve-local-ci --docker-host unix:///Users/filipematos/.docker/run/docker.sock --output-dir reports/session4-ci-devops-daemon-refusal-8e71a1
```

The initial Docker daemon check failed while Docker was offline. The user later reported that Docker Desktop was running but shared with unrelated/company projects, and explicitly prohibited Docker runtime operations. No further Docker commands were run after that instruction. The current blocker is the shared environment, not an assertion that the daemon remains offline. Consequently Docker build, Linux dependency installation in the image, non-root runtime, PostgreSQL integration and local k3s deployment are blocked and not executed in this session. No ambient database target or Kubernetes context was substituted. Jenkins controller-backed declarative linting and a real pipeline build were not executed; shell/static/mocked evidence cannot certify Jenkins execution or agent/plugin configuration.

## QA execution

QA completed its assignment and returned ownership before the coordinator performed final review. Application files under `src/`, approved persisted values, product requirements and Gherkin scenarios were unchanged.

| Check | Actual result |
| --- | --- |
| Focused report/failure/ownership regression tests | 20 passed, 0 failed, 1 warning |
| Full Python 3.12 suite under coverage | 116 passed, 0 failed, 21 skipped, 1 warning; 14.05 seconds |
| Complete normal report runner | 116 passed, 0 failed, 21 skipped; exit 0 |
| Report runner with required PostgreSQL | Same test counts; **exit 1 as required**, `postgres_executed=false` |
| Source statement coverage | 349/382 statements covered; 33 missed; 91.36% (displayed as 91%) |
| Final standalone loopback/browser acceptance | 2 aggregate checks passed, 0 failed, 1 skipped; summary records 0 warnings |
| Final shell and embedded Python syntax | Passed |
| Python AST checks for changed/new scripts and tests | Passed |
| Final whitespace check | Passed |

The full-suite warning is the existing Starlette deprecation concerning HTTPX-backed TestClient. Reporting launches five independent suite processes, each emitting that same warning once (five emissions per report-run command). The 21 suite skips are 18 PostgreSQL cases plus three legacy BDD browser/performance placeholders. Their skip status is retained even though the separate acceptance helper now supplies limited performance and Chrome evidence. No skip is counted as a pass, and statement coverage is not a claim of complete acceptance or branch coverage.

Existing authentication, session/cookie/CSRF, role visibility, denied mutations and ticket lifecycle cases passed using isolated SQLite/HTTP tests. PostgreSQL identity guards and infrastructure ownership checks were exercised with mocks; actual PostgreSQL transactions, persistence and concurrency were not revalidated in Session 4. The reporting regression tests inject failed subprocesses, JUnit failures/errors, missing/malformed/empty XML, PostgreSQL skips and existing output directories. Infrastructure mocks demonstrate exit-status/report failure propagation and refusal of foreign ownership without making Docker calls. Mock success is not image acceptance.

Exact QA invocations used the new optional tooling environment, sanitized process environments, disabled bytecode and pytest caches, and unique/private evidence paths:

```bash
QA_PY=reports/session4-qa-tools-bcfab7d03e/venv/bin/python

env -i PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 \
  "$QA_PY" -m pytest tests/test_validation.py tests/test_session4_ci.py -q -rs -p no:cacheprovider

env -i PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 \
  COVERAGE_FILE=reports/session4-qa-coverage.data \
  "$QA_PY" -m coverage run --source=src -m pytest tests/ -q -rs -p no:cacheprovider \
  --junitxml=reports/session4-qa-full-junit.xml

env -i PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 \
  "$QA_PY" -m scripts.run_validation --output-dir reports/session4-qa-report-normal

env -i PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 \
  "$QA_PY" -m scripts.run_validation --output-dir reports/session4-qa-report-strict --require-postgres

env -i PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 \
  "$QA_PY" -m scripts.session4_acceptance --approve-local-acceptance \
  --output-dir reports/session4-acceptance-20261116-qa2
```

The required-PostgreSQL invocation intentionally fails the gate; it is a successful verification of refusal behavior, not a successful integration run. To repeat a report or acceptance command, choose a new output directory; existing evidence must not be reused or overwritten. The runner now defaults to a unique `reports/validation-<uuid>` directory rather than overwriting the old fixed report paths. Legacy report status keys and existing report presentation remain unchanged; broader translation remains a separate task.

### Performance conditions and real browser evidence

Before the acceptance run, `conditions.json` recorded a new SQLite file, three synthetic users, 30 synthetic tickets assigned to the technician, loopback HTTP, one client, one warmup per page, and ten sequential complete-response timings per page. Each measured request must meet the existing provisional target of at most three seconds. There was no concurrent load. The secure-cookie exception applies only to this synthetic loopback HTTP server.

| Page | Maximum measured response |
| --- | --- |
| `/login` | 0.000936 seconds |
| `/tickets`, signed in as technician | 0.001310 seconds |
| `/tickets/1`, signed in as technician | 0.000862 seconds |

These are warm, small-data HTTP timings, not page rendering measurements, production capacity, PostgreSQL latency, a full browser matrix, or instructor acceptance. Full timings remain in the private summary. Branded headless Chrome 157 completed login, CSRF form submission, ticket creation and detail viewing using a newly created persistent profile. The installed Edge executable was absent and explicitly skipped. Existing browser profiles, browser credentials and account stores were not opened. Browser executable discovery currently uses macOS application paths. The owned loopback server stopped; synthetic data and new profiles remain preserved in ignored private evidence.

The initial Chrome attempt failed because the new harness required an exact title-only heading while the existing application heading includes a ticket ID. Only the harness assertion was corrected; a fresh profile/database repeat passed. This corrected development failure is retained in `reports/session4-acceptance-20261116-qa1/summary.json`. A coverage JSON export and a coordinator here-document syntax check initially hit read-only sandbox restrictions; the authorized escalated reruns succeeded. Neither was an application test failure.

Evidence retained and ignored by Git:

- `reports/session4-qa-full-junit.xml`
- `reports/session4-qa-coverage.json`
- `reports/session4-qa-report-normal/summary.json` and its captured log
- `reports/session4-qa-report-strict/summary.json` and its captured log
- `reports/session4-acceptance-20261116-qa2/conditions.json` and `summary.json`

The coordinator reviewed the final diff, parsed changed Python code and the embedded CI helper, checked shell syntax and whitespace, and performed a pattern-based secret scan of the 14 changed/new files. No private-key block, recognized GitHub/AWS token pattern or literal credential-bearing HTTP/PostgreSQL URL matched. Manual review identified only explicitly synthetic test credentials and runtime-generated private values. This is a scoped review, not a comprehensive secret-scanning product. Evidence directories remain ignored, and no generated credentials, browser profiles, logs, database files or dependency environments are staged.

## Delivery limits and Session 5 readiness

Docker Hub authentication, namespace ownership, image publication, remote image pulls and immutable registry digest verification remain unexecuted. Image-platform agreement, base-image digest pinning, an approved dedicated Jenkins agent/controller and its required plugins, a successful full image/PostgreSQL pipeline, local Kubernetes runtime validation, and missing instructor acceptance remain outstanding before delivery readiness can be asserted. Runtime validation needs a separately approved dedicated personal Docker environment; the current shared daemon must not be used.

Session 5 architecture and prerequisite preparation may be reviewed using these documented limits. Azure authentication, subscription inspection, resource creation and deployment remain separately authorized work. No Revenya resource or credential was accessed. Existing databases, volumes, configuration, and Git history were preserved. No push or Session 5 deployment occurred.

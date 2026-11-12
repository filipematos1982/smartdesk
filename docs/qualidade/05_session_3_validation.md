# Session 3 implementation and validation

## Baseline and scope

Started from clean commit `ad8d55f75821ea5c62bfaaba4d5582febf6aac6b` in the personal SmartDesk repository. Backend, DevOps, and QA worked sequentially. The coordinator then reviewed their changes and repeated validation after final harness safeguards.

Confirmed scope and instructor-reference limits are recorded in [Session 3 reference](../arquitetura/05_session_3_reference.md). Full Notebook 09A/09B instructions are unavailable; exact notebook acceptance is unconfirmed. Session 1 requirements and Session 2 security behavior remain in place.

## Implementation

- Atomic conditional `UPDATE ... RETURNING` checks ticket state and authorization-relevant assignment/ownership at the write boundary. Stale competing writes roll back and return HTTP 409. Success returns the row captured by the update.
- Component PostgreSQL connections avoid password interpolation into URIs. Existing `DATABASE_URL` compatibility is preserved; positive connection timeout and valid component-port checks fail before connecting when malformed.
- Operational Compose scopes environment values by service, preserves `postgres_data`, keeps PostgreSQL unpublished and the web port on loopback, and adds web readiness and runtime restrictions.
- Local k3s configuration requires a unique project/node, uses kubeconfig mode 600, and maps loopback ports to application/Headlamp NodePorts. All four node storage paths have explicit new labelled volumes in the validation harness.
- Kubernetes manifests include namespace, placeholder Secret example, PostgreSQL StatefulSet/PVC with retention, application Deployment/Service, probes, resources, and non-root security contexts.
- Headlamp has separate server and viewer identities. The viewer has namespaced workload observation and cluster discovery, without Secret reading, pod creation, logs, exec, or write permissions. Login requires a short-lived viewer token; the server identity does not automatically authorize a browser user.
- The explicit local lab harness refuses existing or uncertain resources, verifies container IDs and labels, uses an empty Docker configuration and an explicit local Unix socket, avoids ambient credentials/contexts, and preserves all resources rather than deleting them.

## PostgreSQL target verification

The tests used newly created PostgreSQL 16 containers with tmpfs database storage and no persistent or host database mounts. Before writes, exact container ID/name/labels, dedicated network ownership, loopback publication, private metadata permissions, actual database/user identity, and a unique target marker were verified.

Tests require only the generated `SMARTDESK_TEST_DATABASE_URL`, `SMARTDESK_TEST_DATABASE_APPROVED=isolated-ephemeral`, and `SMARTDESK_TEST_TARGET_ID`. Ambient `DATABASE_URL` is never a fallback. Invalid explicit settings fail; absent explicit settings skip PostgreSQL checks. Unique schemas remain in the disposable target; no schema-drop or deletion cleanup is performed.

Private state files are mode 0600 in mode 0700 directories under ignored `reports/`. Generated values are never committed or printed. Tmpfs test data disappears when its owned container stops; a future run must create a fresh target and marker rather than restart an old target as though its identity marker persisted.

## Actual tests executed

Commands below were run with an explicitly verified target where indicated, sanitized subprocess environments, `PYTHONDONTWRITEBYTECODE=1`, and pytest cache disabled.

| Check | Actual result |
| --- | --- |
| Coordinator suite without an explicit test target | 82 passed, 12 skipped, 1 warning; 10.95 seconds |
| Original guarded PostgreSQL cases | 9 passed, 1 warning; 1.34 seconds |
| Expanded PostgreSQL and database guards | 46 passed, 1 warning; 4.07 seconds |
| Harness/database refusal safeguards | 38 passed, 1 warning; 0.25 seconds |
| QA full suite with verified PostgreSQL | **114 passed, 3 skipped, 1 warning; 14.73 seconds** |
| Six deterministic concurrency cases, five repetitions | **30 passes total**; about one second per repetition |
| Coordinator final full suite against a second fresh verified target | **114 passed, 3 skipped, 1 warning; 14.40 seconds** |
| Final whitespace and harness syntax checks | Passed |
| Generated OpenAPI comparison with Session 2 | Paths, request fields, and response schemas unchanged; conflict 409 is intentional runtime handling |

Full-suite invocation: `.venv/bin/python -m pytest tests/ -q -rs -p no:cacheprovider`. Concurrency selection: `-k 'concurrent_start or stale_state'` against `tests/test_postgres.py`.

Coverage includes simultaneous starts, stale start/resolve/assign/close/reopen transitions, HTTP lifecycle, ownership visibility, CSRF and secure cookies, forbidden actions without mutation, transaction rollback, constraints, reconnect persistence, malformed-target refusal, marker/schema checks, and resource-replacement refusal.

No test failed in the final or QA test runs. An ancillary schema-count query initially failed due to a literal percent sign under psycopg; the parameterized correction succeeded. This was not an application or test-suite failure.

The three remaining skips are T-11 performance and two T-12 real Chrome/Edge cases. The warning is the existing Starlette deprecation of HTTPX-backed TestClient. The initial 12-skip run additionally skipped nine PostgreSQL cases before a target existed; those skips are not used as PostgreSQL acceptance evidence.

## Actual Docker Compose and recovery evidence

The harness built a new local image and created a unique Compose project, its own labelled database volume, and synthetic credentials. It did not read the normal `.env` or touch the existing application volume.

Passed checks:

- Configuration parsing, startup, and health/readiness of application and PostgreSQL.
- A synthetic database password containing URI delimiters, passed as component parameters.
- HTTP 403 for a missing CSRF token, followed by successful login and ticket creation with the token.
- A committed synthetic ticket surviving PostgreSQL restart and a fresh application connection.
- A custom-format `pg_dump` restored into another newly created, verified empty tmpfs database without destructive restore options. Restored counts matched one synthetic user and one ticket.

Evidence: `reports/session3_02eb26635e3f09a09ac0f221/manifest.json`. Build log and synthetic backup remain private in that directory. Compose/restore containers are stopped; volumes and networks are retained.

This proves the exercised restart/backup/restore procedure, not point-in-time recovery, disaster recovery, SQLite migration, or recovery of real user data.

## Actual Kubernetes and Headlamp evidence

A fresh isolated k3s node using `rancher/k3s:v1.35.1-k3s1` passed API/node readiness and kubeconfig mode checks. Locally built SmartDesk, PostgreSQL, and pinned Headlamp `v0.46.0` images were imported directly without registry publication.

Namespace/Secret creation and server-side manifest validation/application passed. PostgreSQL StatefulSet/PVC, SmartDesk Deployment, and Headlamp Deployment rolled out. Application `/login` and Headlamp returned HTTP 200 through loopback-only ports. A PostgreSQL query succeeded. Headlamp viewer authorization allowed pod listing and denied Secret reading and pod creation.

After replacing the image's implicit anonymous storage with four explicit labelled node volumes, the coordinator repeated the **complete** k3s runtime smoke successfully. Final evidence: `reports/session3_5f6f060988ced2af316c9d80/manifest.json`. The new node is stopped and its volumes retained. No ambient Kubernetes context or existing cluster was used.

Headlamp's browser token-login flow and a real-browser ticket workflow were not exercised. A node rollout and HTTP response do not establish those browser criteria. PostgreSQL pod replacement/power-loss and full cluster recovery were not simulated.

## Failures corrected during harness development

Initial missing-resource checks did not recognize Docker's network/volume error wording and stopped before creating affected workloads. The checks were corrected to distinguish absence from uncertain failures.

An initial k3s readiness attempt used `k3s kubectl` against an image dispatch that requires direct `kubectl`; the command and healthcheck were corrected. The scoped node was stopped, its diagnostics retained, and subsequent complete runs passed. The final run also verified explicit ownership of all four node-volume mounts. Failed-attempt resources remain retained; no pruning or deletion occurred.

## Retained resources and limitations

- Final read-only inspection verified the recorded IDs and ownership labels of all eight Session 3 containers and confirmed they are stopped, including both QA test targets. Existing databases and Docker volumes were never removed, overwritten, or reset. Newly created volumes, networks, images, stopped containers, and early anonymous k3s volumes remain intentionally retained.
- Original QA evidence: `reports/session3_90cc37838eb5050aef6c3148/manifest.json`; final fresh-target evidence: `reports/session3_a8f1dbc79e6cfb3652520567/manifest.json`. Both record stopped state. Private logs, credentials, backup, and expired viewer tokens must remain ignored.
- The harness is intentionally specific to this macOS Docker Desktop socket and Compose plugin path. It requires Compose support for `!reset`/`!override`; it is not a portable production installer.
- Initialization remains idempotent table creation, not versioned migrations. No schema migration was required or executed. Connection pooling, deployment-specific least-privilege database roles, and production TLS/connection budgets remain future design work.
- Probe `/login` confirms web responsiveness after successful startup, not continuous database availability under later outages.
- No Docker Hub authentication/publication, Git push, Azure operation, company access, real-browser acceptance, or Session 4 work occurred.

## Repeating the local lab safely

After explicit authorization, each command below creates a **new** run with private state and unique resources:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m scripts.session3_lab --approve-local-session3 --phase test-target
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m scripts.session3_lab --approve-local-session3 --phase compose
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m scripts.session3_lab --approve-local-session3 --phase k3s
```

`test-target` deliberately leaves its verified tmpfs database running for QA. Load only its three generated settings through a private process environment after checking its exact manifest/container scope; do not print or shell-evaluate credential files. Reverify identity before tests and before stopping the exact owned container. The other phases stop their owned containers on completion. No command authorizes removal of retained resources or reuse of an existing database.

Stop after the Session 3 local commit and await review before Session 4.

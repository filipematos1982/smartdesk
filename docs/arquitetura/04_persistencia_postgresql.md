# Local PostgreSQL persistence

SmartDesk retains its approved endpoints, business fields, roles, states, and logical `users`/`tickets` schema. PostgreSQL 16 is the operational database; SQLite is selected only by an explicit fixture path.

## Connection configuration

`DATABASE_URL` remains supported for existing clients and takes precedence when explicitly supplied. Local Compose uses separate `POSTGRES_HOST`, `POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD` parameters, with `POSTGRES_PORT=5432`. Passing credentials as psycopg parameters avoids URI encoding mistakes. `SMARTDESK_DB_CONNECT_TIMEOUT` defaults to five seconds and must be a positive integer. Existing private environment files are not rewritten.

Compose must scope variables to each service, keep the database port unpublished in the normal application stack, and wait for PostgreSQL readiness. The existing `postgres_data` volume name and mount path remain compatible. Changing initialization variables does not update credentials already stored in a volume.

## Transactions and concurrent changes

Each assignment or lifecycle transition validates role and business prerequisites, then repeats the expected state and assignment/ownership predicates in an atomic `UPDATE ... RETURNING`. PostgreSQL rechecks the predicates after waiting for a concurrent writer. No matching row produces HTTP 409 and rollback; the caller must reload rather than overwrite a newer state. Successful service methods return the row captured by that update.

Context-managed connections roll back on exceptions and close reliably. The application still uses a connection per operation; a shared connection pool and deployment-specific statement/connection budgets have not been introduced or performance-certified.

## Schema management and data preservation

`initialize()` creates missing tables and preserves existing data and constraints. It is idempotent initialization, **not a schema migration framework**. Session 3 does not introduce schema changes requiring migration. A future schema change needs an explicit reviewed, versioned, additive migration and backup/recovery plan; never assume `CREATE TABLE IF NOT EXISTS` upgrades an existing schema.

There is no automatic import of legacy SQLite data. Do not delete volumes, drop databases/schemas, or replace data to make a demonstration pass.

## Isolated PostgreSQL validation

Real PostgreSQL tests never fall back to the application's `DATABASE_URL`. They require all of:

- `SMARTDESK_TEST_DATABASE_URL`, targeting only the approved local `smartdesk_test` database and login with an explicit port;
- `SMARTDESK_TEST_DATABASE_APPROVED=isolated-ephemeral`;
- a unique `SMARTDESK_TEST_TARGET_ID` matching a precreated `public.smartdesk_test_target` marker.

The harness must verify its newly created Docker container identity, labels, and storage scope before establishing that marker. Tests then check the actual database/login/marker before creating a unique schema. Test connections use explicit connection, lock, and statement timeouts. Schemas remain inside the disposable target; tests never drop them. An explicit invalid target fails; an absent target skips.

Run persistence/restart and backup/restore checks only with synthetic records and new, labelled local resources. Restore into a new empty target without destructive restore options, verify the restored record, and preserve existing volumes. Actual results, skipped checks, retained resources, and Kubernetes evidence belong in the Session 3 validation record.

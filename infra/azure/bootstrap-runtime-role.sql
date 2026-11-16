-- PREPARATION ONLY: do not run without separate database-write authorization.
-- Connect to the new smartdesk database as its dedicated bootstrap administrator,
-- through an approved private-network client with TLS verify-full enabled.
-- Inject a fresh synthetic/lab password through a private process environment.
-- psql variable quoting treats the value as a SQL literal, not executable SQL.
\set ON_ERROR_STOP on
-- Verify the exact new server ID/host outside this script before connecting.
SELECT current_database() = 'smartdesk' AS expected_database \gset
\if :expected_database
\else
  \echo 'Refusing bootstrap outside the approved smartdesk database.'
  \quit 1
\endif
\getenv runtime_password SMARTDESK_RUNTIME_DB_PASSWORD
BEGIN;
CREATE ROLE smartdesk_app WITH LOGIN PASSWORD :'runtime_password'
  NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
REVOKE CONNECT ON DATABASE smartdesk FROM PUBLIC;
GRANT CONNECT ON DATABASE smartdesk TO smartdesk_app;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT USAGE, CREATE ON SCHEMA public TO smartdesk_app;
-- Existing startup initialization needs schema CREATE. A future migrations role
-- can separate DDL from runtime DML after an approved application change.

COMMIT;

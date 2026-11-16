#!/bin/sh
# Local CI infrastructure only: no registry login, publication, or deployment.
set -eu
exec python3 - "$@" <<'PY'
import argparse
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import time
import xml.etree.ElementTree as ET

ROOT = Path.cwd().resolve()
LABEL = "io.smartdesk.session4.run"
ROLE = "io.smartdesk.session4.role"
p = argparse.ArgumentParser(description="Build and test only new local SmartDesk resources")
p.add_argument("--approve-local-ci", action="store_true")
p.add_argument("--docker-host", required=True)
p.add_argument("--output-dir", required=True)
a = p.parse_args()
if not a.approve_local_ci:
    p.error("Explicit authorization for new local CI resources is required")
if not re.fullmatch(r"unix:///[^\s]+", a.docker_host):
    p.error("Only an explicitly selected local Unix Docker socket is supported")
state = (ROOT / a.output_dir).resolve()
if state.parent != ROOT / "reports" or not re.fullmatch(r"session4-ci-[A-Za-z0-9-]+", state.name):
    p.error("Choose a new reports/session4-ci-<unique-id> output directory")
os.umask(0o077)
state.mkdir(parents=True, mode=0o700, exist_ok=False)
config = state / "docker-config"
config.mkdir(mode=0o700)
env = {"PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
       "DOCKER_CONFIG": str(config), "DOCKER_HOST": a.docker_host}
run_id = "session3_ci_" + secrets.token_hex(12)
prefix = "smartdesk-ci-" + secrets.token_hex(12)
resources = []
checks = {}
image = prefix + ":local"

def save():
    (state / "manifest.json").write_text(json.dumps({
        "run_id": run_id, "docker_endpoint": a.docker_host,
        "image": image, "resources": resources, "checks": checks,
    }, indent=2) + "\n")

def call(args, *, check=True, timeout=180, input=None):
    result = subprocess.run(args, cwd=ROOT, env=env, input=input,
                            capture_output=True, timeout=timeout)
    if check and result.returncode:
        # Never print captured output or command arguments containing synthetic secrets.
        raise RuntimeError("Local CI command failed (exit %d)" % result.returncode)
    return result

def docker(*args, **kwargs):
    return call(["docker", "--config", str(config), "--host", a.docker_host,
                 *args], **kwargs)

def absent(kind, name):
    result = docker(kind, "inspect", name, check=False)
    expected = ("no such " + kind, kind + " " + name + " not found")
    if result.returncode == 0 or not any(s.encode() in result.stderr.lower() for s in expected):
        raise RuntimeError("Cannot prove that the new CI resource is absent")

def inspect_container(resource):
    info = json.loads(docker("container", "inspect", resource["id"]).stdout)[0]
    labels = info["Config"].get("Labels") or {}
    if (info["Id"] != resource["id"] or info["Name"].lstrip("/") != resource["name"]
            or labels.get(LABEL) != run_id or labels.get(ROLE) != resource["role"]):
        raise RuntimeError("CI container ownership changed; refusing access")
    return info

def record(name, role, container_id):
    resource = {"kind": "container", "id": container_id, "name": name, "role": role}
    resources.append(resource)
    save()
    inspect_container(resource)
    return resource

save()
exit_code = 1
try:
    # Check daemon access before building or creating any workload.
    docker("version", "--format", "{{.Server.Version}}")
    checks["local_daemon"] = "passed"
    revision = call(["git", "rev-parse", "HEAD"]).stdout.decode().strip()
    dirty = bool(call(["git", "status", "--porcelain"]).stdout.strip())
    absent("image", image)
    built = docker("build", "--iidfile", str(state / "image-id"),
                   "--label", "org.opencontainers.image.revision=" + revision,
                   "--label", "io.smartdesk.source.dirty=" + str(dirty).lower(),
                   "--tag", image, ".", check=False, timeout=900)
    (state / "build.log").write_bytes(built.stdout + built.stderr)
    if built.returncode:
        raise RuntimeError("Local image build failed; private build log retained")
    info = json.loads(docker("image", "inspect", image).stdout)[0]
    if info["Config"].get("User") != "10001:10001":
        raise RuntimeError("Image does not declare the expected non-root identity")
    checks["image_build"] = {"status": "passed", "id": info["Id"], "source_revision": revision,
                              "source_tree_dirty": dirty,
                              "platform": info["Os"] + "/" + info["Architecture"]}
    network = prefix + "-network"
    absent("network", network)
    network_id = docker("network", "create", "--internal", "--label", LABEL + "=" + run_id,
                        network).stdout.decode().strip()
    ni = json.loads(docker("network", "inspect", network_id).stdout)[0]
    if ni["Name"] != network or ni.get("Labels", {}).get(LABEL) != run_id or not ni["Internal"]:
        raise RuntimeError("New CI network identity is invalid")
    resources.append({"kind": "network", "id": network_id, "name": network})
    password = secrets.token_hex(32)
    db_env = state / "postgres.env"
    db_env.write_text("POSTGRES_USER=smartdesk_test\nPOSTGRES_DB=smartdesk_test\nPOSTGRES_PASSWORD=" + password + "\n")
    db_name = prefix + "-postgres"
    absent("container", db_name)
    db_id = docker("create", "--name", db_name,
                   "--label", LABEL + "=" + run_id, "--label", ROLE + "=postgres",
                   "--network", network_id, "--network-alias", "smartdesk-test-db",
                   "--tmpfs", "/var/lib/postgresql/data:rw,nosuid,noexec,size=512m",
                   "--env-file", str(db_env), "postgres:16-alpine").stdout.decode().strip()
    db_resource = record(db_name, "postgres", db_id)
    db_info = inspect_container(db_resource)
    if (db_info.get("HostConfig", {}).get("PortBindings")
            or db_info.get("HostConfig", {}).get("Binds")
            or any(m.get("Type") != "tmpfs" or m.get("Destination") != "/var/lib/postgresql/data"
                   for m in db_info.get("Mounts", []))
            or set(db_info["HostConfig"].get("Tmpfs", {})) != {"/var/lib/postgresql/data"}):
        raise RuntimeError("Disposable PostgreSQL must have only tmpfs data and no published ports or mounts")
    docker("start", db_id)
    for _ in range(60):
        inspect_container(db_resource)
        ready = docker("exec", db_id, "pg_isready", "-U", "smartdesk_test", "-d", "smartdesk_test", check=False)
        if ready.returncode == 0:
            break
        time.sleep(1)
    else:
        raise RuntimeError("Disposable PostgreSQL did not become ready")
    identity = docker("exec", db_id, "psql", "-U", "smartdesk_test", "-d", "smartdesk_test", "-Atc",
                      "SELECT current_database() || '|' || current_user").stdout.strip()
    if identity != b"smartdesk_test|smartdesk_test":
        raise RuntimeError("Disposable database identity does not match")
    # run_id is generated locally from a fixed prefix and hex, never user SQL input.
    docker("exec", db_id, "psql", "-v", "ON_ERROR_STOP=1", "-U", "smartdesk_test", "-d", "smartdesk_test", "-c",
           "CREATE TABLE public.smartdesk_test_target (target_id text PRIMARY KEY); "
           "INSERT INTO public.smartdesk_test_target VALUES ('" + run_id + "')")
    checks["disposable_postgres_identity"] = "passed: new ID/labels, internal network, tmpfs, DB identity and marker"
    test_env = state / "tests.env"
    test_env.write_text("SMARTDESK_TEST_DATABASE_URL=postgresql://smartdesk_test:" + password
                        + "@smartdesk-test-db:5432/smartdesk_test\n"
                        + "SMARTDESK_TEST_DATABASE_APPROVED=isolated-ephemeral\n"
                        + "SMARTDESK_TEST_TARGET_ID=" + run_id + "\n")
    test_name = prefix + "-tests"
    absent("container", test_name)
    command = ("python -c \"import os; assert os.getuid() == 10001; "
               "assert not os.access('/app/src/main.py', os.W_OK)\" && "
               "python -m scripts.run_validation --output-dir /app/reports/run --require-postgres")
    test_id = docker("create", "--name", test_name,
                     "--label", LABEL + "=" + run_id, "--label", ROLE + "=tests",
                     "--network", network_id, "--env-file", str(test_env),
                     "--cap-drop", "ALL", "--security-opt", "no-new-privileges:true",
                     "--entrypoint", "/bin/sh", image, "-ec", command).stdout.decode().strip()
    test_resource = record(test_name, "tests", test_id)
    tests = docker("start", "--attach", test_id, check=False, timeout=900)
    (state / "tests.log").write_bytes(tests.stdout + tests.stderr)
    test_state = inspect_container(test_resource)["State"]
    artifacts = state / "artifacts"
    artifacts.mkdir(mode=0o700)
    copied = docker("cp", test_id + ":/app/reports/run/.", str(artifacts), check=False)
    if copied.returncode:
        raise RuntimeError("Fresh test reports are missing")
    xml_files = list(artifacts.rglob("*.xml"))
    if not xml_files:
        raise RuntimeError("Fresh JUnit test reports are missing")
    cases = []
    for path in xml_files:
        cases.extend(ET.parse(path).getroot().iter("testcase"))
    if not cases or any(c.find("failure") is not None or c.find("error") is not None for c in cases):
        raise RuntimeError("JUnit reports contain no cases or report test failures")
    if tests.returncode or test_state.get("Status") != "exited" or test_state.get("ExitCode") != 0:
        raise RuntimeError("CI tests or the required PostgreSQL gate failed")
    checks["non_root_full_suite_and_required_postgres"] = "passed; see fresh artifacts for counts and explicit remaining skips"
    exit_code = 0
except Exception as exc:
    checks["result"] = "failed: " + str(exc)
    print(checks["result"])
finally:
    # Stop only newly recorded, verified containers. Retain all resources and evidence.
    for resource in reversed(resources):
        if resource["kind"] != "container":
            continue
        try:
            current = inspect_container(resource)
            if current["State"]["Running"]:
                docker("stop", "--time", "15", resource["id"])
            resource["stopped"] = True
        except Exception:
            checks["resource_stop"] = "failed: ownership or stop check; inspect retained private state"
            exit_code = 1
    save()
print("Local CI " + ("passed" if exit_code == 0 else "failed") + "; evidence: " + str(state.relative_to(ROOT)))
raise SystemExit(exit_code)
PY

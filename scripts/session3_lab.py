"""Create only new, labelled local Session 3 validation resources.

This opt-in harness never reads .env, Docker registry credentials, or kubeconfig.
It never removes containers, volumes, databases, or test schemas. Generated
secrets and resource evidence stay in an ignored, private reports directory.
"""
import argparse
import json
import os
from pathlib import Path
import secrets
import subprocess
import time
import http.cookiejar
import re
import urllib.error
import urllib.request
from urllib.parse import urlencode
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
LOCAL_DOCKER = "unix:///Users/filipematos/.docker/run/docker.sock"
LABEL = "io.smartdesk.session3.run"


class Lab:
    def __init__(self):
        self.target_id = "session3_" + secrets.token_hex(12)
        self.prefix = self.target_id.replace("_", "-")
        self.directory = ROOT / "reports" / self.target_id
        self.directory.mkdir(mode=0o700, parents=True, exist_ok=False)
        self.config = self.directory / "docker-config"
        self.config.mkdir(mode=0o700)
        # Do not inherit Docker/Compose/cloud/database configuration or secrets.
        self.env = {"PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
                    "DOCKER_CONFIG": str(self.config), "DOCKER_HOST": LOCAL_DOCKER}
        self.manifest = {"target_id": self.target_id, "docker_endpoint": LOCAL_DOCKER,
                         "resources": [], "checks": {}}
        self.save()

    def private_file(self, name, content):
        path = self.directory / name
        with path.open("x", encoding="utf-8") as output:
            os.chmod(path, 0o600)
            output.write(content)
        return path

    def save(self):
        path = self.directory / "manifest.json"
        with path.open("w", encoding="utf-8") as output:
            os.chmod(path, 0o600)
            json.dump(self.manifest, output, indent=2)
            output.write("\n")

    def command(self, args, *, env=None, input=None, stdin=None, timeout=180, check=True):
        result = subprocess.run(args, cwd=ROOT, env=env or self.env,
                                input=input, stdin=stdin, capture_output=True, timeout=timeout)
        if check and result.returncode:
            # Never include command output: it may contain generated credentials.
            raise RuntimeError(f"Local validation command failed (exit {result.returncode})")
        return result

    def docker(self, *args, **kwargs):
        return self.command(["docker", "--config", str(self.config),
                             "--host", LOCAL_DOCKER, *args], **kwargs)

    def absent(self, kind, name):
        result = self.docker(kind, "inspect", name, check=False)
        if result.returncode == 0:
            raise RuntimeError("Refusing to reuse an existing local resource")
        expected_absence = (f"no such {kind}", f"{kind} {name} not found")
        if not any(message.encode() in result.stderr.lower() for message in expected_absence):
            raise RuntimeError("Cannot prove that the proposed local resource is absent")

    def container(self, name, expected_role):
        info = json.loads(self.docker("container", "inspect", name).stdout)[0]
        labels = info["Config"].get("Labels") or {}
        if labels.get(LABEL) != self.target_id or labels.get("io.smartdesk.session3.role") != expected_role:
            raise RuntimeError("Refusing to access a container with mismatched ownership labels")
        if info["Name"].lstrip("/") != name:
            raise RuntimeError("Local container identity changed")
        recorded = [r for r in self.manifest["resources"]
                    if r["kind"] == "container" and r["name"] == name]
        if recorded and any(r["id"] != info["Id"] for r in recorded):
            raise RuntimeError("Refusing access to a replaced local container")
        return info

    def new_network(self, role):
        name = self.prefix + "-" + role
        self.absent("network", name)
        created_id = self.docker("network", "create", "--label", f"{LABEL}={self.target_id}", name).stdout.decode().strip()
        info = json.loads(self.docker("network", "inspect", created_id).stdout)[0]
        if info["Name"] != name or info.get("Labels", {}).get(LABEL) != self.target_id:
            raise RuntimeError("New test network ownership could not be verified")
        self.manifest["resources"].append({"kind": "network", "name": name, "id": created_id})
        self.save()
        return name

    def record_network(self, name):
        info = json.loads(self.docker("network", "inspect", name).stdout)[0]
        if info.get("Labels", {}).get(LABEL) != self.target_id:
            raise RuntimeError("New network ownership could not be verified")
        self.manifest["resources"].append({"kind": "network", "name": name, "id": info["Id"]})
        self.save()

    def record_container(self, name, role):
        info = self.container(name, role)
        self.manifest["resources"].append({"kind": "container", "name": name,
                                            "id": info["Id"], "role": role})
        self.save()
        return info

    def wait_postgres(self, name, role, user, database):
        self.container(name, role)
        for _ in range(60):
            result = self.docker("exec", name, "pg_isready", "-U", user, "-d", database, check=False)
            if result.returncode == 0:
                return
            time.sleep(1)
        raise RuntimeError("The new local PostgreSQL container did not become ready")

    def test_target(self):
        self.docker("info", "--format", "{{.ServerVersion}}")
        # A fresh checkout must not depend on a previous session's local image.
        marker_image = "smartdesk:" + self.target_id
        built = self.docker("build", "--tag", marker_image, ".", timeout=600)
        self.private_file("build.log", built.stdout.decode(errors="replace") + built.stderr.decode(errors="replace"))
        self.manifest["image"] = marker_image
        self.save()
        network = self.new_network("test-network")
        name = self.prefix + "-test-db"
        self.absent("container", name)
        password = secrets.token_hex(24)
        env = dict(self.env, POSTGRES_DB="smartdesk_test", POSTGRES_USER="smartdesk_test",
                   POSTGRES_PASSWORD=password)
        self.docker("pull", "postgres:16-alpine", timeout=300)
        self.docker("create", "--name", name, "--label", f"{LABEL}={self.target_id}",
                    "--label", "io.smartdesk.session3.role=test-db", "--network", network,
                    "--publish", "127.0.0.1::5432", "--tmpfs",
                    "/var/lib/postgresql/data:rw,nosuid,noexec,size=512m",
                    "--env", "POSTGRES_DB", "--env", "POSTGRES_USER", "--env", "POSTGRES_PASSWORD",
                    "postgres:16-alpine", env=env)
        info = self.record_container(name, "test-db")
        if "/var/lib/postgresql/data" not in info["HostConfig"].get("Tmpfs", {}):
            raise RuntimeError("Test PostgreSQL data must use new tmpfs storage")
        if any(m.get("Type") == "volume" for m in info.get("Mounts", [])):
            raise RuntimeError("Test PostgreSQL must not mount a persistent volume")
        self.docker("start", name)
        self.wait_postgres(name, "test-db", "smartdesk_test", "smartdesk_test")
        info = self.container(name, "test-db")
        published = info["NetworkSettings"]["Ports"]["5432/tcp"]
        if len(published) != 1 or published[0]["HostIp"] != "127.0.0.1":
            raise RuntimeError("Test PostgreSQL must be published only on loopback")
        port = int(published[0]["HostPort"])
        # The newly built local validation image supplies psycopg. This container
        # joins only the new database's network namespace and has no host mounts.
        marker_code = '''import os, psycopg
with psycopg.connect(host="127.0.0.1", dbname="smartdesk_test", user="smartdesk_test",
                     password=os.environ["PGPASSWORD"], connect_timeout=5) as db:
    assert db.execute("SELECT current_database(), current_user").fetchone() == ("smartdesk_test", "smartdesk_test")
    db.execute("CREATE TABLE public.smartdesk_test_target (target_id TEXT PRIMARY KEY)")
    db.execute("INSERT INTO public.smartdesk_test_target (target_id) VALUES (%s)", (os.environ["TARGET_ID"],))
'''
        marker_env = dict(self.env, PGPASSWORD=password, TARGET_ID=self.target_id)
        self.docker("run", "--rm", "--network", "container:" + info["Id"],
                    "--label", f"{LABEL}={self.target_id}", "--label", "io.smartdesk.session3.role=target-marker",
                    "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
                    "--env", "PGPASSWORD", "--env", "TARGET_ID", "--entrypoint", "python",
                    marker_image, "-c", marker_code, env=marker_env)
        url = f"postgresql://smartdesk_test:{quote(password, safe='')}@127.0.0.1:{port}/smartdesk_test"
        self.private_file("qa.env", f"SMARTDESK_TEST_DATABASE_URL={url}\n"
                          "SMARTDESK_TEST_DATABASE_APPROVED=isolated-ephemeral\n"
                          f"SMARTDESK_TEST_TARGET_ID={self.target_id}\n")
        self.manifest["checks"]["isolated_postgres_target"] = "passed: Docker labels/ID/tmpfs, DB identity and parameterized marker"
        self.manifest["qa_target"] = {"container": name, "port": port, "env_file": "qa.env",
                                       "running_for_qa": True, "storage": "tmpfs"}
        self.save()

    def new_volume(self, role):
        name = self.prefix + "-" + role
        self.absent("volume", name)
        self.docker("volume", "create", "--label", f"{LABEL}={self.target_id}", name)
        info = json.loads(self.docker("volume", "inspect", name).stdout)[0]
        if info.get("Labels", {}).get(LABEL) != self.target_id:
            raise RuntimeError("New volume ownership could not be verified")
        self.manifest["resources"].append({"kind": "volume", "name": name})
        self.save()
        return name

    def compose_command(self, *args, **kwargs):
        plugin = "/Applications/Docker.app/Contents/Resources/cli-plugins/docker-compose"
        return self.command([plugin, "--project-name", self.prefix,
                             "--project-directory", str(ROOT), "--env-file", "/dev/null",
                             "-f", str(ROOT / "compose.yaml"), "-f", str(self.override), *args],
                            env=self.compose_env, **kwargs)

    def stop_non_qa(self, include_qa=False):
        for resource in self.manifest["resources"]:
            if resource["kind"] == "container" and (include_qa or resource["role"] != "test-db"):
                info = self.container(resource["name"], resource["role"])
                if info["Id"] != resource["id"]:
                    raise RuntimeError("Refusing to stop a container whose ID changed")
                if info["State"]["Running"]:
                    self.docker("stop", "--time", "15", resource["name"])
        self.manifest["non_qa_resources_stopped"] = True
        self.save()

    def compose_validation(self):
        self.docker("info", "--format", "{{.ServerVersion}}")
        image = "smartdesk:" + self.target_id
        built = self.docker("build", "--tag", image, ".", timeout=600)
        self.private_file("build.log", built.stdout.decode(errors="replace") + built.stderr.decode(errors="replace"))
        self.manifest["image"] = image
        self.manifest["checks"]["image_build"] = "passed"
        self.save()
        print("New local image built; preparing an isolated Compose project.", flush=True)
        volume = self.new_volume("postgres-data")
        self.absent("network", self.prefix + "_default")
        self.absent("container", self.prefix + "-db-1")
        self.absent("container", self.prefix + "-web-1")
        self.override = self.private_file("compose.override.yaml", f'''services:
  db:
    labels:
      {LABEL}: {self.target_id}
      io.smartdesk.session3.role: compose-db
  web:
    labels:
      {LABEL}: {self.target_id}
      io.smartdesk.session3.role: compose-web
    volumes: !reset []
    tmpfs: !override
      - /tmp:rw,noexec,nosuid,size=64m
      - /app/reports:rw,noexec,nosuid,size=32m,uid=10001,gid=10001
volumes:
  postgres_data:
    name: {volume}
    external: true
networks:
  default:
    labels:
      {LABEL}: {self.target_id}
''')
        # Delimiters in this synthetic password exercise component connections.
        password = "Synthetic_" + secrets.token_hex(16) + ":@/$?"
        self.compose_env = dict(self.env, POSTGRES_DB="smartdesk_lab", POSTGRES_USER="smartdesk_lab",
                                POSTGRES_PASSWORD=password, SMARTDESK_IMAGE=image,
                                SMARTDESK_SESSION_SECRET=secrets.token_hex(32),
                                SMARTDESK_COOKIE_SECURE="false", SMARTDESK_HTTP_PORT="0")
        self.compose_command("config", "--quiet")
        self.compose_command("create", "--no-build", "--pull", "never", timeout=180)
        self.record_network(self.prefix + "_default")
        ids = self.compose_command("ps", "--all", "--quiet").stdout.decode().split()
        if len(ids) != 2:
            raise RuntimeError("Expected exactly two new Compose containers")
        containers = {}
        for container_id in ids:
            info = json.loads(self.docker("container", "inspect", container_id).stdout)[0]
            labels = info["Config"].get("Labels", {})
            role = labels.get("io.smartdesk.session3.role")
            if role not in {"compose-db", "compose-web"} or labels.get(LABEL) != self.target_id:
                raise RuntimeError("Unexpected Compose container ownership")
            name = info["Name"].lstrip("/")
            containers[role] = name
            self.record_container(name, role)
            if role == "compose-db":
                data = [m for m in info["Mounts"] if m["Destination"] == "/var/lib/postgresql/data"]
                if len(data) != 1 or data[0].get("Name") != volume:
                    raise RuntimeError("Compose database must mount only the newly verified data volume")
        self.compose_command("start", "--wait", "--wait-timeout", "120", timeout=150)
        web, database = containers["compose-web"], containers["compose-db"]
        info = self.container(web, "compose-web")
        ports = info["NetworkSettings"]["Ports"]["8000/tcp"]
        if len(ports) != 1 or ports[0]["HostIp"] != "127.0.0.1":
            raise RuntimeError("Compose HTTP must bind only loopback")
        base = "http://127.0.0.1:" + ports[0]["HostPort"]
        synthetic_password = secrets.token_hex(20)
        create_user = '''import os
from src.database import connect
from src.auth import hash_password
with connect() as db:
    db.execute("INSERT INTO users(name,email,secret,role) VALUES(?,?,?,?)",
               ("Session 3 employee", "employee@smartdesk.test", hash_password(os.environ["LAB_LOGIN_PASSWORD"]), "employee"))
'''
        self.docker("exec", "--env", "LAB_LOGIN_PASSWORD", web, "python", "-c", create_user,
                    env=dict(self.env, LAB_LOGIN_PASSWORD=synthetic_password))
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}),
                                             urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        def page(path):
            with opener.open(base + path, timeout=10) as response:
                return response.read().decode()
        def post(path, fields):
            return opener.open(base + path, data=urlencode(fields).encode(), timeout=10)
        def csrf(html):
            found = re.search(r'name="csrf_token" value="([^"]+)"', html)
            if not found:
                raise RuntimeError("Expected a session-bound CSRF form token")
            return found.group(1)
        token = csrf(page("/login"))
        try:
            post("/login", {"email": "employee@smartdesk.test", "password": synthetic_password})
        except urllib.error.HTTPError as error:
            if error.code != 403:
                raise
        else:
            raise RuntimeError("Missing CSRF token was not rejected")
        with post("/login", {"email": "employee@smartdesk.test", "password": synthetic_password, "csrf_token": token}) as response:
            if response.status != 200 or "/tickets" not in response.url:
                raise RuntimeError("Synthetic HTTP login failed")
        token = csrf(page("/tickets/new"))
        title = "Session 3 persistence " + self.target_id
        with post("/tickets/new", {"title": title, "description": "Synthetic local validation only",
                                   "category": "Hardware", "csrf_token": token}) as response:
            if response.status != 200 or title not in response.read().decode():
                raise RuntimeError("Synthetic HTTP ticket creation failed")
        self.manifest["checks"]["compose_http_csrf_ticket"] = "passed: no-token login rejected, valid login and ticket creation"
        self.manifest["compose_http"] = base
        self.docker("restart", database, timeout=60)
        self.wait_postgres(database, "compose-db", "smartdesk_lab", "smartdesk_lab")
        if title not in page("/tickets"):
            raise RuntimeError("Ticket did not survive database restart and reconnect")
        self.manifest["checks"]["compose_restart_persistence"] = "passed: same new named volume, database restart, fresh application connection"
        self.save()
        print("Compose HTTP, CSRF, PostgreSQL reconnect and restart persistence passed.", flush=True)
        # Restore only into a second, newly created empty tmpfs database.
        restore = self.prefix + "-restore-db"
        self.absent("container", restore)
        restore_env = dict(self.env, POSTGRES_DB="smartdesk_restore", POSTGRES_USER="smartdesk_lab",
                           POSTGRES_PASSWORD=secrets.token_hex(24))
        self.docker("create", "--name", restore, "--label", f"{LABEL}={self.target_id}",
                    "--label", "io.smartdesk.session3.role=restore-db", "--network", self.prefix + "_default",
                    "--tmpfs", "/var/lib/postgresql/data:rw,nosuid,noexec,size=512m",
                    "--env", "POSTGRES_DB", "--env", "POSTGRES_USER", "--env", "POSTGRES_PASSWORD",
                    "postgres:16-alpine", env=restore_env)
        info = self.record_container(restore, "restore-db")
        if "/var/lib/postgresql/data" not in info["HostConfig"].get("Tmpfs", {}):
            raise RuntimeError("Restore database must use fresh tmpfs storage")
        self.docker("start", restore)
        self.wait_postgres(restore, "restore-db", "smartdesk_lab", "smartdesk_restore")
        empty = self.docker("exec", restore, "psql", "-U", "smartdesk_lab", "-d", "smartdesk_restore", "-Atc",
                            "SELECT count(*) FROM information_schema.tables WHERE table_schema='public'").stdout.strip()
        if empty != b"0":
            raise RuntimeError("Refusing to restore into a nonempty database")
        backup = self.docker("exec", database, "pg_dump", "-U", "smartdesk_lab", "-d", "smartdesk_lab", "--format=custom").stdout
        backup_path = self.directory / "synthetic-backup.dump"
        with backup_path.open("xb") as output:
            os.chmod(backup_path, 0o600)
            output.write(backup)
        self.docker("exec", "-i", restore, "pg_restore", "-U", "smartdesk_lab", "-d", "smartdesk_restore",
                    "--no-owner", "--no-privileges", "--exit-on-error", input=backup)
        expected = self.docker("exec", restore, "psql", "-U", "smartdesk_lab", "-d", "smartdesk_restore", "-Atc",
                               "SELECT (SELECT count(*) FROM users), (SELECT count(*) FROM tickets)").stdout.strip()
        if expected != b"1|1":
            raise RuntimeError("Restored synthetic users/tickets do not match")
        self.manifest["checks"]["pg_dump_restore"] = "passed: custom-format dump, restore into verified new empty database, one user and one ticket"
        self.save()
        self.stop_non_qa()

    def k3s_validation(self):
        self.docker("info", "--format", "{{.ServerVersion}}")
        image = "smartdesk:" + self.target_id
        built = self.docker("build", "--tag", image, ".", timeout=600)
        self.private_file("build.log", built.stdout.decode(errors="replace") + built.stderr.decode(errors="replace"))
        self.manifest["image"] = image
        volume = self.new_volume("k3s-data")
        extra_volumes = {"k3s-cni": self.new_volume("k3s-cni"),
                         "k3s-kubelet": self.new_volume("k3s-kubelet"),
                         "k3s-logs": self.new_volume("k3s-logs")}
        self.absent("network", self.prefix + "_default")
        self.absent("container", self.prefix + "-k3s-1")
        override = self.private_file("k3s.override.yaml", f'''services:
  k3s:
    labels:
      {LABEL}: {self.target_id}
      io.smartdesk.session3.role: k3s-node
volumes:
  k3s-server:
    name: {volume}
    external: true
networks:
  default:
    labels:
      {LABEL}: {self.target_id}
''')
        # Override every image-declared persistent path with a new labelled volume.
        # Never reuse the node's anonymous or existing named volumes.
        text = override.read_text()
        definitions = "".join(f"  {key}:\n    name: {name}\n    external: true\n"
                              for key, name in extra_volumes.items())
        override.write_text(text.replace("networks:\n", definitions + "networks:\n"))
        env = dict(self.env, SMARTDESK_LAB_PROJECT=self.prefix, SMARTDESK_LAB_NODE=self.prefix,
                   SMARTDESK_LAB_HTTP_PORT="0", SMARTDESK_LAB_HEADLAMP_PORT="0")
        plugin = "/Applications/Docker.app/Contents/Resources/cli-plugins/docker-compose"
        def compose(*args):
            return self.command([plugin, "--project-name", self.prefix, "--project-directory", str(ROOT),
                                 "--env-file", "/dev/null", "-f", str(ROOT / "compose.k3s.yaml"),
                                 "-f", str(override), *args], env=env, timeout=300)
        compose("config", "--quiet")
        self.manifest["checks"]["k3s_compose_syntax"] = "passed"
        self.save()
        compose("create", "--pull", "missing")
        self.record_network(self.prefix + "_default")
        ids = compose("ps", "--all", "--quiet").stdout.decode().split()
        if len(ids) != 1:
            raise RuntimeError("Expected exactly one new dedicated k3s container")
        info = json.loads(self.docker("container", "inspect", ids[0]).stdout)[0]
        node = info["Name"].lstrip("/")
        info = self.record_container(node, "k3s-node")
        expected_mounts = {"/var/lib/rancher/k3s": volume,
                           "/var/lib/cni": extra_volumes["k3s-cni"],
                           "/var/lib/kubelet": extra_volumes["k3s-kubelet"],
                           "/var/log": extra_volumes["k3s-logs"]}
        actual_mounts = {m["Destination"]: m.get("Name") for m in info["Mounts"]
                         if m.get("Type") == "volume"}
        if actual_mounts != expected_mounts or any(m.get("Type") == "bind" for m in info["Mounts"]):
            raise RuntimeError("The k3s node must mount exactly its four new labelled volumes and no host binds")
        self.docker("start", node)
        def kubectl(*args, **kwargs):
            self.container(node, "k3s-node")
            return self.docker("exec", "-i", node, "kubectl",
                               "--kubeconfig=/etc/rancher/k3s/k3s.yaml", *args, **kwargs)
        print("New dedicated k3s node started; readiness is bounded to 180 seconds.", flush=True)
        deadline = time.monotonic() + 180
        ready = False
        while time.monotonic() < deadline:
            info = self.container(node, "k3s-node")
            if not info["State"]["Running"]:
                break
            result = kubectl("get", "--raw=/readyz", "--request-timeout=3s", check=False, timeout=10)
            if result.returncode == 0 and result.stdout.strip() == b"ok":
                ready = True
                break
            time.sleep(2)
        if not ready:
            logs = self.docker("logs", "--tail", "150", node, check=False)
            self.private_file("k3s-startup.log", (logs.stdout + logs.stderr).decode(errors="replace"))
            self.private_file("k3s-readiness.log", (result.stdout + result.stderr).decode(errors="replace"))
            self.manifest["checks"]["k3s_runtime"] = "failed: dedicated node did not become API-ready within the bounded check; see private startup log"
            self.save()
            self.stop_non_qa()
            raise RuntimeError("Dedicated local k3s startup failed; scoped diagnostics retained")
        mode = self.docker("exec", node, "stat", "-c", "%a", "/etc/rancher/k3s/k3s.yaml").stdout.strip()
        if mode != b"600":
            raise RuntimeError("Dedicated kubeconfig permissions are not 600")
        kubectl("wait", "--for=condition=Ready", "node/" + self.prefix, "--timeout=120s", timeout=130)
        self.manifest["checks"]["k3s_runtime"] = "passed: API, Ready node, kubeconfig mode600, dedicated new storage"
        self.save()
        print("Dedicated k3s API and node ready; importing anonymous local/public images.", flush=True)
        headlamp_image = "ghcr.io/headlamp-k8s/headlamp:v0.46.0"
        self.docker("pull", headlamp_image, timeout=300)
        self.docker("pull", "postgres:16-alpine", timeout=300)
        archive = self.directory / "local-images.tar"
        with archive.open("xb"):
            os.chmod(archive, 0o600)
        self.docker("image", "save", "--output", str(archive), image, "postgres:16-alpine", headlamp_image, timeout=180)
        with archive.open("rb") as stream:
            self.docker("exec", "-i", node, "ctr", "images", "import", "-", stdin=stream, timeout=180)
        namespace = "sd-" + self.target_id.removeprefix("session3_")
        def manifest(name):
            text = (ROOT / name).read_text().replace("smartdesk-lab", namespace)
            text = text.replace("smartdesk:session3-local", image)
            return text.replace("smartdesk-headlamp-discovery", self.prefix + "-headlamp-discovery")
        kubectl("create", "-f", "-", input=manifest("k8s/namespace.yaml").encode())
        secret = {"apiVersion": "v1", "kind": "Secret", "metadata": {"name": "smartdesk-local", "namespace": namespace},
                  "type": "Opaque", "stringData": {"POSTGRES_DB": "smartdesk_lab", "POSTGRES_USER": "smartdesk_lab",
                  "POSTGRES_PASSWORD": secrets.token_hex(24), "SMARTDESK_SESSION_SECRET": secrets.token_hex(32)}}
        kubectl("create", "-f", "-", input=json.dumps(secret).encode())
        for path in ["k8s/postgres.yaml", "k8s/web.yaml", "headlamp-lab.yaml"]:
            content = manifest(path).encode()
            kubectl("apply", "--dry-run=server", "-f", "-", input=content)
            kubectl("apply", "-f", "-", input=content)
        self.manifest["checks"]["kubernetes_server_validation"] = "passed"
        self.manifest["namespace"] = namespace
        self.save()
        for workload in ["statefulset/postgres", "deployment/smartdesk", "deployment/headlamp"]:
            kubectl("-n", namespace, "rollout", "status", workload, "--timeout=120s", timeout=130)
        info = self.container(node, "k3s-node")
        endpoints = {}
        for port, key in [("30080/tcp", "application"), ("30090/tcp", "headlamp")]:
            binding = info["NetworkSettings"]["Ports"][port]
            if len(binding) != 1 or binding[0]["HostIp"] != "127.0.0.1":
                raise RuntimeError("Kubernetes NodePort access must be loopback-only")
            endpoints[key] = "http://127.0.0.1:" + binding[0]["HostPort"]
        for key, suffix in [("application", "/login"), ("headlamp", "/")]:
            with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(endpoints[key] + suffix, timeout=10) as response:
                if response.status != 200:
                    raise RuntimeError("Kubernetes local HTTP access failed")
        # A user token, not the server pod identity, determines UI authorization.
        viewer = "system:serviceaccount:" + namespace + ":headlamp-viewer"
        for verb, resource, expected in [("list", "pods", b"yes"), ("get", "secrets", b"no"), ("create", "pods", b"no")]:
            result = kubectl("-n", namespace, "auth", "can-i", verb, resource, "--as=" + viewer, check=False)
            if result.stdout.strip() != expected:
                raise RuntimeError("Headlamp viewer RBAC does not match the read-only scope")
        token = kubectl("-n", namespace, "create", "token", "headlamp-viewer", "--duration=10m").stdout.decode().strip()
        self.private_file("headlamp-viewer.token", token + "\n")
        kubectl("-n", namespace, "exec", "statefulset/postgres", "--", "psql", "-U", "smartdesk_lab", "-d", "smartdesk_lab", "-Atc",
                "SELECT current_database(), current_user, (SELECT count(*) FROM information_schema.tables WHERE table_schema='public')")
        self.manifest["checks"]["kubernetes_http_database_headlamp_rbac"] = "passed: app/login and Headlamp HTTP200, database connection, viewer pod-list allowed and Secret/write denied; browser login not exercised"
        self.manifest["endpoints"] = endpoints
        self.save()
        self.stop_non_qa()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--approve-local-session3", action="store_true",
                        help="Confirm authorization to create only new local lab resources")
    parser.add_argument("--phase", choices=["test-target", "compose", "k3s"], default="test-target")
    args = parser.parse_args()
    if not args.approve_local_session3:
        parser.error("Explicit local Session 3 authorization is required")
    lab = Lab()
    try:
        if args.phase == "test-target":
            lab.test_target()
        elif args.phase == "compose":
            lab.compose_validation()
        elif args.phase == "k3s":
            lab.k3s_validation()
    except BaseException:
        lab.manifest["checks"][args.phase] = "failed; resources retained for inspection"
        lab.stop_non_qa(include_qa=args.phase == "test-target")
        lab.save()
        print(f"Validation stopped. Private evidence: {lab.directory.relative_to(ROOT)}/manifest.json")
        raise
    print(f"Validation passed. Private evidence: {lab.directory.relative_to(ROOT)}/manifest.json")


if __name__ == "__main__":
    main()

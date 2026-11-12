"""Lab ownership and refusal safeguards without Docker or database access."""
import json
import stat
import subprocess
from unittest.mock import Mock

import pytest

from scripts import session3_lab


@pytest.fixture
def lab(tmp_path, monkeypatch):
    monkeypatch.setattr(session3_lab, "ROOT", tmp_path)
    monkeypatch.setenv("DATABASE_URL", "postgresql://must-not-be-inherited.invalid/application")
    monkeypatch.setenv("DOCKER_CONTEXT", "must-not-be-inherited")
    monkeypatch.setenv("AZURE_CLIENT_SECRET", "synthetic-must-not-be-inherited")
    return session3_lab.Lab()


def test_lab_uses_private_state_and_does_not_inherit_service_credentials(lab):
    private = lab.private_file("synthetic.env", "SYNTHETIC=value\n")
    assert stat.S_IMODE(lab.directory.stat().st_mode) == 0o700
    assert stat.S_IMODE(lab.config.stat().st_mode) == 0o700
    for path in (private, lab.directory / "manifest.json"):
        assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert list(lab.config.iterdir()) == []
    assert set(lab.env) == {"PATH", "DOCKER_CONFIG", "DOCKER_HOST"}
    assert lab.env["DOCKER_HOST"] == session3_lab.LOCAL_DOCKER
    with pytest.raises(FileExistsError):
        lab.private_file("synthetic.env", "replacement")
    assert private.read_text() == "SYNTHETIC=value\n"


def test_lab_refuses_existing_state_directory(tmp_path, monkeypatch):
    monkeypatch.setattr(session3_lab, "ROOT", tmp_path)
    monkeypatch.setattr(session3_lab.secrets, "token_hex", lambda size: "a" * 24)
    first = session3_lab.Lab()
    original = (first.directory / "manifest.json").read_bytes()
    with pytest.raises(FileExistsError):
        session3_lab.Lab()
    assert (first.directory / "manifest.json").read_bytes() == original


@pytest.mark.parametrize("returncode,stderr", [
    (0, b""),
    (1, b"permission denied while connecting to Docker socket"),
    (1, b"daemon unavailable"),
])
def test_uncertain_or_existing_resource_is_never_created(lab, returncode, stderr):
    lab.docker = Mock(return_value=subprocess.CompletedProcess([], returncode, b"", stderr))
    with pytest.raises(RuntimeError):
        lab.new_network("test-network")
    assert lab.docker.call_count == 1
    assert lab.docker.call_args.args[:2] == ("network", "inspect")
    assert lab.manifest["resources"] == []


@pytest.mark.parametrize("change", ["id", "label", "role", "name"])
def test_replaced_or_mislabelled_container_is_never_stopped(lab, change):
    name = lab.prefix + "-test-db"
    lab.manifest["resources"] = [{"kind": "container", "name": name, "id": "original-id", "role": "test-db"}]
    info = {"Name": "/" + name, "Id": "original-id", "State": {"Running": True},
            "Config": {"Labels": {session3_lab.LABEL: lab.target_id, "io.smartdesk.session3.role": "test-db"}}}
    if change == "id":
        info["Id"] = "replacement-id"
    elif change == "label":
        info["Config"]["Labels"][session3_lab.LABEL] = "another-run"
    elif change == "role":
        info["Config"]["Labels"]["io.smartdesk.session3.role"] = "another-role"
    else:
        info["Name"] = "/another-container"
    lab.docker = Mock(return_value=subprocess.CompletedProcess([], 0, json.dumps([info]).encode(), b""))
    with pytest.raises(RuntimeError):
        lab.stop_non_qa(include_qa=True)
    assert lab.docker.call_count == 1
    assert lab.docker.call_args.args[:2] == ("container", "inspect")


def test_command_failure_does_not_expose_generated_credentials(lab, monkeypatch):
    run = Mock(return_value=subprocess.CompletedProcess([], 1, b"synthetic-sensitive-output", b"synthetic-sensitive-error"))
    monkeypatch.setattr(session3_lab.subprocess, "run", run)
    with pytest.raises(RuntimeError) as failure:
        lab.command(["synthetic-command"])
    assert str(failure.value) == "Local validation command failed (exit 1)"

"""Mock infrastructure operations; these tests do not establish Docker acceptance."""
import json
from pathlib import Path
import subprocess
import sys

import pytest

HELPER = Path(__file__).resolve().parents[1] / 'scripts/session4_ci.sh'
CODE = HELPER.read_text().split("<<'PY'\n", 1)[1].rsplit('\nPY', 1)[0]


def execute_helper(tmp_path, monkeypatch, *, test_exit=0, report='pass', ownership=True, daemon=True):
    monkeypatch.chdir(tmp_path)
    output = 'reports/session4-ci-mocked'
    monkeypatch.setattr(sys, 'argv', ['helper', '--approve-local-ci', '--docker-host',
                                    'unix:///synthetic-personal.sock', '--output-dir', output])
    containers, commands = {}, []
    built = False
    def completed(args, code=0, stdout=b'', stderr=b''):
        return subprocess.CompletedProcess(args, code, stdout, stderr)
    def fake_run(args, **kwargs):
        nonlocal built
        assert set(kwargs['env']) == {'PATH', 'DOCKER_CONFIG', 'DOCKER_HOST'}
        commands.append(args)
        if args[0] == 'git':
            return completed(args, stdout=b'abc123\n' if args[1] == 'rev-parse' else b'')
        parts = args[5:]
        op = parts[0]
        if op == 'version': return completed(args, 0 if daemon else 1, b'local')
        if parts[:2] == ['image', 'inspect']:
            if not built: return completed(args, 1, stderr=b'no such image')
            return completed(args, stdout=json.dumps([{'Config': {'User': '10001:10001'}, 'Id': 'image-id', 'Os':'linux', 'Architecture':'arm64'}]).encode())
        if op == 'build': built = True; return completed(args)
        if parts[:2] == ['network', 'inspect']:
            if parts[2] != 'network-id': return completed(args, 1, stderr=b'no such network')
            label = next(c for c in commands if c[5:7] == ['network', 'create'])
            label_value = label[label.index('--label')+1].split('=',1)[1]
            return completed(args, stdout=json.dumps([{'Name':label[-1], 'Labels':{'io.smartdesk.session4.run':label_value}, 'Internal':True}]).encode())
        if parts[:2] == ['network', 'create']: return completed(args, stdout=b'network-id')
        if parts[:2] == ['container', 'inspect']:
            if parts[2] not in containers: return completed(args, 1, stderr=b'no such container')
            return completed(args, stdout=json.dumps([containers[parts[2]]]).encode())
        if op == 'create':
            name = parts[parts.index('--name')+1]
            role = 'postgres' if name.endswith('-postgres') else 'tests'
            identifier = role+'-id'
            labels = dict(parts[i+1].split('=',1) for i,p in enumerate(parts) if p=='--label')
            if not ownership: labels['io.smartdesk.session4.run'] = 'foreign'
            containers[identifier] = {'Id':identifier, 'Name':'/'+name, 'Config':{'Labels':labels},
                'HostConfig':{'Tmpfs':{'/var/lib/postgresql/data':'tmpfs'}}, 'Mounts':[],
                'State':{'Running':False,'Status':'created','ExitCode':0}}
            return completed(args, stdout=identifier.encode())
        if op == 'start':
            identifier = parts[-1]
            containers[identifier]['State'] = {'Running':identifier=='postgres-id',
                'Status':'running' if identifier=='postgres-id' else 'exited',
                'ExitCode':test_exit if identifier=='tests-id' else 0}
            return completed(args, test_exit if identifier=='tests-id' else 0)
        if op == 'exec':
            return completed(args, stdout=b'smartdesk_test|smartdesk_test' if 'SELECT current_database() ||' in ' '.join(parts) else b'')
        if op == 'cp':
            if report == 'missing': return completed(args, 1)
            destination = Path(parts[-1]); destination.mkdir(exist_ok=True)
            case = '<testcase name="ok"/>' if report=='pass' else '<testcase name="bad"><failure/></testcase>'
            (destination/'junit.xml').write_text('<testsuites>'+case+'</testsuites>')
            return completed(args)
        if op == 'stop': return completed(args)
        raise AssertionError('Unexpected synthetic Docker operation: '+str(parts))
    monkeypatch.setattr(subprocess, 'run', fake_run)
    with pytest.raises(SystemExit) as result:
        exec(compile(CODE, str(HELPER), 'exec'), {'__name__':'__main__'})
    manifest = json.loads((tmp_path/output/'manifest.json').read_text())
    return result.value.code, manifest, commands


@pytest.mark.parametrize('test_exit,report,expected', [(0,'pass',0), (1,'pass',1), (0,'failure',1), (0,'missing',1)])
def test_helper_propagates_test_and_report_failures(tmp_path, monkeypatch, test_exit, report, expected):
    code, manifest, commands = execute_helper(tmp_path, monkeypatch, test_exit=test_exit, report=report)
    assert code == expected
    assert all('--rm' not in cmd and 'rm' not in cmd for cmd in commands)


def test_helper_rejects_foreign_ownership_before_start_or_stop(tmp_path, monkeypatch):
    code, manifest, commands = execute_helper(tmp_path, monkeypatch, ownership=False)
    assert code == 1
    assert not any(cmd[5] in ('start','stop') for cmd in commands if len(cmd)>5)


def test_unavailable_daemon_creates_no_resources(tmp_path, monkeypatch):
    code, manifest, commands = execute_helper(tmp_path, monkeypatch, daemon=False)
    assert code == 1
    assert manifest['resources'] == []
    assert len(commands) == 1

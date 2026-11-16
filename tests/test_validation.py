"""Exercise report integrity and CI failure gates without external services."""
import json
from pathlib import Path
import subprocess

import pytest

from scripts import run_validation
from scripts.generate_report import parse


def test_inventory_includes_each_test_module_once():
    paths = [path for group in run_validation.suites().values() for path in group]
    expected = {str(path.relative_to(run_validation.ROOT))
                for path in (run_validation.ROOT / 'tests').rglob('test_*.py')}
    assert set(paths) == expected
    assert len(paths) == len(set(paths))
    assert 'tests/test_security.py' in paths
    assert 'tests/test_database_safety.py' in paths


@pytest.mark.parametrize('content', [None, '<broken', '<testsuites/>'])
def test_missing_malformed_or_empty_reports_are_not_success(tmp_path, content):
    path = tmp_path / 'junit.xml'
    if content is not None:
        path.write_text(content)
    cases, problem = parse(path)
    assert cases == []
    assert problem


@pytest.mark.parametrize('exit_code,case,required,expected', [
    (0, '<testcase name="ok"/>', True, 0),
    (1, '<testcase name="ok"/>', True, 1),
    (0, '<testcase name="bad"><failure/></testcase>', False, 1),
    (0, '<testcase name="bad"><error/></testcase>', False, 1),
    (0, '<testcase name="pg"><skipped/></testcase>', True, 1),
    (0, '<testcase name="pg"><skipped/></testcase>', False, 0),
    (0, None, False, 1),
    (0, '<broken', False, 1),
    (0, '', False, 1),
])
def test_runner_checks_process_and_report_results(tmp_path, monkeypatch, exit_code, case, required, expected):
    monkeypatch.setattr(run_validation, 'suites', lambda: {'postgres': ['tests/test_postgres.py']})
    monkeypatch.setenv('DATABASE_URL', 'postgresql://ambient-must-not-be-used.invalid/app')
    def fake_run(command, **kwargs):
        assert 'DATABASE_URL' not in kwargs['env']
        if case is not None:
            path = Path(next(arg.split('=', 1)[1] for arg in command if arg.startswith('--junitxml=')))
            path.write_text('<testsuites>' + case + '</testsuites>' if case != '<broken' else case)
        return subprocess.CompletedProcess(command, exit_code)
    monkeypatch.setattr(run_validation.subprocess, 'run', fake_run)
    output = tmp_path / 'new-run'
    assert run_validation.run(output, required) == expected
    assert json.loads((output / 'summary.json').read_text())['exit_code'] == expected


def test_runner_refuses_stale_output_without_touching_it(tmp_path):
    output = tmp_path / 'existing'
    output.mkdir()
    evidence = output / 'junit.xml'
    evidence.write_text('existing evidence')
    with pytest.raises(FileExistsError):
        run_validation.run(output)
    assert evidence.read_text() == 'existing evidence'

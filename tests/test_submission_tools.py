"""Verify local-demo isolation and source-package exclusion/failure safeguards."""
import hashlib
import json
import os
from pathlib import Path
import zipfile

import pytest

from scripts import package_submission as package
from scripts import run_local_demo as demo
from src.database import connect


@pytest.mark.parametrize('name', ['.env','reports/private.json','.azure/token.json','.git/config',
                                  'infra/azure/private.tfvars','infra/azure/private.tfvars.json',
                                  'infra/azure/backend.private.hcl','k8s/secret.yaml',
                                  'src/__pycache__/private.py','../outside.py'])
def test_package_excludes_private_runtime_and_unreviewed_configuration(name):
    assert package.allowed(name) is False


@pytest.mark.parametrize('name', ['SUBMISSION.md','.env.example','src/main.py','scripts/run_local_demo.py',
                                  'infra/azure/example.tfvars','infra/azure/backend.example.hcl',
                                  'infra/azure/.terraform.lock.hcl','k8s/secret.yaml.example'])
def test_package_keeps_reviewed_source_and_placeholder_examples(name):
    assert package.allowed(name)


@pytest.fixture
def fixture_package(tmp_path, monkeypatch):
    monkeypatch.setattr(package, 'ROOT', tmp_path)
    names = ['SUBMISSION.md','src/main.py','requirements.lock','docs/results.md']
    for name in names:
        target = tmp_path/name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text('Reviewed synthetic source\n')
    reports = tmp_path/'reports'; reports.mkdir()
    report = reports/'summary.json'
    report.write_text(json.dumps({'exit_code':0,'postgres_executed':False,'require_postgres':False,
        'private_value':'synthetic-not-to-export', 'suites':{'unit':{'exit_code':0,'passed':2,
        'failed':0,'errors':0,'skipped':1,'report_problem':None,'private_value':'synthetic-not-to-export'}}}))
    def git(*args):
        if args[0]=='ls-files': return ('\0'.join(names+['reports/private.json','.env'])+'\0').encode()
        if args[0]=='rev-parse': return b'abc123\n'
        if args[0]=='status': return b' M SUBMISSION.md\n'
        raise AssertionError(args)
    monkeypatch.setattr(package,'git',git)
    return tmp_path,report,names


def test_package_is_hashed_and_exports_only_numeric_evidence(fixture_package):
    root,report,names = fixture_package
    old_mask=os.umask(0o077)
    try:
        archive=package.build(root/'reports/submission-package-test',report)
    finally:
        os.umask(old_mask)
    with zipfile.ZipFile(archive) as bundle:
        assert set(bundle.namelist()) == set(names+['SUBMISSION_MANIFEST.json','EVIDENCE_SUMMARY.json'])
        manifest=json.loads(bundle.read('SUBMISSION_MANIFEST.json'))
        evidence=json.loads(bundle.read('EVIDENCE_SUMMARY.json'))
        assert manifest['submission_date']=='2026-11-17'
        assert manifest['oral_presentation_date']=='2026-11-26'
        assert manifest['azure_status']=='Prepared, not deployed'
        assert evidence['totals']=={'passed':2,'failed':0,'errors':0,'skipped':1}
        assert 'synthetic-not-to-export' not in json.dumps(evidence)
        for name in names:
            assert hashlib.sha256(bundle.read(name)).hexdigest()==manifest['source_sha256'][name]
    assert hashlib.sha256(archive.read_bytes()).hexdigest() in (archive.parent/'SHA256SUMS').read_text()


@pytest.mark.parametrize('setting,value', [('exit_code',1),('passed',0),('failed',1),('errors',1),('skipped',-1),('report_problem','missing')])
def test_failed_empty_or_invalid_evidence_refuses_package(fixture_package,setting,value):
    root,report,_=fixture_package
    data=json.loads(report.read_text())
    data['suites']['unit'][setting]=value
    report.write_text(json.dumps(data))
    with pytest.raises(ValueError):package.build(root/'reports/submission-package-refused',report)
    assert not (root/'reports/submission-package-refused').exists()


def test_package_refuses_source_symlinks(fixture_package):
    root,report,_=fixture_package
    (root/'src/target.py').write_text('synthetic')
    # Fixture-owned file only; no user's file is removed or replaced.
    (root/'src/main.py').rename(root/'src/main.saved')
    (root/'src/main.py').symlink_to(root/'src/target.py')
    with pytest.raises(ValueError,match='symlinks'):package.build(root/'reports/submission-package-link',report)


def test_package_refuses_sensitive_source_pattern(fixture_package):
    root,report,_=fixture_package
    (root/'src/main.py').write_text('-----BEGIN '+'PRIVATE KEY-----')
    with pytest.raises(ValueError,match='Sensitive'):package.build(root/'reports/submission-package-secret',report)


def test_package_never_overwrites_existing_output(fixture_package):
    root,report,_=fixture_package
    output=root/'reports/submission-package-existing';output.mkdir()
    existing=output/'existing.txt';existing.write_text('preserve')
    with pytest.raises(FileExistsError):package.build(output,report)
    assert existing.read_text()=='preserve'


def test_demo_creates_only_new_private_synthetic_sqlite(tmp_path,monkeypatch):
    monkeypatch.setattr(demo,'ROOT',tmp_path)
    monkeypatch.setenv('DATABASE_URL','postgresql://ambient-must-not-be-used.invalid/db')
    target=tmp_path/'reports/submission-demo-test'
    database=demo.prepare(target)
    accounts=json.loads((target/'accounts.private.json').read_text())
    assert len(accounts)==4
    assert (target/'accounts.private.json').stat().st_mode & 0o777 == 0o600
    assert database.stat().st_mode & 0o777 == 0o600
    with connect(str(database)) as db:
        assert db.execute('SELECT count(*) AS n FROM users').fetchone()['n']==4
        secrets={row['secret'] for row in db.execute('SELECT secret FROM users')}
        assert all(account['password'] not in secrets for account in accounts)
    with pytest.raises(FileExistsError):demo.prepare(target)


def test_demo_refuses_unknown_location(tmp_path,monkeypatch):
    monkeypatch.setattr(demo,'ROOT',tmp_path)
    with pytest.raises(ValueError):demo.prepare(tmp_path/'existing-database')
    assert not (tmp_path/'existing-database').exists()

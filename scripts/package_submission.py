"""Package reviewed source and numeric test evidence; never publish or deploy."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ROOT_FILES = {'README.md', 'SUBMISSION.md', 'Dockerfile', '.dockerignore', '.gitignore',
              'compose.yaml', 'compose.k3s.yaml', 'headlamp-lab.yaml', 'Jenkinsfile',
              'requirements.txt', 'requirements.lock', 'requirements-qa.txt', '.env.example'}
INFRA_FILES = {'versions.tf', 'variables.tf', 'foundation.tf', 'application.tf', 'outputs.tf',
               '.terraform.lock.hcl', '.gitignore', 'backend.example.hcl', 'example.tfvars',
               'deployment.example.json', 'bootstrap-runtime-role.sql'}
K8S_FILES = {'namespace.yaml', 'postgres.yaml', 'web.yaml', 'secret.yaml.example'}
SUFFIXES = {'src': {'.py', '.html', '.css', '.js'}, 'scripts': {'.py', '.sh'},
            'tests': {'.py'}, 'features': {'.feature'}, 'docs': {'.md'}}
SECRET_PATTERNS = [rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
                   rb'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|AKIA[A-Z0-9]{16})\b']


def allowed(name):
    path = Path(name)
    if path.is_absolute() or '..' in path.parts:
        return False
    if name in ROOT_FILES:
        return True
    if len(path.parts) == 3 and path.parts[:2] == ('infra', 'azure'):
        return path.name in INFRA_FILES
    if len(path.parts) == 2 and path.parts[0] == 'k8s':
        return path.name in K8S_FILES
    return (len(path.parts) > 1 and path.parts[0] in SUFFIXES
            and not any(part.startswith('.') or part == '__pycache__' for part in path.parts)
            and path.suffix in SUFFIXES[path.parts[0]])


def git(*args):
    env = {'PATH': os.environ.get('PATH', '/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin')}
    return subprocess.run(['git', *args], cwd=ROOT, env=env, capture_output=True,
                          check=True, timeout=30).stdout


def numeric_evidence(path):
    """Export only bounded numeric report fields, never logs or private strings."""
    path = Path(path).resolve()
    if ROOT / 'reports' not in path.parents or path.is_symlink():
        raise ValueError('Evidence must be a reviewed local report summary under reports/')
    report = json.loads(path.read_text())
    suites = {}
    for name in ('unit', 'integration', 'bdd', 'postgres', 'regression'):
        item = report.get('suites', {}).get(name)
        if item is None:
            continue
        selected = {}
        for key in ('exit_code', 'passed', 'failed', 'errors', 'skipped'):
            value = item.get(key)
            if type(value) is not int or value < 0:
                raise ValueError('Invalid numeric test evidence')
            selected[key] = value
        selected['report_valid'] = not bool(item.get('report_problem'))
        suites[name] = selected
    if (not suites or report.get('exit_code') != 0
            or sum(s['passed'] for s in suites.values()) == 0
            or any(s['failed'] or s['errors'] or s['exit_code'] or not s['report_valid'] for s in suites.values())):
        raise ValueError('A successful nonempty normal report run is required; skips remain explicit')
    return {'suites': suites,
            'totals': {key: sum(s[key] for s in suites.values()) for key in ('passed', 'failed', 'errors', 'skipped')},
            'postgres_executed': report.get('postgres_executed') is True,
            'require_postgres': report.get('require_postgres') is True,
            'runtime_warning_count': 'See the committed validation record; this summary does not count warnings'}


def build(output, evidence_path):
    output = Path(output).resolve()
    if output.parent != ROOT / 'reports' or not re.fullmatch(r'submission-package-[A-Za-z0-9_-]+', output.name):
        raise ValueError('Use a new reports/submission-package-<unique-id> directory')
    if output.exists():
        raise FileExistsError('Existing package/evidence directory must be preserved')
    evidence = numeric_evidence(evidence_path)
    names = sorted({name for name in git('ls-files', '--cached', '--others', '--exclude-standard', '-z').decode().split('\0')
                    if name and allowed(name)})
    if not {'SUBMISSION.md', 'src/main.py', 'requirements.lock'}.issubset(names):
        raise ValueError('Submission entry point, application and dependency lock are required')
    contents, hashes = {}, {}
    for name in names:
        source = ROOT / name
        if source.is_symlink() or ROOT not in source.resolve().parents:
            raise ValueError('Source symlinks/outside-workspace paths are refused')
        content = source.read_bytes()
        if any(re.search(pattern, content) for pattern in SECRET_PATTERNS):
            raise ValueError('Sensitive token/private-key pattern in submission source: ' + name)
        contents[name] = content
        hashes[name] = hashlib.sha256(content).hexdigest()
    manifest = {'submission_date': '2026-11-17', 'oral_presentation_date': '2026-11-26',
                'source_commit': git('rev-parse', 'HEAD').decode().strip(),
                'working_tree_dirty': bool(git('status', '--porcelain').strip()),
                'provenance': 'Current reviewed working files; hashes are authoritative for included content.',
                'azure_status': 'Prepared, not deployed', 'azure_spending_authorized_eur': 0,
                'ai_api_spending_authorized_eur': 0, 'source_sha256': hashes,
                'evidence_summary_sha256': hashlib.sha256(json.dumps(evidence, sort_keys=True).encode()).hexdigest()}
    os.umask(0o077)
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    archive = output / 'smartdesk-submission-2026-11-17.zip'
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED) as package:
        for name, content in contents.items():
            package.writestr(name, content)
        package.writestr('SUBMISSION_MANIFEST.json', json.dumps(manifest, indent=2) + '\n')
        package.writestr('EVIDENCE_SUMMARY.json', json.dumps(evidence, indent=2) + '\n')
    (output / 'source-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    (output / 'SHA256SUMS').write_text(digest + '  ' + archive.name + '\n')
    print(json.dumps({'archive': str(archive.relative_to(ROOT)), 'sha256': digest,
                      'source_files': len(names), 'test_totals': evidence['totals']}, indent=2))
    return archive


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', required=True, type=Path)
    parser.add_argument('--evidence-summary', required=True, type=Path)
    args = parser.parse_args()
    try:
        build(args.output_dir, args.evidence_summary)
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        parser.exit(1, 'Submission package refused: ' + str(exc) + '\n')


if __name__ == '__main__':
    main()

"""Run the complete test inventory with exclusive reports and explicit CI gates."""
import argparse
from collections import Counter
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid
from scripts.generate_report import generate, parse

ROOT = Path(__file__).resolve().parents[1]


def suites():
    """Partition every test module once, including newly added regression tests."""
    groups = {
        "unit": ["tests/test_ticket_rules.py", "tests/test_permissions.py", "tests/test_mvp.py"],
        "integration": ["tests/test_auth.py", "tests/test_api.py", "tests/test_security.py"],
        "bdd": ["tests/bdd/test_scenarios.py"],
        "postgres": ["tests/test_postgres.py"],
    }
    assigned = {path for paths in groups.values() for path in paths}
    groups["regression"] = sorted(str(path.relative_to(ROOT)) for path in (ROOT / "tests").rglob("test_*.py")
                                  if str(path.relative_to(ROOT)) not in assigned)
    return {name: paths for name, paths in groups.items() if paths}


def run(output, require_postgres=False):
    output = Path(output).resolve()
    # Never reuse old reports or silently merge with another run.
    output.mkdir(parents=True, exist_ok=False)
    groups = suites()
    codes, results = {}, {}
    env = {"PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
           "PYTHONDONTWRITEBYTECODE": "1", "PIP_CONFIG_FILE": "/dev/null"}
    for key in ("SMARTDESK_TEST_DATABASE_URL", "SMARTDESK_TEST_DATABASE_APPROVED", "SMARTDESK_TEST_TARGET_ID"):
        if key in os.environ:
            env[key] = os.environ[key]
    for name, paths in groups.items():
        folder = output / name
        folder.mkdir()
        command = [sys.executable, "-m", "pytest", "-q", "-rs", "-p", "no:cacheprovider", *paths,
                   f"--junitxml={folder / 'junit.xml'}", f"--html={folder / 'index.html'}", "--self-contained-html"]
        print(f"\n### {name.upper()} ###", flush=True)
        try:
            codes[name] = subprocess.run(command, cwd=ROOT, env=env, check=False, timeout=300).returncode
        except (OSError, subprocess.TimeoutExpired):
            codes[name] = 1
        cases, problem = parse(folder / "junit.xml")
        counts = Counter(case[2] for case in cases)
        results[name] = {"exit_code": codes[name], "passed": counts["aprovado"],
                         "failed": counts["falhado"], "errors": counts["erro"],
                         "skipped": counts["ignorado"], "report_problem": problem}
    totals = generate(output, codes, suite_names=tuple(groups))
    failed = any(item["exit_code"] or item["report_problem"] or item["failed"] or item["errors"]
                 for item in results.values())
    postgres = results.get("postgres", {})
    postgres_executed = bool(postgres.get("passed")) and not any(
        postgres.get(key) for key in ("failed", "errors", "skipped", "report_problem", "exit_code"))
    if require_postgres and not postgres_executed:
        failed = True
    summary = {"suites": results, "totals": dict(totals), "require_postgres": require_postgres,
               "postgres_executed": postgres_executed, "exit_code": int(failed)}
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"\nReport: {output / 'index.html'}; required PostgreSQL executed: {postgres_executed}", flush=True)
    return int(failed)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "reports" / ("validation-" + uuid.uuid4().hex))
    parser.add_argument("--require-postgres", action="store_true")
    args = parser.parse_args()
    try:
        return run(args.output_dir, args.require_postgres)
    except FileExistsError:
        parser.error("Output directory already exists; choose a new report directory")


if __name__ == "__main__":
    raise SystemExit(main())

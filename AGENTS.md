# SmartDesk Agent Workflow

## Project and language

- Work only on the personal SmartDesk project at `/Users/filipematos/Documents/SmartDesk` and its personal repository, `https://github.com/filipematos1982/smartdesk`.
- Write all instructions, documentation, comments, and new or changed project content in professional English. Propose translation of existing non-English content as a separate approved task; do not rename persisted values or change behavior as an incidental translation.
- Never access, modify, or authenticate against Revenya accounts, repositories, services, or credentials. Do not inspect credential stores or reuse ambient credentials for external services.

## Initial operating mode and approval

- Start in read-only mode. Inspect and propose changes; do not edit files, install dependencies, generate reports, or execute commands with side effects without explicit user approval for the specific task.
- Approval to inspect or configure agents does not authorize implementation or deployment. Before future changes, present the proposed files, purpose, validation, and effects for user approval. Change the parent session's permissions only after that approval.
- Never commit or push without explicit user approval. Never change global Git settings.
- Never create cloud resources. Azure work is limited to deployment preparation and proposals; resource creation requires a separate explicit user authorization that changes this restriction.
- Never run `git clean`, `git reset --hard`, or destructive operations. Do not delete data, remove volumes, discard changes, rewrite history, or replace existing work.

## Preserve existing work

- Treat all existing tracked and untracked files as user or Claude Code work. Do not overwrite, stage, move, or remove them without specific authorization.
- Before any approved implementation, inspect Git status and obtain a clear handoff for the exact files from the user when Claude Code may be working on them. Absence of a Claude configuration file is not evidence that Claude is inactive.
- If a file changes unexpectedly or ownership overlaps, stop work on that file and report the conflict. Do not resolve it by overwriting another tool's changes.
- Do not assume a Git worktree includes untracked files. Establish an approved baseline before proposing worktree-based implementation.

## Coordinator responsibilities

- Do not launch specialists unless the user explicitly requests delegation for the current task. The presence of these agent definitions does not authorize execution.
- Use only the four project specialists: `backend`, `devops`, `qa`, and `azure`. Specialists must not launch additional agents.
- Run at most one specialist at a time across SmartDesk sessions. Before starting, confirm no other specialist is active; wait for its result and close its thread before starting the next.
- The configured thread limit applies per session and excludes the coordinator. It does not coordinate separate Codex sessions or Claude Code. Do not start another SmartDesk session to bypass the limit.
- Assign a concrete task, exact files, read-only or explicitly approved implementation mode, validation expectations, and the required result before delegation.
- While a specialist owns a task, the coordinator must not edit or run validation against its assigned files. Do not execute agents concurrently against the same files, including files they only read for validation.
- Keep shared files such as `requirements.txt`, `README.md`, and cross-cutting documentation under coordinator ownership. Specialists propose shared-file changes for a separate approved step.
- Review each specialist's findings and any approved diff before transferring ownership. Report actual validation results and distinguish passes, failures, skips, and checks not run.

## Specialist boundaries

- Backend: FastAPI routes, authentication, business rules, templates, static assets, and PostgreSQL persistence in `src/`. Propose test and infrastructure changes to their owners.
- DevOps: Dockerfile, Compose, Kubernetes lab manifests, and Jenkins configuration. Do not run builds, start containers, apply manifests, trigger pipelines, or contact clusters in read-only mode.
- QA: `tests/`, `features/`, and validation/report scripts explicitly assigned by the coordinator. Do not repair application or infrastructure files. Tests may write caches, reports, and database schemas, so obtain approval before running them and use isolated local test data.
- Azure: architecture, deployment prerequisites, cost assumptions, draft infrastructure, and deployment documentation in explicitly assigned future paths. Do not authenticate, inspect subscriptions, execute deployments, or create cloud resources.

## Configuration and activation

- Project configuration is in `.codex/config.toml`; specialist definitions are standalone TOML files in `.codex/agents/`.
- Agent file scopes are instructions, not filesystem access controls. Specialists inherit parent permissions and integrations. Read-only sandboxing does not prevent every external tool action; the account and deployment restrictions above remain mandatory.
- Start a fresh CLI session with `codex -C /Users/filipematos/Documents/SmartDesk --sandbox read-only --ask-for-approval on-request`. Review effective permissions before delegating; project configuration may require project trust and higher-priority settings can override defaults.
- Example after the user requests execution: "Use only the backend specialist to inspect src/database.py in read-only mode. Do not run tests or edit files. Return findings and wait."
- Use `/subagents` to inspect specialist activity. Ask the coordinator to close the completed specialist before assigning the next one.

# SmartDesk final delivery and presentation plan

**Presentation date: 26 November 2026. Planning update: 16 November 2026.**

This is a provisional presentation outline and rehearsal plan, not an instructor acceptance specification, finished slide deck or completed demonstration. Sessions 6–8 topics are confirmed by the user; their detailed acceptance requirements remain **UNCONFIRMED**. The [eight-session compliance matrix](../arquitetura/10_zero_cost_training.md), approved [product requirements](../produto/02_requisitos_e_user_stories.md) and [MVP](../produto/03_mvp_backlog_e_aceitacao.md) remain the evidence baseline. Existing categories, roles and persisted states are unchanged.

## Operating limits

Azure and AI API spending authorization is **EUR 0**. Azure status is **Prepared, not deployed**. Do not create cloud resources, activate/upgrade paid subscriptions, use promotional credits, authenticate to company accounts, add AI models or call paid APIs. No company resources may be accessed. No Git push, commit or Session 6–8 feature implementation is authorized by this planning task.

The available Docker environment is shared and prohibited for this project work. Do not run Docker inventory, builds, container operations, volume/network inspection or Kubernetes commands against it or an ambient cluster. A future runtime rehearsal needs a separately approved dedicated personal environment and new synthetic data. Never reset a database, remove a volume, restart retained Session 3 targets, or reuse their expired credentials/tokens for a presentation.

## Evidence labels for every slide and demonstration

| Label | Meaning |
| --- | --- |
| Executed in this planning pass | Documentation review and validation only; no runtime rehearsal. |
| Historical executed evidence | A recorded earlier check, tied to its session/source and limitations. It is not a current build result. |
| Prepared, not executed | Existing code, templates, tests or a written procedure without execution evidence for the proposed demonstration. |
| Blocked | Required environment, authorization or dependency is unavailable. Do not substitute a skip as a pass. |
| UNCONFIRMED | Instructor-specific acceptance is unavailable. A confirmed topic alone is insufficient. |

Do not combine counts from different suite inventories, subtract separate Chrome checks from BDD skips, or project private logs/credentials. Use the reviewed documentation as the default evidence surface. Any screenshots or report extracts prepared later must come from actual execution, be labelled with their source/date and be reviewed for secrets and personal data. Do not manufacture successful screenshots or open private environment, backup, token or browser-profile files on screen.

## Provisional presentation outline

Slide count, duration, format and marking rubric are **UNCONFIRMED**. The following order is a planning proposal that can be adjusted without inventing acceptance criteria.

| Segment | Session coverage | Suggested content and evidence |
| --- | --- | --- |
| 1. Purpose and honest delivery status | All eight | Educational support-ticket project; EUR 0 cloud/API policy; confirmed topics versus missing acceptance. |
| 2. Problem, personas and approved MVP | 1 | Employee, technician and manager; requirements, journey and Gherkin. Explain that backlog P0/P1 is not ticket priority. |
| 3. Application and security foundation | 2 | FastAPI/templates, authentication, CSRF, signed cookies and role checks; Session 2 historical evidence. |
| 4. Ticket workflow walkthrough | 1–3 | Creation, assignment, start, resolution, return to handling and manager closure; synthetic data only. Clearly label live versus historical evidence. |
| 5. Persistence and local infrastructure | 3 | PostgreSQL, Compose, k3s, Headlamp and image workflow; historical restart/restore and rollout evidence plus current shared-environment blocker. |
| 6. Automated tests and delivery gates | 4 | Pass/skip/warning counts, report integrity, required-PostgreSQL failure gate, Chrome/timing evidence; Jenkins execution remains unverified. |
| 7. Azure preparation without deployment | 5 | Terraform, private architecture, identity/secrets/TLS/probes and offline validation; paid design retained as reference only. State **Prepared, not deployed**. |
| 8. AI-assisted classification/prioritization | 6 | Confirmed topic; current manual categories and absent ticket-priority field; unresolved requirements. No model, priority definition or implemented AI outcome is claimed. |
| 9. Security, logging and monitoring | 7 | Existing security controls; difference between server output and an accepted audit/monitoring solution; unresolved evidence requirements. |
| 10. Integration, documentation and demonstration | 8 | Traceable sources, demo checklist, fallbacks, outstanding work and presentation readiness limits. No claim of final instructor sign-off. |
| 11. Conclusions and questions | All eight | What was implemented, what was executed, what is blocked, and exactly which instructor materials are missing. |

## Preserved Session 1–5 evidence

| Source | Historical result/evidence to present | Limit that must accompany it |
| --- | --- | --- |
| [Session 1 requirements](../produto/02_requisitos_e_user_stories.md) and [MVP](../produto/03_mvp_backlog_e_aceitacao.md) | Approved functional scope and traceability | Documentation approval is not execution acceptance for all eight sessions. |
| [Session 2 validation](../qualidade/04_session_2_validation.md) | Authentication/security, HTTP/SQLite and earlier container-hardening checks | Earlier image and suite; not proof of the current image or cloud readiness. |
| [Session 3 validation](../qualidade/05_session_3_validation.md) | Final verified PostgreSQL suite: **114 passed, 3 skipped, 1 warning**; Compose restart persistence and dump/restore; k3s rollout/HTTP/database/RBAC smoke | Historical isolated resources. Headlamp browser token login, cluster recovery and full notebook acceptance were not established. |
| [Session 4 validation](../qualidade/06_session_4_validation.md) | Host suite: **116 passed, 21 skipped, 1 warning**; **91%** source statement coverage; normal runner exit 0; required-PostgreSQL runner exit 1 as expected | 18 PostgreSQL skips and 3 BDD placeholders. Strict exit 1 verifies refusal, not PostgreSQL success. No actual Jenkins build or current image/runtime acceptance. |
| [Session 4 separate acceptance](../qualidade/06_session_4_validation.md) | **2 aggregate checks passed, 1 skipped**: real headless Chrome login/create and small SQLite timing workload; Edge absent | Separate evidence, not a full browser matrix or production/PostgreSQL performance result. Initial Chrome harness assertion was corrected before the passing repeat. |
| [Session 5 validation](../qualidade/07_session_5_preparation.md) | Local Terraform final validation: **0 errors, 0 warnings**; offline preparation/pricing checks | Eleven initial schema errors were corrected. No Azure account access, plan/apply, resource creation, deployment or DB bootstrap. |

Session 3 and Session 4 test inventories differ. Their totals must not be added together or presented as repeated runs of an identical suite. Preserve the recorded corrected failures, warnings and skips alongside successful final results. Private evidence paths are recorded in the session documents; no private evidence is copied or republished by this plan.

## Demonstration readiness

An offline walkthrough of reviewed source, approved requirements, committed validation records, Jenkins configuration, Kubernetes manifests and Azure templates is supported now. It is the current presentation fallback; no live service availability has been checked in this planning pass.

Existing host tooling supports a separately approved rehearsal of SQLite/HTTP tests, a new synthetic loopback server, real Chrome automation and response timings. The acceptance helper stops its server when complete; it is an automated demonstration, not an interactive server kept running for a presenter. A continuous interactive application demonstration still needs an explicit rehearsal setup decision. SQLite evidence must be labelled SQLite, not PostgreSQL.

PostgreSQL persistence, Docker image build/non-root runtime, Compose, k3s/Headlamp and a real Jenkins run need a dedicated approved environment. They are currently blocked for live demonstration. Explain their historical evidence and current limitations rather than reconnecting retained/shared resources. No cloud demonstration is planned.

## Local demonstration checklist

All boxes are initially unchecked. They are future rehearsal/presentation tasks, not results. Record actual date, source revision, environment and outcome if a later authorized rehearsal is performed.

- [ ] **Preflight:** confirm personal checkout/revision and ownership; preserve all tracked/untracked work. Confirm synthetic data only, EUR 0 policy, private-file exclusions and an approved host/dedicated environment. Confirm the presentation duration/format if supplied; otherwise keep the outline provisional.
- [ ] **Application startup:** choose an approved new synthetic host setup or dedicated local environment; demonstrate startup and `/login` responsiveness. Current fallback: explain the app factory/startup sequence and historical records. Do not assume an existing app/DB is running or bypass the shared-Docker restriction.
- [ ] **Authentication:** with synthetic accounts, demonstrate valid login, invalid login and logout; explain cookie/CSRF controls. Current fallback: show existing security tests and historical evidence. Do not display passwords, tokens or cookie contents.
- [ ] **Ticket creation and lifecycle:** employee creates a Hardware, Software or Access ticket; manager assigns technician; responsible technician starts/resolves; employee reports persistence and returns it to handling; technician resolves; manager verifies and closes. Closed tickets cannot reopen. Use the approved business flow, not an invented priority or AI result.
- [ ] **Role-based permissions:** show employee visibility isolation, technician assignment restrictions and manager-only assignment/closure using synthetic data. Explain denied mutations without treating UI hiding as authorization proof. Current fallback: review the relevant existing permission tests.
- [ ] **PostgreSQL persistence:** only in a newly approved verified disposable local target, record a synthetic ticket and a fresh connection/restart result. Any restore uses a new target and preserves source data. **Blocked now.** Fallback: Session 3 restart and backup/restore evidence; SQLite reloads do not substitute.
- [ ] **Automated tests:** in an approved host rehearsal, run the existing full-inventory report tool with a fresh output directory and sanitized environment. Report actual pass/fail/error/skip/warning counts. Without an approved PostgreSQL target, report its skips and demonstrate that the strict gate refuses success. Current fallback: Session 4 records; no tests were rerun for this plan.
- [ ] **Docker and Kubernetes:** explain image allowlisting, declared non-root UID, Compose, namespace/PVC, probes and Headlamp viewer RBAC. **Live runtime blocked now.** Use historical Session 3 evidence; do not run Docker/Kubernetes commands or reuse expired viewer tokens. Image publication and current image architecture/runtime remain unverified.
- [ ] **Jenkins/CI/CD evidence:** show the pipeline and local helper's failure/report/ownership safeguards, plus their historical mocked tests. Label real Jenkins controller lint/build **not executed**. Do not trigger a job, registry publication or external deployment.
- [ ] **Azure infrastructure preparation:** show the templates, scoped identity/secret/TLS design and historical local schema result. Optionally rehearse the existing offline renderer only, which reports EUR 0 and **Prepared, not deployed**. Do not display reference commands as approval to run them; no Azure authentication, plan/apply or provisioning.
- [ ] **Sessions 6–8 limitations:** show confirmed topics, existing foundations, **UNCONFIRMED** details and the separate pending work below. No AI demo, completed monitoring integration or final instructor acceptance is claimed.
- [ ] **Close and preserve:** stop only explicitly owned synthetic rehearsal processes under that rehearsal's approval. Preserve databases, volumes, generated evidence and Git history; perform no cleanup deletion, commit or push. Use a labelled evidence fallback if a rehearsal was not authorized or failed.

## Remaining work safe to plan without further instructor materials

| Work | What can be completed safely | Boundary |
| --- | --- | --- |
| Documentation consistency | Correct confirmed topics/date, maintain links, reconcile evidence labels and create this provisional outline/checklist | Performed in this documentation pass; no new acceptance criteria. |
| Presentation rehearsal | Practice the evidence narrative, adjust provisional slide order and explain known limitations | A future rehearsal; do not claim it occurred here. |
| Host-only evidence refresh | Reuse existing isolated SQLite/HTTP/Chrome tooling with new synthetic output/data and report real outcomes | Requires separate execution approval; no Docker, PostgreSQL substitution or paid API. |
| Sanitized visual aids | Prepare actual screenshots/extracts of reviewed public/synthetic evidence | Review for secrets first; no fabricated success or private files. No visuals generated here. |
| Dedicated local infrastructure | Plan a separate personal environment to close runtime gaps | No runtime operation now; explicit environment/ownership approval needed. |
| Missing-material checklist | Consolidate exact unresolved questions for the instructor | Draft only; no message is sent and the confirmed outline need not be requested again. |

None of these activities authorizes new AI features, priority schema changes, monitoring-platform selection, cloud resources or public exposure.

## Session 6 pending work — AI-assisted classification and prioritization

**Topic confirmed; detailed instructor acceptance: UNCONFIRMED.** The existing MVP has manual categories and no ticket-priority field. Its P0/P1 backlog labels are development ordering, not priority values for tickets. Automated AI resolution is a different capability and must not be added as a substitute.

Needed materials/decisions: the detailed Session 6 notebook/exercises or updated reference branch; input/output contract; target classification taxonomy; priority definitions; permitted AI approach and data handling; human review/fallback behavior; approved dataset, expected outputs and evaluation metrics/thresholds. These are unresolved questions, not prescribed requirements. No model/provider, new labels, confidence threshold, prompt, database migration or API integration is selected. AI API spending remains EUR 0. Implementation waits for an approved scope.

## Session 7 pending work — security, access control, logging and monitoring

**Topics confirmed; detailed instructor acceptance: UNCONFIRMED.** Existing authentication, password hashing, signed cookies, CSRF, role checks and tests are a foundation. Process-local throttling/proxy identity, session revocation limits and outstanding PostgreSQL/runtime checks remain documented. Server console/access output and a transitive telemetry dependency do not establish an accepted security audit trail or operational monitoring system. Azure logging templates are undeployed.

Needed materials/decisions: the detailed Session 7 notebook/exercises; required threat/access scenarios and permissions matrix; expected security evidence; required application events and sensitive-data redaction; log format/retention/access rules; monitoring signals, thresholds, platform constraints and demonstration evidence. No platform, cloud service, external log destination or security feature is added in this pass. Preserve working controls; approved implementation can follow a separate review.

## Session 8 pending work — integration, documentation, demonstration and presentation

**Topics and 26 November 2026 presentation date confirmed; detailed instructor acceptance: UNCONFIRMED.** This file prepares an outline and checklist; it does not establish a finished deck, recorded demo, final integrated build or instructor approval.

Needed materials/decisions: the detailed Session 8 notebook/rubric; final integration/release checklist; required demonstration scenarios and whether offline/local evidence is accepted; slide/presentation format and duration; required documentation/reports/video/artifact formats; submission channel, exact deadline/time and grading criteria. No repository push or publishing action is authorized. Prepare the narrative from actual evidence, retain corrected failures and unresolved blockers, and finalize deliverables only against confirmed criteria.

## Instructor reference and provenance

The completed read-only audit reviewed 22 application/documentation files at [instructor commit e24e539](https://github.com/smartlearningci/smartdesk/tree/e24e539fde5131a0ad6a1843556855ce0707d3a5). No detailed Session 6–8 notebooks were found in that snapshot. Its [MVP](https://github.com/smartlearningci/smartdesk/blob/e24e539fde5131a0ad6a1843556855ce0707d3a5/docs/produto/03_mvp_backlog_e_aceitacao.md) does not define ticket priorities. The user's confirmed later course topics are preserved above; the reference snapshot does not certify their acceptance.

## Validation of this planning pass

Validate relative documentation links, all eight session rows and confirmed topics, the presentation date, the source-recorded evidence counts, EUR 0/Prepared-not-deployed statements, checklist coverage and separate pending sections. Check Markdown whitespace and that unrelated pre-existing changes are byte-for-byte preserved. These are documentation checks only; no application tests, Docker/Kubernetes/Jenkins operations, database work, Azure operation or AI API call is executed. Stop before staging, committing or implementing features.


Documentation validation completed on **16 November 2026**: 31 relative-link checks passed; all eight session rows, the presentation date, EUR 0 policy, nine requested demonstration areas, three pending-work sections and historical evidence counts were checked. Markdown fence/whitespace checks passed. Hash comparisons confirmed that all five unrelated pre-existing modified files were unchanged. Git review found no application, test, feature, infrastructure, dependency or pipeline changes. No runtime test or rehearsal was executed, and nothing was staged or committed.

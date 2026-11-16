# SmartDesk zero-cost policy and eight-session alignment

## Controlling requirement

**Maximum authorized Azure spending: EUR 0. Maximum authorized AI API spending: EUR 0. Azure deployment: Prepared, not deployed.**

SmartDesk is an educational personal project. No AI model, paid API, external inference call or promotional AI credit use is authorized by this plan. The user does not authorize Azure spending, paid resources, subscription activation/upgrades, promotional-credit consumption, cloud provisioning or deployment. Do not authenticate against company tenants/subscriptions or access Revenya resources. No Azure account, subscription, credit balance or billing data is inspected to implement this policy.

Permitted work is infrastructure-as-code, documentation, deployment instructions as reference material, and safe local validation without cloud provisioning. Earlier cost estimates and reference approval sequences do not grant spending permission. The existing paid architecture is retained to preserve work and explain its incompatibility with the zero-spend requirement. It is not the current delivery plan.

Prefer local PostgreSQL, Docker and Kubernetes demonstrations. Existing databases, volumes, networks, configuration and history must remain preserved. The current shared Docker environment remains prohibited; local runtime demonstrations need an explicitly approved dedicated personal environment. No Docker operations are authorized by this document.

## Genuine zero-cost assessment

Current official [Azure account information](https://azure.microsoft.com/en-us/pricing/purchase-options/azure-account) describes time-limited/new-customer offers, free usage quantities and promotional credit. Microsoft's [avoid-charges guidance](https://learn.microsoft.com/en-us/azure/cost-management-billing/manage/avoid-charges-free-account) explains eligibility, usage limits, expiration and charges after an upgrade. These conditions do not establish that the full SmartDesk architecture can run at guaranteed EUR 0 without consuming credits.

**No genuinely zero-cost actual Azure deployment of this complete project has been verified or authorized.** ACR, PostgreSQL, storage, logging, network dependencies and account eligibility must all be considered; a free application-compute allowance is insufficient. Budget alerts and scale-to-zero are not hard cost guarantees. The previously modelled EUR 46.29–70.51 stack is paid and must not be deployed under this policy.

If actual Azure deployment is required by the instructor, first obtain the precise requirement and identify a current, genuinely zero-cost option with all dependencies and limits verified. Do not create an account, upgrade a subscription, consume promotional credits or deploy while investigating. Submit the evidence and exact proposed actions for explicit user approval. Until then, retain **Prepared, not deployed** and use local demonstrations as technical evidence without claiming they satisfy unverified instructor cloud acceptance.

## Eight-session evidence map

This provisional compliance matrix combines existing project evidence with the course topics confirmed by the user on 16 November 2026. Sessions 6–8 topics are confirmed; their detailed notebooks and instructor acceptance criteria remain **UNCONFIRMED**. Topic confirmation is not evidence of completed implementation or instructor acceptance. No AI model, priority scale, monitoring platform or additional cloud service is prescribed here.

| Session | Available scope/evidence | Status and next permitted work |
| --- | --- | --- |
| 1 | Approved requirements, MVP and Gherkin in `docs/produto/` and `features/tickets.feature` | Preserve approved scope; traceability alone does not prove acceptance. |
| 2 | Bootstrap, authentication, CSRF, permissions and Docker preparation; [validation](../qualidade/04_session_2_validation.md) | Historical implementation and test evidence; preserve security behavior. |
| 3 | PostgreSQL, Compose, k3s, Headlamp and image/Docker Hub workflow; [validation](../qualidade/05_session_3_validation.md) | Historical isolated runtime evidence. Notebooks 09A/09B are incomplete; no registry publication acceptance is claimed. |
| 4 | Automated tests/reporting, Jenkins gates, image workflow and local deployment preparation; [validation](../qualidade/06_session_4_validation.md) | Host tests and Chrome/synthetic timing evidence exist. Image/PostgreSQL/Jenkins/runtime gaps remain; shared Docker cannot close them. |
| 5 | Azure architecture, Terraform, offline preparation and EUR reference pricing; [validation](../qualidade/07_session_5_preparation.md) | **Prepared, not deployed.** EUR 0 policy controls. AKS and exact instructor cloud acceptance remain unconfirmed. |
| 6 | **Confirmed:** AI-assisted ticket classification and prioritization | Manual categories exist; no AI classifier or ticket-priority field is implemented. Labels, priority meanings, permitted AI approach, workflow and evaluation criteria are **UNCONFIRMED**. No feature work or AI API spending is authorized. |
| 7 | **Confirmed:** security, access control, application logging and monitoring | Existing authentication, CSRF and role controls provide a foundation. Required security evidence, logging events/redaction/retention and monitoring signals/platform/thresholds are **UNCONFIRMED**. Server logs and undeployed Azure templates do not prove monitoring acceptance. |
| 8 | **Confirmed:** final SmartDesk integration, documentation, demonstration and presentation | Presentation date: **26 November 2026**. Existing lifecycle, documentation and evidence support preparation. Final integration criteria, demonstration rubric, presentation format/duration and submission artifacts are **UNCONFIRMED**. See the [provisional delivery plan](../apresentacao/01_final_delivery_plan.md). |

## Local alignment changes and validation

Started from clean `main` at `7455993dd7fe530417aaed3c51282d76a70b1750`. The existing Session 5 files and application were preserved. README and Azure documents now state the EUR 0 policy and deployment status. The offline renderer records zero authorized spending, denies provisioning/credit authorization and withholds reference cloud commands by default. `--include-reference-commands` is an educational display option only; `--execute` remains unconditionally refused. No Terraform resource or application behavior was changed.

Validation is limited to Python syntax, offline render/refusal checks, policy/status consistency and Git whitespace review. No Azure authentication, cloud operation, paid subscription action, credit use, database access or Docker operation is performed. Account-wide spending is not audited or claimed. Application and Terraform runtime results remain historical; they are not reclassified as new passes.

These policy changes remain local and uncommitted unless the user explicitly authorizes another commit. Existing commits and history are preserved.


## Presentation planning update — 16 November 2026

The provisional final delivery plan targets **26 November 2026** and covers all eight sessions without claiming unverified requirements are complete. It includes a local demonstration checklist, evidence labels and separate pending-work sections for Sessions 6, 7 and 8. Only planning documentation is changed in this pass. Existing Session 1–5 records and the earlier uncommitted renderer/policy work are preserved.

Current-pass validation checks documentation links, confirmed topics/date, evidence counts, policy consistency, whitespace and preservation of pre-existing work. No application tests, container/database operations, Azure calls or AI API calls are executed. Recorded runtime results remain historical evidence, not fresh presentation rehearsals. No commit, push or new Session 6–8 feature is authorized.

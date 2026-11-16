# Session 5 safe Azure preparation validation

## Current status and zero-spending restriction

**Azure deployment: Prepared, not deployed. Authorized Azure spending: EUR 0.**

The user's subsequent zero-cost requirement supersedes the earlier hypothetical cost/deployment proposal below. No Azure resource was created or deployed by this work. Azure billing/account state was not inspected; no assertion about unrelated account spending is made. The retained EUR 46.29–70.51 model describes a paid reference design, not authorized spending or a verified zero-cost solution. No subscription activation/upgrade or promotional-credit use is authorized. Current work is restricted to local preparation and validation. See [training alignment](../arquitetura/10_zero_cost_training.md).

## Baseline and authorization

Verified clean branch `main` at Session 4 commit `84a058a8f0d2d40732576523084493c4ee103ca8`; the existing local tracking reference reported four commits ahead. No fetch or push was performed. The user confirmed the Session 5 file handoff and that no other SmartDesk specialist was active. Only the configured Azure specialist was started for this session; it did not launch other agents. The coordinator owned README, pricing and this validation record while the specialist owned separate infrastructure/architecture/runbook files.

Authorized work is local preparation only. Azure authentication, account/tenant/subscription inspection, provider registration, cloud plan/what-if, resource creation, cost-incurring operations, image publication, public exposure and deployment are not authorized. No Docker command was run in Session 5. The shared Docker environment and all unrelated/company resources remained untouched.

## Instructor evidence and deployment proposal

The public [instructor repository](https://github.com/smartlearningci/smartdesk) README was reviewed anonymously. It describes the existing application, PostgreSQL and local Docker workflow; it does not establish exact Session 5 requirements. Full Session 5 notebooks/materials, prescribed Azure service, AKS requirement, subscription/region, naming, screenshots, public endpoint and assessment criteria remain unconfirmed. No missing acceptance criterion was invented.

The proposed architecture is documented in [Session 5 architecture](../arquitetura/07_session_5_azure.md), with [approval/deployment/verification/rollback procedures](../arquitetura/08_session_5_runbook.md). Container Apps Consumption, ACR Basic, PostgreSQL Flexible Server and supporting identity/secrets/network/logging services form a private training proposal. AKS is not provisioned; whether the instructor mandates it remains a question for the instructor, not an inferred decision. West Europe is proposed pending approval.

## Local tool and configuration checks

A sanitized executable lookup returned `az=None`, `bicep=None`, and Terraform at `/opt/homebrew/bin/terraform`. Azure CLI was not installed or invoked. Existing application, Dockerfile, PostgreSQL and security configuration were read for compatibility; no application files, Docker configuration, approved persisted values, product requirements or existing tests were changed.

The Azure specialist used installed Terraform 1.16.1 and pinned the public HashiCorp AzureRM provider 5.14.0. Provider schema validation is local and cannot establish Azure service availability, identity permissions, quota, network connectivity or deployment success. No Terraform plan/apply or cloud validation was run.

## Public pricing and offline verification

The coordinator queried only Microsoft's anonymous public Retail Prices API with EUR and `api-version=2023-01-01-preview`. It retained the public responses under ignored `reports/session5-pricing-20261116-networked/`. Preview precision was necessary because the default API rounded small Container Apps rates to zero. Managed networking costs omitted during early discovery were added before the final model; earlier lower estimates are superseded.

The [cost record](../arquitetura/09_session_5_costs.md) models 730 hours, PostgreSQL B1ms/32 GiB, ACR Basic, one private Container Apps environment with managed LB/outbound IP, two DNS zones, small request/query/secret/log volumes and no free grants. Current modelled totals are EUR 46.29/month for 40 active app hours with scale-to-zero and EUR 70.51/month for 730 active app hours, before VAT and stated exclusions. This is not a hard spending cap or account-specific quote.

Actual pricing checks passed:

- Public price retrieval with explicit meter/SKU/tier/unit/currency selection.
- Entirely offline CLI recomputation from the saved snapshot, retained at `reports/session5-pricing-20261116-offline-final/`.
- Python AST syntax check; Decimal arithmetic for active compute (EUR 1.404 for 40 hours; EUR 25.623 for 730 hours) and rounded model total (EUR 70.51).
- Four negative cases: missing, duplicate, USD-instead-of-EUR and zero-rate paid meters were rejected.
- Existing output directory refusal returned exit 2 and preserved every evidence-file hash.

Exact public/offline pricing commands:

```bash
env -i PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 \
  /opt/homebrew/bin/python3.12 scripts/azure/pricing.py --fetch-public-prices \
  --region westeurope --output-dir reports/session5-pricing-20261116-networked

env -i PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 \
  /opt/homebrew/bin/python3.12 scripts/azure/pricing.py \
  --snapshot reports/session5-pricing-20261116-networked/snapshot.json \
  --output-dir reports/session5-pricing-20261116-offline-final
```

Choose new output directories when repeating these commands. Public price fetching is not Azure account access.

## Runtime limits and remaining validation

Session 4's 116 passed/21 skipped/one warning and 91% source statement coverage are historical results, not new Session 5 tests. Eighteen PostgreSQL cases skipped in Session 4; its strict PostgreSQL gate correctly failed. A real Jenkins build, Linux image installation/build/non-root runtime, PostgreSQL integration, k3s deployment, Edge compatibility and deployment-level security remain unverified. The shared Docker environment cannot be used to close those gaps.

Before publishing SmartDesk, separately approve a dedicated personal validation environment, verify the target Linux image architecture/non-root identity, produce and scan a tested immutable image, complete mandatory PostgreSQL/Jenkins checks, verify proxy and rate-limit behavior, verify database hostname/certificate validation, test least-privilege bootstrap, validate Key Vault references/managed identity, and check the actual private network and HTTPS endpoint. The existing `/login` probe proves responsiveness after startup, not ongoing database readiness. Database migrations, recovery objectives and any production/HA requirements need explicit decisions.

The internal environment cannot be switched into a public environment in place. A later public publication requires a separately reviewed ingress/migration design, TLS/domain controls, security validation and explicit authorization. Resource cleanup remains a reviewed future procedure; no database, backup, volume or resource deletion is authorized.

## Final template review and commit

The specialist returned ownership and its thread completed before the coordinator's final review. Prepared infrastructure files are `versions.tf`, `variables.tf`, `foundation.tf`, `application.tf`, `outputs.tf`, the signed provider dependency lock, placeholder variable/deployment/backend examples, nested ignore rules, and unexecuted database bootstrap SQL. The application is disabled by default; enabling it requires an immutable image digest and two existing versioned secrets.

The coordinator's review required an explicit protected `azurerm` backend declaration, added private JSON-variable/backend ignore rules, directed rendered plan/configuration paths into ignored workspace reports, and made the SQL proposal transactional with a current-database guard. The SQL still requires independently verified server/host identity and separate write approval. No bootstrap SQL was executed or database syntax/runtime acceptance claimed.

| Check | Actual result |
| --- | --- |
| Azure CLI/Bicep discovery | Absent; no installation or authentication attempted |
| Public provider initialization, backend disabled | Passed; AzureRM 5.14.0 downloaded and signed-provider checks completed |
| Initial template provider validation | 11 schema errors; corrected against pinned provider schema |
| Specialist final Terraform formatting/schema | Passed; 0 errors, 0 warnings |
| Coordinator final formatting/schema after backend review | Passed; `valid=true`, 0 errors, 0 warnings |
| Offline renderer syntax/output/refusal checks | Passed; no authentication/resource/deployment flags, cleanup commands empty, execution refused with exit 2 |
| Pricing fetch/offline arithmetic and negative checks | Passed as recorded above |
| Bootstrap SQL | Static review only; never executed |
| Application tests/image/DB/cloud validation | Not run in Session 5; limitations recorded above |

The coordinator's renderer checks parsed both Python helpers, verified all five individual phase outputs plus all-phase output, rejected missing configuration, exercised the CLI render path, and verified `--execute`/missing-file refusal. This is preparation-tool evidence; no displayed Terraform/Azure command was executed.

Exact Terraform environment and commands used local provider data and a new isolated CLI configuration, without ARM/Azure credentials:

```bash
env -i PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin \
  TF_DATA_DIR=/Users/filipematos/Documents/SmartDesk/reports/session5-terraform-613fceac2f65/data \
  TF_CLI_CONFIG_FILE=/Users/filipematos/Documents/SmartDesk/reports/session5-terraform-613fceac2f65/terraform.rc \
  CHECKPOINT_DISABLE=1 TF_INPUT=0 TF_IN_AUTOMATION=1 \
  /opt/homebrew/bin/terraform -chdir=infra/azure init -backend=false -input=false -lockfile=readonly

env -i PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin \
  TF_DATA_DIR=/Users/filipematos/Documents/SmartDesk/reports/session5-terraform-613fceac2f65/data \
  TF_CLI_CONFIG_FILE=/Users/filipematos/Documents/SmartDesk/reports/session5-terraform-613fceac2f65/terraform.rc \
  CHECKPOINT_DISABLE=1 TF_INPUT=0 TF_IN_AUTOMATION=1 \
  /opt/homebrew/bin/terraform -chdir=infra/azure fmt -check -recursive

env -i PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin \
  TF_DATA_DIR=/Users/filipematos/Documents/SmartDesk/reports/session5-terraform-613fceac2f65/data \
  TF_CLI_CONFIG_FILE=/Users/filipematos/Documents/SmartDesk/reports/session5-terraform-613fceac2f65/terraform.rc \
  CHECKPOINT_DISABLE=1 TF_INPUT=0 TF_IN_AUTOMATION=1 \
  /opt/homebrew/bin/terraform -chdir=infra/azure validate -json

env -i PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 \
  /opt/homebrew/bin/python3.12 scripts/azure/prepare.py --config infra/azure/deployment.example.json --phase all
```

The coordinator repeated backend-disabled initialization with `-lockfile=readonly` after adding the backend declaration; it reused the pinned local provider successfully without changing the lock.

Provider evidence remains ignored under `reports/session5-terraform-613fceac2f65/`: initialization log, initial/final validation JSON, provider schema and initial rendered output. The coordinator's final validation after review also returned zero errors/warnings. Backend-disabled initialization and provider-schema validation do not read an Azure subscription or prove deployability. Terraform's `prevent_destroy` is a plan safeguard, not a guarantee against manual/cloud deletion.

The final review covered 18 changed/new files. A pattern-based scan found no private-key block, recognized GitHub/AWS token pattern or literal credential-bearing HTTP/PostgreSQL URL. Manual review found placeholders and future environment-injected values, not committed credentials. The two application roles are exactly `AcrPull` on the new registry and `Key Vault Secrets User` on the dedicated vault; no application Owner/Contributor or subscription-wide assignment is present. Private reports, Terraform state, backend configuration and private variable JSON passed ignore checks. No generated provider data, pricing evidence, state, credentials or plan files are included in the commit candidate. This is a scoped review, not a comprehensive security certification. Git whitespace checks passed before the explicitly authorized local commit. No deployment success is claimed.

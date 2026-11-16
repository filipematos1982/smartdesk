# Session 5 — deployment, verification and recovery preparation

## Mandatory zero-Azure-spending policy

**Deployment status: Prepared, not deployed. Authorized Azure spending: EUR 0.**

The user's zero-cost requirement supersedes any earlier proposed deployment budget or approval sequence. This educational project permits infrastructure-as-code, documentation, offline command rendering and local validation only. Do not provision cloud infrastructure, deploy, activate/upgrade paid subscriptions, or consume promotional credits. A free-tier label, scale-to-zero, budget alert or unspent credit does not establish guaranteed zero charges. No company tenant, subscription or credential may be accessed.

The preserved ACA/ACR/PostgreSQL architecture is a paid reference design and is incompatible with the current spending policy. Earlier cost estimates and deployment procedures are educational comparisons, not an approved plan or authorization. If the instructor requires an actual deployment, first establish a genuinely zero-cost option and all eligibility/usage limits from current official evidence, then obtain explicit user approval for that exact option. No such option or deployment is currently verified or approved. No cloud action is authorized by a general review of these documents.

Prefer local PostgreSQL, Docker and Kubernetes demonstrations in a separately approved dedicated personal environment. The current shared Docker environment remains off limits; this policy does not authorize any container or network operation. See [zero-cost training alignment](10_zero_cost_training.md) for the evidence and eight-session status.

## Current stop point

Everything here is a future procedure for review. This session stops before Azure authentication, account/tenant/subscription inspection, resource creation, image publication, cloud validation and deployment. The shared Docker environment must not be used. No preparation script executes Azure, Terraform deployment, database or Docker commands.

Render the proposed commands locally:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m scripts.azure.prepare --config infra/azure/deployment.example.json --phase all
```

The default JSON output is marked **Prepared, not deployed**, records the EUR 0 spending limit, and withholds cloud command instructions. `--include-reference-commands` displays preserved educational instructions only; it never authorizes or executes them. The paid design cannot be used under the current policy. The JSON contains placeholders. `--execute` is always refused. Rendering does not indicate that prerequisites passed, that a deployment is authorized or that a resource exists. Do not paste the output into a shell without completing the relevant approval stage. Cleanup has no executable deletion commands.

## Preserved reference approval sequence — not authorized under the EUR 0 policy

1. Obtain the missing Session 5 instructions and settle whether AKS is compulsory. Approve ACA versus alternatives, region, personal tenant/subscription, resource names and scope, private access design, budget and expected charges. No company resources or credentials may be used.
2. Authorize a separate personal Azure authentication step and read-only verification of the exact tenant/subscription. Use a fresh dedicated Azure CLI configuration and an approved personal identity. Do not reuse ambient accounts or credential stores. Azure CLI installation must also be separately planned because it is absent locally. Authentication alone does not authorize creation or provider registration.
3. Approve the required provider registrations, deployment identity and least-privilege scopes. Prepare an encrypted, access-controlled Terraform backend with locking and recovery before storing state. The draft declares an `azurerm` backend and supplies `backend.example.hcl` placeholders only; local validation bypasses backend initialization. Store future private configuration and plans under ignored, mode-0700 workspace reports, never in tracked examples. Rendered relative report paths account for Terraform `-chdir=infra/azure`. The current provider intentionally disables CLI/MSI authentication and automatic registration; select an explicit reviewed personal authentication mechanism in a follow-up change. Federation for a dedicated CI identity is preferable to embedding a long-lived secret. The deployer requires resource creation rights in the approved scope plus narrowly scoped role-assignment privileges; the app receives only registry pull and dedicated-vault secret read.
4. Approve cloud-side validation, quota/SKU checks and a reviewed Terraform foundation plan with exact costs and a no-public-app exposure review. Creation requires new explicit authorization that changes the project's no-cloud-creation restriction. A `plan` is cloud access and is not part of the current offline validation.
5. Approve an isolated build environment and image validation, including Linux amd64, UID 10001, startup, package/image contents and successful mandatory PostgreSQL/security tests. Approve registry authentication/publication separately; verify the published digest and retain source/build provenance. Do not infer ACR or Docker Hub namespace ownership from the GitHub username.
6. Approve foundation creation and review actual resources/IDs, internal environment IP, private DNS, database network isolation, RBAC scopes, disabled registry admin credentials, backups and costs. Confirm ACR permits ARM-audience tokens for managed-identity pulls. Allow for role propagation before application rollout.
7. Approve a temporary private-network administration path, fresh DB administrator input, execution of the reviewed bootstrap SQL only in the newly verified `smartdesk` database, and secure seeding of the two versioned Key Vault secrets. Verify that the app role has no server/database creation or superuser capability. Initialize synthetic app accounts interactively using an approved private procedure; demo seeding stays disabled. Preserve all existing databases and data.
8. Approve the application plan with `deploy_application=true`, the verified image digest and exact existing secret versions. The plan must keep the private environment and HTTPS-only ingress. Confirm private DNS/client access, database TLS trust bundle, proxy/client-IP handling, probe limitations and budget/monitoring configuration before application creation.
9. Approve post-deployment verification using the exact new resources and synthetic data. Public exposure is a separate architecture/security decision and explicit publication approval. The internal environment cannot become public in place; approve migration or edge resources and their costs before making that change.

The account, region, amounts, resource IDs and actions in each approval should be concrete and reviewable. A prior local-preparation approval is not a deployment approval. No push to GitHub is included.

## Proposed identities and permissions to approve

No identity, role assignment or provider registration was inspected or created. The draft's application identity gets only `AcrPull` on the new registry and `Key Vault Secrets User` on the dedicated vault. Approve operator identities separately; do not grant the application broad deployment permissions.

| Future operator | Proposed minimum scope to review |
| --- | --- |
| Resource-group bootstrap | Permission to create the exact new personal resource group; because the template creates a group, resource-group-only Contributor is insufficient for this first step. Approve a separately scoped bootstrap identity or separately created/imported personal group. Do not infer a need for subscription Owner. |
| Infrastructure deployer | Resource creation rights on the approved dedicated group, plus narrowly delegated role-assignment rights for the two reviewed app roles/principal. Review custom-role/assignment conditions before granting. |
| Terraform backend client | Data access such as Storage Blob Data Contributor on the dedicated state container, with approved identity, encryption, locking and recovery; state-account creation is a separate bootstrap approval. |
| Image publisher | Push rights only to the approved personal registry/repository; no registry admin password or subscription-wide Contributor for image publishing. |
| Secret initializer | Secret-writing rights only on the dedicated vault, separate from the app's read role; no credentials in command arguments or logs. |
| Database bootstrap operator | Fresh administrator credentials only for the newly verified private server and the reviewed bootstrap transaction; app runtime gets the nonadministrator role. |

The proposed resources require registration/availability review for `Microsoft.Resources`, `Microsoft.Network`, `Microsoft.ManagedIdentity`, `Microsoft.App`, `Microsoft.ContainerRegistry`, `Microsoft.DBforPostgreSQL`, `Microsoft.KeyVault` and `Microsoft.OperationalInsights`. A separately prepared storage backend also needs `Microsoft.Storage`. The provider disables automatic registration; this list is a preparation requirement, not evidence that any provider is registered. Review actual deployment operations and scoped permissions before approving a plan.

## Post-deployment verification checklist

Run only after authorization, from the approved private-network client and against recorded personal IDs:

- Confirm provisioning/revision health, actual image digest and Linux architecture; confirm runtime UID and writable temporary/report directories without granting interactive administration broadly.
- Resolve the app FQDN privately to the expected internal IP; prove HTTPS certificate validation, HTTP-to-HTTPS behavior, secure cookie flags and absence of an internet-reachable app endpoint. No insecure TLS or temporary public database firewall exception is an acceptable workaround.
- Confirm the app uses the designated managed identity, only `AcrPull` on its registry and secret-read on its dedicated vault, and no administrative DB credential. Read secret metadata rather than values into logs.
- Verify `pg_stat_ssl` for the active app connection and client `verify-full` with the expected FQDN and CA trust. Verify that a deliberately wrong hostname/untrusted certificate fails in a safe isolated check. Record the precise trust-bundle version and server TLS settings.
- Exercise synthetic employee login, missing/invalid CSRF rejection, ticket creation, visibility isolation, technician assignment/start/resolve, employee reopening and manager-only closure. Record denied writes without mutation. Do not run the destructive test suite against the deployed application database; use a separately verified disposable database for automated integration.
- Restart only the newly approved app revision and confirm a committed synthetic ticket persists. Exercise a controlled backup/restore into a new target; preserve source data and record counts, RPO/RTO and actual restoration duration.
- Verify console/system log collection without passwords, session cookies, CSRF tokens or personal ticket content. Decide operational thresholds before measuring; proposed alerts cover revision unavailability, HTTP errors/latency, database CPU/storage/connections and backup failures. Configure a user-approved budget and alert recipient; a workspace ingestion cap or budget alert is not a hard billing ceiling. Capture a test alert only after authorization.
- Confirm cold-start and warm response times, chosen replica limits and private browser behavior. Session 4 Chrome/SQLite evidence and 91% statement coverage do not establish Azure/PostgreSQL, real Edge, public performance or recovery acceptance.

Do not claim deployment success from an HTTP 200 alone, a rendered template, a successful schema check or a configured health probe.

## Rollback proposal

Record the previous source commit, immutable image digest, secret versions, configuration and healthy revision before changing the app. With single-revision mode, prepare a reviewed Terraform update to the previous digest while keeping compatible secret versions and the same signing key. Approve the rollback plan, then apply it and repeat private health and synthetic lifecycle checks. Readiness shifts traffic automatically only after the new revision reports ready; this does not prove database health or schema compatibility.

Existing initialization creates tables but is not a versioned migration system. Do not assume an older application can use a newer schema. Database restoration is a separate recovery operation into a new server, with reconciliation and connection cutover explicitly approved. Never delete or overwrite the original database to roll back. If a signing key must be rotated for security, document that existing sessions become invalid; do not rotate it incidentally during image rollback.

## Cleanup proposal

Inventory only the newly approved personal resource IDs/tags and review dependencies and current data ownership. Stop further application traffic through an approved app change; identify database backups, exports, retention obligations, registry digests and Terraform state that must remain. Estimate residual storage, logs and registry costs. Obtain separate explicit approval for each destructive action and exact retained data. The project's present prohibition on destructive operations must be changed before any deletion, including a resource-group deletion or Terraform destroy.

`prevent_destroy` remains in the draft. No deletion script, destroy command, vault purge, volume removal, Docker pruning or broad resource-group cleanup is prepared for execution. Do not remove retention safeguards merely to complete an exercise. Keep recovery evidence and revoke only the exact personal permissions approved for revocation; never inspect or affect shared/company resources.

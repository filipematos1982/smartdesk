# Session 5 Azure cost estimate — EUR

## Proposal and source

Region proposal: **West Europe (`westeurope`)**, subject to explicit approval, service/SKU availability, subscription quota and data-residency review. This region is a planning assumption, not an instructor requirement or an inspected Azure account setting. No Azure subscription or account was queried.

Microsoft's anonymous [Retail Prices API](https://learn.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices) was queried on **16 November 2026**, with `api-version=2023-01-01-preview`, `currencyCode='EUR'`, and Consumption/pay-as-you-go meters. The preview version preserves small compute-rate precision; the default version returned rounded zero values for some Container Apps rates and was not used for the final estimate. Non-USD API prices are budget references, not a binding EUR offer. No currency conversion from an invented exchange rate was performed.

The reproducible helper is [pricing.py](../../scripts/azure/pricing.py). It validates each meter's identity, SKU, tier, region, currency and unit and refuses missing, ambiguous or nonpositive paid rates. It follows only HTTPS pricing pagination on Microsoft's public pricing host, disables ambient proxy settings, and never invokes Azure CLI, Docker or an Azure SDK. Saved public responses and the computed estimate remain ignored at `reports/session5-pricing-20261116-networked/`.

## Model assumptions

- 730 hours per model month; daily meters use 730/24 days.
- One Container App, Consumption profile, 0.25 vCPU/0.5 GiB, minimum zero/maximum one replica. A busy example uses 40 active hours and 690 hours at zero replicas; a conservative example uses 730 active hours. Cold starts and revision overlaps can add usage. These workloads are assumptions, not observed Azure measurements.
- One PostgreSQL Flexible Server 16, burstable B1ms, 32 GiB provisioned storage, seven-day local backup retention, no high availability, no geo-redundant backup. Storage is multiplied by 32 against Microsoft's published `1 GB/Month` meter. Actual provisioned storage and included backup allowance must be checked before deployment.
- ACR Basic within its included 10 GB storage, one internal Container Apps environment, two Private DNS zones, 100,000 DNS queries/month, 100,000 app requests/month, 10,000 Key Vault operations and 1 GB Log Analytics ingestion/month. Thirty-day log retention is proposed. Workspace daily quota 0.1 GB is a diagnostic control, not a guaranteed spending cap.
- No free grants, introductory credits, reservations, savings plans or negotiated discounts are assumed. They may reduce the bill if the personal subscription is eligible and grants remain available; subscription eligibility was not inspected.
- The internal environment requires one managed Standard load balancer and one Standard static outbound public IP. The outbound IP provides egress; it does not expose the app publicly. Microsoft's [virtual-network documentation](https://learn.microsoft.com/en-us/azure/container-apps/custom-virtual-networks) explicitly lists these additional charges. The model assumes the included first five LB rules and 1 GB processed data; actual platform-managed rule/data usage remains unverified.

## Current rates and modelled monthly amounts

| Component | Official EUR rate | Modelled monthly EUR |
| --- | --- | ---: |
| PostgreSQL B1ms compute | 0.017864/hour | 13.04 |
| PostgreSQL provisioned storage | 0.122896/GB-month × 32 | 3.93 |
| ACR Basic | 0.149558/day | 4.55 |
| Managed Standard load balancer, first five rules | 0.022443/hour | 16.38 |
| Managed Standard outbound IPv4 | 0.004489/hour | 3.28 |
| Managed load-balancer data, 1 GB | 0.004489/GB | 0.0045 |
| Private DNS, two zones | 0.448853/zone-month | 0.90 |
| Private DNS, 100,000 queries | 0.359083/million | 0.036 |
| Log Analytics, 1 GB at paid marginal rate | 2.684142/GB | 2.68 |
| Key Vault Standard, 10,000 operations | 0.026931/10,000 | 0.027 |
| Container Apps, 100,000 requests | 0.502716/million | 0.050 |
| **Subtotal before app compute** | | **44.88** |
| App compute, 40 active hours/690 at zero | CPU 0.000031/vCPU-second + memory 0.000004/GiB-second | **1.40** |
| App compute, 730 active hours | Same rates | **25.62** |

The modelled totals are **EUR 46.29/month** for the small scale-to-zero example and **EUR 70.51/month** for continuous active compute, **before VAT and exclusions below**. If minimum replicas were changed to one, 40 active hours plus 690 idle hours would model **EUR 53.74/month**; idle rates are 0.000004/vCPU-second and 0.000004/GiB-second. This is an alternative, not the template default.

Rate provenance is captured in the helper's `selected_meters` output, including meter IDs and effective dates. API effective dates identify when a meter rate took effect; retrieval on 16 November establishes the observation date. DNS and LB use global/zone meters where the API does not publish a West Europe regional meter. The [DNS price definition](https://azure.microsoft.com/en-us/pricing/details/dns/) establishes zone/query billing, [ACR pricing](https://azure.microsoft.com/en-us/pricing/details/container-registry/) defines included storage, and [Monitor pricing](https://azure.microsoft.com/en-us/pricing/details/monitor/) distinguishes log and alert charges.

## Exclusions and approval implications

VAT, internet/cross-region egress, additional LB rules or outbound IPs, extra processed traffic, backups beyond included allowance, HA, geo-replication, extra registry storage/build tasks, state-backend storage, alert rules/notifications, private administrative access (VPN/Bastion/jump host), custom domains/certificates, and a future public-ingress gateway/WAF are not included. Private access for database bootstrap and verification remains an outstanding design/approval dependency; it is not silently priced as free.

No Container Apps private endpoint, planned maintenance feature, Dedicated compute profile, NAT Gateway or AKS is provisioned by the proposal. Enabling a private endpoint/qualifying environment feature would add a currently observed environment-feature meter of 0.089771/hour, or **EUR 65.53/month**, plus the relevant Private Link/network charges. It is excluded from the default. [Container Apps billing](https://learn.microsoft.com/en-us/azure/container-apps/billing) explains feature management charges and the monthly Consumption grants (180,000 vCPU-seconds, 360,000 GiB-seconds and two million requests). Availability of those grants must not be assumed for a shared subscription.

Earlier discovery estimates omitted managed networking and are superseded by the `networked` snapshot. No final estimate should use those lower subtotals. Expected spending must be rechecked against the exact approved subscription offer and a current Azure calculator before resource authorization. A budget alert is a notification, not an automatic hard spending limit. No costs were incurred to prepare this model.

## Reproduction

Both commands require a new output directory; existing evidence is preserved. The first accesses only public retail pricing; the second is entirely offline:

```bash
env -i PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 \
  /opt/homebrew/bin/python3.12 scripts/azure/pricing.py --fetch-public-prices \
  --region westeurope --output-dir reports/session5-pricing-NEW-UNIQUE-ID

env -i PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 \
  /opt/homebrew/bin/python3.12 scripts/azure/pricing.py \
  --snapshot reports/session5-pricing-20261116-networked/snapshot.json \
  --output-dir reports/session5-pricing-NEW-RECOMPUTATION-ID
```

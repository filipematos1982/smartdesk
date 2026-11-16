"""Fetch public Azure EUR retail meters or recompute a saved local estimate.

No Azure CLI, SDK, identity, account, subscription or credentials are used.
The estimate excludes taxes and unmodelled infrastructure; it is not a quote.
"""
import argparse
from datetime import datetime, timezone
from decimal import Decimal
import json
from pathlib import Path
import re
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
API = "https://prices.azure.com/api/retail/prices"
# Explicit meter, SKU, tier, region and unit selection avoids free-tier/legacy confusion.
SPECS = {
    "aca_cpu_active": ("Azure Container Apps", "0426badc-b719-5201-b141-b2d5c4943b7d", "Standard", 0, None, "1 Second"),
    "aca_memory_active": ("Azure Container Apps", "3ba64b1c-cb46-5ee0-b086-a68736392ac0", "Standard", 0, None, "1 GiB Second"),
    "aca_cpu_idle": ("Azure Container Apps", "7b7747f8-2c0b-5b6b-a6d9-d998e92f6bcc", "Standard", 0, None, "1 Second"),
    "aca_memory_idle": ("Azure Container Apps", "cea8b5c0-c6fe-59cf-baa7-123dbc4c6bb8", "Standard", 0, None, "1 GiB Second"),
    "aca_requests": ("Azure Container Apps", "b110d175-46b6-5bbc-adde-cf3438ed87f0", "Standard", 0, None, "1M"),
    "acr_basic": ("Container Registry", "5c9e7a65-5784-494c-9718-7749d4075dd9", "Basic", 0, None, "1/Day"),
    "postgres_compute": ("Azure Database for PostgreSQL", "5e31969e-0b91-5186-81a1-7475fabe1262", "B1MS", 0, None, "1 Hour"),
    "postgres_storage": ("Azure Database for PostgreSQL", "36845e2a-736f-5a9d-af4e-b2dc7547a06f", "Storage", 0, None, "1 GB/Month"),
    "logs_ingestion": ("Log Analytics", "e5626349-2f1f-4563-babc-dc9219884716", "Analytics Logs", 5, None, "1 GB"),
    "vault_operations": ("Key Vault", "0f824807-2376-435c-95c9-f992b67a07b0", "Standard", 0, None, "10K"),
    "dns_zone": ("Azure DNS", "0b608a26-f611-4232-8192-ce81b6b57194", "Private", 0, "", "1"),
    "dns_queries": ("Azure DNS", "46cff9cb-4b15-4af0-bf41-25143827fef8", "Private", 0, "Zone 1", "1M"),
    "managed_egress_ip": ("Virtual Network", "9c150bf9-2bad-430e-a53c-c213804f49ef", "Standard", 0, None, "1 Hour"),
    "managed_load_balancer": ("Load Balancer", "27827eb0-7f60-4928-940b-f5fe15e7a4cb", "Standard", 0, "Global", "1 Hour"),
    "managed_lb_data": ("Load Balancer", "dfc7cc11-fbe2-41c8-b6fa-24a574223938", "Standard", 0, "Global", "1 GB"),
    "optional_aca_feature": ("Azure Container Apps", "3d952ec1-3455-54fe-86ed-0ae4a5864088", "Environment", 0, None, "1 Hour"),
}


def fetch(region):
    rows, queries = [], []
    # Disable ambient proxy configuration; all requests are anonymous public HTTPS.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    for service in sorted({spec[0] for spec in SPECS.values()}):
        condition = "serviceName eq '" + service + "' and priceType eq 'Consumption'"
        if service not in {"Azure DNS", "Load Balancer"}:
            condition += " and armRegionName eq '" + region + "'"
        url = API + "?" + urllib.parse.urlencode({"api-version": "2023-01-01-preview",
                                                  "currencyCode": "'EUR'", "$filter": condition})
        queries.append(url)
        seen = set()
        while url:
            parsed = urllib.parse.urlsplit(url)
            if parsed.scheme != "https" or parsed.hostname != "prices.azure.com" or url in seen or len(seen) >= 50:
                raise ValueError("Unexpected pricing pagination target or loop")
            seen.add(url)
            with opener.open(url, timeout=30) as response:
                page = json.load(response)
            rows.extend(page["Items"])
            url = page.get("NextPageLink")
    return {"retrieved_at_utc": datetime.now(timezone.utc).isoformat(), "region": region,
            "currency": "EUR", "api_version": "2023-01-01-preview", "queries": queries, "items": rows}


def estimate(snapshot):
    region = snapshot["region"]
    selected = {}
    for name, (service, meter, sku, tier, meter_region, unit) in SPECS.items():
        matches = [row for row in snapshot["items"] if row.get("serviceName") == service
                   and row.get("meterId") == meter and row.get("skuName") == sku
                   and row.get("tierMinimumUnits") == tier
                   and row.get("armRegionName") == (region if meter_region is None else meter_region)
                   and row.get("type") == "Consumption" and row.get("currencyCode") == "EUR"
                   and row.get("unitOfMeasure") == unit]
        if len(matches) != 1 or Decimal(str(matches[0]["retailPrice"])) <= 0:
            raise ValueError("Missing, ambiguous or nonpositive paid meter: " + name)
        selected[name] = {key: matches[0][key] for key in
                          ("meterId", "meterName", "skuName", "armRegionName", "unitOfMeasure",
                           "retailPrice", "tierMinimumUnits", "effectiveStartDate")}
    rate = {name: Decimal(str(row["retailPrice"])) for name, row in selected.items()}
    hours, cpu, memory = Decimal(730), Decimal("0.25"), Decimal("0.5")
    fixed = {"managed_egress_ip": hours * rate["managed_egress_ip"],
             "managed_load_balancer": hours * rate["managed_load_balancer"],
             "managed_lb_1gb_data": rate["managed_lb_data"],
             "postgres_compute": hours * rate["postgres_compute"],
             "postgres_storage_32": 32 * rate["postgres_storage"],
             "acr_basic": hours / 24 * rate["acr_basic"],
             "two_private_dns_zones": 2 * rate["dns_zone"],
             "dns_100k_queries": Decimal("0.1") * rate["dns_queries"],
             "logs_1gb_no_grant": rate["logs_ingestion"],
             "vault_10k_operations": rate["vault_operations"],
             "aca_100k_requests_no_grant": Decimal("0.1") * rate["aca_requests"]}
    def app(active, idle):
        return 3600 * (Decimal(active) * (cpu * rate["aca_cpu_active"] + memory * rate["aca_memory_active"])
                       + Decimal(idle) * (cpu * rate["aca_cpu_idle"] + memory * rate["aca_memory_idle"]))
    scenarios = {"40h_active_690h_idle_min1_alternative": app(40, 690), "730h_active": app(730, 0),
                 "40h_active_690h_zero_replicas": app(40, 0)}
    base = sum(fixed.values())
    return {"region": region, "currency": "EUR", "hours": 730, "cpu": str(cpu), "memory_gib": str(memory),
            "selected_meters": selected, "fixed_components_eur": {k: str(v) for k, v in fixed.items()},
            "fixed_subtotal_eur": str(base),
            "scenarios": {name: {"app_compute_eur": str(value), "modelled_total_eur": str(base + value)}
                          for name, value in scenarios.items()},
            "optional_aca_private_endpoint_feature_730h_eur": str(hours * rate["optional_aca_feature"]),
            "limitations": "No grants assumed; excludes VAT, egress, extra backup/storage, alerts, private access, state storage, extra load-balancer rules, extra egress IPs and extra network traffic. Not a quote or spending cap."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--fetch-public-prices", action="store_true")
    source.add_argument("--snapshot", type=Path)
    parser.add_argument("--region", default="westeurope")
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    if not re.fullmatch(r"[a-z0-9]+", args.region):
        parser.error("Region must be an Azure region identifier")
    output = (ROOT / args.output_dir).resolve()
    if output.parent != ROOT / "reports" or not output.name.startswith("session5-pricing-"):
        parser.error("Use a new reports/session5-pricing-<unique-id> directory")
    if output.exists():
        parser.error("Output directory already exists; preserve existing evidence")
    snapshot = fetch(args.region) if args.fetch_public_prices else json.loads(args.snapshot.read_text())
    result = estimate(snapshot)
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    (output / "snapshot.json").write_text(json.dumps(snapshot, indent=2) + "\n")
    (output / "estimate.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"evidence": str(output.relative_to(ROOT)), "scenarios": result["scenarios"]}, indent=2))


if __name__ == "__main__":
    main()

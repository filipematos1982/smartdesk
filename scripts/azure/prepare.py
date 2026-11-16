"""Render Azure deployment review steps only; never authenticate or run commands."""
import argparse
import json
from pathlib import Path


def render(config, phase, include_reference_commands=False):
    required = ("subscription_id", "tenant_id", "prefix", "location", "image_digest")
    missing = [name for name in required if not isinstance(config.get(name), str) or not config[name]]
    if missing:
        raise ValueError("Missing preparation fields: " + ", ".join(missing))
    group = config["prefix"] + "-rg"
    commands = {
        "foundation": [
            ["terraform", "-chdir=infra/azure", "init", "-backend-config=../../reports/APPROVED_PRIVATE_BACKEND.hcl", "-lockfile=readonly"],
            ["terraform", "-chdir=infra/azure", "plan", "-var-file=../../reports/APPROVED_PRIVATE_VARIABLES.tfvars", "-out=../../reports/PRIVATE_REVIEWED_FOUNDATION.tfplan"],
            ["terraform", "-chdir=infra/azure", "apply", "../../reports/PRIVATE_REVIEWED_FOUNDATION.tfplan"],
        ],
        "application": [
            ["terraform", "-chdir=infra/azure", "plan", "-var-file=../../reports/APPROVED_PRIVATE_VARIABLES.tfvars", "-var=deploy_application=true", "-var=image_digest=" + config["image_digest"], "-out=../../reports/PRIVATE_REVIEWED_APPLICATION.tfplan"],
            ["terraform", "-chdir=infra/azure", "apply", "../../reports/PRIVATE_REVIEWED_APPLICATION.tfplan"],
        ],
        "verification": [
            ["az", "containerapp", "show", "--subscription", config["subscription_id"], "--resource-group", group, "--name", config["prefix"] + "-web", "--query", "{state:properties.provisioningState,fqdn:properties.configuration.ingress.fqdn}"],
            ["az", "containerapp", "revision", "list", "--subscription", config["subscription_id"], "--resource-group", group, "--name", config["prefix"] + "-web", "--query", "[].{name:name,active:properties.active,health:properties.healthState}"],
            ["curl", "--fail", "--proto", "=https", "https://CONFIRMED_PRIVATE_APP_FQDN/login"],
        ],
        "rollback": [
            ["terraform", "-chdir=infra/azure", "plan", "-var-file=../../reports/APPROVED_PRIVATE_VARIABLES.tfvars", "-var=deploy_application=true", "-var=image_digest=PREVIOUS_VERIFIED_SHA256_DIGEST", "-out=../../reports/PRIVATE_REVIEWED_ROLLBACK.tfplan"],
            ["terraform", "-chdir=infra/azure", "apply", "../../reports/PRIVATE_REVIEWED_ROLLBACK.tfplan"],
        ],
        "cleanup": [],
    }
    reference = commands if phase == "all" else {phase: commands[phase]}
    selected = reference if include_reference_commands else {name: [] for name in reference}
    return {
        "mode": "OFFLINE RENDER ONLY: commands have not been executed",
        "deployment_status": "Prepared, not deployed",
        "azure_spending_limit_eur": 0,
        "cloud_provisioning_authorized": False,
        "promotional_credit_use_authorized": False,
        "reference_commands_included": include_reference_commands,
        "rendered_commands_are_authorized": False,
        "authentication_performed": False,
        "resources_created": False,
        "deployment_success": False,
        "region_proposal": config["location"],
        "requires_separate_approval": [
            "Instructor confirmation that an actual Azure deployment is required",
            "Verified genuinely zero-cost option, eligibility, limits and dependencies",
            "Explicit user approval of that exact zero-cost option before any cloud action",
            "Promotional credit consumption is not authorized and cannot be assumed",
        ],
        "rendered_commands": selected,
        "cleanup": "Procedure only: preserve databases, backups, registry and state; no deletion commands are generated.",
        "warning": "The paid reference architecture is incompatible with the EUR 0 policy. Instructions are withheld by default; reference output is documentation only. No plan/apply/what-if, Azure CLI or Docker call is made.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("infra/azure/deployment.example.json"))
    parser.add_argument("--phase", choices=("all", "foundation", "application", "verification", "rollback", "cleanup"), default="all")
    parser.add_argument("--include-reference-commands", action="store_true", help="Display preserved educational instructions only; never authorizes execution or spending")
    parser.add_argument("--execute", action="store_true", help="Always refused; execution is outside this preparation tool")
    args = parser.parse_args()
    if args.execute:
        parser.error("Execution is not implemented or authorized; this tool renders review material only")
    try:
        result = render(json.loads(args.config.read_text()), args.phase, args.include_reference_commands)
    except (OSError, ValueError, TypeError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

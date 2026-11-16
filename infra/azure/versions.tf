terraform {
  # Configure an approved protected remote backend before any future plan/apply.
  # Local validation always initializes with -backend=false.
  backend "azurerm" {}
  required_version = ">= 1.11.0, < 2.0.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "5.14.0"
    }
  }
}

provider "azurerm" {
  features {}
  subscription_id                 = var.subscription_id
  tenant_id                       = var.tenant_id
  use_cli                         = false
  use_msi                         = false
  resource_provider_registrations = "none"
}

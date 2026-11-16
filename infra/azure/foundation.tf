locals {
  tags = { project = "personal-smartdesk", purpose = "training", session = "5" }
}
resource "azurerm_resource_group" "lab" {
  name     = "${var.prefix}-rg"
  location = var.location
  tags     = local.tags
  lifecycle { prevent_destroy = true }
}
resource "azurerm_virtual_network" "lab" {
  name                = "${var.prefix}-vnet"
  location            = azurerm_resource_group.lab.location
  resource_group_name = azurerm_resource_group.lab.name
  address_space       = ["10.72.0.0/16"]
  tags                = local.tags
}
resource "azurerm_subnet" "apps" {
  name                 = "container-apps"
  resource_group_name  = azurerm_resource_group.lab.name
  virtual_network_name = azurerm_virtual_network.lab.name
  address_prefixes     = ["10.72.0.0/23"]
  delegation {
    name = "container-apps"
    service_delegation {
      name    = "Microsoft.App/environments"
      actions = ["Microsoft.Network/virtualNetworks/subnets/join/action"]
    }
  }
}
resource "azurerm_subnet" "database" {
  name                 = "postgresql"
  resource_group_name  = azurerm_resource_group.lab.name
  virtual_network_name = azurerm_virtual_network.lab.name
  address_prefixes     = ["10.72.2.0/27"]
  delegation {
    name = "postgresql"
    service_delegation {
      name    = "Microsoft.DBforPostgreSQL/flexibleServers"
      actions = ["Microsoft.Network/virtualNetworks/subnets/join/action"]
    }
  }
}
resource "azurerm_private_dns_zone" "database" {
  name                = "${var.prefix}.postgres.database.azure.com"
  resource_group_name = azurerm_resource_group.lab.name
}
resource "azurerm_private_dns_zone_virtual_network_link" "database" {
  name                = "postgresql-link"
  private_dns_zone_id = azurerm_private_dns_zone.database.id
  virtual_network_id  = azurerm_virtual_network.lab.id
}
resource "azurerm_postgresql_flexible_server" "database" {
  name                              = "${var.prefix}-pg"
  resource_group_name               = azurerm_resource_group.lab.name
  location                          = azurerm_resource_group.lab.location
  version                           = "16"
  administrator_login               = "smartdesk_admin"
  administrator_password_wo         = var.postgres_admin_password
  administrator_password_wo_version = var.postgres_admin_password_version
  sku_name                          = "B_Standard_B1ms"
  storage_mb                        = 32768
  backup_retention_days             = 7
  geo_redundant_backup_enabled      = false
  public_network_access_enabled     = false
  delegated_subnet_id               = azurerm_subnet.database.id
  private_dns_zone_id               = azurerm_private_dns_zone.database.id
  tags                              = local.tags
  depends_on                        = [azurerm_private_dns_zone_virtual_network_link.database]
  lifecycle { prevent_destroy = true }
}
resource "azurerm_postgresql_flexible_server_database" "smartdesk" {
  name      = "smartdesk"
  server_id = azurerm_postgresql_flexible_server.database.id
  charset   = "UTF8"
  collation = "en_US.utf8"
  lifecycle { prevent_destroy = true }
}
resource "azurerm_postgresql_flexible_server_configuration" "tls" {
  name      = "require_secure_transport"
  server_id = azurerm_postgresql_flexible_server.database.id
  value     = "on"
}
resource "azurerm_container_registry" "images" {
  name                = "${var.prefix}acr"
  resource_group_name = azurerm_resource_group.lab.name
  location            = azurerm_resource_group.lab.location
  sku                 = "Basic"
  admin_enabled       = false
  tags                = local.tags
  lifecycle { prevent_destroy = true }
}
resource "azurerm_user_assigned_identity" "app" {
  name                = "${var.prefix}-app-identity"
  resource_group_name = azurerm_resource_group.lab.name
  location            = azurerm_resource_group.lab.location
  tags                = local.tags
}
resource "azurerm_key_vault" "secrets" {
  name                       = "${var.prefix}-kv"
  location                   = azurerm_resource_group.lab.location
  resource_group_name        = azurerm_resource_group.lab.name
  tenant_id                  = var.tenant_id
  sku_name                   = "standard"
  rbac_authorization_enabled = true
  soft_delete_retention_days = 90
  purge_protection_enabled   = true
  tags                       = local.tags
  lifecycle { prevent_destroy = true }
}
resource "azurerm_role_assignment" "image_pull" {
  scope                = azurerm_container_registry.images.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_user_assigned_identity.app.principal_id
  principal_type       = "ServicePrincipal"
}
resource "azurerm_role_assignment" "secret_read" {
  scope                = azurerm_key_vault.secrets.id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = azurerm_user_assigned_identity.app.principal_id
  principal_type       = "ServicePrincipal"
}
resource "azurerm_log_analytics_workspace" "logs" {
  name                = "${var.prefix}-logs"
  location            = azurerm_resource_group.lab.location
  resource_group_name = azurerm_resource_group.lab.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
  daily_quota_gb      = 0.1
  tags                = local.tags
}
resource "azurerm_container_app_environment" "apps" {
  name                           = "${var.prefix}-apps"
  location                       = azurerm_resource_group.lab.location
  resource_group_name            = azurerm_resource_group.lab.name
  log_analytics_workspace_id     = azurerm_log_analytics_workspace.logs.id
  infrastructure_subnet_id       = azurerm_subnet.apps.id
  internal_load_balancer_enabled = true
  public_network_access          = "Disabled"
  workload_profile {
    name                  = "Consumption"
    workload_profile_type = "Consumption"
  }
  tags = local.tags
}
resource "azurerm_private_dns_zone" "apps" {
  name                = azurerm_container_app_environment.apps.default_domain
  resource_group_name = azurerm_resource_group.lab.name
}
resource "azurerm_private_dns_zone_virtual_network_link" "apps" {
  name                = "container-apps-link"
  private_dns_zone_id = azurerm_private_dns_zone.apps.id
  virtual_network_id  = azurerm_virtual_network.lab.id
}
resource "azurerm_private_dns_a_record" "apps" {
  name                = "*"
  private_dns_zone_id = azurerm_private_dns_zone.apps.id
  ttl                 = 300
  records             = [azurerm_container_app_environment.apps.static_ip_address]
}

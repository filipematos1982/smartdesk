output "registry_login_server" { value = azurerm_container_registry.images.login_server }
output "database_fqdn" { value = azurerm_postgresql_flexible_server.database.fqdn }
output "key_vault_uri" { value = azurerm_key_vault.secrets.vault_uri }
output "private_app_domain" { value = azurerm_container_app_environment.apps.default_domain }

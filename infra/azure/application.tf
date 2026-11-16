resource "azurerm_container_app" "web" {
  count                        = var.deploy_application ? 1 : 0
  name                         = "${var.prefix}-web"
  resource_group_name          = azurerm_resource_group.lab.name
  container_app_environment_id = azurerm_container_app_environment.apps.id
  revision_mode                = "Single"
  workload_profile_name        = "Consumption"
  tags                         = local.tags
  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.app.id]
  }
  registry {
    server   = azurerm_container_registry.images.login_server
    identity = azurerm_user_assigned_identity.app.id
  }
  secret {
    name                = "database-password"
    identity            = azurerm_user_assigned_identity.app.id
    key_vault_secret_id = "${azurerm_key_vault.secrets.vault_uri}secrets/smartdesk-db-password/${var.runtime_password_secret_version}"
  }
  secret {
    name                = "session-signing-key"
    identity            = azurerm_user_assigned_identity.app.id
    key_vault_secret_id = "${azurerm_key_vault.secrets.vault_uri}secrets/smartdesk-session-secret/${var.session_secret_version}"
  }
  ingress {
    # External to this app's environment, but only on the environment's PRIVATE VNet IP.
    external_enabled           = true
    allow_insecure_connections = false
    target_port                = 8000
    transport                  = "http"
    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }
  template {
    min_replicas = 0
    max_replicas = 1
    container {
      name   = "web"
      image  = "${azurerm_container_registry.images.login_server}/smartdesk@${var.image_digest}"
      cpu    = 0.25
      memory = "0.5Gi"
      env {
        name  = "POSTGRES_HOST"
        value = azurerm_postgresql_flexible_server.database.fqdn
      }
      env {
        name  = "POSTGRES_PORT"
        value = "5432"
      }
      env {
        name  = "POSTGRES_DB"
        value = azurerm_postgresql_flexible_server_database.smartdesk.name
      }
      env {
        name  = "POSTGRES_USER"
        value = "smartdesk_app"
      }
      env {
        name        = "POSTGRES_PASSWORD"
        secret_name = "database-password"
      }
      env {
        name  = "PGSSLMODE"
        value = "verify-full"
      }
      env {
        name  = "PGSSLROOTCERT"
        value = "/etc/ssl/certs/ca-certificates.crt"
      }
      env {
        name  = "SMARTDESK_DB_CONNECT_TIMEOUT"
        value = "5"
      }
      env {
        name        = "SMARTDESK_SESSION_SECRET"
        secret_name = "session-signing-key"
      }
      env {
        name  = "SMARTDESK_COOKIE_SECURE"
        value = "true"
      }
      env {
        name  = "SMARTDESK_SESSION_MAX_AGE"
        value = "3600"
      }
      env {
        name  = "SMARTDESK_SEED_DEMO_USERS"
        value = "0"
      }
      startup_probe {
        transport               = "HTTP"
        port                    = 8000
        path                    = "/login"
        interval_seconds        = 5
        timeout                 = 3
        failure_count_threshold = 60
      }
      readiness_probe {
        transport               = "HTTP"
        port                    = 8000
        path                    = "/login"
        interval_seconds        = 10
        timeout                 = 3
        failure_count_threshold = 3
        success_count_threshold = 1
      }
      liveness_probe {
        transport               = "HTTP"
        port                    = 8000
        path                    = "/login"
        interval_seconds        = 30
        timeout                 = 3
        failure_count_threshold = 3
      }
    }
  }
  depends_on = [azurerm_role_assignment.image_pull, azurerm_role_assignment.secret_read]
  lifecycle {
    prevent_destroy = true
    precondition {
      condition     = can(regex("^sha256:[0-9a-f]{64}$", var.image_digest)) && can(regex("^[0-9a-f]{32}$", var.runtime_password_secret_version)) && can(regex("^[0-9a-f]{32}$", var.session_secret_version))
      error_message = "Application deployment requires a verified image digest and two existing versioned Key Vault secrets."
    }
  }
}

variable "subscription_id" {
  type        = string
  description = "Approved personal subscription UUID; placeholder until separately authorized."
}
variable "tenant_id" {
  type        = string
  description = "Approved personal tenant UUID; never infer from ambient Azure state."
}
variable "location" {
  type        = string
  default     = "westeurope"
  description = "Proposed pricing region, pending user approval and actual SKU/quota checks."
}
variable "prefix" {
  type        = string
  description = "Unique personal lab prefix used for globally unique registry, vault and server names."
  validation {
    condition     = can(regex("^[a-z][a-z0-9]{5,14}$", var.prefix))
    error_message = "Use 6-15 lowercase alphanumeric characters starting with a letter."
  }
}
variable "postgres_admin_password" {
  type        = string
  sensitive   = true
  ephemeral   = true
  description = "Future fresh administrative password; ephemeral input to the provider write-only argument, never committed."
}
variable "deploy_application" {
  type        = bool
  default     = false
  description = "False prepares foundation only; enable only after image, DB role and versioned secrets exist and deployment is approved."
}
variable "image_digest" {
  type        = string
  default     = ""
  description = "Verified sha256 digest of the linux/amd64 smartdesk image already published to this ACR."
  validation {
    condition     = var.image_digest == "" || can(regex("^sha256:[0-9a-f]{64}$", var.image_digest))
    error_message = "Supply a sha256 digest, never a mutable image tag."
  }
}
variable "runtime_password_secret_version" {
  type        = string
  default     = ""
  description = "Version ID of separately seeded smartdesk-db-password in the dedicated Key Vault."
}
variable "session_secret_version" {
  type        = string
  default     = ""
  description = "Version ID of separately seeded smartdesk-session-secret; retain across revisions."
}

variable "postgres_admin_password_version" {
  type        = number
  default     = 1
  description = "Increase only for an approved administrator password rotation; write-only input is not compared from state."
}

# PLACEHOLDERS ONLY. Backend creation and authentication are separate approvals.
# Copy to an ignored private location and confirm ownership before initialization.
resource_group_name  = "REPLACE_WITH_APPROVED_PERSONAL_STATE_RESOURCE_GROUP"
storage_account_name = "REPLACE_WITH_APPROVED_PERSONAL_STATE_ACCOUNT"
container_name       = "REPLACE_WITH_APPROVED_PRIVATE_STATE_CONTAINER"
key                  = "smartdesk/session5.tfstate"
use_azuread_auth     = true
# Select an explicitly approved personal authentication mechanism before use.
# Never place access keys, client secrets or tokens in this example or Git.

terraform {
  required_version = ">= 1.0"

  required_providers {
    routeros = {
      source  = "terraform-routeros/terraform-provider-routeros"
      version = "~> 1.0"
    }
  }
}

provider "routeros" {
  # Credentials sourced from environment variables or terraform.rc
  # TF_VAR_mikrotik_user, TF_VAR_mikrotik_password, TF_VAR_mikrotik_host
  # Or use .terraformrc provider_meta
}

# Alternative: use terraform pass for secrets
# terraform {
#   extra_arguments "mikrotik_secret" {
#     commands = ["apply"]
#   }
# }
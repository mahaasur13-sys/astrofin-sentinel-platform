# =============================================================================
# TERRAFORM BACKEND — S3 (MinIO)
# =============================================================================
# Uses the existing MinIO deployment as S3-compatible state backend.
#
# Prerequisites:
#   1. MinIO running with a "tf-state" bucket
#   2. Credentials via TF_VAR_minio_access_key / TF_VAR_minio_secret_key
#
# Migration from local backend:
#   make tf-backend-init
#
# Credentials (env vars recommended — never committed):
#   export TF_VAR_minio_access_key="your-key"
#   export TF_VAR_minio_secret_key="your-secret"
# =============================================================================

terraform {
  required_version = ">= 1.6"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # ── S3 Backend (MinIO) ──────────────────────────────────────
  backend "s3" {
    endpoint                    = "http://localhost:9000"
    bucket                       = "tf-state"
    key                          = "home-cluster/terraform.tfstate"
    region                       = "us-east-1"
    encrypt                      = true
    skip_credentials_validation  = true
    skip_metadata_api_check      = true
    skip_region_validation       = true
    force_path_style             = true
    dynamodb_table               = ""   # disabled — single-user / Velero handles DR
  }
}

# ── AWS Provider (MinIO as S3) ──────────────────────────────────────────────
# Used only for the S3 backend. Credentials via TF_VAR_minio_*.
# ──────────────────────────────────────────────────────────────────────────
provider "aws" {
  alias = "minio"

  endpoints {
    s3 = "http://localhost:9000"
  }

  region                      = "us-east-1"
  access_key                  = var.minio_access_key
  secret_key                 = var.minio_secret_key
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_region_validation      = true
  force_path_style            = true
}
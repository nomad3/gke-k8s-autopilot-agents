# GCS Backend for Terraform State
# This requires a pre-existing GCS bucket. Create it manually first:
# gcloud storage buckets create gs://YOUR-PROJECT-terraform-state --location=US

terraform {
  backend "gcs" {
    bucket = "ai-agency-479516-terraform-state" # Replace with your GCS bucket name
    # prefix = "gke-autopilot/state" # REMOVED: Use workspaces or pass -backend-config="prefix=..."

    # Note: GCS backend does not support native state locking.
    # Multiple concurrent applies could potentially corrupt state.
    # Best practices:
    # - Use CI/CD pipelines with concurrency controls
    # - Avoid manual applies when automation is running
    # - Consider using Terraform Cloud for built-in state locking
  }

  required_version = ">= 1.5.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }
}

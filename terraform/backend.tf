# GCS Backend for Terraform State
# This requires a pre-existing GCS bucket. Create it manually first:
# gcloud storage buckets create gs://YOUR-PROJECT-terraform-state --location=US

terraform {
  backend "gcs" {
    bucket = "YOUR-PROJECT-terraform-state" # Replace with your GCS bucket name
    # prefix = "gke-autopilot/state" # REMOVED: Use workspaces or pass -backend-config="prefix=..."
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
  }
}

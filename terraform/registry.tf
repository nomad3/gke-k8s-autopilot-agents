# Google Container Registry Configuration

# Enable Container Registry API
resource "google_project_service" "containerregistry" {
  project = var.project_id
  service = "containerregistry.googleapis.com"
# Storage bucket for Container Registry (automatically created)
# GCR uses Cloud Storage bucket: gs://artifacts.{project-id}.appspot.com

# IAM binding: GKE nodes can pull images
resource "google_project_iam_member" "gke_gcr_reader" {
  project = var.project_id
  role    = "roles/storage.objectViewer"
  member  = "serviceAccount:${module.gke.gke_sa_email}"
}

# ------------------------------
# Reference existing CI/CD Service Account
# ------------------------------
data "google_service_account" "cicd_sa" {
  account_id = var.environment == "prod" ? "terraform-prod-sa" : "terraform-dev-sa"
  project    = var.project_id
}

# Enable Artifact Registry API
resource "google_project_service" "artifactregistry" {
  project = var.project_id
  service = "artifactregistry.googleapis.com"
  disable_on_destroy = false
}

# Optional: Artifact Registry repository
resource "google_artifact_registry_repository" "docker_repo" {
  location      = var.region
  repository_id = "${var.environment}-docker-repo"
  description   = "Docker container registry for ${var.environment} environment"
  format        = "DOCKER"
  project       = var.project_id

  labels = merge(
    var.labels,
    {
      environment = var.environment
    }
  )

  cleanup_policy_dry_run = false

  cleanup_policies {
    id     = "keep-tagged-releases"
    action = "KEEP"
    condition {
      tag_state = "TAGGED"
    }
  }

  cleanup_policies {
    id     = "delete-old-untagged"
    action = "DELETE"
    condition {
      tag_state  = "UNTAGGED"
      older_than = "2592000s" # 30 days
    }
  }

  depends_on = [google_project_service.artifactregistry]
}

# IAM: GKE nodes can pull from Artifact Registry
resource "google_artifact_registry_repository_iam_member" "gke_ar_reader" {
  project    = var.project_id
  location   = var.region
  repository = google_artifact_registry_repository.docker_repo.name
  role       = "roles/artifactregistry.reader"
  member     = "serviceAccount:${module.gke.gke_sa_email}"
}

# IAM: CI/CD can push to Artifact Registry
resource "google_artifact_registry_repository_iam_member" "cicd_ar_writer" {
  project    = var.project_id
  location   = var.region
  repository = google_artifact_registry_repository.docker_repo.name
  role       = "roles/artifactregistry.writer"
  member     = "serviceAccount:${data.google_service_account.cicd_sa.email}"
}

# ------------------------------
# Outputs
# ------------------------------
output "gcr_hostname" {
  description = "Container Registry hostname"
  value       = "gcr.io/${var.project_id}"
}

output "artifact_registry_repository" {
  description = "Artifact Registry repository name"
  value       = google_artifact_registry_repository.docker_repo.name
}

output "artifact_registry_location" {
  description = "Artifact Registry location"
  value       = google_artifact_registry_repository.docker_repo.location
}

output "docker_image_path_gcr" {
  description = "Example Docker image path for GCR"
  value       = "gcr.io/${var.project_id}/IMAGE_NAME:TAG"
}

output "docker_image_path_ar" {
  description = "Example Docker image path for Artifact Registry"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker_repo.name}/IMAGE_NAME:TAG"
}



# ========================================
# IAM Configuration for GKE Autopilot and Application Workloads
# ========================================

# ----------------------------------------
# Reference Existing Service Accounts
# ----------------------------------------

# CI/CD Service Account (GitHub Actions)
data "google_service_account" "cicd_sa" {
  project    = var.project_id
  account_id = "github-actions-sa"
}

# Backend application service account (Terraform-managed)
data "google_service_account" "backend_app_sa" {
  project    = var.project_id
  account_id = "terraform-${var.environment}-sa"
}

# Frontend application service account (optional if exists)
data "google_service_account" "frontend_app_sa" {
  project    = var.project_id
  account_id = "terraform-${var.environment}-sa"
}

# Database application service account (Terraform-managed)
data "google_service_account" "database_app_sa" {
  project    = var.project_id
  account_id = "terraform-${var.environment}-sa"
}

# Backup service account (optional)
data "google_service_account" "backup_sa" {
  project    = var.project_id
  account_id = "terraform-${var.cluster_name}-backup"
}

# Monitoring service account (optional)
data "google_service_account" "monitoring_sa" {
  project    = var.project_id
  account_id = "terraform-${var.cluster_name}-mon"
}

# ========================================
# IAM Bindings
# ========================================

# CI/CD Bindings
resource "google_project_iam_member" "cicd_gke_developer" {
  project = var.project_id
  role    = "roles/container.developer"
  member  = "serviceAccount:${data.google_service_account.cicd_sa.email}"
}

resource "google_project_iam_member" "cicd_gcr_writer" {
  project = var.project_id
  role    = "roles/storage.objectCreator"
  member  = "serviceAccount:${data.google_service_account.cicd_sa.email}"
}

resource "google_project_iam_member" "cicd_artifact_registry_writer" {
  project = var.project_id
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${data.google_service_account.cicd_sa.email}"
}

# Backend app IAM
resource "google_project_iam_member" "backend_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${data.google_service_account.backend_app_sa.email}"
}

resource "google_project_iam_member" "backend_storage_object_admin" {
  project = var.project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${data.google_service_account.backend_app_sa.email}"
}

# Frontend app IAM (if needed)
resource "google_project_iam_member" "frontend_storage_viewer" {
  project = var.project_id
  role    = "roles/storage.objectViewer"
  member  = "serviceAccount:${data.google_service_account.frontend_app_sa.email}"
}

# Database app IAM
resource "google_project_iam_member" "database_cloudsql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${data.google_service_account.database_app_sa.email}"
}

# Backup IAM
resource "google_project_iam_member" "backup_storage_admin" {
  project = var.project_id
  role    = "roles/storage.admin"
  member  = "serviceAccount:${data.google_service_account.backup_sa.email}"
}

resource "google_project_iam_member" "backup_gke_admin" {
  project = var.project_id
  role    = "roles/gkebackup.admin"
  member  = "serviceAccount:${data.google_service_account.backup_sa.email}"
}

# Monitoring IAM
resource "google_project_iam_member" "monitoring_metric_writer" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${data.google_service_account.monitoring_sa.email}"
}

resource "google_project_iam_member" "monitoring_log_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${data.google_service_account.monitoring_sa.email}"
}

# ========================================
# Workload Identity Bindings (optional)
# ========================================

# Backend K8s SA -> GCP SA
resource "google_service_account_iam_member" "backend_workload_identity" {
  service_account_id = data.google_service_account.backend_app_sa.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "serviceAccount:${var.project_id}.svc.id.goog[backend/${var.environment}-backend-sa]"
}

# Frontend K8s SA -> GCP SA
resource "google_service_account_iam_member" "frontend_workload_identity" {
  service_account_id = data.google_service_account.frontend_app_sa.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "serviceAccount:${var.project_id}.svc.id.goog[frontend/${var.environment}-frontend-sa]"
}

# Database K8s SA -> GCP SA
resource "google_service_account_iam_member" "database_workload_identity" {
  service_account_id = data.google_service_account.database_app_sa.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "serviceAccount:${var.project_id}.svc.id.goog[database/${var.environment}-database-sa]"
}


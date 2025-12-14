# ========================================
# IAM Configuration for GKE Autopilot and Application Workloads
# ========================================

# ========================================
# Service Accounts for CI/CD Pipeline
# ========================================
resource "google_service_account" "cicd_sa" {
  account_id   = "${var.cluster_name}-cicd"
  display_name = "CI/CD Pipeline Service Account"
  description  = "Service account for GitHub Actions CI/CD pipeline"
  project      = var.project_id
}

# CI/CD IAM bindings
resource "google_project_iam_member" "cicd_gke_developer" {
  project = var.project_id
  role    = "roles/container.developer"
  member  = "serviceAccount:${google_service_account.cicd_sa.email}"
}

resource "google_project_iam_member" "cicd_gcr_writer" {
  project = var.project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${google_service_account.cicd_sa.email}"
}

resource "google_project_iam_member" "cicd_artifact_registry_writer" {
  project = var.project_id
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${google_service_account.cicd_sa.email}"
}

# ========================================
# Service Accounts for Application Pods (Workload Identity)
# ========================================
resource "google_service_account" "backend_app_sa" {
  account_id   = "${var.environment}-backend-app"
  display_name = "Backend Application Service Account"
  project      = var.project_id
}

resource "google_service_account" "frontend_app_sa" {
  account_id   = "${var.environment}-frontend-app"
  display_name = "Frontend Application Service Account"
  project      = var.project_id
}

resource "google_service_account" "database_app_sa" {
  account_id   = "${var.environment}-database-app"
  display_name = "Database Application Service Account"
  project      = var.project_id
}

# Workload Identity Bindings
# Workload Identity Bindings
resource "google_service_account_iam_member" "backend_workload_identity" {
  service_account_id = google_service_account.backend_app_sa.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "serviceAccount:${var.project_id}.svc.id.goog[backend/${var.environment}-backend-sa]"

  depends_on = [module.gke]
}

resource "google_service_account_iam_member" "frontend_workload_identity" {
  service_account_id = google_service_account.frontend_app_sa.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "serviceAccount:${var.project_id}.svc.id.goog[frontend/${var.environment}-frontend-sa]"

  depends_on = [module.gke]
}

resource "google_service_account_iam_member" "database_workload_identity" {
  service_account_id = google_service_account.database_app_sa.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "serviceAccount:${var.project_id}.svc.id.goog[database/${var.environment}-database-sa]"

  depends_on = [module.gke]
}

# Workload Identity for AgentProvision API
# This allows agentprovision-api K8s SA to use the backend app GCP SA
resource "google_service_account_iam_member" "agentprovision_api_workload_identity" {
  service_account_id = google_service_account.backend_app_sa.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "serviceAccount:${var.project_id}.svc.id.goog[${var.environment}/agentprovision-api]"

  depends_on = [module.gke]
}

# Workload Identity for AgentProvision Worker (disabled when replicaCount=0)
resource "google_service_account_iam_member" "agentprovision_worker_workload_identity" {
  count              = var.enable_agentprovision_worker ? 1 : 0
  service_account_id = google_service_account.backend_app_sa.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "serviceAccount:${var.project_id}.svc.id.goog[${var.environment}/agentprovision-worker]"

  depends_on = [module.gke]
}

# Application-specific IAM
resource "google_project_iam_member" "backend_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.backend_app_sa.email}"
}

resource "google_project_iam_member" "backend_storage_object_admin" {
  project = var.project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${google_service_account.backend_app_sa.email}"
}

resource "google_project_iam_member" "frontend_storage_viewer" {
  project = var.project_id
  role    = "roles/storage.objectViewer"
  member  = "serviceAccount:${google_service_account.frontend_app_sa.email}"
}

resource "google_project_iam_member" "database_cloudsql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.database_app_sa.email}"
}

# ========================================
# Backup and Monitoring Service Accounts
# ========================================
resource "google_service_account" "backup_sa" {
  account_id   = "${var.cluster_name}-backup"
  display_name = "Backup and Restore Service Account"
  project      = var.project_id
}

resource "google_project_iam_member" "backup_storage_admin" {
  project = var.project_id
  role    = "roles/storage.admin"
  member  = "serviceAccount:${google_service_account.backup_sa.email}"
}

resource "google_project_iam_member" "backup_gke_admin" {
  project = var.project_id
  role    = "roles/gkebackup.admin"
  member  = "serviceAccount:${google_service_account.backup_sa.email}"
}

resource "google_service_account" "monitoring_sa" {
  account_id   = "${var.cluster_name}-mon"
  display_name = "Monitoring Service Account"
  project      = var.project_id
}

resource "google_project_iam_member" "monitoring_metric_writer" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.monitoring_sa.email}"
}

resource "google_project_iam_member" "monitoring_log_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.monitoring_sa.email}"
}

# ========================================
# Optional Custom IAM Role
# ========================================
# resource "google_project_iam_custom_role" "app_minimal_role" {
#   role_id     = "appMinimalRole"
#   title       = "Application Minimal Role"
#   description = "Minimal permissions for application pods"
#   project     = var.project_id
#
#   permissions = [
#     "logging.logEntries.create",
#     "monitoring.timeSeries.create",
#   ]
# }

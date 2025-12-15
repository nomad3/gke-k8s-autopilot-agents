# Google Secret Manager Configuration

# Enable Secret Manager API
resource "google_project_service" "secretmanager" {
  project = var.project_id
  service = "secretmanager.googleapis.com"

  disable_on_destroy = false
}

# ========================================
# Deployment Service Account
# ========================================
data "google_service_account" "deployment_sa" {
  account_id = var.environment == "prod" ? "terraform-prod-sa" : "terraform-dev-sa"
  project    = var.project_id
}

# ========================================
# Application Secrets
# ========================================

# Database secrets managed in module.db

# JWT secret
resource "google_secret_manager_secret" "jwt_secret" {
  project   = var.project_id
  secret_id = "${var.environment}-jwt-secret"

  replication {
    auto {}
  }

  labels = merge(
    var.labels,
    {
      environment = var.environment
      component   = "backend"
    }
  )

  depends_on = [google_project_service.secretmanager]
}

# API keys secret
resource "google_secret_manager_secret" "api_keys" {
  project   = var.project_id
  secret_id = "${var.environment}-api-keys"

  replication {
    auto {}
  }

  labels = merge(
    var.labels,
    {
      environment = var.environment
      component   = "backend"
    }
  )

  depends_on = [google_project_service.secretmanager]
}

# TLS certificate (if not using Google-managed certs)
resource "google_secret_manager_secret" "tls_cert" {
  project   = var.project_id
  secret_id = "${var.environment}-tls-cert"

  replication {
    auto {}
  }

  labels = merge(
    var.labels,
    {
      environment = var.environment
      component   = "ingress"
    }
  )

  depends_on = [google_project_service.secretmanager]
}

resource "google_secret_manager_secret" "tls_key" {
  project   = var.project_id
  secret_id = "${var.environment}-tls-key"

  replication {
    auto {}
  }

  labels = merge(
    var.labels,
    {
      environment = var.environment
      component   = "ingress"
    }
  )

  depends_on = [google_project_service.secretmanager]
}

# ========================================
# IAM Permissions for Secret Access
# ========================================

# Grant Deployment SA access to secrets
resource "google_secret_manager_secret_iam_member" "deployment_sa_database_password" {
  project   = var.project_id
  secret_id = module.db.database_password_secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${data.google_service_account.deployment_sa.email}"
}

resource "google_secret_manager_secret_iam_member" "deployment_sa_database_url" {
  project   = var.project_id
  secret_id = module.db.database_url_secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${data.google_service_account.deployment_sa.email}"
}

resource "google_secret_manager_secret_iam_member" "deployment_sa_jwt_secret" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.jwt_secret.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${data.google_service_account.deployment_sa.email}"
}

resource "google_secret_manager_secret_iam_member" "deployment_sa_api_keys" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.api_keys.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${data.google_service_account.deployment_sa.email}"
}

# ========================================
# Outputs
# ========================================

output "secret_manager_secrets" {
  description = "Map of created secrets"
  value = {
    database_password = module.db.database_password_secret_id
    database_url      = module.db.database_url_secret_id
    jwt_secret        = google_secret_manager_secret.jwt_secret.id
    api_keys          = google_secret_manager_secret.api_keys.id
    tls_cert          = google_secret_manager_secret.tls_cert.id
    tls_key           = google_secret_manager_secret.tls_key.id
  }
}


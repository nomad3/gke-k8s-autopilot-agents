# Database credentials secret
resource "google_secret_manager_secret" "database_password" {
  project   = var.project_id
  secret_id = "${var.environment}-database-password"

  replication {
    auto {}
  }

  labels = merge(
    var.labels,
    {
      environment = var.environment
      component   = "database"
    }
  )
}

# Database connection string
resource "google_secret_manager_secret" "database_url" {
  project   = var.project_id
  secret_id = "${var.environment}-database-url"

  replication {
    auto {}
  }

  labels = merge(
    var.labels,
    {
      environment = var.environment
      component   = "database"
    }
  )
}

# Cloud SQL PostgreSQL Instance

# Reserve IP range for Cloud SQL private IP
resource "google_compute_global_address" "private_ip_address" {
  name          = "${var.environment}-postgres-ip-range"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = var.network_id
  project       = var.project_id
}

# Create VPC peering connection for Cloud SQL
resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = var.network_id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_address.name]
}

# Random password generation for database user
resource "random_password" "db_password" {
  length  = 32
  special = true
}

# Store password in Secret Manager
resource "google_secret_manager_secret_version" "database_password_version" {
  secret      = google_secret_manager_secret.database_password.id
  secret_data = random_password.db_password.result
}

# Cloud SQL PostgreSQL Instance
resource "google_sql_database_instance" "postgres" {
  name             = "${var.environment}-postgres-instance"
  database_version = var.db_version
  region           = var.region
  project          = var.project_id

  settings {
    tier              = var.db_tier
    availability_type = var.enable_ha ? "REGIONAL" : "ZONAL"
    disk_size         = var.db_storage_gb
    disk_autoresize   = true
    disk_type         = "PD_SSD"

    # Backup configuration
    backup_configuration {
      enabled                        = true
      start_time                     = "03:00"
      point_in_time_recovery_enabled = true
      transaction_log_retention_days = 7
      backup_retention_settings {
        retained_backups = 7
        retention_unit   = "COUNT"
      }
    }

    # IP configuration - Private IP only
    ip_configuration {
      ipv4_enabled    = false
      private_network = var.network_id
      require_ssl     = true
    }

    # Maintenance window
    maintenance_window {
      day          = 7 # Sunday
      hour         = 3
      update_track = "stable"
    }

    # Database flags for PostgreSQL optimization
    database_flags {
      name  = "max_connections"
      value = "100"
    }

    database_flags {
      name  = "shared_buffers"
      value = "20000" # 128MB in 8KB pages (Safe for db-g1-small)
    }

    database_flags {
      name  = "log_checkpoints"
      value = "on"
    }

    database_flags {
      name  = "log_connections"
      value = "on"
    }

    database_flags {
      name  = "log_disconnections"
      value = "on"
    }

    database_flags {
      name  = "log_lock_waits"
      value = "on"
    }

    # Resource labels
    user_labels = merge(
      var.labels,
      {
        environment = var.environment
        component   = "database"
      }
    )
  }

  deletion_protection = var.environment == "prod" ? true : false

  depends_on = [
    google_service_networking_connection.private_vpc_connection,
    google_secret_manager_secret_version.database_password_version
  ]
}

# Database user
resource "google_sql_user" "db_user" {
  name     = "${var.environment}-db-user"
  instance = google_sql_database_instance.postgres.name
  password = random_password.db_password.result
  project  = var.project_id
}

# Default database
resource "google_sql_database" "default_db" {
  name     = "${var.environment}-app-db"
  instance = google_sql_database_instance.postgres.name
  project  = var.project_id
}

# Store database URL in Secret Manager
resource "google_secret_manager_secret_version" "database_url_version" {
  secret = google_secret_manager_secret.database_url.id
  secret_data = format(
    "postgresql://%s:%s@%s/%s",
    google_sql_user.db_user.name,
    random_password.db_password.result,
    google_sql_database_instance.postgres.private_ip_address,
    google_sql_database.default_db.name
  )
}

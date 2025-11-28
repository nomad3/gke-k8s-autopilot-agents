output "database_password_secret_id" {
  description = "The secret ID for the database password"
  value       = google_secret_manager_secret.database_password.id
}

output "database_url_secret_id" {
  description = "The secret ID for the database URL"
  value       = google_secret_manager_secret.database_url.id
}

output "database_password_secret_name" {
  description = "The secret name for the database password"
  value       = google_secret_manager_secret.database_password.secret_id
}

output "database_url_secret_name" {
  description = "The secret name for the database URL"
  value       = google_secret_manager_secret.database_url.secret_id
}

output "instance_connection_name" {
  description = "The connection name of the Cloud SQL instance"
  value       = google_sql_database_instance.postgres.connection_name
}

output "private_ip" {
  description = "The private IP address of the Cloud SQL instance"
  value       = google_sql_database_instance.postgres.private_ip_address
}

output "database_user_name" {
  description = "The database user name"
  value       = google_sql_user.db_user.name
}

output "database_name" {
  description = "The default database name"
  value       = google_sql_database.default_db.name
}

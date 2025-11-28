# Cloud DNS Managed Zone and Records

# Create DNS Managed Zone
resource "google_dns_managed_zone" "main" {
  name        = "${var.environment}-${replace(var.domain_name, ".", "-")}-zone"
  dns_name    = "${var.domain_name}."
  description = "Managed zone for ${var.domain_name} (${var.environment})"
  project     = var.project_id

  labels = merge(
    var.labels,
    {
      environment = var.environment
      managed_by  = "terraform"
    }
  )

  dnssec_config {
    state = "on"
  }
}

# Create A records pointing to Gateway IP
resource "google_dns_record_set" "a_records" {
  for_each = { for record in var.dns_records : record.name => record }

  name         = "${each.value.name}.${var.domain_name}."
  type         = "A"
  ttl          = each.value.ttl
  managed_zone = google_dns_managed_zone.main.name
  project      = var.project_id

  rrdatas = [var.gateway_ip]
}

# Create root domain A record if gateway_ip is provided
resource "google_dns_record_set" "root" {
  count = var.gateway_ip != "" ? 1 : 0

  name         = "${var.domain_name}."
  type         = "A"
  ttl          = 300
  managed_zone = google_dns_managed_zone.main.name
  project      = var.project_id

  rrdatas = [var.gateway_ip]
}

# DNS Module Outputs

output "zone_name" {
  description = "Name of the DNS managed zone"
  value       = google_dns_managed_zone.main.name
}

output "zone_dns_name" {
  description = "DNS name of the managed zone"
  value       = google_dns_managed_zone.main.dns_name
}

output "name_servers" {
  description = "List of name servers for the managed zone"
  value       = google_dns_managed_zone.main.name_servers
}

output "dns_records" {
  description = "Map of created DNS records"
  value = {
    for k, v in google_dns_record_set.a_records : k => {
      name = v.name
      type = v.type
      ttl  = v.ttl
    }
  }
}

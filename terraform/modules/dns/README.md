# DNS Module README

This module manages Cloud DNS zones and records for the GKE Autopilot cluster.

## Features

- Creates a Cloud DNS managed zone
- Configures DNSSEC for enhanced security
- Creates A records pointing to the Gateway load balancer
- Supports multiple DNS records per zone

## Usage

### Enable DNS in Terraform

In your `terraform.tfvars`:

```hcl
enable_dns  = true
domain_name = "example.com"
gateway_ip  = "34.120.0.1"  # IP from Gateway

dns_records = [
  {
    name = "api"
    ttl  = 300
  },
  {
    name = "www"
    ttl  = 300
  }
]
```

### Deploy

```bash
terraform apply
```

### Update Nameservers

After deployment, get the nameservers:

```bash
terraform output dns_name_servers
```

Update your domain registrar to use these nameservers.

## Variables

| Variable | Description | Type | Default |
|----------|-------------|------|---------|
| `project_id` | GCP Project ID | string | required |
| `domain_name` | Primary domain name | string | required |
| `environment` | Environment name | string | required |
| `dns_records` | List of DNS records | list(object) | `[]` |
| `gateway_ip` | Gateway IP address | string | `""` |
| `labels` | Resource labels | map(string) | `{}` |

## Outputs

| Output | Description |
|--------|-------------|
| `zone_name` | DNS managed zone name |
| `zone_dns_name` | DNS name of the zone |
| `name_servers` | Nameservers for the zone |
| `dns_records` | Created DNS records |

## Cost

- $0.20 per hosted zone per month
- $0.40 per million queries
- Typically ~$1-2/month for small deployments

## Notes

- DNSSEC is enabled by default for security
- You must update your domain registrar's nameservers
- DNS propagation can take 24-48 hours
